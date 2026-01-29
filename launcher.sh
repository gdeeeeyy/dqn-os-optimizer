#!/bin/bash

# Enhanced Launcher for DQN CPU Scheduler with Better Terminal Dashboard
# Run with: ./launcher.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

clear

echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                                                            ║${NC}"
echo -e "${CYAN}║${BOLD}         DQN CPU SCHEDULER - ENHANCED LAUNCHER         ${NC}${CYAN}║${NC}"
echo -e "${CYAN}║                                                            ║${NC}"
echo -e "${CYAN}║           Deep Reinforcement Learning Optimizer           ║${NC}"
echo -e "${CYAN}║                                                            ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Function to check if a process is running
check_process() {
    if pgrep -f "$1" > /dev/null; then
        return 0
    else
        return 1
    fi
}

# Function to display menu
show_menu() {
    echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}  MAIN MENU${NC}"
    echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "  ${GREEN}1)${NC} Run with Enhanced Terminal Dashboard ${YELLOW}[RECOMMENDED]${NC}"
    echo -e "     └─ Beautiful rich terminal UI with real-time charts"
    echo ""
    echo -e "  ${GREEN}2)${NC} Run with Basic Dashboard"
    echo -e "     └─ Original tmux-based dashboard"
    echo ""
    echo -e "  ${GREEN}3)${NC} Run in Background (No Dashboard)"
    echo -e "     └─ Headless mode, check logs later"
    echo ""
    echo -e "  ${GREEN}4)${NC} View Live Metrics"
    echo -e "     └─ Real-time tail of metrics file"
    echo ""
    echo -e "  ${GREEN}5)${NC} View System Logs"
    echo -e "     └─ Check Rust and Python logs"
    echo ""
    echo -e "  ${GREEN}6)${NC} Stop All Processes"
    echo -e "     └─ Kill running optimizer and agents"
    echo ""
    echo -e "  ${GREEN}7)${NC} Clean All Data"
    echo -e "     └─ Remove temporary files and metrics"
    echo ""
    echo -e "  ${GREEN}8)${NC} Generate Plots and Analysis"
    echo -e "     └─ Create research-quality visualizations"
    echo ""
    echo -e "  ${GREEN}9)${NC} Run Full Research Experiment (30 min)"
    echo -e "     └─ Publication-ready data collection"
    echo ""
    echo -e "  ${RED}0)${NC} Exit"
    echo ""
    echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    # Show status
    echo -e "${BOLD}System Status:${NC}"
    if check_process "cpu_scheduler_optimizer"; then
        echo -e "  ${GREEN}●${NC} Rust Monitor: ${GREEN}Running${NC}"
    else
        echo -e "  ${RED}●${NC} Rust Monitor: ${RED}Stopped${NC}"
    fi
    
    if check_process "advanced_dqn_agent"; then
        echo -e "  ${GREEN}●${NC} DQN Agent: ${GREEN}Running${NC}"
    else
        echo -e "  ${RED}●${NC} DQN Agent: ${RED}Stopped${NC}"
    fi
    
    if check_process "enhanced_terminal_dashboard"; then
        echo -e "  ${GREEN}●${NC} Dashboard: ${GREEN}Running${NC}"
    else
        echo -e "  ${RED}●${NC} Dashboard: ${RED}Stopped${NC}"
    fi
    echo ""
}

# Function to run with enhanced terminal dashboard
run_enhanced_dashboard() {
    echo -e "${CYAN}Starting DQN Optimizer with Enhanced Terminal Dashboard...${NC}"
    echo ""
    
    # Check if setup is done
    if [ ! -f "rust/target/release/cpu_scheduler_optimizer" ]; then
        echo -e "${YELLOW}Running setup first...${NC}"
        ./setup.sh
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Start Rust monitor in background
    echo -e "${GREEN}[1/3]${NC} Starting Rust monitor..."
    ./rust/target/release/cpu_scheduler_optimizer > data/logs/rust_monitor.log 2>&1 &
    RUST_PID=$!
    sleep 2
    
    # Start Python DQN agent in background
    echo -e "${GREEN}[2/3]${NC} Starting DQN agent..."
    python3 python/advanced_dqn_agent.py > data/logs/python_agent.log 2>&1 &
    PYTHON_PID=$!
    sleep 3
    
    # Start enhanced dashboard
    echo -e "${GREEN}[3/3]${NC} Starting enhanced terminal dashboard..."
    echo ""
    echo -e "${YELLOW}Press Ctrl+C to stop the dashboard${NC}"
    echo ""
    sleep 2
    
    python3 enhanced_terminal_dashboard.py
    
    # Cleanup on exit
    kill $RUST_PID $PYTHON_PID 2>/dev/null
    echo -e "${GREEN}All processes stopped.${NC}"
}

