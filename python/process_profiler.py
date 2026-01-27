#!/usr/bin/env python3
"""
Process Profiler & Intelligent Selector (NO psutil dependency)
Uses /proc filesystem directly for all process information
"""

import os
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import List, Dict, Optional
import numpy as np


@dataclass
class ProcessProfile:
    """Detailed process profile for scheduling decisions"""
    pid: int
    name: str
    cpu_percent: float
    cpu_time: float
    memory_percent: float
    num_threads: int
    io_read_bytes: int
    io_write_bytes: int
    ctx_switches_voluntary: int
    ctx_switches_involuntary: int
    nice: int
    status: str
    priority: int
    create_time: float
    
    # Derived metrics
    cpu_variance: float = 0.0
    io_intensity: float = 0.0
    interactivity_score: float = 0.0
    resource_consumption: float = 0.0


class ProcessClassifier:
    """Classify processes by workload type"""
    
    WORKLOAD_TYPES = {
        'CPU_INTENSIVE': 0,
        'IO_INTENSIVE': 1,
        'INTERACTIVE': 2,
        'BACKGROUND': 3,
        'MIXED': 4
    }
    
    @staticmethod
    def classify(profile: ProcessProfile, history: List[float]) -> str:
        """Classify process workload type"""
        
        # CPU-intensive: High CPU, low I/O
        if profile.cpu_percent > 70 and profile.io_intensity < 0.3:
            return 'CPU_INTENSIVE'
        
        # I/O-intensive: High I/O
        if profile.io_intensity > 0.6:
            return 'IO_INTENSIVE'
        
        # Interactive: High voluntary context switches, bursty CPU
        if profile.ctx_switches_voluntary > 100 and profile.cpu_variance > 10:
            return 'INTERACTIVE'
        
        # Background: Low priority or low resource usage
        if profile.nice > 5 or profile.cpu_percent < 5:
            return 'BACKGROUND'
        
        return 'MIXED'
    
    @staticmethod
    def get_optimal_policy(workload_type: str) -> str:
        """Get optimal scheduler policy for workload type"""
        policies = {
            'CPU_INTENSIVE': 'SCHED_BATCH',
            'IO_INTENSIVE': 'SCHED_OTHER',
            'INTERACTIVE': 'SCHED_OTHER',
            'BACKGROUND': 'SCHED_IDLE',
            'MIXED': 'SCHED_OTHER'
        }
        return policies.get(workload_type, 'SCHED_OTHER')
    
    @staticmethod
    def get_optimal_nice(workload_type: str) -> int:
        """Get optimal nice value for workload type"""
        nice_values = {
            'CPU_INTENSIVE': 5,      # Lower priority for CPU hogs
            'IO_INTENSIVE': 0,       # Normal priority
            'INTERACTIVE': -5,       # Higher priority for responsiveness
            'BACKGROUND': 15,        # Very low priority
            'MIXED': 0
        }
        return nice_values.get(workload_type, 0)


