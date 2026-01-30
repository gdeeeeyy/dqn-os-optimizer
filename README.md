# CPU Scheduler Optimizer using Deep Reinforcement Learning

**User-space, research-grade CPU scheduling optimization using Deep Q-Networks (DQN)**  
_No kernel patches. Real-time metrics. Safe scheduler control._

---

## 📌 Project Overview

This project implements a **CPU scheduler optimization system** using **Deep Reinforcement Learning (DQN)** to dynamically adjust OS-level scheduling parameters in real time.

The system runs entirely in **user space**, observing system metrics from `/proc`, learning optimal scheduling actions, and applying them using safe Linux interfaces such as:

- `nice`
- `chrt`
- cgroup-based controls (optional)

The goal is to **reduce CPU instability, improve scheduling efficiency, and optimize fairness and responsiveness** under varying workloads.

---

## 🧠 Core Idea

Traditional Linux schedulers rely on static or heuristic-driven policies.  
This project replaces fixed heuristics with a **learning agent** that:

1. Observes real-time CPU and process metrics
2. Learns scheduling actions using a **Deep Q-Network (DQN)**
3. Applies actions continuously based on system behavior

All learning and control happen **without modifying the kernel**.

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────┐
│                 USER SPACE                  │
│                                             │
│  ┌──────────────┐      ┌─────────────────┐ │
│  │ Rust Monitor │◄────►│ Python DQN Agent│ │
│  │  - Metrics   │ JSON │  - RL Training  │ │
│  │  - Control   │ IPC  │  - Action Select│ │
│  └──────────────┘      └─────────────────┘ │
│         │                      │            │
│         ▼                      ▼            │
│  /tmp/scheduler_metrics.csv  /tmp/rl_*.json│
└─────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────┐
│              KERNEL SPACE                   │
│  • /proc/stat, /proc/loadavg                │
│  • nice, chrt                               │
│  • cgroups (optional)                       │
└─────────────────────────────────────────────┘
```

---

## ⚙️ Technology Stack

### Languages

- **Rust** → High-performance metrics collection & scheduler control
- **Python** → Deep Reinforcement Learning (DQN)

### ML Components

- Deep Q-Network (DQN)
- Experience Replay
- ε-greedy exploration
- Reward shaping based on CPU behavior

### System Interfaces

- `/proc/stat`
- `/proc/loadavg`
- Linux process priorities (`nice`, `chrt`)
- File-based IPC via `/tmp`

---

## 📁 Final Project Structure

```
cpu-scheduler-optimizer/
├── python/
│   ├── advanced_dqn_agent.py
│   └── process_profiler.py
│
├── rust/
│   └── src/
│       └── main.rs
│
├── enhanced_terminal_dashboard.py
├── run.sh
│
├── data/
│   └── logs/
│
├── venv/
└── rust/target/release/
```

**Only 5 core files are required to run the system.**

---

## 🧩 Component Responsibilities

### 1. Rust Scheduler Monitor

- Collects CPU statistics from `/proc`
- Writes metrics to `/tmp/scheduler_metrics.csv`
- Reads actions from `/tmp/rl_action.json`
- Applies scheduling changes safely
- Switches automatically between **baseline** and **RL mode**

### 2. Python Process Profiler

- Reads low-level CPU and process stats
- Computes state vectors
- Ensures accurate CPU usage (delta-based, no `psutil`)

### 3. Python DQN Agent

- Implements Deep Q-Learning
- Chooses scheduling actions
- Writes actions back to Rust
- Handles baseline vs training mode

### 4. Terminal Dashboard

- Displays live CPU behavior
- Shows training status and mode transitions
- Helps verify correct system operation

---

## 🚀 Implementation Steps

### Step 1: Prerequisites

Ensure the following are installed:

- Linux (Kernel 3.10+)
- Python 3.8+
- Rust 1.70+
- `build-essential`

```bash
# Ubuntu / Debian
sudo apt update
sudo apt install -y build-essential python3 python3-venv
```

Install Rust if required:

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env
```

### Step 2: Initial Setup (One Time)

```bash
cd cpu-scheduler-optimizer
chmod +x run.sh
./run.sh setup
```

This will:

- Build the Rust binary
- Create a Python virtual environment
- Install required Python packages
- Initialize log and data directories

### Step 3: Running the System

```bash
./run.sh run
```

What happens internally:

1. Rust monitor starts collecting metrics
2. Python agent enters baseline mode
3. Baseline data is collected automatically
4. System switches to training mode
5. RL actions begin applying dynamically

### Step 4: Monitoring

Live terminal dashboard shows:

- CPU usage trends
- Current mode (baseline / training)
- Agent activity

Logs stored in:

```
data/logs/
```

### Step 5: Stopping the System

```bash
# Ctrl + C to exit dashboard
./run.sh stop
```

---

## 🧪 Verification Checklist

After starting:

```bash
ps aux | grep -E "advanced_dqn|cpu_scheduler"
```

Ensure IPC files exist:

```bash
ls -lh /tmp/scheduler_metrics.csv /tmp/rl_state.json
```

Check logs:

```bash
tail -f data/logs/python_agent.log
tail -f data/logs/rust_monitor.log
```

---

## 🛠️ Troubleshooting

### CPU usage shows 0.0%

Ensure system is not idle

Generate load:

```bash
python3 -c "while True: pass" &
```

### Permission issues

```bash
sudo rm -f /tmp/scheduler_*
chmod +x run.sh
```

### Rust binary missing

```bash
./run.sh setup
```

---

## 🔮 Extensibility

This architecture supports:

- GPU scheduling extensions
- cgroup-based multi-agent control
- eBPF integration
- Multi-node or NUMA-aware learning
- Transfer learning for workloads

---
