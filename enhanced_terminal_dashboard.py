#!/usr/bin/env python3
"""
Enhanced Terminal Dashboard for DQN CPU Scheduler
Shows real-time improvements, process optimization, and training progress
Run with: python3 enhanced_terminal_dashboard.py
"""

import os
import sys
import time
import json
import pandas as pd
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
    from rich.progress import Progress, BarColumn, TextColumn, SpinnerColumn
    from rich.text import Text
    from rich.align import Align
    from rich import box
    from rich.columns import Columns
    from rich.syntax import Syntax
except ImportError:
    print("Installing required package: rich")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "rich", "--break-system-packages"])
    from rich.console import Console
    from rich.layout import Layout
    from rich.panel import Panel
    from rich.table import Table
    from rich.live import Live
    from rich.progress import Progress, BarColumn, TextColumn, SpinnerColumn
    from rich.text import Text
    from rich.align import Align
    from rich import box
    from rich.columns import Columns

console = Console()

class EnhancedDashboard:
    def __init__(self):
        self.metrics_file = '/tmp/scheduler_metrics.csv'
        self.state_file = '/tmp/rl_state.json'
        self.action_file = '/tmp/scheduler_actions.log'
        
        # Data buffers
        self.cpu_history = deque(maxlen=30)
        self.reward_history = deque(maxlen=30)
        self.process_stats = {}
        
        # Baseline vs Optimized stats
        self.baseline_avg = {'cpu': 0, 'switches': 0, 'load': 0}
        self.optimized_avg = {'cpu': 0, 'switches': 0, 'load': 0}
        
        # Training state
        self.episode = 0
        self.epsilon = 1.0
        self.avg_reward = 0
        self.q_value = 0
        
    def read_metrics(self):
        """Read latest metrics from CSV"""
        try:
            if not os.path.exists(self.metrics_file):
                return None
            
            df = pd.read_csv(self.metrics_file)
            if len(df) == 0:
                return None
                
            # Calculate baseline vs optimized averages
            baseline_data = df[df['mode'] == 'baseline']
            optimized_data = df[df['mode'] == 'rl']
            
            if len(baseline_data) > 0:
                self.baseline_avg = {
                    'cpu': baseline_data['cpu_usage'].mean(),
                    'variance': baseline_data['cpu_variance'].mean(),
                    'switches': baseline_data['context_switches'].mean(),
                    'load': baseline_data['load_avg'].mean()
                }
            
            if len(optimized_data) > 0:
                self.optimized_avg = {
                    'cpu': optimized_data['cpu_usage'].mean(),
                    'variance': optimized_data['cpu_variance'].mean(),
                    'switches': optimized_data['context_switches'].mean(),
                    'load': optimized_data['load_avg'].mean()
                }
            
            # Store CPU history
            recent = df.tail(30)
            for _, row in recent.iterrows():
                self.cpu_history.append({
                    'mode': row['mode'],
                    'cpu': row['cpu_usage']
                })
            
            return df.iloc[-1]
            
        except Exception as e:
            return None
    
    def read_state(self):
        """Read DQN training state"""
        try:
            if not os.path.exists(self.state_file):
                return None
            
            with open(self.state_file, 'r') as f:
                state = json.load(f)
                self.episode = state.get('episode', 0)
                self.epsilon = state.get('epsilon', 1.0)
                self.avg_reward = state.get('avg_reward', 0)
                self.q_value = state.get('avg_q_value', 0)
                
                # Process information
                if 'processes' in state:
                    for proc in state['processes']:
                        pid = proc.get('pid')
                        if pid:
                            self.process_stats[pid] = proc
                
                return state
        except:
            return None
    
    def read_actions(self):
        """Read recent scheduler actions"""
        try:
            if not os.path.exists(self.action_file):
                return []
            
            with open(self.action_file, 'r') as f:
                lines = f.readlines()
                return [line.strip() for line in lines[-10:]]  # Last 10 actions
        except:
            return []
    
    def create_header(self):
        """Create dashboard header"""
        title = Text()
        title.append("DQN CPU SCHEDULER ", style="bold cyan")
        title.append("- Enhanced Terminal Dashboard", style="bold white")
        
        status = Text()
        status.append("● ", style="bold green")
        status.append("TRAINING ACTIVE", style="bold green")
        
        header_table = Table.grid(padding=1)
        header_table.add_column(justify="left")
        header_table.add_column(justify="right")
        header_table.add_row(title, status)
        
        return Panel(
            header_table,
            style="bold cyan",
            border_style="bright_cyan",
            box=box.DOUBLE
        )
    
    def create_improvement_panel(self):
        """Show improvement metrics"""
        if self.baseline_avg['cpu'] == 0:
            return Panel("[yellow]Collecting baseline data...[/yellow]", title="Improvements")
        
        # Calculate improvements
        cpu_improvement = ((self.baseline_avg['cpu'] - self.optimized_avg['cpu']) / self.baseline_avg['cpu'] * 100) if self.baseline_avg['cpu'] > 0 else 0
        variance_improvement = ((self.baseline_avg['variance'] - self.optimized_avg['variance']) / self.baseline_avg['variance'] * 100) if self.baseline_avg['variance'] > 0 else 0
        switches_improvement = ((self.baseline_avg['switches'] - self.optimized_avg['switches']) / self.baseline_avg['switches'] * 100) if self.baseline_avg['switches'] > 0 else 0
        load_improvement = ((self.baseline_avg['load'] - self.optimized_avg['load']) / self.baseline_avg['load'] * 100) if self.baseline_avg['load'] > 0 else 0
        
        table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
        table.add_column("Metric", style="cyan", width=20)
        table.add_column("Baseline", justify="right", style="white")
        table.add_column("Optimized", justify="right", style="green")
        table.add_column("Improvement", justify="right", style="bold yellow")
        
        # CPU Usage
        table.add_row(
            "CPU Usage",
            f"{self.baseline_avg['cpu']:.1f}%",
            f"{self.optimized_avg['cpu']:.1f}%",
            f"[green]↓ {cpu_improvement:.1f}%[/green]" if cpu_improvement > 0 else f"[red]↑ {abs(cpu_improvement):.1f}%[/red]"
        )
        
        # CPU Variance
        table.add_row(
            "CPU Variance",
            f"{self.baseline_avg['variance']:.1f}%",
            f"{self.optimized_avg['variance']:.1f}%",
            f"[green]↓ {variance_improvement:.1f}%[/green]" if variance_improvement > 0 else f"[red]↑ {abs(variance_improvement):.1f}%[/red]"
        )
        
        # Context Switches
        table.add_row(
            "Context Switches/s",
            f"{self.baseline_avg['switches']:.0f}",
            f"{self.optimized_avg['switches']:.0f}",
            f"[green]↓ {switches_improvement:.1f}%[/green]" if switches_improvement > 0 else f"[red]↑ {abs(switches_improvement):.1f}%[/red]"
        )
        
        # Load Average
        table.add_row(
            "Load Average",
            f"{self.baseline_avg['load']:.2f}",
            f"{self.optimized_avg['load']:.2f}",
            f"[green]↓ {load_improvement:.1f}%[/green]" if load_improvement > 0 else f"[red]↑ {abs(load_improvement):.1f}%[/red]"
        )
        
        return Panel(
            table,
            title="[bold cyan]Performance Improvements[/bold cyan]",
            border_style="cyan",
            padding=(1, 2)
        )
    
    def create_training_panel(self):
        """Show DQN training progress"""
        grid = Table.grid(padding=1)
        grid.add_column(justify="left")
        grid.add_column(justify="left")
        
        # Episode
        grid.add_row(
            Text("Episodes:", style="cyan"),
            Text(f"{self.episode:,}", style="bold white")
        )
        
        # Epsilon
        epsilon_bar = "█" * int(self.epsilon * 20) + "░" * (20 - int(self.epsilon * 20))
        grid.add_row(
            Text("Exploration (ε):", style="cyan"),
            Text(f"{epsilon_bar} {self.epsilon:.3f}", style="yellow")
        )
        
        # Average Reward
        grid.add_row(
            Text("Avg Reward:", style="cyan"),
            Text(f"{self.avg_reward:+.2f}", style="bold green" if self.avg_reward > 0 else "bold red")
        )
        
        # Q-Value
        grid.add_row(
            Text("Q-Value:", style="cyan"),
            Text(f"{self.q_value:.1f}", style="bold magenta")
        )
        
        return Panel(
            grid,
            title="[bold yellow]Training Progress[/bold yellow]",
            border_style="yellow",
            padding=(1, 2)
        )
    
    def create_cpu_chart(self):
        """Create ASCII CPU usage chart"""
        if len(self.cpu_history) < 2:
            return Panel("[yellow]Collecting data...[/yellow]", title="CPU Usage History")
        
        chart_height = 10
        chart_width = 50
        
        # Get data points
        baseline_points = [p['cpu'] for p in self.cpu_history if p['mode'] == 'baseline']
        optimized_points = [p['cpu'] for p in self.cpu_history if p['mode'] == 'rl']
        
        if not baseline_points or not optimized_points:
            return Panel("[yellow]Waiting for both baseline and optimized data...[/yellow]", title="CPU Usage History")
        
        max_val = max(max(baseline_points), max(optimized_points))
        min_val = min(min(baseline_points), min(optimized_points))
        
        # Create chart
        chart_lines = []
        for i in range(chart_height):
            line = ""
            threshold = max_val - (i * (max_val - min_val) / chart_height)
            
            for j in range(min(chart_width, len(baseline_points))):
                if j < len(baseline_points):
                    if baseline_points[j] >= threshold:
                        line += "▓"
                    else:
                        line += " "
            
            chart_lines.append(line)
        
        # Add labels
        chart_text = Text()
        chart_text.append(f"{max_val:.0f}% ", style="dim")
        chart_text.append("┐\n", style="dim")
        
        for i, line in enumerate(chart_lines):
            if i == chart_height // 2:
                chart_text.append(f"{(max_val + min_val)/2:.0f}% ", style="dim")
            else:
                chart_text.append("      ")
            chart_text.append("│", style="dim")
            chart_text.append(line, style="cyan")
            chart_text.append("\n")
        
        chart_text.append(f"{min_val:.0f}% ", style="dim")
        chart_text.append("└" + "─" * chart_width + ">\n", style="dim")
        chart_text.append("      ", style="dim")
        chart_text.append(f"Last {len(baseline_points)} samples", style="dim italic")
        
        return Panel(
            chart_text,
            title="[bold blue]CPU Usage Over Time[/bold blue]",
            border_style="blue",
            padding=(1, 2)
        )
    
    def create_process_panel(self):
        """Show optimized processes"""
        if not self.process_stats:
            return Panel("[yellow]No process data available[/yellow]", title="Optimized Processes")
        
        table = Table(show_header=True, header_style="bold cyan", box=box.SIMPLE)
        table.add_column("PID", style="yellow", width=8)
        table.add_column("Process", style="cyan", width=20)
        table.add_column("Type", style="magenta", width=15)
        table.add_column("CPU %", justify="right", style="green")
        table.add_column("Priority", justify="right", style="blue")
        
        for pid, proc in sorted(self.process_stats.items(), key=lambda x: x[1].get('cpu_usage', 0), reverse=True)[:8]:
            cpu = proc.get('cpu_usage', 0)
            cpu_style = "bold red" if cpu > 80 else "bold yellow" if cpu > 50 else "green"
            
            table.add_row(
                str(pid),
                proc.get('name', 'unknown')[:20],
                proc.get('type', 'unknown'),
                f"[{cpu_style}]{cpu:.1f}%[/{cpu_style}]",
                str(proc.get('nice', 0))
            )
        
        return Panel(
            table,
            title="[bold green]Active Processes Being Optimized[/bold green]",
            border_style="green",
            padding=(1, 2)
        )
    
    def create_action_log(self):
        """Show recent scheduler actions"""
        actions = self.read_actions()
        
        if not actions:
            return Panel("[yellow]No actions recorded yet[/yellow]", title="Recent Actions")
        
        text = Text()
        for action in actions[-8:]:
            # Parse timestamp and action
            parts = action.split(' - ', 1)
            if len(parts) == 2:
                timestamp, action_text = parts
                text.append(f"[{timestamp}] ", style="dim cyan")
                text.append(f"{action_text}\n", style="white")
            else:
                text.append(f"{action}\n", style="white")
        
        return Panel(
            text,
            title="[bold magenta]Scheduler Actions Log[/bold magenta]",
            border_style="magenta",
            padding=(1, 2)
        )
    
    def create_layout(self):
        """Create the dashboard layout"""
        layout = Layout()
        
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3)
        )
        
        layout["main"].split_row(
            Layout(name="left"),
            Layout(name="right")
        )
        
        layout["left"].split_column(
            Layout(name="improvements", size=12),
            Layout(name="training", size=10),
            Layout(name="chart")
        )
        
        layout["right"].split_column(
            Layout(name="processes"),
            Layout(name="actions")
        )
        
        return layout
    
    def update_layout(self, layout):
        """Update all panels"""
        # Read latest data
        self.read_metrics()
        self.read_state()
        
        # Update panels
        layout["header"].update(self.create_header())
        layout["improvements"].update(self.create_improvement_panel())
        layout["training"].update(self.create_training_panel())
        layout["chart"].update(self.create_cpu_chart())
        layout["processes"].update(self.create_process_panel())
        layout["actions"].update(self.create_action_log())
        
        # Footer
        footer_text = Text()
        footer_text.append("Press ", style="dim")
        footer_text.append("Ctrl+C", style="bold red")
        footer_text.append(" to exit | Refreshing every 2 seconds | ", style="dim")
        footer_text.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), style="cyan")
        
        layout["footer"].update(Panel(Align.center(footer_text), border_style="dim"))
    
    def run(self):
        """Run the dashboard"""
        layout = self.create_layout()
        
        try:
            with Live(layout, refresh_per_second=0.5, screen=True) as live:
                while True:
                    self.update_layout(layout)
                    time.sleep(2)
        except KeyboardInterrupt:
            console.print("\n[yellow]Dashboard stopped by user[/yellow]")

if __name__ == "__main__":
    console.print("[bold cyan]Starting Enhanced Terminal Dashboard...[/bold cyan]\n")
    
    # Check if data files exist
    if not os.path.exists('/tmp/scheduler_metrics.csv'):
        console.print("[yellow]Warning: /tmp/scheduler_metrics.csv not found[/yellow]")
        console.print("[yellow]Make sure the DQN optimizer is running![/yellow]\n")
    
    dashboard = EnhancedDashboard()
    dashboard.run()