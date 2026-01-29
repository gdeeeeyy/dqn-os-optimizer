# DQN CPU Scheduler - Timing & Performance Guide

## ⏱️ Expected Timeline

### Phase 1: Initialization (0-10 seconds)

```
[0s]  Dashboard starts
[2s]  Rust monitor begins collecting metrics
[5s]  Python DQN agent initializes
[10s] First data points appear in dashboard
```

**What you'll see:**

- Dashboard shows "⏳ INITIALIZING"
- All panels show "⏳ Waiting for data..."
- This is normal - system is starting up

---

### Phase 2: Baseline Collection (10-70 seconds)

```
[10s]  Baseline data collection begins
[30s]  ~20 baseline samples collected
[50s]  ~40 baseline samples collected
[60s]  Baseline phase complete
[70s]  Switch to RL training mode
```

**What you'll see:**

- Header shows "📊 BASELINE (Xs/60s)"
- Progress bar in Improvements panel
- Baseline samples counter increases
- NO improvements shown yet (this is expected!)
- CPU graph shows white dots (baseline data)

**Important:** The system MUST collect 60 seconds of baseline data before training starts. This is by design!

---

### Phase 3: RL Training Starts (70-120 seconds)

```
[70s]   Training mode activated
[80s]   First RL optimization actions
[90s]   ~10-15 optimized samples
[100s]  ~20 optimized samples
[120s]  First improvements become visible
```

**What you'll see:**

- Header changes to "● TRAINING (Xs)"
- Status changes from "Baseline" to "Training started..."
- Optimized samples counter appears
- CPU graph shows cyan blocks (optimized data)
- Actions start appearing in log
- Episodes counter increases
- Epsilon starts decreasing
- **After ~30 optimized samples, improvements show!**

---

### Phase 4: Learning & Improvement (2-5 minutes)

```
[2 min]  Clear improvements visible (10-20%)
[3 min]  Stable improvements (20-40%)
[5 min]  Optimal performance reached (30-50%)
```

**What you'll see:**

- ✅ **Improvements panel shows GREEN percentages**
- CPU Usage: typically 10-30% reduction
- CPU Variance: typically 30-50% reduction
- Context Switches: typically 20-40% reduction
- Load Average: typically 10-25% reduction
- Reward graph trending upward
- Q-values increasing
- Epsilon decreasing to ~0.1-0.3

---

## 🎯 Performance Expectations

### Typical Improvements After 5 Minutes

| Metric           | Baseline    | Optimized   | Improvement |
| ---------------- | ----------- | ----------- | ----------- |
| CPU Usage        | 65-75%      | 45-55%      | ↓ 20-30%    |
| CPU Variance     | 15-20%      | 7-10%       | ↓ 40-55%    |
| Context Switches | 7000-9000/s | 4500-6000/s | ↓ 30-40%    |
| Load Average     | 1.7-2.1     | 1.3-1.6     | ↓ 15-25%    |

### When Improvements Are LOWER Than Expected

**If improvements are < 5% after 5 minutes:**

1. **Not enough workload**
   - Generate more CPU load:

   ```bash
   ./generate_load.sh
   # Select option 1 or 3
   ```

2. **Insufficient training time**
   - Wait longer (10-15 minutes)
   - Check epsilon - should be < 0.5

3. **Process diversity**
   - Need mix of CPU/IO/interactive processes
   - Check "Optimized Processes" panel
   - Should show 5+ different processes

---

## 📊 Graph Behavior

### CPU Usage Graph

**Early (0-2 min):**

- Only white dots (baseline)
- No cyan blocks yet

**Mid (2-3 min):**

- White dots + some cyan blocks
- Graphs may overlap initially

**Late (3+ min):**

- Cyan blocks clearly BELOW white dots
- Visual separation = improvement

### Reward Graph

**Expected pattern:**

- Start: Negative or near-zero
- 2-3 min: Trending upward
- 5 min: Positive and stable
- Should show general upward slope

**Bad patterns:**

- Flat line = no learning
- Decreasing = problem (check logs)
- Wild oscillation = unstable (normal early on)

---

## 🔧 Troubleshooting

### Problem: "Collecting baseline data..." stuck forever

**Causes:**

1. Rust monitor not writing to `/tmp/scheduler_metrics.csv`
2. File permissions issue
3. No CPU load to measure

**Solutions:**

```bash
# Check file exists and is being written
ls -lh /tmp/scheduler_metrics.csv
tail -f /tmp/scheduler_metrics.csv

# Check Rust process running
ps aux | grep cpu_scheduler_optimizer

# Generate workload
./generate_load.sh
```

---

### Problem: "Training started" but no improvements

**Timeline:**

- First 30 samples (60-90s): NO improvements shown (normal!)
- 30-50 samples (90-120s): First improvements appear
- 50+ samples (2+ min): Clear improvements

**If still no improvements after 3 minutes:**

1. **Check optimized sample count**
   - Look at panel title: "(n=X)"
   - Need n >= 30 for reliable comparison

2. **Verify mode switching**

   ```bash
   tail -20 /tmp/scheduler_metrics.csv
   # Should show "rl" in mode column
   ```

3. **Check DQN agent is running**
   ```bash
   ps aux | grep advanced_dqn_agent
   tail -f data/logs/python_agent.log
   ```

---

### Problem: No process data showing

