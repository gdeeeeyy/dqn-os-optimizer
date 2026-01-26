# Complete File Mapping Guide

## Exact File Placement for CPU Scheduler Optimizer

---

## 📁 File Placement Map

### **RUST COMPONENTS**

```bash
rust/
├── Cargo.toml                    # ← Copy "Cargo.toml - Rust Dependencies"
└── src/
    ├── main.rs                   # ← Copy "Integrated Rust Main (main.rs with modules)"
    ├── logger.rs                 # ← Copy "Rust Logger Module (logger.rs)"
    └── controller.rs             # ← Copy "Rust Controller Module (controller.rs)"
```

### **PYTHON COMPONENTS**

```bash
python/
├── requirements.txt              # ← Copy "Python Requirements (requirements.txt)"
├── dqn_agent.py                  # ← Copy "DQN Agent - Python RL Core (dqn_agent.py)"
├── dashboard.py                  # ← Copy "Real-Time TUI Dashboard (dashboard.py)"
├── analyze.py                    # ← Copy "Performance Analysis & Visualization (analyze.py)"
├── realtime_monitor.py           # ← Copy "Complete Real-Time Monitor (realtime_monitor.py)"
├── web_server.py                 # ← Create (see below)
└── models/
    ├── dqn.py                    # ← Create (see below)
    ├── replay_buffer.py          # ← Create (see below)
    └── utils.py                  # ← Create empty or copy utilities
```

### **WEB DASHBOARD**

```bash
web/
├── index.html                    # ← Copy "Web-Based Monitoring Dashboard"
└── static/
    ├── css/
    │   └── dashboard.css         # ← Optional (styles in HTML)
    └── js/
        └── charts.js             # ← Optional (scripts in HTML)
```

### **CONFIGURATION FILES**

```bash
config/
├── scheduler.yaml                # ← Create (see below)
├── monitoring.yaml               # ← Create (see below)
└── actions.yaml                  # ← Create (see below)
```

### **ROOT DIRECTORY**

```bash
.
├── README.md                     # ← Copy "Complete Documentation (README.md)"
├── .gitignore                    # ← Create (see below)
├── setup.sh                      # ← Create (see below)
├── run.sh                        # ← Copy "Deployment Script (run.sh)"
├── stop.sh                       # ← Create (see below)
└── clean.sh                      # ← Create (see below)
```

---

## 🚀 Quick Setup Commands

### **Step 1: Create Directory Structure**

```bash
# Create project root
mkdir -p cpu-scheduler-optimizer
cd cpu-scheduler-optimizer

# Create all directories
mkdir -p rust/src
mkdir -p python/{models,config}
mkdir -p web/{static/{css,js},templates}
mkdir -p config
mkdir -p data/{metrics/{baseline,rl_controlled},models,logs}
mkdir -p results/{plots,reports,exports,live}
mkdir -p scripts
mkdir -p docs
```

### **Step 2: Copy Core Files**

Now copy the artifacts I provided into these locations:

#### **Rust Files**

```bash
# Copy these to rust/
rust/Cargo.toml           ← "Cargo.toml - Rust Dependencies"
rust/src/main.rs          ← "Integrated Rust Main (main.rs with modules)"
rust/src/logger.rs        ← "Rust Logger Module (logger.rs)"
rust/src/controller.rs    ← "Rust Controller Module (controller.rs)"
```

#### **Python Files**

```bash
# Copy these to python/
python/requirements.txt   ← "Python Requirements"
python/dqn_agent.py      ← "DQN Agent - Python RL Core"
python/dashboard.py      ← "Real-Time TUI Dashboard"
python/analyze.py        ← "Performance Analysis & Visualization"
python/realtime_monitor.py ← "Complete Real-Time Monitor"
```

#### **Web Files**

```bash
# Copy to web/
web/index.html           ← "Web-Based Monitoring Dashboard"
```

#### **Documentation**

```bash
# Copy to root
README.md                ← "Complete Documentation (README.md)"
```

---

## 📝 Additional Files to Create

### **1. python/web_server.py**

