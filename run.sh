#!/bin/bash

# ═══════════════════════════════════════════════════════════════════════════
# DQN CPU SCHEDULER - ALL-IN-ONE SCRIPT
# This single script replaces: setup.sh, run.sh, launcher.sh, start_here.sh,
# run_with_dashboard.sh, fix_permissions.sh, fix_profiler.sh, etc.
# ═══════════════════════════════════════════════════════════════════════════

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# ═══════════════════════════════════════════════════════════════════════════
# FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

header() {
    clear
    echo -e "${CYAN}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${BOLD}          DQN CPU SCHEDULER - ALL-IN-ONE              ${NC}${CYAN}║${NC}"
    echo -e "${CYAN}╚═══════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

check_running() {
    pgrep -f "$1" > /dev/null 2>&1
}

wait_for_file() {
    local file=$1
    local timeout=$2
    local elapsed=0
    while [ ! -f "$file" ] && [ $elapsed -lt $timeout ]; do
        sleep 1
        elapsed=$((elapsed + 1))
    done
    [ -f "$file" ]
}

# ═══════════════════════════════════════════════════════════════════════════
# OPTION 1: SETUP
# ═══════════════════════════════════════════════════════════════════════════

do_setup() {
    header
    echo -e "${YELLOW}Setting up DQN CPU Scheduler...${NC}\n"
    
    # Check Rust
    if ! command -v cargo &> /dev/null; then
        echo -e "${RED}✗ Rust not installed!${NC}"
        echo "Install from: https://rustup.rs/"
        exit 1
    fi
    echo -e "${GREEN}✓ Rust installed${NC}"
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}✗ Python3 not installed!${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Python3 installed${NC}"
    
    # Create directories
    echo -e "\n${CYAN}Creating directories...${NC}"
    mkdir -p data/logs data/metrics results checkpoints
    echo -e "${GREEN}✓ Directories created${NC}"
    
    # Build Rust
    echo -e "\n${CYAN}Building Rust binary...${NC}"
    cd rust
    cargo build --release
    cd ..
    echo -e "${GREEN}✓ Rust binary built${NC}"
    
    # Setup Python venv
    if [ ! -d "venv" ]; then
        echo -e "\n${CYAN}Creating Python virtual environment...${NC}"
        python3 -m venv venv
        echo -e "${GREEN}✓ Virtual environment created${NC}"
    fi
    
    # Install Python packages (minimal, no psutil)
    echo -e "\n${CYAN}Installing Python packages...${NC}"
    source venv/bin/activate
    pip install --quiet torch numpy pandas matplotlib scipy rich --break-system-packages
    echo -e "${GREEN}✓ Packages installed${NC}"
    
    echo -e "\n${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║${BOLD}                SETUP COMPLETE!                        ${NC}${GREEN}║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}\n"
    
    echo -e "${CYAN}Next step: Run the system${NC}"
    echo -e "  ${GREEN}./run.sh${NC}\n"
}

# ═══════════════════════════════════════════════════════════════════════════
# OPTION 2: RUN SYSTEM
# ═══════════════════════════════════════════════════════════════════════════

do_run() {
    header
    echo -e "${YELLOW}Starting DQN CPU Scheduler...${NC}\n"
    
    # Stop existing
    echo -e "${CYAN}[1/7]${NC} Stopping existing processes..."
    pkill -f cpu_scheduler_optimizer 2>/dev/null || true
    pkill -f advanced_dqn_agent 2>/dev/null || true
    pkill -f enhanced_terminal_dashboard 2>/dev/null || true
    sleep 2
    echo -e "${GREEN}✓ Clean slate${NC}"
    
    # Fix permissions
    echo -e "\n${CYAN}[2/7]${NC} Setting up /tmp files..."
    sudo rm -f /tmp/scheduler_* /tmp/rl_* 2>/dev/null || rm -f /tmp/scheduler_* /tmp/rl_* 2>/dev/null
    touch /tmp/scheduler_metrics.csv
    touch /tmp/rl_state.json
    touch /tmp/rl_action.json
    touch /tmp/scheduler_actions.log
    chmod 666 /tmp/scheduler_*.* /tmp/rl_*.* 2>/dev/null || true
    echo -e "${GREEN}✓ Files ready${NC}"
    
    # Check files
    echo -e "\n${CYAN}[3/7]${NC} Checking files..."
    [ -f "rust/target/release/cpu_scheduler_optimizer" ] || { echo -e "${RED}✗ Rust binary missing! Run setup first.${NC}"; exit 1; }
    [ -f "python/advanced_dqn_agent.py" ] || { echo -e "${RED}✗ Python agent missing!${NC}"; exit 1; }
    [ -f "python/process_profiler.py" ] || { echo -e "${RED}✗ Process profiler missing!${NC}"; exit 1; }
    [ -f "enhanced_terminal_dashboard.py" ] || { echo -e "${RED}✗ Dashboard missing!${NC}"; exit 1; }
    echo -e "${GREEN}✓ All files present${NC}"
    
    # Start Rust
    echo -e "\n${CYAN}[4/7]${NC} Starting Rust monitor..."
    ./rust/target/release/cpu_scheduler_optimizer > data/logs/rust_monitor.log 2>&1 &
    RUST_PID=$!
    echo -e "${GREEN}✓ Started (PID: $RUST_PID)${NC}"
    
    # Wait for metrics
    echo -e "${CYAN}  Waiting for metrics file...${NC}"
    wait_for_file "/tmp/scheduler_metrics.csv" 10 || { echo -e "${RED}✗ Metrics file not created${NC}"; kill $RUST_PID; exit 1; }
    chmod 666 /tmp/scheduler_metrics.csv 2>/dev/null || true
    echo -e "${GREEN}  ✓ Metrics file ready${NC}"
    
    # Start Python
    echo -e "\n${CYAN}[5/7]${NC} Starting Python DQN agent..."
    source venv/bin/activate
    python3 python/advanced_dqn_agent.py > data/logs/python_agent.log 2>&1 &
    PYTHON_PID=$!
    echo -e "${GREEN}✓ Started (PID: $PYTHON_PID)${NC}"
    
    # Wait for state
    echo -e "${CYAN}  Waiting for state file...${NC}"
    wait_for_file "/tmp/rl_state.json" 15 || { echo -e "${RED}✗ State file not created${NC}"; kill $RUST_PID $PYTHON_PID; exit 1; }
    chmod 666 /tmp/rl_state.json 2>/dev/null || true
    echo -e "${GREEN}  ✓ State file ready${NC}"
    
    # Verify
    echo -e "\n${CYAN}[6/7]${NC} Verifying components..."
    check_running "cpu_scheduler_optimizer" && echo -e "${GREEN}✓ Rust monitor running${NC}" || { echo -e "${RED}✗ Rust stopped${NC}"; exit 1; }
    check_running "advanced_dqn_agent" && echo -e "${GREEN}✓ Python agent running${NC}" || { echo -e "${RED}✗ Python stopped${NC}"; exit 1; }
    
    # Start dashboard
    echo -e "\n${CYAN}[7/7]${NC} Starting dashboard..."
    echo ""
    echo -e "${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║${BOLD}              SYSTEM RUNNING!                          ${NC}${GREEN}║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}\n"
    
    echo -e "${CYAN}Timeline:${NC}"
    echo "  • 0-60s:   Baseline collection"
    echo "  • 60s:     Training starts automatically"
    echo "  • 90-120s: First improvements visible"
    echo "  • 3-5min:  Stable improvements (20-50%)"
    echo ""
    echo -e "${YELLOW}Press Ctrl+C to stop dashboard${NC}\n"
    sleep 3
    
    trap "echo -e '\n${YELLOW}Dashboard stopped. Use ./run.sh stop to stop components.${NC}'" INT
    python3 enhanced_terminal_dashboard.py
    
    echo -e "\n${CYAN}Dashboard stopped. Components still running.${NC}"
    echo -e "${YELLOW}To stop everything: ./run.sh stop${NC}\n"
}

# ═══════════════════════════════════════════════════════════════════════════
# OPTION 3: STOP
# ═══════════════════════════════════════════════════════════════════════════

do_stop() {
    header
    echo -e "${YELLOW}Stopping all processes...${NC}\n"
    
    pkill -f cpu_scheduler_optimizer 2>/dev/null && echo -e "${GREEN}✓ Rust monitor stopped${NC}" || echo -e "${YELLOW}⚠ Rust not running${NC}"
    pkill -f advanced_dqn_agent 2>/dev/null && echo -e "${GREEN}✓ Python agent stopped${NC}" || echo -e "${YELLOW}⚠ Python not running${NC}"
    pkill -f enhanced_terminal_dashboard 2>/dev/null && echo -e "${GREEN}✓ Dashboard stopped${NC}" || echo -e "${YELLOW}⚠ Dashboard not running${NC}"
    
    echo -e "\n${GREEN}All processes stopped.${NC}\n"
}

# ═══════════════════════════════════════════════════════════════════════════
# OPTION 4: CLEAN
# ═══════════════════════════════════════════════════════════════════════════

do_clean() {
    header
    echo -e "${YELLOW}Cleaning temporary data...${NC}\n"
    
    do_stop
    
    echo -e "${CYAN}Removing /tmp files...${NC}"
    sudo rm -f /tmp/scheduler_* /tmp/rl_* 2>/dev/null || rm -f /tmp/scheduler_* /tmp/rl_* 2>/dev/null
    echo -e "${GREEN}✓ /tmp cleaned${NC}"
    
    echo -e "\n${GREEN}Cleanup complete!${NC}\n"
}

# ═══════════════════════════════════════════════════════════════════════════
# MAIN MENU
# ═══════════════════════════════════════════════════════════════════════════

show_menu() {
    header
    echo -e "${BOLD}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}  MAIN MENU${NC}"
    echo -e "${BOLD}═══════════════════════════════════════════════════════════${NC}\n"
    
    echo -e "  ${GREEN}1)${NC} Setup (first time only)"
    echo -e "  ${GREEN}2)${NC} Run System ${YELLOW}[DEFAULT]${NC}"
    echo -e "  ${GREEN}3)${NC} Stop All"
    echo -e "  ${GREEN}4)${NC} Clean Data"
    echo -e "  ${GREEN}5)${NC} View Logs"
    echo -e "  ${RED}0)${NC} Exit"
    echo ""
    
    # Show status
    echo -e "${BOLD}Status:${NC}"
    check_running "cpu_scheduler_optimizer" && echo -e "  ${GREEN}●${NC} Rust: Running" || echo -e "  ${RED}●${NC} Rust: Stopped"
    check_running "advanced_dqn_agent" && echo -e "  ${GREEN}●${NC} Python: Running" || echo -e "  ${RED}●${NC} Python: Stopped"
    echo ""
}

# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

case "${1:-menu}" in
    setup)
        do_setup
        ;;
    run)
        do_run
        ;;
    stop)
        do_stop
        ;;
    clean)
        do_clean
        ;;
    menu|"")
        while true; do
            show_menu
            read -p "Enter choice [0-5]: " choice
            case $choice in
                1) do_setup; read -p "Press enter to continue..." ;;
                2) do_run ;;
                3) do_stop; read -p "Press enter to continue..." ;;
                4) do_clean; read -p "Press enter to continue..." ;;
                5)
                    header
                    echo "Rust log:"
                    tail -30 data/logs/rust_monitor.log 2>/dev/null || echo "No logs yet"
                    echo ""
                    echo "Python log:"
                    tail -30 data/logs/python_agent.log 2>/dev/null || echo "No logs yet"
                    read -p "Press enter to continue..."
                    ;;
                0) echo -e "\n${GREEN}Goodbye!${NC}\n"; exit 0 ;;
                *) echo -e "${RED}Invalid choice${NC}"; sleep 2 ;;
            esac
        done
        ;;
    *)
        echo "Usage: $0 [setup|run|stop|clean|menu]"
        exit 1
        ;;
esac