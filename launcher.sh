#!/bin/bash

# Beautiful Terminal Launcher with ASCII Art

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

# Unicode box drawing characters
TL="╔"  # Top left
TR="╗"  # Top right
BL="╚"  # Bottom left
BR="╝"  # Bottom right
H="═"   # Horizontal
V="║"   # Vertical
VR="╠"  # Vertical right
VL="╣"  # Vertical left
HU="╩"  # Horizontal up
HD="╦"  # Horizontal down
CROSS="╬" # Cross

clear

# ASCII Art Header
echo -e "${CYAN}${BOLD}"
cat << 'EOF'
    ╔═══════════════════════════════════════════════════════════════════════╗
    ║                                                                       ║
    ║        ██████╗██████╗ ██╗   ██╗    ███████╗ ██████╗██╗  ██╗███████╗ ║
    ║       ██╔════╝██╔══██╗██║   ██║    ██╔════╝██╔════╝██║  ██║██╔════╝ ║
    ║       ██║     ██████╔╝██║   ██║    ███████╗██║     ███████║█████╗   ║
    ║       ██║     ██╔═══╝ ██║   ██║    ╚════██║██║     ██╔══██║██╔══╝   ║
    ║       ╚██████╗██║     ╚██████╔╝    ███████║╚██████╗██║  ██║███████╗ ║
    ║        ╚═════╝╚═╝      ╚═════╝     ╚══════╝ ╚═════╝╚═╝  ╚═╝╚══════╝ ║
    ║                                                                       ║
    ║              SCHEDULER OPTIMIZER - Deep RL for OS Scheduling         ║
    ║              Research-Grade System • User-Space Implementation       ║
    ║                                                                       ║
    ╚═══════════════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Check system status
SETUP_DONE=false
DATA_AVAILABLE=false
RESULTS_AVAILABLE=false

if [ -d "venv" ] && [ -f "rust/target/release/cpu_scheduler_optimizer" ]; then
    SETUP_DONE=true
fi

if [ -f "/tmp/scheduler_metrics.csv" ]; then
    DATA_AVAILABLE=true
    DATA_LINES=$(wc -l < /tmp/scheduler_metrics.csv 2>/dev/null || echo "0")
fi