```python
#!/usr/bin/env python3
from flask import Flask, send_from_directory, jsonify
import json
import os

app = Flask(__name__, static_folder='../web/static')

@app.route('/')
def index():
    return send_from_directory('../web', 'index.html')

@app.route('/api/metrics')
def metrics():
    try:
        with open('/tmp/rl_state.json', 'r') as f:
            return jsonify(json.load(f))
    except:
        return jsonify({'error': 'No data'})

if __name__ == '__main__':
    print("🌐 Web dashboard starting on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)
```

### **2. python/models/dqn.py**

```python
import torch
import torch.nn as nn

class DQN(nn.Module):
    def __init__(self, state_dim, action_dim, hidden_dim=128):
        super(DQN, self).__init__()
        self.network = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, action_dim)
        )

    def forward(self, state):
        return self.network(state)
```

### **3. python/models/replay_buffer.py**

```python
import random
from collections import deque

class ReplayBuffer:
    def __init__(self, capacity):
        self.buffer = deque(maxlen=capacity)

    def push(self, state, action, reward, next_state, done):
        self.buffer.append((state, action, reward, next_state, done))

    def sample(self, batch_size):
        return random.sample(self.buffer, min(batch_size, len(self.buffer)))

    def __len__(self):
        return len(self.buffer)
```

### **4. python/models/utils.py**

```python
# Utility functions (currently empty - can add helpers later)
pass
```

### **5. config/scheduler.yaml**

```yaml
scheduler:
  baseline_duration: 60
  optimization_duration: 240
  metrics_interval: 1.0

actions:
  enabled:
    - set_nice
    - set_scheduler

  nice_values:
    high_priority: -5
    normal_priority: 0
    low_priority: 10

safety:
  max_actions_per_minute: 30
  min_action_interval: 2.0
```

### **6. config/monitoring.yaml**

```yaml
monitoring:
  metrics_sources:
    - /proc/stat
    - /proc/loadavg

  export_formats:
    - csv
    - json

  retention:
    metrics_days: 7
    logs_days: 30
```

### **7. config/actions.yaml**

```yaml
action_space:
  - name: NO_OP
    id: 0
  - name: REDUCE_NICE
    id: 1
    nice_value: -5
  - name: INCREASE_NICE
    id: 2
    nice_value: 10
  - name: SET_SCHED_BATCH
    id: 3
    policy: SCHED_BATCH
  - name: SET_SCHED_OTHER
    id: 4
    policy: SCHED_OTHER
```

### **8. .gitignore**

```gitignore
# Python
venv/
__pycache__/
*.pyc
*.pyo
*.egg-info/

# Rust
rust/target/
rust/Cargo.lock

# Data
data/
results/
*.csv
*.log
*.json
/tmp/

# Models
*.pth

# IDE
.vscode/
.idea/
*.swp
```

### **9. setup.sh**

```bash
#!/bin/bash
set -e

echo "🔧 CPU Scheduler Optimizer - Setup"
echo "===================================="

# Check Rust
if ! command -v rustc &> /dev/null; then
    echo "❌ Rust not installed!"
    echo "Install from: https://rustup.rs/"
    exit 1
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not installed!"
    exit 1
fi

echo "✓ Rust: $(rustc --version)"
echo "✓ Python: $(python3 --version)"

# Setup Python venv
echo ""
echo "📦 Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo "📦 Installing Python dependencies..."
pip install -q --upgrade pip
pip install -q -r python/requirements.txt

# Build Rust
echo ""
echo "🦀 Building Rust components..."
cd rust
cargo build --release
cd ..

# Create directories
echo ""
echo "📁 Creating data directories..."
mkdir -p data/{metrics/{baseline,rl_controlled},models,logs}
mkdir -p results/{plots,reports,exports,live}

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  ./run.sh          # Start the system"
echo "  ./stop.sh         # Stop the system"
echo "  ./clean.sh        # Clean temporary files"
```

### **10. stop.sh**

```bash
#!/bin/bash

echo "Stopping CPU Scheduler Optimizer..."

# Kill tmux session if exists
if command -v tmux &> /dev/null; then
    tmux kill-session -t scheduler 2>/dev/null && echo "✓ Tmux session stopped"
fi

# Kill background processes if PID file exists
if [ -f .pids ]; then
    while read pid; do
        kill $pid 2>/dev/null
    done < .pids
    rm .pids
    echo "✓ Background processes stopped"
fi

echo "✅ System stopped"
```

### **11. clean.sh**

