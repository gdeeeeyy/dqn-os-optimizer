#!/bin/bash
# ALL-IN-ONE SCRIPT - Complete CPU Scheduler Optimizer
# This script does EVERYTHING: setup, run, collect data, generate plots

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

clear

echo -e "${BOLD}${CYAN}"
cat << 'EOF'
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║          CPU SCHEDULER OPTIMIZER                           ║
║          All-in-One Setup & Run Script                     ║
║                                                            ║
║          Deep RL for OS-Level Scheduling                   ║
║          Research-Grade System                             ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

echo ""
echo -e "${BOLD}This script will:${NC}"
echo "  1. Check prerequisites"
echo "  2. Set up the environment (if needed)"
echo "  3. Run the system with terminal dashboard"
echo "  4. Collect REAL data from your CPU"
echo "  5. Generate publication-quality plots"
echo ""
echo -e "${YELLOW}Total time: ~15 minutes (5 min setup + 10 min data collection)${NC}"
echo ""
echo -e -n "${BOLD}Continue? (y/n): ${NC}"
read -r confirm

if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo "  STEP 1: CHECKING PREREQUISITES"
echo "════════════════════════════════════════════════════════════"
echo ""

# Check Rust
if ! command -v rustc &> /dev/null; then
    echo -e "${RED}❌ Rust not installed${NC}"
    echo ""
    echo "Install Rust with:"
    echo "  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"
    echo "  source \$HOME/.cargo/env"
    exit 1
fi
echo -e "${GREEN}✓${NC} Rust: $(rustc --version)"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✓${NC} Python: $(python3 --version)"

# Check tmux
if ! command -v tmux &> /dev/null; then
    echo -e "${YELLOW}⚠  tmux not installed${NC}"
    echo "Installing tmux..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get update && sudo apt-get install -y tmux
    elif command -v dnf &> /dev/null; then
        sudo dnf install -y tmux
    else
        echo -e "${RED}Please install tmux manually${NC}"
        exit 1
    fi
fi
echo -e "${GREEN}✓${NC} tmux: $(tmux -V)"

echo -e "${GREEN}✓${NC} CPU cores: $(nproc)"

# Check if already set up
NEEDS_SETUP=false
if [ ! -d "venv" ] || [ ! -f "rust/target/release/cpu_scheduler_optimizer" ]; then
    NEEDS_SETUP=true
fi

if [ "$NEEDS_SETUP" = true ]; then
    echo ""
    echo "════════════════════════════════════════════════════════════"
    echo "  STEP 2: SETTING UP ENVIRONMENT"
    echo "════════════════════════════════════════════════════════════"
    echo ""
    
    # Create venv
    echo -e "${BLUE}Creating Python virtual environment...${NC}"
    python3 -m venv venv
    source venv/bin/activate
    
    # Install Python deps
    echo -e "${BLUE}Installing Python dependencies (this may take a few minutes)...${NC}"
    pip install --quiet --upgrade pip
    pip install --quiet torch numpy pandas matplotlib seaborn scipy flask pyyaml
    echo -e "${GREEN}✓${NC} Python packages installed"
    
    # Build Rust
    echo -e "${BLUE}Building Rust components...${NC}"
    cd rust
    cargo build --release
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} Rust binary compiled"
    else
        echo -e "${RED}❌ Rust compilation failed${NC}"
        exit 1
    fi
    cd ..
    
    # Create directories
    mkdir -p data/{metrics/{baseline,rl_controlled},models,logs}
    mkdir -p results/{plots,reports,exports,live}
    mkdir -p checkpoints
    echo -e "${GREEN}✓${NC} Directories created"
    
else
    echo ""
    echo -e "${GREEN}✓ Environment already set up${NC}"
    source venv/bin/activate
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo "  STEP 3: STARTING WORKLOAD (OPTIONAL)"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "Would you like to generate CPU load for better test results?"
echo ""
echo "  y) Yes - Start CPU workload (recommended for clear results)"
echo "  n) No  - Use existing system load"
echo ""
echo -e -n "${BOLD}Choice (y/n): ${NC}"
read -r load_choice

if [[ "$load_choice" =~ ^[Yy]$ ]]; then
    echo ""
    echo -e "${GREEN}Starting CPU workload...${NC}"
    
    NUM_CPUS=$(nproc)
    WORKERS=$((NUM_CPUS / 2))
    
    echo "  Using $WORKERS worker threads"
    echo "  This will create ~50-70% CPU load"
    
    for i in $(seq 1 $WORKERS); do
        python3 -c "
import time
import math
start = time.time()
while time.time() - start < 900:  # 15 minutes
    [math.sqrt(x) for x in range(10000)]
