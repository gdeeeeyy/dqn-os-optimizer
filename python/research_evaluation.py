#!/usr/bin/env python3
"""
Research-Grade Evaluation Framework
Comprehensive statistical analysis for publication-quality results
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from typing import Dict, List, Tuple
import json
from pathlib import Path


class ResearchEvaluator:
    """Rigorous evaluation for research paper"""
    
    def __init__(self, results_dir='results'):
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)
        
        # Load experimental data
        self.baseline_data = None
        self.dqn_data = None
        self.random_data = None  # For ablation study
        
        # Statistical test results
        self.statistical_tests = {}
        
    def load_experiment_data(self, csv_path: str) -> pd.DataFrame:
        """Load metrics from CSV"""
        df = pd.read_csv(csv_path)
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
        return df
    
    def compute_performance_metrics(self, df: pd.DataFrame) -> Dict:
        """Compute comprehensive performance metrics"""
        
        metrics = {}
        
        # 1. CPU Utilization Metrics
        cpu_util = df['avg_util']
        metrics['cpu_mean'] = cpu_util.mean()
        metrics['cpu_std'] = cpu_util.std()
        metrics['cpu_cv'] = cpu_util.std() / cpu_util.mean() if cpu_util.mean() > 0 else 0  # Coefficient of variation
        metrics['cpu_stability'] = 100 - metrics['cpu_cv'] * 100  # Stability score
        
        # 2. Context Switch Metrics
        cs = df['context_switches']
        metrics['cs_mean'] = cs.mean()
        metrics['cs_std'] = cs.std()
        metrics['cs_max'] = cs.max()
        metrics['cs_p95'] = cs.quantile(0.95)
        
        # 3. Load Average Metrics
        load = df['load_avg']
        metrics['load_mean'] = load.mean()
        metrics['load_std'] = load.std()
        metrics['load_max'] = load.max()
        
        # 4. Task Metrics
        metrics['running_tasks_mean'] = df['running_tasks'].mean()
        metrics['blocked_tasks_mean'] = df['blocked_tasks'].mean()
        
        # 5. Responsiveness (based on load and blocked tasks)
        metrics['responsiveness'] = 100 / (1 + metrics['load_mean'] + metrics['blocked_tasks_mean'])
        
        # 6. Efficiency Score (composite metric)
        # Balance between CPU utilization and stability
        ideal_cpu = 60  # Target CPU utilization
        cpu_penalty = abs(metrics['cpu_mean'] - ideal_cpu) / ideal_cpu
        efficiency = (1 - cpu_penalty) * (metrics['cpu_stability'] / 100)
        metrics['efficiency_score'] = efficiency * 100
        
        return metrics
    
    def statistical_comparison(self, baseline: pd.Series, treatment: pd.Series, 
                               metric_name: str) -> Dict:
        """
        Perform statistical significance tests
        Returns p-values and effect sizes
        """
        
        # 1. T-test (parametric)
        t_stat, t_pvalue = stats.ttest_ind(baseline, treatment)
        
        # 2. Mann-Whitney U test (non-parametric)
        u_stat, u_pvalue = stats.mannwhitneyu(baseline, treatment, alternative='two-sided')
        
        # 3. Effect size (Cohen's d)
        cohens_d = (treatment.mean() - baseline.mean()) / np.sqrt(
            (baseline.std()**2 + treatment.std()**2) / 2
        )
        
        # 4. Percentage improvement
        pct_improvement = ((baseline.mean() - treatment.mean()) / baseline.mean() * 100)
        
        # 5. Confidence interval (95%)
        ci_low, ci_high = stats.t.interval(
            0.95, 
            len(treatment)-1,
            loc=treatment.mean(),
            scale=stats.sem(treatment)
        )
        
        return {
            'metric': metric_name,
            'baseline_mean': baseline.mean(),
            'baseline_std': baseline.std(),
            'treatment_mean': treatment.mean(),
            'treatment_std': treatment.std(),
            't_statistic': t_stat,
            't_pvalue': t_pvalue,
            'u_statistic': u_stat,
            'u_pvalue': u_pvalue,
            'cohens_d': cohens_d,
            'effect_size_interpretation': self.interpret_cohens_d(cohens_d),
            'pct_improvement': pct_improvement,
            'ci_95_low': ci_low,
            'ci_95_high': ci_high,
            'statistically_significant': u_pvalue < 0.05
        }
    
    @staticmethod
    def interpret_cohens_d(d: float) -> str:
        """Interpret Cohen's d effect size"""
        abs_d = abs(d)
        if abs_d < 0.2:
            return "negligible"
        elif abs_d < 0.5:
            return "small"
        elif abs_d < 0.8:
            return "medium"
        else:
            return "large"
    
    def ablation_study(self) -> Dict:
        """
        Ablation study: Compare different components
        - Full DQN (Dueling + PER + Double)
        - DQN without Dueling
        - DQN without PER
        - Random policy
        - Greedy policy
        """
        
        # This requires running multiple experiments
        # For now, we'll document the framework
        
        ablation_results = {
            'components_tested': [
                'Full DQN (Dueling + PER + Double)',
                'DQN without Dueling',
                'DQN without Prioritized Replay',
                'DQN without Double Q-learning',
                'Random Policy',
                'Heuristic Policy'
            ],
            'metrics': [
                'cpu_stability',
                'context_switch_reduction',
                'learning_speed',
                'final_reward'
            ]
        }
        
        return ablation_results
    
    def generate_latex_table(self, comparison_results: List[Dict]) -> str:
        """Generate LaTeX table for paper"""
        
        latex = "\\begin{table}[h]\n"
        latex += "\\centering\n"
        latex += "\\caption{Performance Comparison: Baseline vs DQN-Optimized Scheduler}\n"
        latex += "\\label{tab:performance}\n"
        latex += "\\begin{tabular}{lrrrrr}\n"
        latex += "\\hline\n"
        latex += "Metric & Baseline & DQN & Improvement & $p$-value & Effect Size \\\\\n"
        latex += "\\hline\n"
        
        for result in comparison_results:
            metric = result['metric'].replace('_', ' ').title()
            baseline = f"{result['baseline_mean']:.2f}"
            treatment = f"{result['treatment_mean']:.2f}"
            improvement = f"{result['pct_improvement']:+.1f}\\%"
            pvalue = f"{result['u_pvalue']:.4f}" if result['u_pvalue'] >= 0.001 else "$< 0.001$"
            effect = result['effect_size_interpretation']
            
            latex += f"{metric} & {baseline} & {treatment} & {improvement} & {pvalue} & {effect} \\\\\n"
        
        latex += "\\hline\n"
        latex += "\\end{tabular}\n"
        latex += "\\end{table}\n"
        
        return latex
    
    def plot_learning_curves(self, rewards: List[float], save_path: str):
        """Plot learning curves with confidence intervals"""
        
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # Moving average
        window = 100
        rewards_ma = pd.Series(rewards).rolling(window).mean()
        rewards_std = pd.Series(rewards).rolling(window).std()
        
        # 1. Reward over time
        ax = axes[0, 0]
        ax.plot(rewards_ma, label='Reward (MA-100)', linewidth=2)
        ax.fill_between(range(len(rewards_ma)), 
                        rewards_ma - rewards_std,
                        rewards_ma + rewards_std,
                        alpha=0.3)
        ax.set_xlabel('Training Steps')
        ax.set_ylabel('Reward')
        ax.set_title('Learning Progress')
        ax.legend()
        ax.grid(alpha=0.3)
        
        # 2. Cumulative reward
        ax = axes[0, 1]
        cumulative = np.cumsum(rewards)
        ax.plot(cumulative, linewidth=2, color='green')
        ax.set_xlabel('Training Steps')
        ax.set_ylabel('Cumulative Reward')
        ax.set_title('Cumulative Learning')
        ax.grid(alpha=0.3)
        
        # 3. Reward distribution
        ax = axes[1, 0]
        ax.hist(rewards, bins=50, alpha=0.7, edgecolor='black')
        ax.axvline(np.mean(rewards), color='red', linestyle='--', 
                   label=f'Mean: {np.mean(rewards):.3f}')
        ax.set_xlabel('Reward')
        ax.set_ylabel('Frequency')
        ax.set_title('Reward Distribution')
        ax.legend()
        
        # 4. Episode length vs reward
        ax = axes[1, 1]
        episodes = np.arange(len(rewards)) // 100  # Approximate episodes
        episode_rewards = [np.mean(rewards[i:i+100]) for i in range(0, len(rewards), 100)]
        ax.plot(episode_rewards, marker='o', linewidth=2)
        ax.set_xlabel('Episode')
        ax.set_ylabel('Average Reward')
        ax.set_title('Per-Episode Performance')
        ax.grid(alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"✓ Learning curves saved to {save_path}")
    
    def plot_comparison(self, baseline_df: pd.DataFrame, dqn_df: pd.DataFrame, 
                       save_path: str):
        """Generate publication-quality comparison plots"""
        
        fig, axes = plt.subplots(2, 3, figsize=(18, 10))
        
        # 1. CPU Utilization
        ax = axes[0, 0]
        ax.plot(baseline_df.index, baseline_df['avg_util'], 
                label='Baseline', alpha=0.7, linewidth=1.5)
        ax.plot(dqn_df.index, dqn_df['avg_util'], 
                label='DQN-Optimized', alpha=0.7, linewidth=1.5)
        ax.axhline(baseline_df['avg_util'].mean(), color='blue', 
                   linestyle='--', alpha=0.5, label='Baseline Mean')
        ax.axhline(dqn_df['avg_util'].mean(), color='orange', 
                   linestyle='--', alpha=0.5, label='DQN Mean')
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('CPU Utilization (%)')
        ax.set_title('CPU Utilization Comparison')
        ax.legend(fontsize=8)
        ax.grid(alpha=0.3)
        
        # 2. CPU Distribution
        ax = axes[0, 1]
        ax.hist(baseline_df['avg_util'], bins=30, alpha=0.5, 
                label='Baseline', density=True)
        ax.hist(dqn_df['avg_util'], bins=30, alpha=0.5, 
                label='DQN-Optimized', density=True)
        ax.set_xlabel('CPU Utilization (%)')
        ax.set_ylabel('Density')
        ax.set_title('CPU Utilization Distribution')
        ax.legend()
        ax.grid(alpha=0.3)
        
        # 3. Context Switches
        ax = axes[0, 2]
        ax.plot(baseline_df.index, baseline_df['context_switches'], 
                label='Baseline', alpha=0.7)
        ax.plot(dqn_df.index, dqn_df['context_switches'], 
                label='DQN-Optimized', alpha=0.7)
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Context Switches/sec')
        ax.set_title('Context Switch Rate')
        ax.legend(fontsize=8)
        ax.grid(alpha=0.3)
        
        # 4. Load Average
        ax = axes[1, 0]
        ax.plot(baseline_df.index, baseline_df['load_avg'], 
                label='Baseline', alpha=0.7)
        ax.plot(dqn_df.index, dqn_df['load_avg'], 
                label='DQN-Optimized', alpha=0.7)
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Load Average')
        ax.set_title('System Load Average')
        ax.legend()
        ax.grid(alpha=0.3)
        
        # 5. Box plot comparison
        ax = axes[1, 1]
        data_to_plot = [baseline_df['avg_util'], dqn_df['avg_util']]
        box = ax.boxplot(data_to_plot, labels=['Baseline', 'DQN'],
                         patch_artist=True)
        box['boxes'][0].set_facecolor('lightblue')
        box['boxes'][1].set_facecolor('lightgreen')
        ax.set_ylabel('CPU Utilization (%)')
        ax.set_title('CPU Utilization Variability')
        ax.grid(alpha=0.3)
        
        # 6. Improvement metrics
        ax = axes[1, 2]
        
        baseline_metrics = self.compute_performance_metrics(baseline_df)
        dqn_metrics = self.compute_performance_metrics(dqn_df)
        
        improvements = {
            'CPU Stability': ((dqn_metrics['cpu_stability'] - baseline_metrics['cpu_stability']) 
                             / baseline_metrics['cpu_stability'] * 100),
            'CS Reduction': ((baseline_metrics['cs_mean'] - dqn_metrics['cs_mean']) 
                            / baseline_metrics['cs_mean'] * 100),
            'Load Reduction': ((baseline_metrics['load_mean'] - dqn_metrics['load_mean']) 
                              / baseline_metrics['load_mean'] * 100),
        }
        
        colors = ['green' if v > 0 else 'red' for v in improvements.values()]
        bars = ax.barh(list(improvements.keys()), list(improvements.values()), 
                       color=colors, alpha=0.7)
        ax.axvline(0, color='black', linewidth=0.8)
        ax.set_xlabel('Improvement (%)')
        ax.set_title('Performance Improvements')
        ax.grid(alpha=0.3, axis='x')
        
        # Add value labels
        for i, (bar, value) in enumerate(zip(bars, improvements.values())):
            ax.text(value, i, f'{value:+.1f}%', 
                   va='center', ha='left' if value > 0 else 'right')
        
        plt.suptitle('DQN Scheduler vs Baseline: Comprehensive Comparison', 
                    fontsize=16, fontweight='bold')
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"✓ Comparison plots saved to {save_path}")
    
    def generate_research_report(self, baseline_df: pd.DataFrame, 
                                dqn_df: pd.DataFrame) -> str:
        """Generate comprehensive research report"""
        
        report = []
        report.append("="*80)
        report.append("RESEARCH EVALUATION REPORT")
        report.append("Deep Reinforcement Learning for CPU Scheduling Optimization")
        report.append("="*80)
        report.append("")
        
        # Compute metrics
        baseline_metrics = self.compute_performance_metrics(baseline_df)
        dqn_metrics = self.compute_performance_metrics(dqn_df)
        
        # Statistical tests
        tests = [
            ('CPU Utilization Variance', baseline_df['avg_util'], dqn_df['avg_util']),
            ('Context Switches', baseline_df['context_switches'], dqn_df['context_switches']),
            ('Load Average', baseline_df['load_avg'], dqn_df['load_avg']),
        ]
        
        comparison_results = []
        for metric_name, baseline_series, dqn_series in tests:
            result = self.statistical_comparison(baseline_series, dqn_series, metric_name)
            comparison_results.append(result)
        
        # Performance summary
        report.append("1. PERFORMANCE SUMMARY")
        report.append("-" * 80)
        report.append(f"{'Metric':<30} {'Baseline':<15} {'DQN':<15} {'Improvement':<15}")
        report.append("-" * 80)
        
        metrics_to_report = [
            ('CPU Utilization Mean (%)', 'cpu_mean', 'cpu_mean'),
            ('CPU Stability Score', 'cpu_stability', 'cpu_stability'),
            ('Context Switches/sec', 'cs_mean', 'cs_mean'),
            ('Load Average', 'load_mean', 'load_mean'),
            ('Efficiency Score', 'efficiency_score', 'efficiency_score'),
        ]
        
        for label, baseline_key, dqn_key in metrics_to_report:
            baseline_val = baseline_metrics[baseline_key]
            dqn_val = dqn_metrics[dqn_key]
            improvement = ((dqn_val - baseline_val) / baseline_val * 100) if 'Reduction' not in label else ((baseline_val - dqn_val) / baseline_val * 100)
            
            report.append(f"{label:<30} {baseline_val:<15.2f} {dqn_val:<15.2f} {improvement:+14.1f}%")
        
        report.append("")
        
        # Statistical significance
        report.append("2. STATISTICAL SIGNIFICANCE TESTS")
        report.append("-" * 80)
        
        for result in comparison_results:
            report.append(f"\n{result['metric']}:")
            report.append(f"  Mann-Whitney U p-value: {result['u_pvalue']:.6f}")
            report.append(f"  Cohen's d: {result['cohens_d']:.3f} ({result['effect_size_interpretation']})")
            report.append(f"  Statistically significant: {'YES' if result['statistically_significant'] else 'NO'}")
            report.append(f"  95% CI: [{result['ci_95_low']:.2f}, {result['ci_95_high']:.2f}]")
        
        report.append("")
        
        # Conclusions
        report.append("3. CONCLUSIONS")
        report.append("-" * 80)
        
        significant_improvements = sum(1 for r in comparison_results if r['statistically_significant'] and r['pct_improvement'] > 0)
        
        if significant_improvements >= 2:
            report.append("✓ STRONG EVIDENCE of performance improvement")
            report.append("  The DQN-based scheduler shows statistically significant improvements")
            report.append("  across multiple metrics compared to the baseline scheduler.")
        elif significant_improvements == 1:
            report.append("✓ MODERATE EVIDENCE of performance improvement")
            report.append("  Some metrics show statistically significant improvement.")
        else:
            report.append("⚠ LIMITED EVIDENCE of performance improvement")
            report.append("  Further experimentation with longer duration or different workloads recommended.")
        
        report.append("")
        report.append("4. RECOMMENDATIONS FOR PUBLICATION")
        report.append("-" * 80)
        report.append("- Include ablation study results comparing architectural choices")
        report.append("- Run experiments under varied workload scenarios (CPU-intensive, I/O-intensive, mixed)")
        report.append("- Compare against additional baselines (CFS, other heuristics)")
        report.append("- Conduct multi-day experiments for long-term stability")
        report.append("- Analyze per-process fairness and response time distributions")
        
        report.append("")
        report.append("="*80)
        
        return "\n".join(report)
    
    def full_evaluation(self, metrics_csv: str = '/tmp/scheduler_metrics.csv'):
        """Run complete evaluation pipeline"""
        
        print("📊 Loading experimental data...")
        
        # Check if file exists
        if not os.path.exists(metrics_csv):
            print(f"❌ Metrics file not found: {metrics_csv}")
            print("\nRun the system first to collect data:")
            print("  ./run_with_dashboard.sh")
            return
        
        # Load all data
        all_df = self.load_experiment_data(metrics_csv)
        
        # Split into baseline and RL-controlled
        baseline_df = all_df[all_df['mode'] == 'baseline']
        dqn_df = all_df[all_df['mode'] == 'rl_controlled']
        
        if len(baseline_df) == 0:
            print("❌ No baseline data found in metrics file!")
            print("Make sure the system ran for at least 60 seconds.")
            return
        
        if len(dqn_df) == 0:
            print("❌ No RL-controlled data found in metrics file!")
            print("Make sure the DQN agent ran and collected data.")
            return
        
        print(f"✓ Loaded {len(baseline_df)} baseline samples")
        print(f"✓ Loaded {len(dqn_df)} RL-controlled samples")
        
        print("📈 Generating comparison plots...")
        self.plot_comparison(baseline_df, dqn_df, 
                           str(self.results_dir / 'research_comparison.png'))
        
        print("📄 Generating research report...")
        report = self.generate_research_report(baseline_df, dqn_df)
        
        report_path = self.results_dir / 'research_report.txt'
        with open(report_path, 'w') as f:
            f.write(report)
        
        print(f"✓ Report saved to {report_path}")
        print("\n" + report)
        
        print("\n📝 Generating LaTeX table...")
        comparison_results = []
        tests = [
            ('CPU Variance', baseline_df['avg_util'], dqn_df['avg_util']),
            ('Context Switches', baseline_df['context_switches'], dqn_df['context_switches']),
            ('Load Average', baseline_df['load_avg'], dqn_df['load_avg']),
        ]
        
        for metric_name, baseline_series, dqn_series in tests:
            result = self.statistical_comparison(baseline_series, dqn_series, metric_name)
            comparison_results.append(result)
        
        latex_table = self.generate_latex_table(comparison_results)
        latex_path = self.results_dir / 'performance_table.tex'
        with open(latex_path, 'w') as f:
            f.write(latex_table)
        
        print(f"✓ LaTeX table saved to {latex_path}")
        
        print("\n✅ Full evaluation complete!")


if __name__ == '__main__':
    evaluator = ResearchEvaluator()
    
    # Check if metrics file exists
    metrics_file = '/tmp/scheduler_metrics.csv'
    
    if not os.path.exists(metrics_file):
        print("=" * 80)
        print("❌ NO DATA FOUND")
        print("=" * 80)
        print()
        print("The metrics file does not exist yet.")
        print()
        print("To collect real data:")
        print("  1. Run: ./run_with_dashboard.sh")
        print("  2. Wait for data collection (6+ minutes)")
        print("  3. Stop the system (Ctrl+C or ./stop.sh)")
        print("  4. Run this script again")
        print()
        print("The system will collect real CPU metrics from your system.")
        print("=" * 80)
    else:
        # Run full evaluation
        evaluator.full_evaluation(metrics_csv=metrics_file)