class ProcessProfiler:
    """Profile and track processes using /proc filesystem directly"""
    
    def __init__(self, history_size=100, min_cpu_threshold=1.0):
        self.history_size = history_size
        self.min_cpu_threshold = min_cpu_threshold
        
        # Process history tracking
        self.process_history: Dict[int, deque] = defaultdict(
            lambda: deque(maxlen=history_size)
        )
        
        # Process profiles cache
        self.profiles_cache: Dict[int, ProcessProfile] = {}
        
        # Previous CPU times for calculating usage
        self.prev_cpu_times: Dict[int, tuple] = {}
        self.prev_measure_time = time.time()
        
        # Tracking metrics
        self.total_processes = 0
        self.tracked_processes = set()
        
        # Classification cache
        self.workload_classifications: Dict[int, str] = {}
        
        # System info
        self.num_cpus = self._get_num_cpus()
        self.total_memory = self._get_total_memory()
        self.page_size = 4096  # Standard page size
        
    def _get_num_cpus(self) -> int:
        """Get number of CPU cores from /proc/cpuinfo"""
        try:
            with open('/proc/cpuinfo', 'r') as f:
                return sum(1 for line in f if line.startswith('processor'))
        except:
            return 1
    
    def _get_total_memory(self) -> int:
        """Get total system memory from /proc/meminfo"""
        try:
            with open('/proc/meminfo', 'r') as f:
                for line in f:
                    if line.startswith('MemTotal:'):
                        return int(line.split()[1]) * 1024  # Convert KB to bytes
        except:
            return 8 * 1024 * 1024 * 1024  # Default 8GB
    
    def _read_proc_stat(self, pid: int) -> Optional[Dict]:
        """Read /proc/[pid]/stat"""
        try:
            with open(f'/proc/{pid}/stat', 'r') as f:
                content = f.read()
                
            # Split by last ) to handle process names with spaces
            parts = content.split(')')
            if len(parts) < 2:
                return None
            
            fields = parts[1].strip().split()
            
            return {
                'pid': pid,
                'comm': parts[0].split('(')[1],  # Process name
                'state': fields[0],
                'priority': int(fields[15]),
                'nice': int(fields[16]),
                'num_threads': int(fields[17]),
                'utime': int(fields[11]),  # User mode jiffies
                'stime': int(fields[12]),  # Kernel mode jiffies
                'cutime': int(fields[13]),  # Children user time
                'cstime': int(fields[14]),  # Children kernel time
            }
        except (FileNotFoundError, PermissionError, IndexError, ValueError):
            return None
    
    def _read_proc_status(self, pid: int) -> Optional[Dict]:
        """Read /proc/[pid]/status"""
        try:
            data = {}
            with open(f'/proc/{pid}/status', 'r') as f:
                for line in f:
                    if ':' in line:
                        key, value = line.split(':', 1)
                        data[key.strip()] = value.strip()
            return data
        except (FileNotFoundError, PermissionError):
            return None
    
    def _read_proc_io(self, pid: int) -> Optional[Dict]:
        """Read /proc/[pid]/io"""
        try:
            data = {}
            with open(f'/proc/{pid}/io', 'r') as f:
                for line in f:
                    if ':' in line:
                        key, value = line.split(':', 1)
                        data[key.strip()] = int(value.strip())
            return data
        except (FileNotFoundError, PermissionError, ValueError):
            return {'read_bytes': 0, 'write_bytes': 0}
    
    def _parse_memory(self, status_data: Dict) -> float:
        """Parse memory usage from status"""
        try:
            # VmRSS is resident set size (actual physical memory)
            vmrss = status_data.get('VmRSS', '0 kB')
            mem_kb = int(vmrss.split()[0])
            mem_bytes = mem_kb * 1024
            return (mem_bytes / self.total_memory) * 100.0
        except:
            return 0.0
    
    def _parse_ctx_switches(self, status_data: Dict) -> tuple:
        """Parse voluntary and involuntary context switches"""
        try:
            vol = int(status_data.get('voluntary_ctxt_switches', '0'))
            invol = int(status_data.get('nonvoluntary_ctxt_switches', '0'))
            return vol, invol
        except:
            return 0, 0
    
    def get_process_list(self) -> List[int]:
        """Get list of active process PIDs"""
        pids = []
        try:
            for entry in os.listdir('/proc'):
                if entry.isdigit():
                    pid = int(entry)
                    if pid > 100:  # Skip kernel threads
                        pids.append(pid)
        except PermissionError:
            pass
        return pids
    
    def _calculate_cpu_percent(self, pid: int, stat_data: Dict) -> float:
        """Calculate CPU percentage for a process"""
        current_time = time.time()
        
        # Total CPU time (user + system)
        total_time = stat_data['utime'] + stat_data['stime']
        
        if pid in self.prev_cpu_times:
            prev_total, prev_time = self.prev_cpu_times[pid]
            
            time_delta = current_time - prev_time
            cpu_delta = total_time - prev_total
            
            if time_delta > 0:
                # CPU usage = (delta_cpu_time / delta_real_time) / num_cpus * 100
                # Jiffies to seconds: divide by 100 (USER_HZ)
                cpu_percent = (cpu_delta / 100.0 / time_delta) * 100.0
                cpu_percent = min(cpu_percent, 100.0 * self.num_cpus)  # Cap at num_cpus * 100
            else:
                cpu_percent = 0.0
        else:
            cpu_percent = 0.0
        
        # Update previous
        self.prev_cpu_times[pid] = (total_time, current_time)
        
        return cpu_percent
    
    def profile_process(self, pid: int) -> Optional[ProcessProfile]:
        """Create detailed profile of a process"""
        try:
            stat_data = self._read_proc_stat(pid)
            if not stat_data:
                return None
            
            status_data = self._read_proc_status(pid)
            if not status_data:
                return None
            
            io_data = self._read_proc_io(pid)
            
            # Calculate metrics
            cpu_percent = self._calculate_cpu_percent(pid, stat_data)
            
            # Skip low CPU processes
            if cpu_percent < self.min_cpu_threshold:
                return None
            
            memory_percent = self._parse_memory(status_data)
            ctx_vol, ctx_invol = self._parse_ctx_switches(status_data)
            
            cpu_time_total = (stat_data['utime'] + stat_data['stime']) / 100.0  # Convert jiffies to seconds
            
            # Get historical CPU variance
            if pid in self.process_history:
                history = list(self.process_history[pid])
                cpu_variance = np.var(history) if len(history) > 5 else 0.0
            else:
                cpu_variance = 0.0
            
            # Calculate I/O intensity
            io_total = io_data.get('read_bytes', 0) + io_data.get('write_bytes', 0)
            io_intensity = min(io_total / (1024 * 1024 * 100), 1.0)
            
            # Interactivity score
            interactivity_score = min((ctx_vol / 1000.0) * (cpu_variance / 20.0), 1.0) if cpu_variance > 0 else 0.0
            
            # Resource consumption
            resource_consumption = (cpu_percent / 100.0) * 0.6 + (memory_percent / 100.0) * 0.4
            
            profile = ProcessProfile(
                pid=pid,
                name=stat_data['comm'],
                cpu_percent=cpu_percent,
                cpu_time=cpu_time_total,
                memory_percent=memory_percent,
                num_threads=stat_data['num_threads'],
                io_read_bytes=io_data.get('read_bytes', 0),
                io_write_bytes=io_data.get('write_bytes', 0),
                ctx_switches_voluntary=ctx_vol,
                ctx_switches_involuntary=ctx_invol,
                nice=stat_data['nice'],
                status=stat_data['state'],
                priority=stat_data['priority'],
                num_fds=0,  # Would need to count /proc/[pid]/fd entries
                create_time=time.time(),  # Approximate
                cpu_variance=cpu_variance,
                io_intensity=io_intensity,
                interactivity_score=interactivity_score,
                resource_consumption=resource_consumption
            )
            
            # Update history
            self.process_history[pid].append(cpu_percent)
            self.profiles_cache[pid] = profile
            self.tracked_processes.add(pid)
            
            return profile
            
        except Exception as e:
            return None
    
    def get_schedulable_processes(self, top_k=10) -> List[ProcessProfile]:
        """Get top K processes that should be scheduled"""
        pids = self.get_process_list()
        profiles = []
        
        for pid in pids:
            profile = self.profile_process(pid)
            if profile:
                profiles.append(profile)
        
        # Sort by resource consumption
        profiles.sort(key=lambda p: p.resource_consumption, reverse=True)
        
        return profiles[:top_k]
    
    def classify_and_recommend(self, profile: ProcessProfile) -> Dict:
        """Classify process and recommend scheduling action"""
        history = list(self.process_history.get(profile.pid, []))
        
        workload_type = ProcessClassifier.classify(profile, history)
        optimal_policy = ProcessClassifier.get_optimal_policy(workload_type)
        optimal_nice = ProcessClassifier.get_optimal_nice(workload_type)
        
        self.workload_classifications[profile.pid] = workload_type
        
        return {
            'pid': profile.pid,
            'name': profile.name,
            'workload_type': workload_type,
            'current_nice': profile.nice,
            'recommended_nice': optimal_nice,
            'current_policy': 'SCHED_OTHER',
            'recommended_policy': optimal_policy,
            'cpu_percent': profile.cpu_percent,
            'resource_score': profile.resource_consumption,
            'should_adjust': abs(profile.nice - optimal_nice) > 2
        }
    
    def get_system_state_vector(self) -> np.ndarray:
        """Get comprehensive system state for RL agent"""
        profiles = self.get_schedulable_processes(top_k=5)
        
        # Aggregate metrics
        total_cpu = sum(p.cpu_percent for p in profiles)
        avg_cpu = total_cpu / len(profiles) if profiles else 0
        max_cpu = max([p.cpu_percent for p in profiles], default=0)
        
        total_mem = sum(p.memory_percent for p in profiles)
        avg_io = sum(p.io_intensity for p in profiles) / len(profiles) if profiles else 0
        
        # Workload distribution
        workload_counts = defaultdict(int)
        for p in profiles:
            wtype = self.workload_classifications.get(p.pid, 'MIXED')
            workload_counts[wtype] += 1
        
        cpu_intensive_count = workload_counts['CPU_INTENSIVE']
        io_intensive_count = workload_counts['IO_INTENSIVE']
        interactive_count = workload_counts['INTERACTIVE']
        
        # System-wide metrics from /proc
        system_cpu = self._get_system_cpu()
        system_mem = self._get_system_memory()
        load_avg = self._get_load_avg()
        ctx_switches = self._get_context_switches()
        
        state_vector = np.array([
            system_cpu / 100.0,
            system_mem / 100.0,
            load_avg / self.num_cpus,
            ctx_switches / 10000.0,
            avg_cpu / 100.0,
            max_cpu / 100.0,
            avg_io,
            cpu_intensive_count / 5.0,
            io_intensive_count / 5.0,
            interactive_count / 5.0,
            len(profiles) / 10.0,
            total_mem / 100.0,
        ], dtype=np.float32)
        
        return state_vector
    
    def _get_system_cpu(self) -> float:
        """Get system-wide CPU usage from /proc/stat"""
        try:
            with open('/proc/stat', 'r') as f:
                line = f.readline()
            
            fields = line.split()
            user = int(fields[1])
            nice = int(fields[2])
            system = int(fields[3])
            idle = int(fields[4])
            
            total = user + nice + system + idle
            used = user + nice + system
            
            return (used / total * 100.0) if total > 0 else 0.0
        except:
            return 0.0
    
    def _get_system_memory(self) -> float:
        """Get system memory usage from /proc/meminfo"""
        try:
            with open('/proc/meminfo', 'r') as f:
                lines = f.readlines()
            
            mem_total = 0
            mem_available = 0
            
            for line in lines:
                if line.startswith('MemTotal:'):
                    mem_total = int(line.split()[1])
                elif line.startswith('MemAvailable:'):
                    mem_available = int(line.split()[1])
            
            if mem_total > 0:
                used = mem_total - mem_available
                return (used / mem_total * 100.0)
        except:
            pass
        return 0.0
    
    def _get_load_avg(self) -> float:
        """Get load average from /proc/loadavg"""
        try:
            with open('/proc/loadavg', 'r') as f:
                return float(f.read().split()[0])
        except:
            return 0.0
    
    def _get_context_switches(self) -> int:
        """Get context switches from /proc/stat"""
        try:
            with open('/proc/stat', 'r') as f:
                for line in f:
                    if line.startswith('ctxt'):
                        return int(line.split()[1])
        except:
            pass
        return 0
    
    def get_action_target(self, action_id: int) -> Optional[Dict]:
        """Get target process for action"""
        profiles = self.get_schedulable_processes(top_k=10)
        
        if not profiles:
            return None
        
        if action_id == 0:
            return None
        
        elif action_id == 1:  # REDUCE_NICE
            targets = [p for p in profiles if p.cpu_percent > 50 and p.nice < 5]
            if targets:
                return {'pid': targets[0].pid, 'name': targets[0].name, 'nice_delta': 5}
        
        elif action_id == 2:  # INCREASE_NICE
            targets = [p for p in profiles if p.nice > -5 and p.cpu_percent < 30]
            if targets:
                return {'pid': targets[-1].pid, 'name': targets[-1].name, 'nice_delta': -5}
        
        elif action_id == 3:  # SET_SCHED_BATCH
            targets = [p for p in profiles 
                      if p.cpu_percent > 60 and p.ctx_switches_voluntary < 50]
            if targets:
                return {'pid': targets[0].pid, 'name': targets[0].name, 'policy': 'SCHED_BATCH'}
        
        elif action_id == 4:  # SET_SCHED_OTHER
            targets = [p for p in profiles if p.interactivity_score > 0.4]
            if targets:
                return {'pid': targets[0].pid, 'name': targets[0].name, 'policy': 'SCHED_OTHER'}
        
        return None
    
    def get_statistics(self) -> Dict:
        """Get profiling statistics"""
        return {
            'total_tracked': len(self.tracked_processes),
            'currently_active': len(self.profiles_cache),
            'workload_distribution': dict(
                (k, v) for k, v in 
                defaultdict(int, 
                    ((wtype, 1) for wtype in self.workload_classifications.values())
                ).items()
            ),
            'avg_cpu': np.mean([p.cpu_percent for p in self.profiles_cache.values()]) 
                      if self.profiles_cache else 0,
        }


if __name__ == '__main__':
    profiler = ProcessProfiler()
    
    print("Process Profiler Test (NO psutil)")
    print("=" * 80)
    
    # Wait a bit to collect CPU data
    time.sleep(2)
    
    profiles = profiler.get_schedulable_processes(top_k=10)
    
    print(f"\nFound {len(profiles)} schedulable processes:\n")
    
    for i, profile in enumerate(profiles[:5], 1):
        rec = profiler.classify_and_recommend(profile)
        print(f"{i}. {profile.name} (PID {profile.pid})")
        print(f"   CPU: {profile.cpu_percent:.1f}% | Mem: {profile.memory_percent:.1f}%")
        print(f"   Workload: {rec['workload_type']}")
        print(f"   Nice: {profile.nice} → {rec['recommended_nice']}")
        print()
    
    print("System State Vector:")
    state = profiler.get_system_state_vector()
    print(state)