#!/usr/bin/env python3
"""
Real-Time Monitoring & Comparison System
Live side-by-side comparison of baseline vs RL-optimized performance
with comprehensive metrics tracking and export capabilities
"""

import os
import sys
import time
import json
import csv
import argparse
from datetime import datetime
from collections import deque
from pathlib import Path

# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class SystemMetricsCollector:
    """Collects system metrics from /proc filesystem"""
    
    def __init__(self):
        self.prev_cpu_total = 0
        self.prev_cpu_idle = 0
        self.prev_context_switches = 0
        self.prev_time = time.time()
    
    def read_cpu_stats(self):
        """Read CPU statistics from /proc/stat"""
        try:
            with open('/proc/stat', 'r') as f:
                cpu_line = f.readline()
                fields = cpu_line.split()
                
                # cpu  user nice system idle iowait irq softirq
                user = int(fields[1])
                nice = int(fields[2])
                system = int(fields[3])
                idle = int(fields[4])
                iowait = int(fields[5])
                
                total = user + nice + system + idle + iowait
                
                return total, idle
        except Exception as e:
            print(f"Error reading CPU stats: {e}")
            return 0, 0
    
    def read_context_switches(self):
        """Read context switch count from /proc/stat"""
        try:
            with open('/proc/stat', 'r') as f:
                for line in f:
                    if line.startswith('ctxt'):
                        return int(line.split()[1])
        except Exception as e:
            print(f"Error reading context switches: {e}")
        return 0
    
    def read_load_average(self):
        """Read load average from /proc/loadavg"""
        try:
            with open('/proc/loadavg', 'r') as f:
                return float(f.read().split()[0])
        except Exception as e:
            print(f"Error reading load average: {e}")
        return 0.0
    
    def read_task_stats(self):
        """Read running and blocked task counts"""
        running = 0
        blocked = 0
        
        try:
            with open('/proc/stat', 'r') as f:
                for line in f:
                    if line.startswith('procs_running'):
                        running = int(line.split()[1])
                    elif line.startswith('procs_blocked'):
                        blocked = int(line.split()[1])
        except Exception as e:
            print(f"Error reading task stats: {e}")
        
        return running, blocked
    
    def collect_metrics(self):
        """Collect all system metrics"""
        current_time = time.time()
        total, idle = self.read_cpu_stats()
        context_switches = self.read_context_switches()
        load_avg = self.read_load_average()
        running, blocked = self.read_task_stats()
        
        # Calculate CPU utilization
        if self.prev_cpu_total > 0:
            total_diff = total - self.prev_cpu_total
            idle_diff = idle - self.prev_cpu_idle
            
            if total_diff > 0:
                cpu_util = ((total_diff - idle_diff) / total_diff) * 100.0
            else:
                cpu_util = 0.0
        else:
            cpu_util = 0.0
        
        # Calculate context switches per second
        time_diff = current_time - self.prev_time
        if time_diff > 0 and self.prev_context_switches > 0:
            cs_per_sec = (context_switches - self.prev_context_switches) / time_diff
        else:
            cs_per_sec = 0
        
        # Update previous values
        self.prev_cpu_total = total
        self.prev_cpu_idle = idle
        self.prev_context_switches = context_switches
        self.prev_time = current_time
        
        return {
            'timestamp': current_time,
            'cpu_util': cpu_util,
            'context_switches': int(cs_per_sec),
            'load_avg': load_avg,
            'running_tasks': running,
            'blocked_tasks': blocked,
        }


