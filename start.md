# QUICK START - Collect Real Data & Generate Plots

## 🚀 Complete Setup in 5 Minutes

### **Step 1: Initial Setup (One-time, 3 minutes)**

```bash
# Navigate to project directory
cd cpu-scheduler-optimizer

# Run setup
./setup.sh

# This will:
# - Create Python virtual environment
# - Install dependencies (torch, numpy, pandas, etc.)
# - Build Rust binary
# - Create all directories
```

**Expected output:**

```
✓ Rust: rustc 1.xx.x
✓ Python: Python 3.xx
✓ Virtual environment created
✓ Python dependencies installed
✓ Rust binary compiled successfully
✓ Directory structure created

✅ Setup complete!
```

---

### **Step 2: Run System with Dashboard (6 minutes)**

```bash
# Launch interactive menu
./launcher.sh

# Select option 1: Run system with terminal dashboard
```

**OR directly:**

```bash
./run_with_dashboard.sh
```

**What happens:**

```
Phase 1 (0-60s):   BASELINE - Collecting normal scheduler metrics
Phase 2 (60-360s): RL-OPTIMIZED - DQN agent optimizing

You'll see 3 panes:
┌──────────────┬──────────────┐
│  Rust Core   │  Dashboard   │  ← Real-time metrics
├──────────────┴──────────────┤
│       DQN Agent              │  ← Learning progress
└──────────────────────────────┘
```

**Dashboard shows:**

- Real-time CPU utilization
- Context switches
- Baseline vs RL comparison (after 60s)
- Action history
- Performance improvements

**Controls:**

- `q` = Quit dashboard
- `Ctrl+B` then arrow keys = Navigate panes
- `Ctrl+C` = Stop system

---

### **Step 3: Generate Plots (1 minute)**

After the system has run for at least 2 minutes:

```bash
# Option A: Use launcher
./launcher.sh
# Select option 2: Generate analysis & plots

# Option B: Direct command
source venv/bin/activate
python3 python/research_evaluation.py
```

**Generated files:**

```
results/
├── research_comparison.png      ← Main publication figure (6 panels)
├── research_report.txt          ← Statistical analysis
└── performance_table.tex        ← LaTeX table for paper
```

---

## 📊 Expected Results (Real Data)

Your results will show **actual improvements** from your system:

```
RESEARCH EVALUATION REPORT
================================================================================

1. PERFORMANCE SUMMARY
--------------------------------------------------------------------------------
Metric                         Baseline        DQN             Improvement
--------------------------------------------------------------------------------
CPU Stability Score            XX.XX           YY.YY           +ZZ.Z%
Context Switches/sec           XXXX            YYYY            +ZZ.Z%
Load Average                   X.XX            Y.YY            +ZZ.Z%
Efficiency Score               XX.XX           YY.YY           +ZZ.Z%

2. STATISTICAL SIGNIFICANCE TESTS
--------------------------------------------------------------------------------

CPU Variance:
  Mann-Whitney U p-value: 0.XXXXXX
  Cohen's d: X.XXX (large/medium/small)
  Statistically significant: YES/NO
  95% CI: [X.XX, Y.YY]
```

---

## 🎯 Creating CPU Load (Optional)

To see more dramatic results, generate some CPU load:

```bash
# Terminal 1: Start workload generator
./generate_load.sh
# Select option 1: CPU-intensive workload

# Terminal 2: Run scheduler
./run_with_dashboard.sh

# Watch the scheduler optimize the workload!
```

---

## 🐛 Troubleshooting

### **Error: "FileNotFoundError: scheduler_metrics.csv"**

**Cause:** System hasn't run yet or didn't collect data.

**Fix:**

```bash
# 1. Make sure you ran the system first
./run_with_dashboard.sh

# 2. Let it run for at least 2 minutes (60s baseline + some RL time)

# 3. Then generate plots
python3 python/research_evaluation.py
```

### **Error: "tmux not found"**

```bash
# Install tmux
sudo apt install tmux          # Ubuntu/Debian
sudo dnf install tmux          # Fedora
```