" &
    done
    
    WORKLOAD_PIDS=$!
    echo -e "${GREEN}✓${NC} Workload started (will run for 15 minutes)"
    sleep 2
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo "  STEP 4: RUNNING SYSTEM WITH DASHBOARD"
echo "════════════════════════════════════════════════════════════"
echo ""
echo -e "${BOLD}Configuration:${NC}"
echo "  Baseline Period:  60 seconds (normal Linux scheduler)"
echo "  RL Period:        300 seconds (DQN optimization)"
echo "  Total Duration:   6 minutes"
echo ""
echo "The system will collect REAL metrics from your CPU!"
echo ""
echo -e "${YELLOW}Dashboard Controls:${NC}"
echo "  • Navigate panes:  Ctrl+B then arrow keys"
echo "  • Quit dashboard:  q"
echo "  • Stop system:     Ctrl+C"
echo ""
echo -e -n "${BOLD}Press Enter to start...${NC}"
read

# Clean previous data
rm -f /tmp/scheduler_*.{csv,log,json} 2>/dev/null
rm -f /tmp/rl_*.json 2>/dev/null

# Kill existing tmux session
tmux kill-session -t scheduler 2>/dev/null || true

# Create tmux session
tmux new-session -d -s scheduler -n main
tmux split-window -h -t scheduler:main
tmux split-window -v -t scheduler:main.0

# Pane 0: Rust monitor
tmux send-keys -t scheduler:main.0 \
    "cd $(pwd) && sudo ./rust/target/release/cpu_scheduler_optimizer 2>&1 | tee data/logs/rust_monitor.log" C-m

# Pane 1: Dashboard
tmux send-keys -t scheduler:main.1 \
    "cd $(pwd) && source venv/bin/activate && sleep 5 && python3 python/dashboard.py" C-m

# Pane 2: DQN Agent
tmux send-keys -t scheduler:main.2 \
    "cd $(pwd) && source venv/bin/activate && sleep 8 && python3 python/advanced_dqn_agent.py 2>&1 | tee data/logs/python_agent.log" C-m

echo ""
echo -e "${GREEN}✅ System launched!${NC}"
echo ""
echo "Layout:"
echo "  ┌──────────────┬──────────────┐"
echo "  │  Rust Core   │  Dashboard   │"
echo "  ├──────────────┴──────────────┤"
echo "  │       DQN Agent              │"
echo "  └──────────────────────────────┘"
echo ""
echo "Attaching to dashboard in 3 seconds..."
sleep 3

# Attach to tmux
tmux attach -t scheduler

echo ""
echo "════════════════════════════════════════════════════════════"
echo "  STEP 5: GENERATING ANALYSIS & PLOTS"
echo "════════════════════════════════════════════════════════════"
echo ""

# Stop workload if started
if [[ "$load_choice" =~ ^[Yy]$ ]]; then
    echo "Stopping workload..."
    pkill -f "math.sqrt" 2>/dev/null || true
    echo -e "${GREEN}✓${NC} Workload stopped"
    echo ""
fi

# Check if data exists
if [ ! -f "/tmp/scheduler_metrics.csv" ]; then
    echo -e "${RED}❌ No data collected!${NC}"
    echo ""
    echo "The system didn't collect any data."
    echo "This might mean it didn't run long enough."
    exit 1
fi

# Count samples
TOTAL_LINES=$(wc -l < /tmp/scheduler_metrics.csv)
BASELINE_LINES=$(grep -c "baseline" /tmp/scheduler_metrics.csv || true)
RL_LINES=$(grep -c "rl_controlled" /tmp/scheduler_metrics.csv || true)

echo -e "${BLUE}Data collected:${NC}"
echo "  Total samples:      $TOTAL_LINES"
echo "  Baseline samples:   $BASELINE_LINES"
echo "  RL samples:         $RL_LINES"
echo ""

if [ "$BASELINE_LINES" -lt 30 ] || [ "$RL_LINES" -lt 30 ]; then
    echo -e "${YELLOW}⚠  Warning: Not enough data for reliable analysis${NC}"
    echo "Minimum recommended: 60 samples each"
    echo ""
fi

echo -e "${BLUE}Generating plots and statistical analysis...${NC}"
python3 python/research_evaluation.py

if [ $? -eq 0 ]; then
    echo ""
    echo "════════════════════════════════════════════════════════════"
    echo -e "${GREEN}✅ SUCCESS - ALL DONE!${NC}"
    echo "════════════════════════════════════════════════════════════"
    echo ""
    echo -e "${BOLD}Results generated:${NC}"
    ls -lh results/*.png 2>/dev/null | awk '{print "  " $9 " (" $5 ")"}'
    ls -lh results/*.txt 2>/dev/null | awk '{print "  " $9 " (" $5 ")"}'
    ls -lh results/*.tex 2>/dev/null | awk '{print "  " $9 " (" $5 ")"}'
    echo ""
    echo -e "${BOLD}View results:${NC}"
    echo "  Plots:         eog results/research_comparison.png"
    echo "  Report:        cat results/research_report.txt"
    echo "  LaTeX table:   cat results/performance_table.tex"
    echo ""
    echo -e "${BOLD}Data location:${NC}"
    echo "  Raw metrics:   /tmp/scheduler_metrics.csv"
    echo "  Logs:          data/logs/"
    echo ""
else
    echo -e "${RED}❌ Plot generation failed${NC}"
    echo "Check the error messages above."
fi

echo "════════════════════════════════════════════════════════════"