if [ -d "results" ] && [ "$(ls -A results/*.png 2>/dev/null)" ]; then
    RESULTS_AVAILABLE=true
    RESULT_COUNT=$(ls -1 results/*.png 2>/dev/null | wc -l)
fi

# System Status Panel
echo ""
echo -e "${BOLD}${BLUE}╔═══════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}${BLUE}║${NC}  ${BOLD}SYSTEM STATUS${NC}                                                          ${BOLD}${BLUE}║${NC}"
echo -e "${BOLD}${BLUE}╠═══════════════════════════════════════════════════════════════════════╣${NC}"

# Setup status
if [ "$SETUP_DONE" = true ]; then
    echo -e "${BOLD}${BLUE}║${NC}  ${GREEN}✓${NC} Setup Complete      ${DIM}Python venv + Rust binary ready${NC}             ${BOLD}${BLUE}║${NC}"
else
    echo -e "${BOLD}${BLUE}║${NC}  ${YELLOW}⚠${NC} Setup Needed        ${DIM}Run ./setup.sh first${NC}                       ${BOLD}${BLUE}║${NC}"
fi

# Data status
if [ "$DATA_AVAILABLE" = true ]; then
    echo -e "${BOLD}${BLUE}║${NC}  ${GREEN}✓${NC} Data Collected      ${DIM}$DATA_LINES samples in /tmp/scheduler_metrics.csv${NC} ${BOLD}${BLUE}║${NC}"
else
    echo -e "${BOLD}${BLUE}║${NC}  ${YELLOW}○${NC} No Data Yet         ${DIM}Run option 1 to collect real data${NC}            ${BOLD}${BLUE}║${NC}"
fi

# Results status
if [ "$RESULTS_AVAILABLE" = true ]; then
    echo -e "${BOLD}${BLUE}║${NC}  ${GREEN}✓${NC} Results Generated   ${DIM}$RESULT_COUNT plot(s) in results/ directory${NC}       ${BOLD}${BLUE}║${NC}"
else
    echo -e "${BOLD}${BLUE}║${NC}  ${YELLOW}○${NC} No Results          ${DIM}Run option 2 after collecting data${NC}            ${BOLD}${BLUE}║${NC}"
fi

# System info
echo -e "${BOLD}${BLUE}║${NC}  ${CYAN}ℹ${NC} CPU Cores: $(nproc)      ${DIM}Monitoring $(nproc) logical processors${NC}         ${BOLD}${BLUE}║${NC}"
echo -e "${BOLD}${BLUE}╚═══════════════════════════════════════════════════════════════════════╝${NC}"

# Main Menu
echo ""
echo -e "${BOLD}${MAGENTA}╔═══════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}${MAGENTA}║${NC}  ${BOLD}MAIN MENU${NC}                                                              ${BOLD}${MAGENTA}║${NC}"
echo -e "${BOLD}${MAGENTA}╠═══════════════════════════════════════════════════════════════════════╣${NC}"
echo -e "${BOLD}${MAGENTA}║${NC}                                                                       ${BOLD}${MAGENTA}║${NC}"
echo -e "${BOLD}${MAGENTA}║${NC}  ${BOLD}${GREEN}[1]${NC} ${BOLD}Run System with Live Dashboard${NC}                               ${BOLD}${MAGENTA}║${NC}"
echo -e "${BOLD}${MAGENTA}║${NC}      ${DIM}• Collect REAL CPU metrics from your system${NC}                   ${BOLD}${MAGENTA}║${NC}"
echo -e "${BOLD}${MAGENTA}║${NC}      ${DIM}• Terminal dashboard with live comparison${NC}                     ${BOLD}${MAGENTA}║${NC}"
echo -e "${BOLD}${MAGENTA}║${NC}      ${DIM}• Duration: ~6 minutes (60s baseline + 5min RL)${NC}               ${BOLD}${MAGENTA}║${NC}"
echo -e "${BOLD}${MAGENTA}║${NC}      ${DIM}• Creates: /tmp/scheduler_metrics.csv${NC}                         ${BOLD}${MAGENTA}║${NC}"
echo -e "${BOLD}${MAGENTA}║${NC}                                                                       ${BOLD}${MAGENTA}║${NC}"
echo -e "${BOLD}${MAGENTA}║${NC}  ${BOLD}${GREEN}[2]${NC} ${BOLD}Generate Analysis & Publication Plots${NC}                        ${BOLD}${MAGENTA}║${NC}"
echo -e "${BOLD}${MAGENTA}║${NC}      ${DIM}• Statistical analysis (p-values, effect sizes)${NC}               ${BOLD}${MAGENTA}║${NC}"
echo -e "${BOLD}${MAGENTA}║${NC}      ${DIM}• Publication-quality figures (6-panel comparison)${NC}            ${BOLD}${MAGENTA}║${NC}"
echo -e "${BOLD}${MAGENTA}║${NC}      ${DIM}• LaTeX table for research paper${NC}                              ${BOLD}${MAGENTA}║${NC}"
if [ "$DATA_AVAILABLE" = false ]; then
    echo -e "${BOLD}${MAGENTA}║${NC}      ${YELLOW}⚠ Requires data from option 1${NC}                                ${BOLD}${MAGENTA}║${NC}"
fi
echo -e "${BOLD}${MAGENTA}║${NC}                                                                       ${BOLD}${MAGENTA}║${NC}"
echo -e "${BOLD}${MAGENTA}║${NC}  ${BOLD}${GREEN}[3]${NC} ${BOLD}View Existing Results${NC}                                         ${BOLD}${MAGENTA}║${NC}"
echo -e "${BOLD}${MAGENTA}║${NC}      ${DIM}• List generated plots and reports${NC}                             ${BOLD}${MAGENTA}║${NC}"
echo -e "${BOLD}${MAGENTA}║${NC}      ${DIM}• Show file sizes and locations${NC}                               ${BOLD}${MAGENTA}║${NC}"
if [ "$RESULTS_AVAILABLE" = false ]; then
    echo -e "${BOLD}${MAGENTA}║${NC}      ${YELLOW}⚠ No results yet - run option 2 first${NC}                        ${BOLD}${MAGENTA}║${NC}"
fi
echo -e "${BOLD}${MAGENTA}║${NC}                                                                       ${BOLD}${MAGENTA}║${NC}"
echo -e "${BOLD}${MAGENTA}║${NC}  ${BOLD}${CYAN}[4]${NC} ${BOLD}Run Full Research Experiment (30 minutes)${NC}                     ${BOLD}${MAGENTA}║${NC}"
echo -e "${BOLD}${MAGENTA}║${NC}      ${DIM}• Extended data collection for publication${NC}                     ${BOLD}${MAGENTA}║${NC}"
echo -e "${BOLD}${MAGENTA}║${NC}      ${DIM}• 5 min baseline + 25 min RL optimization${NC}                     ${BOLD}${MAGENTA}║${NC}"
echo -e "${BOLD}${MAGENTA}║${NC}      ${DIM}• Auto-generates all plots at completion${NC}                      ${BOLD}${MAGENTA}║${NC}"
echo -e "${BOLD}${MAGENTA}║${NC}                                                                       ${BOLD}${MAGENTA}║${NC}"
echo -e "${BOLD}${MAGENTA}║${NC}  ${BOLD}${CYAN}[5]${NC} ${BOLD}Generate CPU Workload (for testing)${NC}                           ${BOLD}${MAGENTA}║${NC}"
echo -e "${BOLD}${MAGENTA}║${NC}      ${DIM}• Create synthetic CPU load${NC}                                   ${BOLD}${MAGENTA}║${NC}"
echo -e "${BOLD}${MAGENTA}║${NC}      ${DIM}• Better results with active workload${NC}                          ${BOLD}${MAGENTA}║${NC}"
echo -e "${BOLD}${MAGENTA}║${NC}                                                                       ${BOLD}${MAGENTA}║${NC}"
echo -e "${BOLD}${MAGENTA}║${NC}  ${BOLD}${CYAN}[6]${NC} ${BOLD}Test Process Profiler${NC}                                         ${BOLD}${MAGENTA}║${NC}"
echo -e "${BOLD}${MAGENTA}║${NC}      ${DIM}• See which processes are being monitored${NC}                     ${BOLD}${MAGENTA}║${NC}"
echo -e "${BOLD}${MAGENTA}║${NC}      ${DIM}• Check workload classification${NC}                               ${BOLD}${MAGENTA}║${NC}"
echo -e "${BOLD}${MAGENTA}║${NC}                                                                       ${BOLD}${MAGENTA}║${NC}"
echo -e "${BOLD}${MAGENTA}╠═══════════════════════════════════════════════════════════════════════╣${NC}"
echo -e "${BOLD}${MAGENTA}║${NC}                                                                       ${BOLD}${MAGENTA}║${NC}"
echo -e "${BOLD}${MAGENTA}║${NC}  ${BOLD}${YELLOW}[7]${NC} ${BOLD}Clean Temporary Files${NC}                                         ${BOLD}${MAGENTA}║${NC}"
echo -e "${BOLD}${MAGENTA}║${NC}      ${DIM}• Remove /tmp files and PIDs${NC}                                  ${BOLD}${MAGENTA}║${NC}"
echo -e "${BOLD}${MAGENTA}║${NC}      ${DIM}• Preserves results and logs${NC}                                  ${BOLD}${MAGENTA}║${NC}"
echo -e "${BOLD}${MAGENTA}║${NC}                                                                       ${BOLD}${MAGENTA}║${NC}"
echo -e "${BOLD}${MAGENTA}║${NC}  ${BOLD}${YELLOW}[8]${NC} ${BOLD}Deep Clean (All Data & Results)${NC}                              ${BOLD}${MAGENTA}║${NC}"
echo -e "${BOLD}${MAGENTA}║${NC}      ${DIM}• Remove all data, results, checkpoints${NC}                       ${BOLD}${MAGENTA}║${NC}"
echo -e "${BOLD}${MAGENTA}║${NC}      ${DIM}• Start completely fresh${NC}                                      ${BOLD}${MAGENTA}║${NC}"
echo -e "${BOLD}${MAGENTA}║${NC}                                                                       ${BOLD}${MAGENTA}║${NC}"
echo -e "${BOLD}${MAGENTA}║${NC}  ${BOLD}${RED}[0]${NC} ${BOLD}Exit${NC}                                                           ${BOLD}${MAGENTA}║${NC}"
echo -e "${BOLD}${MAGENTA}║${NC}                                                                       ${BOLD}${MAGENTA}║${NC}"
echo -e "${BOLD}${MAGENTA}╚═══════════════════════════════════════════════════════════════════════╝${NC}"

echo ""
echo -e -n "${BOLD}${CYAN}➤ Enter your choice [0-8]: ${NC}"
read -r choice

echo ""

case $choice in
    1)
        echo -e "${BOLD}${GREEN}╔═══════════════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${BOLD}${GREEN}║ Starting System with Terminal Dashboard...                           ║${NC}"
        echo -e "${BOLD}${GREEN}╚═══════════════════════════════════════════════════════════════════════╝${NC}"
        echo ""
        
        if [ ! -x "run_with_dashboard.sh" ]; then
            chmod +x run_with_dashboard.sh
        fi
        
        if [ "$SETUP_DONE" = false ]; then
            echo -e "${RED}❌ Setup required first!${NC}"
            echo "Run: ./setup.sh"
            exit 1
        fi
        
        ./run_with_dashboard.sh
        ;;
    
    2)
        echo -e "${BOLD}${GREEN}╔═══════════════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${BOLD}${GREEN}║ Generating Analysis & Plots...                                        ║${NC}"
        echo -e "${BOLD}${GREEN}╚═══════════════════════════════════════════════════════════════════════╝${NC}"
        echo ""
        
        if [ "$DATA_AVAILABLE" = false ]; then
            echo -e "${RED}❌ No data available!${NC}"
            echo ""
            echo "You need to collect data first:"
            echo "  1. Run option 1 (System with Dashboard)"
            echo "  2. Wait at least 6 minutes"
            echo "  3. Then run this option again"
            echo ""
        else
            source venv/bin/activate
            python3 python/research_evaluation.py
            
            echo ""
            echo -e "${BOLD}${GREEN}╔═══════════════════════════════════════════════════════════════════════╗${NC}"
            echo -e "${BOLD}${GREEN}║ ✓ Analysis Complete!                                                  ║${NC}"
            echo -e "${BOLD}${GREEN}╚═══════════════════════════════════════════════════════════════════════╝${NC}"
            echo ""
            echo "Results saved to results/ directory:"
            ls -lh results/*.png 2>/dev/null | awk '{printf "  📊 %-40s %8s\n", $9, $5}'
            ls -lh results/*.txt 2>/dev/null | awk '{printf "  📝 %-40s %8s\n", $9, $5}'
            ls -lh results/*.tex 2>/dev/null | awk '{printf "  📄 %-40s %8s\n", $9, $5}'
        fi
        ;;
    
    3)
        echo -e "${BOLD}${CYAN}╔═══════════════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${BOLD}${CYAN}║ Existing Results                                                      ║${NC}"
        echo -e "${BOLD}${CYAN}╚═══════════════════════════════════════════════════════════════════════╝${NC}"
        echo ""
        
        if [ "$RESULTS_AVAILABLE" = true ]; then
            echo -e "${BOLD}Available files:${NC}"
            echo ""
            ls -lh results/ 2>/dev/null | grep -v "^total" | awk '{printf "  %-10s %-40s %8s\n", $1, $9, $5}'
            echo ""
            echo -e "${BOLD}Commands to view:${NC}"
            echo "  eog results/research_comparison.png    # View main plot"
            echo "  cat results/research_report.txt        # Read statistical report"
            echo "  cat results/performance_table.tex      # LaTeX table for paper"
        else
            echo -e "${YELLOW}No results found.${NC}"
            echo ""
            echo "Generate results:"
            echo "  1. Run option 1 to collect data"
            echo "  2. Run option 2 to generate plots"
        fi
        ;;
    
    4)
        echo -e "${BOLD}${CYAN}╔═══════════════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${BOLD}${CYAN}║ Full Research Experiment (30 minutes)                                 ║${NC}"
        echo -e "${BOLD}${CYAN}╚═══════════════════════════════════════════════════════════════════════╝${NC}"
        echo ""
        echo "This will:"
        echo "  • Collect 5 minutes of baseline data"
        echo "  • Run DQN optimization for 25 minutes"
        echo "  • Generate all publication plots"
        echo "  • Create statistical analysis report"
        echo ""
        echo -e -n "${BOLD}Continue? (y/n): ${NC}"
        read -r confirm
        
        if [[ "$confirm" =~ ^[Yy]$ ]]; then
            if [ ! -x "run_research.sh" ]; then
                chmod +x run_research.sh
            fi
            ./run_research.sh
        else
            echo "Cancelled."
        fi
        ;;
    
    5)
        echo -e "${BOLD}${CYAN}╔═══════════════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${BOLD}${CYAN}║ CPU Workload Generator                                                ║${NC}"
        echo -e "${BOLD}${CYAN}╚═══════════════════════════════════════════════════════════════════════╝${NC}"
        echo ""
        
        if [ ! -x "generate_load.sh" ]; then
            chmod +x generate_load.sh
        fi
        ./generate_load.sh
        ;;
    
    6)
        echo -e "${BOLD}${CYAN}╔═══════════════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${BOLD}${CYAN}║ Testing Process Profiler                                              ║${NC}"
        echo -e "${BOLD}${CYAN}╚═══════════════════════════════════════════════════════════════════════╝${NC}"
        echo ""
        source venv/bin/activate
        python3 python/process_profiler.py
        ;;
    
    7)
        echo -e "${BOLD}${YELLOW}╔═══════════════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${BOLD}${YELLOW}║ Cleaning Temporary Files...                                           ║${NC}"
        echo -e "${BOLD}${YELLOW}╚═══════════════════════════════════════════════════════════════════════╝${NC}"
        echo ""
        ./clean.sh
        echo ""
        echo -e "${GREEN}✓ Temporary files cleaned${NC}"
        ;;
    
    8)
        echo -e "${BOLD}${RED}╔═══════════════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${BOLD}${RED}║ WARNING: Deep Clean                                                   ║${NC}"
        echo -e "${BOLD}${RED}╚═══════════════════════════════════════════════════════════════════════╝${NC}"
        echo ""
        echo -e "${RED}This will permanently delete:${NC}"
        echo "  • All collected data (data/metrics/)"
        echo "  • All results and plots (results/)"
        echo "  • All trained models (checkpoints/)"
        echo "  • All temporary files (/tmp/scheduler_*)"
        echo ""
        echo -e -n "${BOLD}${RED}Are you absolutely sure? (yes/no): ${NC}"
        read -r confirm
        
        if [ "$confirm" = "yes" ]; then
            ./clean.sh
            rm -rf results/*
            rm -rf data/metrics/*
            rm -rf checkpoints/*
            rm -rf data/logs/*
            echo ""
            echo -e "${GREEN}✓ Deep clean complete - system reset to initial state${NC}"
        else
            echo "Cancelled - no files were deleted."
        fi
        ;;
    
    0)
        echo -e "${BOLD}${BLUE}╔═══════════════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${BOLD}${BLUE}║ Thank you for using CPU Scheduler Optimizer!                         ║${NC}"
        echo -e "${BOLD}${BLUE}╚═══════════════════════════════════════════════════════════════════════╝${NC}"
        echo ""
        exit 0
        ;;
    
    *)
        echo -e "${RED}╔═══════════════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${RED}║ Invalid choice!                                                       ║${NC}"
        echo -e "${RED}╚═══════════════════════════════════════════════════════════════════════╝${NC}"
        ;;
esac

echo ""
echo -e "${BOLD}${BLUE}╔═══════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}${BLUE}║ Press Enter to return to menu...                                     ║${NC}"
echo -e "${BOLD}${BLUE}╚═══════════════════════════════════════════════════════════════════════╝${NC}"
read
exec ./launcher.sh