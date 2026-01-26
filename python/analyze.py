#!/usr/bin/env python3
"""
Performance Analysis and Visualization
Generate comprehensive plots comparing baseline vs RL-optimized scheduling
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats
import seaborn as sns

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

def load_metrics(csv_path='/tmp/scheduler_metrics.csv'):
    """Load metrics CSV"""
    try:
        df = pd.read_csv(csv_path)
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
        return df
    except Exception as e:
        print(f"Error loading metrics: {e}")
        return None

def calculate_statistics(df):
    """Calculate performance statistics"""
    baseline = df[df['mode'] == 'baseline']
    rl = df[df['mode'] == 'rl_controlled']
    
    stats_dict = {
        'Baseline CPU Mean': baseline['avg_util'].mean(),
        'Baseline CPU Std': baseline['avg_util'].std(),
        'RL CPU Mean': rl['avg_util'].mean(),
        'RL CPU Std': rl['avg_util'].std(),
        'CPU Improvement (%)': ((baseline['avg_util'].std() - rl['avg_util'].std()) / baseline['avg_util'].std() * 100),
        'Baseline CS Mean': baseline['context_switches'].mean(),
        'RL CS Mean': rl['context_switches'].mean(),
        'CS Improvement (%)': ((baseline['context_switches'].mean() - rl['context_switches'].mean()) / baseline['context_switches'].mean() * 100),
        'Baseline Load Avg': baseline['load_avg'].mean(),
        'RL Load Avg': rl['load_avg'].mean(),
    }
    
    return stats_dict

def plot_cpu_comparison(df, ax):
    """Plot CPU utilization comparison"""
    baseline = df[df['mode'] == 'baseline']
    rl = df[df['mode'] == 'rl_controlled']
    
    ax.plot(range(len(baseline)), baseline['avg_util'].values, 
            label='Baseline', alpha=0.7, linewidth=1.5)
    ax.plot(range(len(rl)), rl['avg_util'].values, 
            label='RL-Optimized', alpha=0.7, linewidth=1.5)
    
    ax.axhline(baseline['avg_util'].mean(), color='blue', 
               linestyle='--', alpha=0.5, label='Baseline Mean')
    ax.axhline(rl['avg_util'].mean(), color='orange', 
               linestyle='--', alpha=0.5, label='RL Mean')
    
    ax.set_xlabel('Time (seconds)')
    ax.set_ylabel('CPU Utilization (%)')
    ax.set_title('CPU Utilization: Baseline vs RL-Optimized')
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)

def plot_stability(df, ax):
    """Plot CPU utilization variance over time"""
    baseline = df[df['mode'] == 'baseline']
    rl = df[df['mode'] == 'rl_controlled']
    
    window = 10
    baseline_rolling_std = baseline['avg_util'].rolling(window=window).std()
    rl_rolling_std = rl['avg_util'].rolling(window=window).std()
    
    ax.plot(range(len(baseline_rolling_std)), baseline_rolling_std.values, 
            label='Baseline Variance', alpha=0.7, linewidth=2)
    ax.plot(range(len(rl_rolling_std)), rl_rolling_std.values, 
            label='RL-Optimized Variance', alpha=0.7, linewidth=2)
    
    ax.set_xlabel('Time (seconds)')
    ax.set_ylabel('CPU Utilization Std Dev (10s window)')
    ax.set_title('Scheduling Stability Comparison')
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)

def plot_context_switches(df, ax):
    """Plot context switches comparison"""
    baseline = df[df['mode'] == 'baseline']
    rl = df[df['mode'] == 'rl_controlled']
    
    ax.plot(range(len(baseline)), baseline['context_switches'].values, 
            label='Baseline', alpha=0.7, linewidth=1.5)
    ax.plot(range(len(rl)), rl['context_switches'].values, 
            label='RL-Optimized', alpha=0.7, linewidth=1.5)
    
    ax.set_xlabel('Time (seconds)')
    ax.set_ylabel('Context Switches per Second')
    ax.set_title('Context Switch Rate Comparison')
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)

def plot_load_average(df, ax):
    """Plot load average comparison"""
    baseline = df[df['mode'] == 'baseline']
    rl = df[df['mode'] == 'rl_controlled']
    
    ax.plot(range(len(baseline)), baseline['load_avg'].values, 
            label='Baseline', alpha=0.7, linewidth=1.5)
    ax.plot(range(len(rl)), rl['load_avg'].values, 
            label='RL-Optimized', alpha=0.7, linewidth=1.5)
    
    ax.set_xlabel('Time (seconds)')
    ax.set_ylabel('Load Average (1 minute)')
    ax.set_title('System Load Average Comparison')
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)

def plot_distribution(df, ax):
    """Plot CPU utilization distribution"""
    baseline = df[df['mode'] == 'baseline']['avg_util']
    rl = df[df['mode'] == 'rl_controlled']['avg_util']
    
    ax.hist(baseline, bins=30, alpha=0.5, label='Baseline', density=True)
    ax.hist(rl, bins=30, alpha=0.5, label='RL-Optimized', density=True)
    
    ax.set_xlabel('CPU Utilization (%)')
    ax.set_ylabel('Probability Density')
    ax.set_title('CPU Utilization Distribution')
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)

def plot_improvement_bars(stats, ax):
    """Plot improvement metrics as bar chart"""
    metrics = ['CPU Stability\nImprovement', 'Context Switch\nReduction']
    values = [
        stats['CPU Improvement (%)'],
        stats['CS Improvement (%)']
    ]
    
    colors = ['green' if v > 0 else 'red' for v in values]
    bars = ax.bar(metrics, values, color=colors, alpha=0.7)
    
    # Add value labels
    for bar, value in zip(bars, values):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{value:.1f}%',
                ha='center', va='bottom' if value > 0 else 'top')
    
    ax.set_ylabel('Improvement (%)')
    ax.set_title('Performance Improvements')
    ax.axhline(0, color='black', linewidth=0.8)
    ax.grid(True, alpha=0.3, axis='y')

def create_comprehensive_report(df):
    """Create comprehensive analysis report"""
    fig = plt.figure(figsize=(20, 12))
    gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
    
    # Main plots
    ax1 = fig.add_subplot(gs[0, :2])
    plot_cpu_comparison(df, ax1)
    
    ax2 = fig.add_subplot(gs[0, 2])
    plot_distribution(df, ax2)
    
    ax3 = fig.add_subplot(gs[1, 0])
    plot_stability(df, ax3)
    
    ax4 = fig.add_subplot(gs[1, 1])
    plot_context_switches(df, ax4)
    
    ax5 = fig.add_subplot(gs[1, 2])
    plot_load_average(df, ax5)
    
    # Statistics
    stats = calculate_statistics(df)
    ax6 = fig.add_subplot(gs[2, :2])
    plot_improvement_bars(stats, ax6)
    
    # Text summary
    ax7 = fig.add_subplot(gs[2, 2])
    ax7.axis('off')
    
    summary_text = f"""
    PERFORMANCE SUMMARY
    ══════════════════════════════
    
    CPU Utilization:
      Baseline: {stats['Baseline CPU Mean']:.2f}% ± {stats['Baseline CPU Std']:.2f}%
      RL-Optimized: {stats['RL CPU Mean']:.2f}% ± {stats['RL CPU Std']:.2f}%
      Stability Gain: {stats['CPU Improvement (%)']:.1f}%
    
    Context Switches:
      Baseline: {stats['Baseline CS Mean']:.0f} /sec
      RL-Optimized: {stats['RL CS Mean']:.0f} /sec
      Reduction: {stats['CS Improvement (%)']:.1f}%
    
    Load Average:
      Baseline: {stats['Baseline Load Avg']:.2f}
      RL-Optimized: {stats['RL Load Avg']:.2f}
    """
    
    ax7.text(0.1, 0.9, summary_text, transform=ax7.transAxes,
             fontsize=10, verticalalignment='top', fontfamily='monospace',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))
    
    plt.suptitle('CPU Scheduler Optimizer - Deep RL Performance Analysis', 
                 fontsize=16, fontweight='bold')
    
    plt.savefig('scheduler_analysis.png', dpi=300, bbox_inches='tight')
    print("\n✅ Comprehensive analysis saved to 'scheduler_analysis.png'")
    
    # Also save individual plots
    save_individual_plots(df, stats)
    
    return stats

def save_individual_plots(df, stats):
    """Save individual plots for detailed analysis"""
    
    # CPU comparison
    fig, ax = plt.subplots(figsize=(12, 6))
    plot_cpu_comparison(df, ax)
    plt.tight_layout()
    plt.savefig('cpu_comparison.png', dpi=200)
    plt.close()
    
    # Stability
    fig, ax = plt.subplots(figsize=(12, 6))
    plot_stability(df, ax)
    plt.tight_layout()
    plt.savefig('stability_comparison.png', dpi=200)
    plt.close()
    
    # Context switches
    fig, ax = plt.subplots(figsize=(12, 6))
    plot_context_switches(df, ax)
    plt.tight_layout()
    plt.savefig('context_switches.png', dpi=200)
    plt.close()
    
    print("✅ Individual plots saved:")
    print("   - cpu_comparison.png")
    print("   - stability_comparison.png")
    print("   - context_switches.png")

def main():
    print("=" * 60)
    print("📊 CPU Scheduler Performance Analysis")
    print("=" * 60)
    
    df = load_metrics()
    
    if df is None or len(df) == 0:
        print("❌ No metrics data found!")
        return
    
    print(f"\n📈 Loaded {len(df)} data points")
    print(f"   Baseline samples: {len(df[df['mode'] == 'baseline'])}")
    print(f"   RL-controlled samples: {len(df[df['mode'] == 'rl_controlled'])}")
    
    stats = create_comprehensive_report(df)
    
    print("\n" + "=" * 60)
    print("PERFORMANCE SUMMARY")
    print("=" * 60)
    for key, value in stats.items():
        print(f"{key:.<40} {value:>10.2f}")
    print("=" * 60)
    
    print("\n✅ Analysis complete!")

if __name__ == '__main__':
    main()