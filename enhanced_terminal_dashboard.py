#!/usr/bin/env python3
"""
Optimized Enhanced Terminal Dashboard for DQN CPU Scheduler
- Real-time ASCII graphs with live updates
- Faster data processing  
- Shows improvements immediately
- Better visual feedback

TIMING EXPECTATIONS:
- 0-60s: Baseline data collection phase
- 60s+: RL training starts, improvements visible after ~90-120s
- Stable improvements: 3-5 minutes of training
"""

import os
import sys
import time
import json
from datetime import datetime
from collections import deque
import subprocess

# Rich library for beautiful terminal output
try:
    from rich.console import Console
    from rich.layout import Layout
    from rich.panel import Panel
    from rich.table import Table
    from rich.live import Live
    from rich.text import Text
    from rich import box
except ImportError:
    print("Installing required package: rich")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "rich", "--break-system-packages"])
    from rich.console import Console
    from rich.layout import Layout
    from rich.panel import Panel
    from rich.table import Table
    from rich.live import Live
    from rich.text import Text
    from rich import box

console = Console()

class OptimizedDashboard:
    def __init__(self):
        self.metrics_file = '/tmp/scheduler_metrics.csv'
        self.state_file = '/tmp/rl_state.json'
        self.action_file = '/tmp/scheduler_actions.log'
        
        # Data buffers
        self.cpu_baseline_history = deque(maxlen=50)
        self.cpu_optimized_history = deque(maxlen=50)
        self.reward_history = deque(maxlen=40)
        
        # Statistics
        self.baseline_stats = {'cpu': [], 'variance': [], 'switches': [], 'load': []}
        self.optimized_stats = {'cpu': [], 'variance': [], 'switches': [], 'load': []}
        
        # Training state
        self.episode = 0
        self.epsilon = 1.0
        self.avg_reward = 0.0
        self.q_value = 0.0
        
        # Process tracking
        self.processes = {}
        self.actions = deque(maxlen=15)
        
        # Timing
        self.start_time = time.time()
        self.baseline_start = None
        self.rl_start = None
        
    def read_metrics_fast(self):
        """Fast CSV reading"""
        try:
            if not os.path.exists(self.metrics_file):
                return None
            
            with open(self.metrics_file, 'r') as f:
                lines = f.readlines()
                if len(lines) < 2:
                    return None
                
                header = lines[0].strip().split(',')
                
                # Parse last 100 lines
                for line in lines[-100:]:
                    parts = line.strip().split(',')
                    if len(parts) < len(header):
                        continue
                    
                    data = dict(zip(header, parts))
                    
                    try:
                        mode = data.get('mode', '')
                        cpu = float(data.get('cpu_usage', 0))
                        variance = float(data.get('cpu_variance', 0))
                        switches = float(data.get('context_switches', 0))
                        load = float(data.get('load_avg', 0))
                        
                        if mode == 'baseline':
                            if not self.baseline_start:
                                self.baseline_start = time.time()
                            self.baseline_stats['cpu'].append(cpu)
                            self.baseline_stats['variance'].append(variance)
                            self.baseline_stats['switches'].append(switches)
                            self.baseline_stats['load'].append(load)
                            self.cpu_baseline_history.append(cpu)
                            
                        elif mode == 'rl':
                            if not self.rl_start:
                                self.rl_start = time.time()
                            self.optimized_stats['cpu'].append(cpu)
                            self.optimized_stats['variance'].append(variance)
                            self.optimized_stats['switches'].append(switches)
                            self.optimized_stats['load'].append(load)
                            self.cpu_optimized_history.append(cpu)
                    except:
                        continue
            
            return True
        except:
            return None
    
    def read_state_fast(self):
        """Fast JSON reading"""
        try:
            if not os.path.exists(self.state_file):
                return None
            
            with open(self.state_file, 'r') as f:
                state = json.load(f)
                
                self.episode = state.get('episode', 0)
                self.epsilon = state.get('epsilon', 1.0)
                self.avg_reward = state.get('avg_reward', 0.0)
                self.q_value = state.get('avg_q_value', 0.0)
                
                if self.avg_reward != 0:
                    self.reward_history.append(self.avg_reward)
                
                # Process information
                self.processes = {}
                if 'processes' in state:
                    for proc in state['processes']:
                        if isinstance(proc, dict):
                            pid = proc.get('pid')
                            if pid:
                                self.processes[pid] = {
                                    'name': proc.get('name', 'unknown'),
                                    'type': proc.get('type', 'unknown'),
                                    'cpu': proc.get('cpu_usage', 0),
                                    'nice': proc.get('nice', 0)
                                }
                return state
        except:
            return None
    
    def read_actions_fast(self):
        """Fast action reading"""
        try:
            if not os.path.exists(self.action_file):
                return
            
            with open(self.action_file, 'r') as f:
                for line in f.readlines()[-15:]:
                    line = line.strip()
                    if line and line not in self.actions:
                        self.actions.append(line)
        except:
            pass
    
    def calc_improvement(self, baseline, optimized):
        """Calculate improvement percentage"""
        if not baseline or not optimized:
            return 0.0
        b_avg = sum(baseline) / len(baseline)
        o_avg = sum(optimized) / len(optimized)
        if b_avg == 0:
            return 0.0
        return ((b_avg - o_avg) / b_avg) * 100
    
    def create_header(self):
        """Dashboard header"""
        runtime = int(time.time() - self.start_time)
        
        title = Text()
        title.append("DQN CPU SCHEDULER ", style="bold cyan")
        title.append("- Enhanced Terminal Dashboard ", style="bold white")
        
        # Phase
        if not self.baseline_start:
            phase = Text("⏳ INITIALIZING", style="bold yellow")
        elif not self.rl_start:
            baseline_time = int(time.time() - self.baseline_start)
            phase = Text(f"📊 BASELINE ({baseline_time}s/60s)", style="bold yellow")
        else:
            rl_time = int(time.time() - self.rl_start)
            phase = Text(f"● TRAINING ({rl_time}s)", style="bold green")
        
        header_table = Table.grid(padding=1)
        header_table.add_column(justify="left")
        header_table.add_column(justify="right")
        header_table.add_row(title, phase)
        
        return Panel(header_table, style="bold cyan", border_style="bright_cyan", box=box.DOUBLE)
    
    def create_improvement_panel(self):
        """Show improvements"""
        if not self.baseline_stats['cpu'] or not self.optimized_stats['cpu']:
            elapsed = int(time.time() - self.start_time)
            
            if not self.baseline_start:
                msg = Text()
                msg.append("⏳ Waiting for data...\n\n", style="yellow")
                msg.append(f"Elapsed: {elapsed}s\n", style="dim")
            elif not self.rl_start:
                baseline_time = int(time.time() - self.baseline_start)
                progress = min(100, int(baseline_time / 60 * 100))
                bar = "█" * (progress // 5) + "░" * (20 - progress // 5)
                
                msg = Text()
                msg.append("📊 Collecting baseline...\n\n", style="yellow")
                msg.append(f"{bar} {progress}%\n\n", style="cyan")
                msg.append(f"Time: {baseline_time}s / 60s\n", style="dim")
                msg.append(f"Samples: {len(self.baseline_stats['cpu'])}", style="dim")
            else:
                msg = Text()
                msg.append("⚙️  Training started...\n\n", style="yellow")
                msg.append(f"Baseline: {len(self.baseline_stats['cpu'])}\n", style="dim")
                msg.append(f"Optimized: {len(self.optimized_stats['cpu'])}\n", style="dim")
                msg.append("\nImprovements show after ~30 samples", style="dim italic")
            
            return Panel(msg, title="[bold yellow]Status[/bold yellow]", border_style="yellow")
        
        # Calculate
        cpu_imp = self.calc_improvement(self.baseline_stats['cpu'], self.optimized_stats['cpu'])
        var_imp = self.calc_improvement(self.baseline_stats['variance'], self.optimized_stats['variance'])
        switch_imp = self.calc_improvement(self.baseline_stats['switches'], self.optimized_stats['switches'])
        load_imp = self.calc_improvement(self.baseline_stats['load'], self.optimized_stats['load'])
        
        # Averages
        b_cpu = sum(self.baseline_stats['cpu']) / len(self.baseline_stats['cpu'])
        o_cpu = sum(self.optimized_stats['cpu']) / len(self.optimized_stats['cpu'])
        b_var = sum(self.baseline_stats['variance']) / len(self.baseline_stats['variance'])
        o_var = sum(self.optimized_stats['variance']) / len(self.optimized_stats['variance'])
        b_switch = sum(self.baseline_stats['switches']) / len(self.baseline_stats['switches'])
        o_switch = sum(self.optimized_stats['switches']) / len(self.optimized_stats['switches'])
        b_load = sum(self.baseline_stats['load']) / len(self.baseline_stats['load'])
        o_load = sum(self.optimized_stats['load']) / len(self.optimized_stats['load'])
        
        table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED, padding=(0, 1))
        table.add_column("Metric", style="cyan", width=18)
        table.add_column("Baseline", justify="right", style="white", width=12)
        table.add_column("Optimized", justify="right", style="green", width=12)
        table.add_column("Δ Change", justify="right", width=12)
        
        def fmt(v):
            if abs(v) < 0.1:
                return f"[dim]~0.0%[/dim]"
            return f"[bold green]↓ {v:.1f}%[/bold green]" if v > 0 else f"[bold red]↑ {abs(v):.1f}%[/bold red]"
        
        table.add_row("CPU Usage", f"{b_cpu:.1f}%", f"{o_cpu:.1f}%", fmt(cpu_imp))
        table.add_row("CPU Variance", f"{b_var:.1f}%", f"{o_var:.1f}%", fmt(var_imp))
        table.add_row("Ctx Switches/s", f"{b_switch:.0f}", f"{o_switch:.0f}", fmt(switch_imp))
        table.add_row("Load Average", f"{b_load:.2f}", f"{o_load:.2f}", fmt(load_imp))
        
        avg_imp = (cpu_imp + var_imp + switch_imp + load_imp) / 4
        summary = Text()
        summary.append("\nOverall: ", style="dim")
        summary.append(f"{avg_imp:.1f}%", style="bold green" if avg_imp > 0 else "bold red")
        
        content = Table.grid()
        content.add_row(table)
        content.add_row(summary)
        
        return Panel(content, title=f"[bold cyan]Improvements[/bold cyan] [dim](n={len(self.optimized_stats['cpu'])})[/dim]", border_style="cyan")
    
    def create_training_panel(self):
        """Training progress"""
        grid = Table.grid(padding=1)
        grid.add_column(justify="left", width=18)
        grid.add_column(justify="left")
        
        grid.add_row(Text("Episodes:", style="cyan"), Text(f"{self.episode:,}", style="bold white"))
        
        eps_pct = int(self.epsilon * 20)
        eps_bar = "█" * eps_pct + "░" * (20 - eps_pct)
        grid.add_row(Text("Exploration (ε):", style="cyan"), Text(f"{eps_bar} {self.epsilon:.3f}", style="yellow"))
        
        r_style = "bold green" if self.avg_reward > 0 else "bold red" if self.avg_reward < 0 else "white"
        grid.add_row(Text("Avg Reward:", style="cyan"), Text(f"{self.avg_reward:+.2f}", style=r_style))
        grid.add_row(Text("Q-Value:", style="cyan"), Text(f"{self.q_value:.1f}", style="bold magenta"))
        
        return Panel(grid, title="[bold yellow]Training[/bold yellow]", border_style="yellow")
    
    def create_realtime_graph(self):
        """Real-time ASCII graph"""
        if len(self.cpu_baseline_history) < 2 and len(self.cpu_optimized_history) < 2:
            return Panel(Text("⏳ Collecting graph data...", style="yellow"), title="[bold blue]CPU Usage[/bold blue]", border_style="blue")
        
        h = 12
        w = 50
        
        all_data = list(self.cpu_baseline_history) + list(self.cpu_optimized_history)
        if not all_data:
            return Panel(Text("No data", style="dim"), title="CPU")
        
        max_val = max(all_data)
        min_val = min(all_data)
        rng = max_val - min_val if max_val != min_val else 1
        
        # Create chart
        chart = []
        for i in range(h):
            thresh = max_val - (i * rng / h)
            line = Text()
            
            # Y-axis
            if i == 0:
                line.append(f"{max_val:5.1f}% ", style="dim")
            elif i == h - 1:
                line.append(f"{min_val:5.1f}% ", style="dim")
            elif i == h // 2:
                line.append(f"{(max_val+min_val)/2:5.1f}% ", style="dim")
            else:
                line.append("       ")
            
            line.append("│", style="dim")
            
            # Baseline dots
            for j, val in enumerate(self.cpu_baseline_history):
                if j >= w:
                    break
                if abs(val - thresh) < (rng / h):
                    line.append("·", style="white")
                else:
                    line.append(" ")
            
            chart.append(line)
        
        # Overlay optimized
        for i in range(h):
            thresh = max_val - (i * rng / h)
            offset = max(0, len(self.cpu_baseline_history) - len(self.cpu_optimized_history))
            
            for j, val in enumerate(self.cpu_optimized_history):
                if j >= w:
                    break
                pos = 8 + offset + j
                
                if abs(val - thresh) < (rng / h):
                    old = chart[i].plain
                    if pos < len(old):
                        new = old[:pos] + "█" + old[pos+1:]
                        chart[i] = Text()
                        chart[i].append(new[:pos], style="dim")
                        chart[i].append("█", style="bold cyan")
                        chart[i].append(new[pos+1:], style="white")
        
        result = Text()
        for line in chart:
            result.append(line)
            result.append("\n")
        result.append(f"       └{'─'*w}>\n", style="dim")
        
        legend = Text()
        legend.append("  ·  ", style="white")
        legend.append("Baseline  ", style="dim")
        legend.append("█  ", style="bold cyan")
        legend.append("Optimized", style="cyan")
        result.append(legend)
        
        return Panel(result, title="[bold blue]CPU - Real-time[/bold blue]", border_style="blue")
    
    def create_reward_graph(self):
        """Reward trend"""
        if len(self.reward_history) < 2:
            return Panel(Text("⏳ Waiting for training...", style="yellow"), title="[bold green]Rewards[/bold green]", border_style="green")
        
        h = 8
        w = 40
        
        max_val = max(self.reward_history)
        min_val = min(self.reward_history)
        rng = max_val - min_val if max_val != min_val else 1
        
        chart = []
        for i in range(h):
            thresh = max_val - (i * rng / h)
            line = Text()
            
            if i == 0:
                line.append(f"{max_val:6.1f} ", style="dim")
            elif i == h - 1:
                line.append(f"{min_val:6.1f} ", style="dim")
            else:
                line.append("        ")
            
            line.append("│", style="dim")
            
            for j, val in enumerate(self.reward_history):
                if j >= w:
                    break
                if abs(val - thresh) < (rng / h):
                    line.append("●", style="bold green")
                else:
                    line.append(" ")
            
            chart.append(line)
        
        result = Text()
        for line in chart:
            result.append(line)
            result.append("\n")
        result.append(f"        └{'─'*w}>\n", style="dim")
        
        return Panel(result, title="[bold green]Reward Trend[/bold green]", border_style="green")
    
    def create_process_panel(self):
        """Show processes"""
        if not self.processes:
            return Panel(Text("⏳ No process data", style="yellow"), title="[bold green]Processes[/bold green]", border_style="green")
        
        table = Table(show_header=True, header_style="bold cyan", box=box.SIMPLE, padding=(0, 1))
        table.add_column("PID", style="yellow", width=7)
        table.add_column("Process", style="cyan", width=16)
        table.add_column("Type", style="magenta", width=14)
        table.add_column("CPU%", justify="right", width=8)
        table.add_column("Nice", justify="right", width=5)
        
        for pid, proc in sorted(self.processes.items(), key=lambda x: x[1].get('cpu', 0), reverse=True)[:10]:
            cpu = proc.get('cpu', 0)
            style = "bold red" if cpu > 70 else "bold yellow" if cpu > 40 else "green"
            
            table.add_row(
                str(pid),
                proc.get('name', 'unknown')[:16],
                proc.get('type', 'unknown')[:14],
                f"[{style}]{cpu:.1f}%[/{style}]",
                str(proc.get('nice', 0))
            )
        
        return Panel(table, title=f"[bold green]Processes[/bold green] [dim]({len(self.processes)})[/dim]", border_style="green")
    
    def create_action_log(self):
        """Action log"""
        if not self.actions:
            return Panel(Text("⏳ No actions yet", style="yellow"), title="[bold magenta]Actions[/bold magenta]", border_style="magenta")
        
        text = Text()
        for action in list(self.actions)[-10:]:
            parts = action.split(' - ', 1)
            if len(parts) == 2:
                ts, txt = parts
                text.append(f"[{ts}] ", style="dim cyan")
                text.append(f"{txt}\n", style="white")
            else:
                text.append(f"• {action}\n", style="white")
        
        return Panel(text, title="[bold magenta]Recent Actions[/bold magenta]", border_style="magenta")
    
    def create_footer(self):
        """Footer"""
        runtime = int(time.time() - self.start_time)
        
        footer = Text()
        footer.append("Press ", style="dim")
        footer.append("Ctrl+C", style="bold red")
        footer.append(" to exit  │  Runtime: ", style="dim")
        footer.append(f"{runtime}s", style="cyan")
        footer.append("  │  ", style="dim")
        footer.append(datetime.now().strftime("%H:%M:%S"), style="cyan")
        
        if not self.rl_start and self.baseline_start:
            bt = int(time.time() - self.baseline_start)
            footer.append(f"  │  Baseline ETA: {max(0, 60-bt)}s", style="yellow")
        
        return Panel(footer, border_style="dim")
    
    def create_layout(self):
        """Layout"""
        layout = Layout()
        
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3)
        )
        
        layout["main"].split_row(
            Layout(name="left", ratio=3),
            Layout(name="right", ratio=2)
        )
        
        layout["left"].split_column(
            Layout(name="improvements", size=14),
            Layout(name="graph", size=20),
            Layout(name="training", size=12)
        )
        
        layout["right"].split_column(
            Layout(name="reward", size=16),
            Layout(name="processes"),
            Layout(name="actions")
        )
        
        return layout
    
    def update_layout(self, layout):
        """Update"""
        self.read_metrics_fast()
        self.read_state_fast()
        self.read_actions_fast()
        
        layout["header"].update(self.create_header())
        layout["improvements"].update(self.create_improvement_panel())
        layout["graph"].update(self.create_realtime_graph())
        layout["training"].update(self.create_training_panel())
        layout["reward"].update(self.create_reward_graph())
        layout["processes"].update(self.create_process_panel())
        layout["actions"].update(self.create_action_log())
        layout["footer"].update(self.create_footer())
    
    def run(self):
        """Run"""
        layout = self.create_layout()
        
        console.print("\n[bold cyan]🚀 Starting Dashboard...[/bold cyan]")
        console.print("[dim]Waiting for DQN optimizer data...[/dim]\n")
        time.sleep(1)
        
        try:
            with Live(layout, refresh_per_second=2, screen=True) as live:
                while True:
                    self.update_layout(layout)
                    time.sleep(1)
        except KeyboardInterrupt:
            console.print("\n\n[yellow]Dashboard stopped[/yellow]")
            console.print("[green]✓ Clean exit[/green]\n")

if __name__ == "__main__":
    console.print("\n[bold cyan]═══════════════════════════════════════════════════[/bold cyan]")
    console.print("[bold cyan]   DQN CPU SCHEDULER - Enhanced Dashboard[/bold cyan]")
    console.print("[bold cyan]═══════════════════════════════════════════════════[/bold cyan]\n")
    console.print("[bold yellow]TIMING EXPECTATIONS:[/bold yellow]")
    console.print("  • 0-60s: Baseline collection")
    console.print("  • 60s+: Training starts")
    console.print("  • 90-120s: First improvements visible")
    console.print("  • 3-5 min: Stable improvements\n")
    
    dashboard = OptimizedDashboard()
    dashboard.run()