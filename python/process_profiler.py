#!/usr/bin/env python3
"""
Process Profiler for DQN CPU Scheduler
NO EXTERNAL DEPENDENCIES - Uses /proc filesystem only
"""

import os
import time
from collections import defaultdict

class ProcessProfiler:
    def __init__(self):
        self.process_history = defaultdict(list)
        self.max_history = 10
        self._last_cpu_times = {}
        
    def get_high_cpu_processes(self, min_cpu=5.0, limit=10):
        """
        Get processes with high CPU usage using /proc filesystem
        
        Args:
            min_cpu: Minimum CPU percentage to consider (default: 5.0)
            limit: Maximum number of processes to return (default: 10)
            
        Returns:
            List of process dictionaries with pid, name, cpu_usage, type, nice
        """
        processes = []
        
        try:
            # Get list of all process PIDs
            pids = [int(d) for d in os.listdir('/proc') if d.isdigit()]
            
            for pid in pids:
                try:
                    # Read process info
                    proc_info = self._get_process_info(pid)
                    
                    if proc_info is None:
                        continue
                    
                    cpu_percent = proc_info.get('cpu_usage', 0)
                    
                    # Skip if CPU usage too low
                    if cpu_percent < min_cpu:
                        continue
                    
                    # Skip kernel threads and system processes
                    name = proc_info.get('name', '')
                    if name in ['systemd', 'init', 'kthreadd', 'migration', 'ksoftirqd', 'kworker']:
                        continue
                    
                    # Classify process type
                    proc_type = self._classify_process(name, cpu_percent)
                    
                    processes.append({
                        'pid': pid,
                        'name': name,
                        'cpu_usage': cpu_percent,
                        'nice': proc_info.get('nice', 0),
                        'type': proc_type,
                        'threads': proc_info.get('threads', 1)
                    })
                    
                except (FileNotFoundError, PermissionError, ProcessLookupError):
                    # Process ended or we don't have permission
                    continue
                except Exception:
                    # Skip problematic processes
                    continue
        
        except Exception as e:
            print(f"[ProcessProfiler] Error: {e}")
            return []
        
        # Sort by CPU usage (highest first) and limit
        processes.sort(key=lambda x: x['cpu_usage'], reverse=True)
        return processes[:limit]
    
    def _get_process_info(self, pid):
        """
        Get process information from /proc/[pid]/
        
        Args:
            pid: Process ID
            
        Returns:
            Dictionary with process info or None
        """
        try:
            # Read /proc/[pid]/stat
            with open(f'/proc/{pid}/stat', 'r') as f:
                stat = f.read().strip()
            
            # Parse stat file
            # Format: pid (comm) state ppid pgrp session tty_nr tpgid flags ...
            # Find the last ')' to split correctly (comm can contain spaces and parens)
            comm_end = stat.rfind(')')
            if comm_end == -1:
                return None
            
            name = stat[stat.find('(') + 1:comm_end]
            stat_parts = stat[comm_end + 2:].split()
            
            if len(stat_parts) < 20:
                return None
            
            # Extract values (indices adjusted after splitting)
            utime = int(stat_parts[11])  # User time
            stime = int(stat_parts[12])  # System time
            nice = int(stat_parts[16])   # Nice value
            num_threads = int(stat_parts[17])  # Number of threads
            
            # Calculate CPU usage
            cpu_usage = self._calculate_cpu_usage(pid, utime + stime)
            
            return {
                'name': name,
                'cpu_usage': cpu_usage,
                'nice': nice,
                'threads': num_threads
            }
            
        except (FileNotFoundError, PermissionError, ValueError, IndexError):
            return None
    
    def _calculate_cpu_usage(self, pid, total_time):
        """
        Calculate CPU usage percentage for a process
        
        Args:
            pid: Process ID
            total_time: Total CPU time (utime + stime)
            
        Returns:
            CPU usage percentage
        """
        current_time = time.time()
        
        # Get previous measurement
        if pid in self._last_cpu_times:
            last_time, last_total = self._last_cpu_times[pid]
            time_delta = current_time - last_time
            cpu_delta = total_time - last_total
            
            if time_delta > 0:
                # CPU time is in clock ticks (typically 100 per second)
                # Convert to percentage
                cpu_percent = (cpu_delta / (time_delta * 100)) * 100
                
                # Store current measurement
                self._last_cpu_times[pid] = (current_time, total_time)
                
                return min(100.0, max(0.0, cpu_percent))
        
        # First measurement, store and return 0
        self._last_cpu_times[pid] = (current_time, total_time)
        return 0.0
    
    def _classify_process(self, name, cpu_percent):
        """
        Classify process type based on name and CPU usage
        
        Args:
            name: Process name
            cpu_percent: Current CPU usage percentage
            
        Returns:
            String classification
        """
        name_lower = name.lower()
        
        # CPU-intensive applications
        cpu_intensive = ['python', 'gcc', 'g++', 'clang', 'rustc', 'cargo',
                        'make', 'cmake', 'javac', 'java', 'node', 'npm',
                        'ffmpeg', 'convert', 'blender', 'stress', 'sysbench']
        
        # I/O-bound applications
        io_bound = ['rsync', 'cp', 'mv', 'tar', 'zip', 'dd', 'sync',
                   'postgres', 'mysql', 'mongo', 'redis', 'docker']
        
        # Interactive applications
        interactive = ['chrome', 'firefox', 'code', 'vim', 'emacs',
                      'terminal', 'gnome', 'kde', 'xorg']
        
        # Check keywords
        for keyword in cpu_intensive:
            if keyword in name_lower:
                return 'CPU-Intensive'
        
        for keyword in io_bound:
            if keyword in name_lower:
                return 'I/O-Bound'
        
        for keyword in interactive:
            if keyword in name_lower:
                return 'Interactive'
        
        # Heuristic based on CPU
        if cpu_percent > 70:
            return 'CPU-Intensive'
        elif cpu_percent > 40:
            return 'Mixed'
        else:
            return 'I/O-Bound'
    
    def get_process_stats(self, pid):
        """Get detailed statistics for a specific process"""
        return self._get_process_info(pid)
    
    def get_cpu_intensive_pids(self, threshold=50.0):
        """Get PIDs of CPU-intensive processes"""
        processes = self.get_high_cpu_processes(min_cpu=threshold)
        return [p['pid'] for p in processes]
    
    def get_system_load(self):
        """Get overall system load from /proc"""
        try:
            cpu_count = os.cpu_count() or 1
            
            # Read load average
            with open('/proc/loadavg', 'r') as f:
                load_data = f.read().strip().split()
            
            # Calculate CPU percentage
            with open('/proc/stat', 'r') as f:
                line = f.readline()
            
            parts = line.split()
            if parts[0] == 'cpu':
                user = int(parts[1])
                nice = int(parts[2])
                system = int(parts[3])
                idle = int(parts[4])
                
                total = user + nice + system + idle
                active = user + nice + system
                cpu_percent = (active / total * 100) if total > 0 else 0
            else:
                cpu_percent = 0
            
            return {
                'cpu_percent': cpu_percent,
                'cpu_count': cpu_count,
                'load_avg_1min': float(load_data[0]),
                'load_avg_5min': float(load_data[1]),
                'load_avg_15min': float(load_data[2])
            }
            
        except Exception:
            return {
                'cpu_percent': 0,
                'cpu_count': 1,
                'load_avg_1min': 0,
                'load_avg_5min': 0,
                'load_avg_15min': 0
            }
    
    def monitor_processes(self, pids, interval=1.0):
        """Monitor a list of processes"""
        results = {}
        for pid in pids:
            stats = self.get_process_stats(pid)
            if stats:
                results[pid] = stats
        return results

# Test function
def test_profiler():
    """Test the process profiler"""
    print("Testing ProcessProfiler (no dependencies)...")
    print("=" * 60)
    
    profiler = ProcessProfiler()
    
    print("\n1. High CPU processes:")
    print("-" * 60)
    
    # Two measurements for accurate CPU
    profiler.get_high_cpu_processes(min_cpu=0.1, limit=20)
    time.sleep(1)
    
    processes = profiler.get_high_cpu_processes(min_cpu=0.1, limit=10)
    
    if processes:
        for proc in processes:
            print(f"  PID: {proc['pid']:6d} | "
                  f"Name: {proc['name']:20s} | "
                  f"CPU: {proc['cpu_usage']:5.1f}% | "
                  f"Type: {proc['type']}")
    else:
        print("  No high CPU processes found")
    
    print("\n2. System load:")
    print("-" * 60)
    load = profiler.get_system_load()
    print(f"  CPU: {load['cpu_percent']:.1f}%")
    print(f"  CPUs: {load['cpu_count']}")
    print(f"  Load: {load['load_avg_1min']:.2f}")
    
    print("\n" + "=" * 60)
    print("Test complete! Pure Python + /proc")

if __name__ == "__main__":
    test_profiler()