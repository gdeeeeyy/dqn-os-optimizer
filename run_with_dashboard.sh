#!/bin/bash
set -e

echo "════════════════════════════════════════════════════════════"
echo "  CPU SCHEDULER OPTIMIZER - LIVE SYSTEM WITH DASHBOARD"
echo "  Collecting REAL data from your system"
echo "════════════════════════════════════════════════════════════"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Activate environment
source venv/bin/activate

# Clean previous runs
echo -e "${BLUE}Cleaning previous data...${NC}"
rm -f /tmp/scheduler_*.{csv,log,json} 2>/dev/null
rm -f /tmp/rl_*.json 2>/dev/null
echo -e "${GREEN}✓${NC} Cleaned"

# Configuration
BASELINE_DURATION=60    # 60 seconds for baseline
RL_DURATION=300        # 5 minutes for RL optimization
TOTAL_DURATION=$((BASELINE_DURATION + RL_DURATION))

echo ""
echo -e "${BLUE}Configuration:${NC}"
echo "  Baseline Period:  ${BASELINE_DURATION}s (collecting normal scheduler data)"
echo "  RL Period:        ${RL_DURATION}s (DQN optimization)"
echo "  Total Duration:   ${TOTAL_DURATION}s ($(($TOTAL_DURATION / 60)) minutes)"
echo ""
echo -e "${YELLOW}This will collect REAL metrics from your running system.${NC}"
echo ""

# Check for tmux
if ! command -v tmux &> /dev/null; then
    echo -e "${RED}❌ tmux not installed!${NC}"
    echo "Install with: sudo apt install tmux"
    exit 1
fi

# Check if Rust binary exists
if [ ! -f "rust/target/release/cpu_scheduler_optimizer" ]; then
    echo -e "${YELLOW}⚠  Rust binary not found. Building...${NC}"
    cd rust
    cargo build --release
    cd ..
fi

echo -e "${GREEN}Starting system with terminal dashboard...${NC}"
echo ""
echo "The system will:"
echo "  1. Collect 60s of baseline metrics (normal Linux scheduler)"
echo "  2. Start DQN agent and optimize for 5 minutes"
echo "  3. Show live dashboard with real-time comparison"
echo ""
echo "Press Ctrl+C to stop at any time."
echo ""
sleep 3

# Kill existing session
tmux kill-session -t scheduler 2>/dev/null || true

# Create tmux session with dashboard layout
tmux new-session -d -s scheduler -n main

# Split into 3 panes:
# ┌──────────────┬──────────────┐
# │              │              │
# │  Rust Core   │  Dashboard   │
# │              │              │
# ├──────────────┴──────────────┤
# │       DQN Agent              │
# └──────────────────────────────┘

tmux split-window -h -t scheduler:main
tmux split-window -v -t scheduler:main.0

# Pane 0 (top-left): Rust monitor
tmux send-keys -t scheduler:main.0 \
    "cd $(pwd) && echo 'Starting Rust monitor (collecting metrics)...' && sleep 2 && sudo ./rust/target/release/cpu_scheduler_optimizer 2>&1 | tee data/logs/rust_monitor.log" C-m

# Pane 1 (top-right): Terminal Dashboard
tmux send-keys -t scheduler:main.1 \
    "cd $(pwd) && source venv/bin/activate && sleep 5 && echo 'Starting Dashboard...' && python3 python/dashboard.py" C-m

# Pane 2 (bottom): DQN Agent
tmux send-keys -t scheduler:main.2 \
    "cd $(pwd) && source venv/bin/activate && sleep 8 && echo 'Starting DQN Agent...' && python3 python/advanced_dqn_agent.py 2>&1 | tee data/logs/python_agent.log" C-m

echo -e "${GREEN}✅ All components launched!${NC}"
echo ""
echo "Layout:"
echo "  ┌──────────────┬──────────────┐"
echo "  │  Rust Core   │  Dashboard   │"
echo "  ├──────────────┴──────────────┤"
echo "  │       DQN Agent              │"
echo "  └──────────────────────────────┘"
echo ""
echo "Controls:"
echo "  • Navigate panes:  Ctrl+B then arrow keys"
echo "  • Detach:          Ctrl+B then D"
echo "  • Stop system:     ./stop.sh (or Ctrl+C)"
echo "  • Quit dashboard:  q"
echo ""
echo "Attaching to session..."
sleep 2

# Attach to tmux session
tmux attach -t scheduler