```bash
#!/bin/bash

echo "Cleaning temporary files..."

rm -f /tmp/scheduler_*.{csv,log,json}
rm -f /tmp/rl_*.json
rm -f .pids

echo "✅ Cleanup complete"
```

### **12. python/config/hyperparameters.yaml**

```yaml
model:
  state_dim: 6
  action_dim: 5
  hidden_dim: 128

training:
  learning_rate: 0.001
  gamma: 0.99
  batch_size: 64
  memory_size: 10000
  target_update_freq: 100

exploration:
  epsilon_start: 1.0
  epsilon_end: 0.01
  epsilon_decay: 0.995
```

---

## 🎯 Final Setup Steps

### **1. Make Scripts Executable**

```bash
chmod +x setup.sh run.sh stop.sh clean.sh
chmod +x python/*.py
```

### **2. Run Setup**

```bash
./setup.sh
```

This will:

- Create Python virtual environment
- Install all dependencies
- Build Rust release binary
- Create data directories

### **3. Launch System**

```bash
./run.sh
```

This will:

- Start Rust monitor (baseline collection)
- Start Python DQN agent (after 5s)
- Start real-time monitor
- Start web server
- Display everything in tmux panes

### **4. Monitor Results**

**Option A: In tmux session**

- Attach: `tmux attach -t scheduler`
- Navigate: `Ctrl+B` then arrow keys
- Detach: `Ctrl+B` then `D`

**Option B: Web browser**

- Open: `http://localhost:5000`

**Option C: Console output**

- The real-time monitor updates every 5 seconds

### **5. Stop System**

```bash
./stop.sh
# or press Ctrl+C in terminal
```

### **6. Analyze Results**

```bash
source venv/bin/activate
python3 python/analyze.py
```

Results will be in:

- `results/plots/` - PNG images
- `results/live/` - CSV comparisons and text summary

---

## 📊 Expected Directory After Setup

```
cpu-scheduler-optimizer/
├── venv/                         # Created by setup.sh
├── rust/
│   ├── target/release/
│   │   └── cpu_scheduler_optimizer   # Built by setup.sh
│   ├── Cargo.toml
│   └── src/
│       ├── main.rs
│       ├── logger.rs
│       └── controller.rs
├── python/
│   ├── *.py (all Python files)
│   └── models/
│       └── *.py
├── data/
│   ├── logs/
│   │   ├── rust_monitor.log     # Created during run
│   │   └── python_agent.log     # Created during run
│   └── metrics/
│       ├── baseline/
│       └── rl_controlled/
├── results/
│   ├── plots/                    # Created by analyze.py
│   └── live/                     # Created by realtime_monitor.py
└── /tmp/
    ├── scheduler_metrics.csv     # Live metrics
    ├── rl_state.json            # Current state
    └── rl_action.json           # Current action
```

---

## 🎓 Verification Checklist

Before running, verify:

- [ ] All Rust files in `rust/src/`
- [ ] All Python files in `python/`
- [ ] `requirements.txt` in `python/`
- [ ] `Cargo.toml` in `rust/`
- [ ] All shell scripts in root directory
- [ ] Shell scripts are executable (`chmod +x`)
- [ ] Config files in `config/`
- [ ] Web dashboard in `web/`

After setup:

- [ ] `venv/` directory created
- [ ] `rust/target/release/cpu_scheduler_optimizer` exists
- [ ] No errors in setup output
- [ ] Can import torch: `python3 -c "import torch; print('OK')"`

After running:

- [ ] `/tmp/scheduler_metrics.csv` exists and growing
- [ ] Console shows CPU metrics
- [ ] Web dashboard accessible
- [ ] Plots generated in `results/plots/`

---

## 🚨 Quick Troubleshooting

**Setup fails:**

```bash
# Clean and retry
./clean.sh
rm -rf venv rust/target
./setup.sh
```

**Rust doesn't compile:**

```bash
cd rust
cargo clean
cargo build --release
```

**Python imports fail:**

```bash
source venv/bin/activate
pip install --force-reinstall -r python/requirements.txt
```

**No metrics collected:**

```bash
# Check permissions
ls -la /proc/stat
# Should be readable

# Check Rust binary runs
./rust/target/release/cpu_scheduler_optimizer
```

---

This guide provides the complete file mapping. Copy each artifact to its designated location and you'll have a working system!