**Causes:**

- DQN agent not profiling processes
- No high-CPU processes to optimize
- /tmp/rl_state.json not being written

**Solutions:**

```bash
# Check state file
cat /tmp/rl_state.json

# Should contain "processes" array
# If empty or missing, check agent logs:
tail -f data/logs/python_agent.log

# Generate processes to optimize
./generate_load.sh
```

---

### Problem: No actions in log

**Expected:**

- First actions: 60-90 seconds (after baseline)
- Frequency: 1-2 actions every 5-10 seconds

**If no actions after 2 minutes:**

```bash
# Check action file exists
ls -lh /tmp/scheduler_actions.log

# View directly
tail -f /tmp/scheduler_actions.log

# Check agent has permissions
# May need sudo for process priority changes
sudo ./run_with_dashboard.sh
```

---

### Problem: Improvements are negative (red arrows)

**This can happen for several reasons:**

1. **Too early** - Wait longer, need more samples
2. **System variance** - Natural fluctuation, will stabilize
3. **Workload changed** - Baseline and RL measured different loads
4. **Insufficient training** - Epsilon still high (>0.7), keep waiting

**What to do:**

- Wait 5+ minutes for stability
- Check epsilon < 0.5
- Ensure consistent workload
- Look at "Overall Improvement" - if positive, individual metrics OK

---

## 🚀 Optimizing Performance

### Get Better Results Faster

1. **Start with workload:**

   ```bash
   # Before running dashboard
   ./generate_load.sh
   # Select mixed workload (option 3)
   ```

2. **Run longer:**

   ```bash
   # Instead of stopping at 5 min, run 10-15 min
   # Improvements become more stable
   ```

3. **Tune hyperparameters** (advanced):
   Edit `python/config/hyperparameters.yaml`:

   ```yaml
   learning_rate: 0.0001 # Lower = more stable
   epsilon_decay: 0.9995 # Higher = faster exploration
   gamma: 0.99 # Discount factor
   ```

4. **Multiple runs:**
   ```bash
   # Run 3-5 times, average results
   # Each run learns differently
   ```

---

## 📈 Success Indicators

### ✅ System is Working Well When:

- Baseline collected in ~60 seconds
- Training starts automatically
- Optimized samples accumulating (n increases)
- Green improvements showing after 2-3 minutes
- Rewards trending upward
- Epsilon decreasing
- Actions appearing regularly
- Process list populated
- Graphs show clear separation

### ❌ System Has Issues When:

- Stuck at "Initializing" > 30 seconds
- No mode switch after 70 seconds
- No optimized samples after 2 minutes
- All improvements red after 5 minutes
- Epsilon not decreasing
- No actions logged
- Empty process list after 3 minutes
- Graphs show no data

---

## 🎓 Understanding the Metrics

### CPU Usage

- **Lower is better** = DQN reduces average CPU load
- Typical improvement: 15-30%
- Shows efficiency of scheduling

### CPU Variance

- **Lower is better** = More stable performance
- Typical improvement: 40-60%
- Most dramatic improvement
- Shows consistency of DQN

### Context Switches

- **Lower is better** = Less overhead
- Typical improvement: 25-40%
- Shows smarter scheduling decisions

### Load Average

- **Lower is better** = Less system stress
- Typical improvement: 15-25%
- Shows overall system health

---

## ⚡ Quick Reference

| Time    | Expected State   | What's Happening            |
| ------- | ---------------- | --------------------------- |
| 0-10s   | Initializing     | Starting up                 |
| 10-60s  | Baseline         | Collecting baseline metrics |
| 60-90s  | Training Started | First RL optimizations      |
| 90-120s | Early Training   | First improvements appear   |
| 2-3 min | Active Training  | Clear improvements          |
| 3-5 min | Stable Training  | Optimal performance         |
| 5+ min  | Converged        | Steady-state improvement    |

---

## 🔍 Data File Reference

| File                         | Purpose        | Update Frequency |
| ---------------------------- | -------------- | ---------------- |
| `/tmp/scheduler_metrics.csv` | CPU metrics    | Every 2 seconds  |
| `/tmp/rl_state.json`         | Training state | Every 5 seconds  |
| `/tmp/scheduler_actions.log` | Actions taken  | Per action (~5s) |
| `data/logs/rust_monitor.log` | Rust logs      | Continuous       |
| `data/logs/python_agent.log` | Python logs    | Continuous       |

---

## 💡 Pro Tips

1. **Be patient** - First improvements take 2-3 minutes minimum
2. **Check sample counts** - Need n >= 30 for both baseline and optimized
3. **Consistent workload** - Generate load before starting
4. **Watch the graphs** - Visual separation = working well
5. **Read the logs** - If stuck, logs tell you why
6. **Multiple runs** - Average results across 3-5 runs for research
7. **Longer is better** - 10-15 minute runs show best results

---

## 📞 Still Having Issues?

1. Check the README.md troubleshooting section
2. View logs: `tail -f data/logs/*.log`
3. Verify all processes running: `ps aux | grep scheduler`
4. Ensure files exist: `ls -lh /tmp/scheduler_*`
5. Try clean restart: `./clean.sh && ./setup.sh`

---

**Remember:** The DQN agent is a neural network that needs time to learn. The first 2-3 minutes are essential for data collection and initial training. Be patient - improvements WILL show!
