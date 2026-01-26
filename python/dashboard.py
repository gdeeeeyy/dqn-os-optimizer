#!/usr/bin/env python3
"""
Real-time Terminal Dashboard for CPU Scheduler Optimizer
htop-style visualization of scheduling decisions and learning progress
"""

import curses
import time
import json
import os
import csv
from collections import deque
from datetime import datetime

METRICS_FILE = '/tmp/scheduler_metrics.csv'
STATE_FILE = '/tmp/rl_state.json'
ACTION_LOG = '/tmp/scheduler_actions.log'

class Dashboard:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.height, self.width = stdscr.getmaxyx()
        curses.curs_set(0)
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(5, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        
        self.cpu_history = deque(maxlen=60)
        self.cs_history = deque(maxlen=60)
        self.stability_history = deque(maxlen=60)
        self.actions = deque(maxlen=10)
        
        self.baseline_cpu_avg = 0.0
        self.rl_cpu_avg = 0.0
        self.baseline_cs_avg = 0
        self.rl_cs_avg = 0
        
    def load_metrics(self):
        """Load latest metrics from CSV"""
        if not os.path.exists(METRICS_FILE):
            return
        
        try:
            with open(METRICS_FILE, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
                if not rows:
                    return
                
                # Calculate baseline stats
                baseline_rows = [r for r in rows if r['mode'] == 'baseline']
                if baseline_rows:
                    self.baseline_cpu_avg = sum(float(r['avg_util']) for r in baseline_rows) / len(baseline_rows)
                    self.baseline_cs_avg = sum(int(r['context_switches']) for r in baseline_rows) / len(baseline_rows)
                
                # Calculate RL stats
                rl_rows = [r for r in rows if r['mode'] == 'rl_controlled']
                if rl_rows:
                    self.rl_cpu_avg = sum(float(r['avg_util']) for r in rl_rows) / len(rl_rows)
                    self.rl_cs_avg = sum(int(r['context_switches']) for r in rl_rows) / len(rl_rows)
                    
                    # Update recent history
                    recent = rl_rows[-60:]
                    for row in recent:
                        self.cpu_history.append(float(row['avg_util']))
                        self.cs_history.append(int(row['context_switches']))
        except Exception as e:
            pass
    
    def load_current_state(self):
        """Load current state from JSON"""
        if not os.path.exists(STATE_FILE):
            return {}
        
        try:
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    
    def load_recent_actions(self):
        """Load recent actions from log"""
        if not os.path.exists(ACTION_LOG):
            return
        
        try:
            with open(ACTION_LOG, 'r') as f:
                lines = f.readlines()
                self.actions = deque(lines[-10:], maxlen=10)
        except:
            pass
    
    def draw_header(self):
        """Draw header section"""
        header = "═" * self.width
        title = "  CPU SCHEDULER OPTIMIZER - DEEP RL DASHBOARD  "
        title_x = (self.width - len(title)) // 2
        
        self.stdscr.addstr(0, 0, header, curses.color_pair(2) | curses.A_BOLD)
        self.stdscr.addstr(0, title_x, title, curses.color_pair(2) | curses.A_BOLD)
        self.stdscr.addstr(1, 2, f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", curses.color_pair(1))
    
    def draw_metrics(self, state):
        """Draw current metrics section"""
        y = 3
        self.stdscr.addstr(y, 2, "┌─ CURRENT METRICS ─────────────────────────────────────┐", curses.color_pair(2))
        
        cpu = state.get('cpu_util', 0.0)
        cs = state.get('context_switches', 0)
        stability = state.get('stability', 0.0)
        running = state.get('running_tasks', 0)
        load_avg = state.get('load_avg', 0.0)
        
        # CPU utilization bar
        y += 1
        cpu_bar = self.create_bar(cpu, 100, 40)
        cpu_color = self.get_color_for_value(cpu, 70, 85)
        self.stdscr.addstr(y, 2, f"│ CPU Usage:  {cpu:5.1f}% ", curses.color_pair(2))
        self.stdscr.addstr(y, 25, cpu_bar, curses.color_pair(cpu_color))
        self.stdscr.addstr(y, 55, "│", curses.color_pair(2))
        
        # Context switches
        y += 1
        cs_level = min(cs / 100, 100)
        cs_bar = self.create_bar(cs_level, 100, 20)
        cs_color = 1 if cs < 5000 else 3 if cs < 10000 else 4
        self.stdscr.addstr(y, 2, f"│ Context SW: {cs:6d}  ", curses.color_pair(2))
        self.stdscr.addstr(y, 25, cs_bar, curses.color_pair(cs_color))
        self.stdscr.addstr(y, 55, "│", curses.color_pair(2))
        
        # Stability
        y += 1
        stab_bar = self.create_bar(stability, 100, 40)
        stab_color = 4 if stability < 50 else 3 if stability < 75 else 1
        self.stdscr.addstr(y, 2, f"│ Stability:  {stability:5.1f}% ", curses.color_pair(2))
        self.stdscr.addstr(y, 25, stab_bar, curses.color_pair(stab_color))
        self.stdscr.addstr(y, 55, "│", curses.color_pair(2))
        
        # Load average
        y += 1
        self.stdscr.addstr(y, 2, f"│ Load Avg:   {load_avg:5.2f}   Running Tasks: {running:3d}      │", curses.color_pair(2))
        
        y += 1
        self.stdscr.addstr(y, 2, "└───────────────────────────────────────────────────────┘", curses.color_pair(2))
        
        return y + 1
    
    def draw_comparison(self):
        """Draw baseline vs RL comparison"""
        y = 10
        self.stdscr.addstr(y, 2, "┌─ PERFORMANCE COMPARISON ──────────────────────────────┐", curses.color_pair(2))
        
        y += 1
        self.stdscr.addstr(y, 2, "│                    Baseline    RL-Optimized    Improvement│", curses.color_pair(2))
        
        y += 1
        cpu_improvement = ((self.baseline_cpu_avg - self.rl_cpu_avg) / self.baseline_cpu_avg * 100) if self.baseline_cpu_avg > 0 else 0
        improvement_str = f"{cpu_improvement:+.1f}%"
        improvement_color = 1 if cpu_improvement > 0 else 4
        self.stdscr.addstr(y, 2, f"│ CPU Variance:      {self.baseline_cpu_avg:6.2f}%    {self.rl_cpu_avg:6.2f}%      ", curses.color_pair(2))
        self.stdscr.addstr(y, 50, improvement_str, curses.color_pair(improvement_color))
        self.stdscr.addstr(y, 57, "│", curses.color_pair(2))
        
        y += 1
        cs_improvement = ((self.baseline_cs_avg - self.rl_cs_avg) / self.baseline_cs_avg * 100) if self.baseline_cs_avg > 0 else 0
        cs_improvement_str = f"{cs_improvement:+.1f}%"
        cs_improvement_color = 1 if cs_improvement > 0 else 4
        self.stdscr.addstr(y, 2, f"│ Context Switches:  {self.baseline_cs_avg:7.0f}    {self.rl_cs_avg:7.0f}      ", curses.color_pair(2))
        self.stdscr.addstr(y, 50, cs_improvement_str, curses.color_pair(cs_improvement_color))
        self.stdscr.addstr(y, 57, "│", curses.color_pair(2))
        
        y += 1
        self.stdscr.addstr(y, 2, "└───────────────────────────────────────────────────────┘", curses.color_pair(2))
        
        return y + 1
    
    def draw_graph(self, y_start):
        """Draw CPU utilization graph"""
        y = y_start
        self.stdscr.addstr(y, 2, "┌─ CPU UTILIZATION TREND (60s) ─────────────────────────┐", curses.color_pair(2))
        
        graph_height = 8
        graph_width = 50
        
        if len(self.cpu_history) > 0:
            max_val = 100
            for i in range(graph_height):
                y += 1
                threshold = max_val * (1 - i / graph_height)
                line = "│ "
                
                for j, val in enumerate(self.cpu_history):
                    if j >= graph_width:
                        break
                    char = '█' if val >= threshold else ' '
                    line += char
                
                line += " " * (graph_width - len(self.cpu_history))
                self.stdscr.addstr(y, 2, line[:graph_width+2], curses.color_pair(1))
                self.stdscr.addstr(y, graph_width + 3, "│", curses.color_pair(2))
        
        y += 1
        self.stdscr.addstr(y, 2, "└───────────────────────────────────────────────────────┘", curses.color_pair(2))
        
        return y + 1
    
    def draw_actions(self, y_start):
        """Draw recent actions"""
        y = y_start
        self.stdscr.addstr(y, 2, "┌─ RECENT SCHEDULER ACTIONS ────────────────────────────┐", curses.color_pair(2))
        
        for i in range(6):
            y += 1
            if i < len(self.actions):
                action_text = self.actions[-(i+1)].strip()[:52]
                self.stdscr.addstr(y, 2, f"│ {action_text:<52}│", curses.color_pair(3))
            else:
                self.stdscr.addstr(y, 2, f"│ {' '*52}│", curses.color_pair(2))
        
        y += 1
        self.stdscr.addstr(y, 2, "└───────────────────────────────────────────────────────┘", curses.color_pair(2))
        
        return y + 1
    
    def draw_footer(self):
        """Draw footer with controls"""
        y = self.height - 2
        footer_text = "Press 'q' to quit | Press 'r' to refresh"
        self.stdscr.addstr(y, 2, footer_text, curses.color_pair(5) | curses.A_BOLD)
    
    def create_bar(self, value, max_value, width):
        """Create a text-based progress bar"""
        filled = int((value / max_value) * width)
        return '█' * filled + '░' * (width - filled)
    
    def get_color_for_value(self, value, warning_threshold, critical_threshold):
        """Get color based on value thresholds"""
        if value < warning_threshold:
            return 1  # Green
        elif value < critical_threshold:
            return 3  # Yellow
        else:
            return 4  # Red
    
    def run(self):
        """Main dashboard loop"""
        self.stdscr.nodelay(True)
        
        while True:
            try:
                self.stdscr.clear()
                
                # Load data
                self.load_metrics()
                state = self.load_current_state()
                self.load_recent_actions()
                
                # Draw components
                self.draw_header()
                y = self.draw_metrics(state)
                y = self.draw_comparison()
                y = self.draw_graph(y)
                y = self.draw_actions(y)
                self.draw_footer()
                
                self.stdscr.refresh()
                
                # Check for quit
                key = self.stdscr.getch()
                if key == ord('q') or key == ord('Q'):
                    break
                
                time.sleep(1.0)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                # Error handling for terminal resize, etc.
                self.height, self.width = self.stdscr.getmaxyx()
                time.sleep(0.1)

def main(stdscr):
    dashboard = Dashboard(stdscr)
    dashboard.run()

if __name__ == '__main__':
    curses.wrapper(main)