class RealtimeMonitor:
    """Real-time monitoring with live baseline comparison"""
    
    def __init__(self, baseline_window=60, comparison_window=30, results_dir='results'):
        self.baseline_window = baseline_window
        self.comparison_window = comparison_window
        self.results_dir = results_dir
        
        # Create results directory
        Path(results_dir).mkdir(parents=True, exist_ok=True)
        Path(f'{results_dir}/live').mkdir(exist_ok=True)
        
        # Data storage
        self.baseline_metrics = {
            'cpu_util': deque(maxlen=baseline_window),
            'context_switches': deque(maxlen=baseline_window),
            'load_avg': deque(maxlen=baseline_window),
            'running_tasks': deque(maxlen=baseline_window),
        }
        
        self.rl_metrics = {
            'cpu_util': deque(maxlen=comparison_window * 2),  # Keep more for analysis
            'context_switches': deque(maxlen=comparison_window * 2),
            'load_avg': deque(maxlen=comparison_window * 2),
            'running_tasks': deque(maxlen=comparison_window * 2),
        }
        
        self.current_metrics = {}
        self.baseline_collected = False
        self.start_time = time.time()
        
        # Metrics collector
        self.collector = SystemMetricsCollector()
        
        # CSV writer for continuous export
        self.csv_file = None
        self.csv_writer = None
        self.init_csv()
    
    def init_csv(self):
        """Initialize CSV file for continuous logging"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        csv_path = f'{self.results_dir}/live/realtime_metrics_{timestamp}.csv'
        
        self.csv_file = open(csv_path, 'w', newline='')
        self.csv_writer = csv.writer(self.csv_file)
        self.csv_writer.writerow([
            'timestamp', 'elapsed', 'mode', 'cpu_util', 'context_switches',
            'load_avg', 'running_tasks', 'blocked_tasks'
        ])
        self.csv_file.flush()
    
    def update_baseline(self, metrics):
        """Update baseline metrics"""
        self.baseline_metrics['cpu_util'].append(metrics['cpu_util'])
        self.baseline_metrics['context_switches'].append(metrics['context_switches'])
        self.baseline_metrics['load_avg'].append(metrics['load_avg'])
        self.baseline_metrics['running_tasks'].append(metrics['running_tasks'])
    
    def update_rl(self, metrics):
        """Update RL-controlled metrics"""
        self.rl_metrics['cpu_util'].append(metrics['cpu_util'])
        self.rl_metrics['context_switches'].append(metrics['context_switches'])
        self.rl_metrics['load_avg'].append(metrics['load_avg'])
        self.rl_metrics['running_tasks'].append(metrics['running_tasks'])
    
    def calculate_statistics(self, data_deque):
        """Calculate mean and standard deviation"""
        if len(data_deque) == 0:
            return 0.0, 0.0
        
        data = list(data_deque)
        n = len(data)
        mean = sum(data) / n
        
        if n > 1:
            variance = sum((x - mean) ** 2 for x in data) / (n - 1)
            std = variance ** 0.5
        else:
            std = 0.0
        
        return mean, std
    
    def get_comparison(self):
        """Get baseline vs RL comparison statistics"""
        comparison = {}
        
        # CPU utilization
        baseline_cpu_mean, baseline_cpu_std = self.calculate_statistics(
            self.baseline_metrics['cpu_util']
        )
        rl_cpu_mean, rl_cpu_std = self.calculate_statistics(
            self.rl_metrics['cpu_util']
        )
        
        cpu_stability_improvement = (
            ((baseline_cpu_std - rl_cpu_std) / baseline_cpu_std * 100)
            if baseline_cpu_std > 0 else 0
        )
        
        comparison['cpu'] = {
            'baseline_mean': baseline_cpu_mean,
            'baseline_std': baseline_cpu_std,
            'rl_mean': rl_cpu_mean,
            'rl_std': rl_cpu_std,
            'stability_improvement': cpu_stability_improvement
        }
        
        # Context switches
        baseline_cs_mean, _ = self.calculate_statistics(
            self.baseline_metrics['context_switches']
        )
        rl_cs_mean, _ = self.calculate_statistics(
            self.rl_metrics['context_switches']
        )
        
        cs_reduction = (
            ((baseline_cs_mean - rl_cs_mean) / baseline_cs_mean * 100)
            if baseline_cs_mean > 0 else 0
        )
        
        comparison['context_switches'] = {
            'baseline_mean': baseline_cs_mean,
            'rl_mean': rl_cs_mean,
            'reduction': cs_reduction
        }
        
        # Load average
        baseline_load_mean, _ = self.calculate_statistics(
            self.baseline_metrics['load_avg']
        )
        rl_load_mean, _ = self.calculate_statistics(
            self.rl_metrics['load_avg']
        )
        
        load_improvement = (
            ((baseline_load_mean - rl_load_mean) / baseline_load_mean * 100)
            if baseline_load_mean > 0 else 0
        )
        
        comparison['load'] = {
            'baseline_mean': baseline_load_mean,
            'rl_mean': rl_load_mean,
            'improvement': load_improvement
        }
        
        return comparison
    
    def export_comparison(self):
        """Export comparison data to CSV"""
        if not self.baseline_collected or len(self.rl_metrics['cpu_util']) < 10:
            return None
        
        comparison = self.get_comparison()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        csv_path = f"{self.results_dir}/live/comparison_{timestamp}.csv"
        
        with open(csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Metric', 'Baseline Mean', 'Baseline Std', 'RL Mean', 'RL Std', 'Improvement %'])
            
            cpu = comparison['cpu']
            writer.writerow([
                'CPU Utilization',
                f"{cpu['baseline_mean']:.2f}",
                f"{cpu['baseline_std']:.2f}",
                f"{cpu['rl_mean']:.2f}",
                f"{cpu['rl_std']:.2f}",
                f"{cpu['stability_improvement']:.2f}"
            ])
            
            cs = comparison['context_switches']
            writer.writerow([
                'Context Switches',
                f"{cs['baseline_mean']:.0f}",
                'N/A',
                f"{cs['rl_mean']:.0f}",
                'N/A',
                f"{cs['reduction']:.2f}"
            ])
            
            load = comparison['load']
            writer.writerow([
                'Load Average',
                f"{load['baseline_mean']:.2f}",
                'N/A',
                f"{load['rl_mean']:.2f}",
                'N/A',
                f"{load['improvement']:.2f}"
            ])
        
        return csv_path
    
    def clear_screen(self):
        """Clear terminal screen"""
        os.system('clear' if os.name == 'posix' else 'cls')
    
    def print_header(self):
        """Print header section"""
        print(f"{Colors.BOLD}{Colors.OKCYAN}{'='*80}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.OKCYAN}CPU SCHEDULER OPTIMIZER - REAL-TIME MONITORING{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.OKCYAN}{'='*80}{Colors.ENDC}")
    
    def print_status(self):
        """Print current status to console"""
        elapsed = time.time() - self.start_time
        
        self.clear_screen()
        self.print_header()
        
        print(f"{Colors.BOLD}Runtime:{Colors.ENDC} {elapsed:.0f}s")
        
        if elapsed < self.baseline_window:
            mode = f"{Colors.WARNING}COLLECTING BASELINE{Colors.ENDC}"
            progress = elapsed / self.baseline_window
            bar_length = 40
            filled = int(progress * bar_length)
            bar = f"[{'#' * filled:<{bar_length}}] {progress*100:.0f}%"
            print(f"{Colors.BOLD}Status:{Colors.ENDC} {mode} ({elapsed:.0f}/{self.baseline_window}s)")
            print(f"{Colors.BOLD}Progress:{Colors.ENDC} {bar}")
        else:
            mode = f"{Colors.OKGREEN}RL-OPTIMIZED MODE{Colors.ENDC}"
            rl_duration = elapsed - self.baseline_window
            print(f"{Colors.BOLD}Status:{Colors.ENDC} {mode} (Active for {rl_duration:.0f}s)")
        
        print(f"\n{Colors.BOLD}{Colors.OKBLUE}{'-'*80}{Colors.ENDC}")
        print(f"{Colors.BOLD}CURRENT METRICS{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.OKBLUE}{'-'*80}{Colors.ENDC}")
        
        if self.current_metrics:
            cpu = self.current_metrics.get('cpu_util', 0)
            cpu_color = Colors.OKGREEN if cpu < 70 else Colors.WARNING if cpu < 85 else Colors.FAIL
            
            print(f"{Colors.BOLD}CPU Utilization:{Colors.ENDC}   {cpu_color}{cpu:.2f}%{Colors.ENDC}")
            print(f"{Colors.BOLD}Context Switches:{Colors.ENDC}  {self.current_metrics.get('context_switches', 0)}")
            print(f"{Colors.BOLD}Load Average:{Colors.ENDC}      {self.current_metrics.get('load_avg', 0):.2f}")
            print(f"{Colors.BOLD}Running Tasks:{Colors.ENDC}     {self.current_metrics.get('running_tasks', 0)}")
            print(f"{Colors.BOLD}Blocked Tasks:{Colors.ENDC}     {self.current_metrics.get('blocked_tasks', 0)}")
        
        if self.baseline_collected and len(self.rl_metrics['cpu_util']) > 10:
            comparison = self.get_comparison()
            
            print(f"\n{Colors.BOLD}{Colors.OKBLUE}{'-'*80}{Colors.ENDC}")
            print(f"{Colors.BOLD}PERFORMANCE COMPARISON{Colors.ENDC}")
            print(f"{Colors.BOLD}{Colors.OKBLUE}{'-'*80}{Colors.ENDC}")
            
            print(f"\n{Colors.BOLD}{'Metric':<25} {'Baseline':<15} {'RL-Optimized':<15} {'Improvement':<15}{Colors.ENDC}")
            print(f"{'-'*80}")
            
            cpu = comparison['cpu']
            cpu_imp = cpu['stability_improvement']
            imp_color = Colors.OKGREEN if cpu_imp > 0 else Colors.FAIL
            print(f"{'CPU Variance':<25} {cpu['baseline_std']:<15.2f} {cpu['rl_std']:<15.2f} {imp_color}{cpu_imp:>+14.1f}%{Colors.ENDC}")
            
            cs = comparison['context_switches']
            cs_red = cs['reduction']
            red_color = Colors.OKGREEN if cs_red > 0 else Colors.FAIL
            print(f"{'Context Switches':<25} {cs['baseline_mean']:<15.0f} {cs['rl_mean']:<15.0f} {red_color}{cs_red:>+14.1f}%{Colors.ENDC}")
            
            load = comparison['load']
            load_imp = load['improvement']
            load_color = Colors.OKGREEN if load_imp > 0 else Colors.FAIL
            print(f"{'Load Average':<25} {load['baseline_mean']:<15.2f} {load['rl_mean']:<15.2f} {load_color}{load_imp:>+14.1f}%{Colors.ENDC}")
        
        print(f"\n{Colors.BOLD}{Colors.OKCYAN}{'='*80}{Colors.ENDC}")
        print(f"{Colors.BOLD}Press Ctrl+C to stop monitoring{Colors.ENDC}")
    
    def generate_summary(self):
        """Generate final summary report"""
        comparison = self.get_comparison()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        summary_path = f"{self.results_dir}/live/summary_{timestamp}.txt"
        
        with open(summary_path, 'w') as f:
            f.write("="*80 + "\n")
            f.write("CPU SCHEDULER OPTIMIZER - PERFORMANCE SUMMARY\n")
            f.write("="*80 + "\n\n")
            
            f.write(f"Run Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Runtime: {time.time() - self.start_time:.0f} seconds\n")
            f.write(f"Baseline Duration: {self.baseline_window} seconds\n")
            f.write(f"RL-Optimized Duration: {time.time() - self.start_time - self.baseline_window:.0f} seconds\n\n")
            
            f.write("-"*80 + "\n")
            f.write("PERFORMANCE IMPROVEMENTS\n")
            f.write("-"*80 + "\n\n")
            
            cpu = comparison['cpu']
            f.write(f"CPU Stability Improvement:\n")
            f.write(f"  Baseline Variance:     {cpu['baseline_std']:.2f}%\n")
            f.write(f"  RL-Optimized Variance: {cpu['rl_std']:.2f}%\n")
            f.write(f"  Improvement:           {cpu['stability_improvement']:+.1f}%\n\n")
            
            cs = comparison['context_switches']
            f.write(f"Context Switch Reduction:\n")
            f.write(f"  Baseline Avg:          {cs['baseline_mean']:.0f} switches/sec\n")
            f.write(f"  RL-Optimized Avg:      {cs['rl_mean']:.0f} switches/sec\n")
            f.write(f"  Reduction:             {cs['reduction']:+.1f}%\n\n")
            
            load = comparison['load']
            f.write(f"Load Average Optimization:\n")
            f.write(f"  Baseline:              {load['baseline_mean']:.2f}\n")
            f.write(f"  RL-Optimized:          {load['rl_mean']:.2f}\n")
            f.write(f"  Improvement:           {load['improvement']:+.1f}%\n\n")
            
            f.write("-"*80 + "\n")
            f.write("CONCLUSION\n")
            f.write("-"*80 + "\n\n")
            
            if cpu['stability_improvement'] > 10 and cs['reduction'] > 10:
                f.write("✅ SIGNIFICANT IMPROVEMENT: The RL-based scheduler shows substantial\n")
                f.write("   improvements in both CPU stability and context switch reduction.\n")
            elif cpu['stability_improvement'] > 5 or cs['reduction'] > 5:
                f.write("✓ MODERATE IMPROVEMENT: The RL-based scheduler shows measurable\n")
                f.write("  improvements in system performance.\n")
            else:
                f.write("⚠ LIMITED IMPROVEMENT: Results are inconclusive. Consider running\n")
                f.write("  for a longer duration or under different workloads.\n")
        
        return summary_path
    
    def run(self, duration=300, display_interval=5, export_interval=30):
        """Run monitoring for specified duration"""
        print(f"\n{Colors.BOLD}{Colors.OKGREEN}🚀 Starting Real-Time Monitoring{Colors.ENDC}")
        print(f"   Duration: {duration} seconds")
        print(f"   Baseline: {self.baseline_window} seconds")
        print(f"   RL Optimization: {duration - self.baseline_window} seconds\n")
        
        end_time = self.start_time + duration
        last_display = self.start_time
        last_export = self.start_time
        
        try:
            while time.time() < end_time:
                elapsed = time.time() - self.start_time
                
                # Collect current metrics
                self.current_metrics = self.collector.collect_metrics()
                
                # Determine mode
                mode = 'baseline' if elapsed < self.baseline_window else 'rl_controlled'
                
                # Log to CSV
                if self.csv_writer:
                    self.csv_writer.writerow([
                        self.current_metrics['timestamp'],
                        elapsed,
                        mode,
                        self.current_metrics['cpu_util'],
                        self.current_metrics['context_switches'],
                        self.current_metrics['load_avg'],
                        self.current_metrics['running_tasks'],
                        self.current_metrics['blocked_tasks']
                    ])
                    self.csv_file.flush()
                
                # Update appropriate dataset
                if mode == 'baseline':
                    self.update_baseline(self.current_metrics)
                else:
                    if not self.baseline_collected:
                        self.baseline_collected = True
                        print(f"\n{Colors.OKGREEN}✅ Baseline collection complete!{Colors.ENDC}")
                        print(f"{Colors.OKGREEN}🤖 Starting RL-optimized mode...{Colors.ENDC}\n")
                    
                    self.update_rl(self.current_metrics)
                
                # Display status
                if (time.time() - last_display) >= display_interval:
                    self.print_status()
                    last_display = time.time()
                
                # Export comparison
                if self.baseline_collected and (time.time() - last_export) >= export_interval:
                    csv_path = self.export_comparison()
                    if csv_path:
                        print(f"\n{Colors.OKCYAN}📊 Exported comparison to: {csv_path}{Colors.ENDC}")
                    last_export = time.time()
                
                time.sleep(1)
        
        except KeyboardInterrupt:
            print(f"\n\n{Colors.WARNING}⚠️  Monitoring interrupted by user{Colors.ENDC}")
        
        finally:
            # Close CSV file
            if self.csv_file:
                self.csv_file.close()
        
        # Final export and summary
        if self.baseline_collected:
            print(f"\n{Colors.OKBLUE}📊 Generating final reports...{Colors.ENDC}")
            
            csv_path = self.export_comparison()
            summary_path = self.generate_summary()
            
            print(f"{Colors.OKGREEN}✅ Final comparison saved to: {csv_path}{Colors.ENDC}")
            print(f"{Colors.OKGREEN}✅ Summary saved to: {summary_path}{Colors.ENDC}")
            
            # Print summary to console
            with open(summary_path, 'r') as f:
                print(f"\n{Colors.BOLD}{f.read()}{Colors.ENDC}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Real-Time CPU Scheduler Monitor with Baseline Comparison',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('-d', '--duration', type=int, default=300,
                       help='Total monitoring duration in seconds')
    parser.add_argument('-b', '--baseline', type=int, default=60,
                       help='Baseline collection duration in seconds')
    parser.add_argument('-i', '--interval', type=int, default=5,
                       help='Display update interval in seconds')
    parser.add_argument('-e', '--export', type=int, default=30,
                       help='Comparison export interval in seconds')
    parser.add_argument('-r', '--results', type=str, default='results',
                       help='Results directory path')
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.baseline >= args.duration:
        print(f"{Colors.FAIL}Error: Baseline duration must be less than total duration{Colors.ENDC}")
        sys.exit(1)
    
    # Create monitor
    monitor = RealtimeMonitor(
        baseline_window=args.baseline,
        comparison_window=30,
        results_dir=args.results
    )
    
    # Run monitoring
    monitor.run(
        duration=args.duration,
        display_interval=args.interval,
        export_interval=args.export
    )
    
    print(f"\n{Colors.OKGREEN}✅ Monitoring complete!{Colors.ENDC}\n")


if __name__ == '__main__':
    main()