### **Error: "Permission denied" for nice/chrt**

```bash
# Run with sudo
sudo ./run_with_dashboard.sh
```

### **No processes being profiled**

```bash
# Generate some load first
./generate_load.sh

# Then run the scheduler
./run_with_dashboard.sh
```

### **Dashboard shows "No data"**

Wait 60 seconds for baseline collection to complete. The dashboard will show comparison data after the baseline period.

---

## 📈 Viewing Results

### **View Plots:**

```bash
# List generated files
ls results/

# View PNG files
eog results/research_comparison.png     # Eye of GNOME
feh results/research_comparison.png     # feh image viewer
xdg-open results/research_comparison.png # Default viewer
```

### **View Statistical Report:**

```bash
cat results/research_report.txt
```

### **View LaTeX Table:**

```bash
cat results/performance_table.tex

# Copy this directly into your LaTeX paper!
```

---

## ⚡ Common Workflows

### **Workflow 1: Quick Test (2 minutes)**

```bash
./run_with_dashboard.sh
# Wait 2 minutes
# Press Ctrl+C
python3 python/research_evaluation.py
```

### **Workflow 2: Full Research Data (30 minutes)**

```bash
./launcher.sh
# Select option 4: Run full research experiment
# Come back in 30 minutes
# Plots auto-generated
```

### **Workflow 3: Test with Workload**

```bash
# Terminal 1
./generate_load.sh
# Select option 1

# Terminal 2
./run_with_dashboard.sh
# Watch it optimize!
```

---

## 📝 Data Collection Details

### **Where data is stored:**

```
/tmp/scheduler_metrics.csv    ← All collected metrics

Format:
timestamp,mode,avg_util,context_switches,running_tasks,blocked_tasks,load_avg
1234567890,baseline,55.2,8023,3,1,1.89
1234567891,baseline,56.1,8145,3,2,1.92
...
1234567950,rl_controlled,54.3,5234,2,0,1.52
1234567951,rl_controlled,53.8,5187,3,1,1.48
```

### **Minimum data requirements:**

- **Baseline:** At least 60 samples (60 seconds)
- **RL-controlled:** At least 60 samples (60 seconds)
- **Recommended:** 300+ samples of each for statistical significance

### **What gets measured:**

1. **CPU Utilization** - System-wide CPU usage
2. **Context Switches** - Scheduler overhead
3. **Load Average** - System responsiveness
4. **Running Tasks** - Active processes
5. **Blocked Tasks** - Waiting processes

---

## 🎓 For Publication

### **Minimum Requirements:**

✅ Run for at least 6 minutes (60s baseline + 5min RL)  
✅ Generate plots with `research_evaluation.py`  
✅ Check statistical significance (p < 0.05)  
✅ Report effect sizes (Cohen's d)

### **Recommended:**

✅ Run 30-minute experiment (`./run_research.sh`)  
✅ Run with synthetic workload for clear results  
✅ Run multiple times (3-5 runs) for reproducibility  
✅ Report mean ± std dev across runs

### **Files for Paper:**

```
results/research_comparison.png    → Figure 1: Performance comparison
results/performance_table.tex      → Table 1: Statistical results
results/research_report.txt        → Results section (copy statistics)
```

---

## ✅ Verification Checklist

Before claiming you have working results:

- [ ] System ran for at least 6 minutes
- [ ] `/tmp/scheduler_metrics.csv` exists and has >300 lines
- [ ] `results/research_comparison.png` was generated
- [ ] Statistical tests show p-values
- [ ] Dashboard showed real-time data during run
- [ ] No error messages in logs

**Check logs:**

```bash
tail data/logs/rust_monitor.log
tail data/logs/python_agent.log
```

---

## 🚀 You're Ready!

Now you can:

1. ✅ Collect real CPU scheduling data
2. ✅ Train DQN agent on live system
3. ✅ Generate publication-quality plots
4. ✅ Get statistical significance results
5. ✅ Write research paper with real data

**Everything runs with REAL data from your actual system!** 🎉