# Function to run with basic dashboard
run_basic_dashboard() {
    echo -e "${CYAN}Starting with basic tmux dashboard...${NC}"
    
    if ! command -v tmux &> /dev/null; then
        echo -e "${RED}tmux is not installed!${NC}"
        echo -e "${YELLOW}Install with: sudo apt install tmux${NC}"
        read -p "Press enter to continue..."
        return
    fi
    
    ./run_with_dashboard.sh
}

# Function to run in background
run_background() {
    echo -e "${CYAN}Starting in background mode...${NC}"
    ./run.sh
    echo ""
    echo -e "${GREEN}Optimizer started in background.${NC}"
    echo -e "${YELLOW}View logs with option 5${NC}"
    read -p "Press enter to continue..."
}

# Function to view metrics
view_metrics() {
    echo -e "${CYAN}Live Metrics (Press Ctrl+C to exit)${NC}"
    echo ""
    
    if [ ! -f "/tmp/scheduler_metrics.csv" ]; then
        echo -e "${RED}No metrics file found. Start the optimizer first!${NC}"
        read -p "Press enter to continue..."
        return
    fi
    
    tail -f /tmp/scheduler_metrics.csv
}

# Function to view logs
view_logs() {
    clear
    echo -e "${CYAN}System Logs${NC}"
    echo ""
    echo -e "${BOLD}Choose log to view:${NC}"
    echo "  1) Rust Monitor"
    echo "  2) Python DQN Agent"
    echo "  3) Both (side by side)"
    echo "  0) Back to menu"
    echo ""
    read -p "Enter choice: " log_choice
    
    case $log_choice in
        1)
            if [ -f "data/logs/rust_monitor.log" ]; then
                tail -f data/logs/rust_monitor.log
            else
                echo -e "${RED}Log file not found${NC}"
                read -p "Press enter to continue..."
            fi
            ;;
        2)
            if [ -f "data/logs/python_agent.log" ]; then
                tail -f data/logs/python_agent.log
            else
                echo -e "${RED}Log file not found${NC}"
                read -p "Press enter to continue..."
            fi
            ;;
        3)
            if command -v tmux &> /dev/null; then
                tmux new-session \; \
                    split-window -h \; \
                    send-keys 'tail -f data/logs/rust_monitor.log' C-m \; \
                    select-pane -t 0 \; \
                    send-keys 'tail -f data/logs/python_agent.log' C-m \;
            else
                echo -e "${RED}tmux not installed${NC}"
                read -p "Press enter to continue..."
            fi
            ;;
    esac
}

# Function to stop all
stop_all() {
    echo -e "${CYAN}Stopping all processes...${NC}"
    ./stop.sh
    echo -e "${GREEN}All processes stopped.${NC}"
    read -p "Press enter to continue..."
}

# Function to clean data
clean_data() {
    echo -e "${YELLOW}This will remove all temporary data and metrics.${NC}"
    read -p "Are you sure? (y/N): " confirm
    
    if [[ $confirm =~ ^[Yy]$ ]]; then
        echo -e "${CYAN}Cleaning...${NC}"
        ./clean.sh
        echo -e "${GREEN}Cleanup complete.${NC}"
    else
        echo -e "${YELLOW}Cancelled.${NC}"
    fi
    read -p "Press enter to continue..."
}

# Function to generate plots
generate_plots() {
    echo -e "${CYAN}Generating plots and analysis...${NC}"
    
    if [ ! -f "/tmp/scheduler_metrics.csv" ]; then
        echo -e "${RED}No metrics data found. Run the optimizer first!${NC}"
        read -p "Press enter to continue..."
        return
    fi
    
    source venv/bin/activate
    python3 python/research_evaluation.py
    
    echo ""
    echo -e "${GREEN}Plots generated in results/ directory${NC}"
    echo ""
    read -p "Press enter to continue..."
}

# Function to run research experiment
run_research() {
    echo -e "${CYAN}Starting 30-minute research experiment...${NC}"
    echo -e "${YELLOW}This will collect baseline and training data.${NC}"
    echo ""
    read -p "Continue? (y/N): " confirm
    
    if [[ $confirm =~ ^[Yy]$ ]]; then
        ./run_research.sh
    else
        echo -e "${YELLOW}Cancelled.${NC}"
        read -p "Press enter to continue..."
    fi
}

# Main loop
while true; do
    clear
    echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${BOLD}         DQN CPU SCHEDULER - ENHANCED LAUNCHER         ${NC}${CYAN}║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    show_menu
    
    read -p "Enter your choice [0-9]: " choice
    echo ""
    
    case $choice in
        1)
            run_enhanced_dashboard
            ;;
        2)
            run_basic_dashboard
            ;;
        3)
            run_background
            ;;
        4)
            view_metrics
            ;;
        5)
            view_logs
            ;;
        6)
            stop_all
            ;;
        7)
            clean_data
            ;;
        8)
            generate_plots
            ;;
        9)
            run_research
            ;;
        0)
            echo -e "${GREEN}Exiting launcher. Goodbye!${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid choice. Please try again.${NC}"
            sleep 2
            ;;
    esac
done