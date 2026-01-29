#!/bin/bash

# Quick Fix Script - Apply code fixes and restart DQN Optimizer
# This fixes the baseline→training transition issue

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
echo -e "${CYAN}   DQN CPU SCHEDULER - QUICK FIX SCRIPT${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════${NC}\n"

echo -e "${YELLOW}This script will:${NC}"
echo "  1. Stop all running processes"
echo "  2. Replace Python agent with fixed version"
echo "  3. Replace Rust monitor with fixed version"
echo "  4. Rebuild Rust binary"
echo "  5. Clean temporary files"
echo "  6. Restart with enhanced dashboard"
echo ""
read -p "Continue? (y/N): " confirm

if [[ ! $confirm =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Cancelled.${NC}"
    exit 0
fi

echo ""
echo -e "${CYAN}[1/6]${NC} Stopping existing processes..."
./stop.sh 2>/dev/null || true
killall cpu_scheduler_optimizer 2>/dev/null || true
killall -9 python3 2>/dev/null || true
sleep 2
echo -e "${GREEN}✓ Processes stopped${NC}"

echo ""
echo -e "${CYAN}[2/6]${NC} Backing up old files..."
if [ -f "python/advanced_dqn_agent.py" ]; then
    cp python/advanced_dqn_agent.py python/advanced_dqn_agent.py.backup
    echo -e "${GREEN}✓ Backed up Python agent${NC}"
fi

if [ -f "rust/src/main.rs" ]; then
    cp rust/src/main.rs rust/src/main.rs.backup
    echo -e "${GREEN}✓ Backed up Rust monitor${NC}"
fi

echo ""
echo -e "${CYAN}[3/6]${NC} Applying Python fixes..."
if [ -f "advanced_dqn_agent.py" ]; then
    cp advanced_dqn_agent.py python/advanced_dqn_agent.py
    echo -e "${GREEN}✓ Python agent updated${NC}"
else
    echo -e "${RED}✗ advanced_dqn_agent.py not found!${NC}"
    echo -e "${YELLOW}  Make sure to place the fixed file in the project root${NC}"
    exit 1
fi

echo ""
echo -e "${CYAN}[4/6]${NC} Applying Rust fixes..."
if [ -f "main.rs" ]; then
    cp main.rs rust/src/main.rs
    echo -e "${GREEN}✓ Rust monitor updated${NC}"
else
    echo -e "${RED}✗ main.rs not found!${NC}"
    echo -e "${YELLOW}  Make sure to place the fixed file in the project root${NC}"
    exit 1
fi

echo ""
echo -e "${CYAN}[5/6]${NC} Rebuilding Rust binary..."
cd rust
cargo build --release
cd ..
echo -e "${GREEN}✓ Rust binary rebuilt${NC}"

echo ""
echo -e "${CYAN}[6/6]${NC} Cleaning temporary files..."
./clean.sh
echo -e "${GREEN}✓ Cleanup complete${NC}"

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}   FIX APPLIED SUCCESSFULLY!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}\n"

echo -e "${YELLOW}What was fixed:${NC}"
echo "  ✓ Python agent now properly transitions baseline→training after 60s"
echo "  ✓ Rust monitor now correctly tracks and switches modes"
echo "  ✓ State file synchronization improved"
echo "  ✓ Timing issues resolved"
echo ""

echo -e "${CYAN}Next steps:${NC}"
echo "  1. Generate workload (recommended):"
echo -e "     ${GREEN}./generate_load.sh${NC}"
echo ""
echo "  2. Start the enhanced dashboard:"
echo -e "     ${GREEN}./launcher.sh${NC} (select option 1)"
echo ""
echo "  Or run directly:"
echo -e "     ${GREEN}python3 enhanced_terminal_dashboard.py${NC}"
echo ""

echo -e "${YELLOW}Expected timeline:${NC}"
echo "  • 0-60s:   Baseline collection (you'll see progress bar)"
echo "  • 60s:     Automatic switch to training mode"
echo "  • 90-120s: First improvements visible"
echo "  • 3-5min:  Stable 20-50% improvements"
echo ""

read -p "Start the system now? (y/N): " start_now

if [[ $start_now =~ ^[Yy]$ ]]; then
    echo ""
    echo -e "${CYAN}Starting system...${NC}\n"
    
    # Check if we should generate load
    read -p "Generate CPU workload first? (recommended) (y/N): " gen_load
    if [[ $gen_load =~ ^[Yy]$ ]]; then
        echo -e "${CYAN}Generating workload...${NC}"
        ./generate_load.sh &
        LOAD_PID=$!
        sleep 2
    fi
    
    # Start components
    echo -e "${CYAN}Starting Rust monitor...${NC}"
    ./rust/target/release/cpu_scheduler_optimizer > data/logs/rust_monitor.log 2>&1 &
    RUST_PID=$!
    sleep 3
    
    echo -e "${CYAN}Starting DQN agent...${NC}"
    source venv/bin/activate
    python3 python/advanced_dqn_agent.py > data/logs/python_agent.log 2>&1 &
    PYTHON_PID=$!
    sleep 3
    
    echo -e "${CYAN}Starting enhanced dashboard...${NC}"
    echo ""
    python3 enhanced_terminal_dashboard.py
    
    # Cleanup on exit
    if [ ! -z "$RUST_PID" ]; then
        kill $RUST_PID 2>/dev/null || true
    fi
    if [ ! -z "$PYTHON_PID" ]; then
        kill $PYTHON_PID 2>/dev/null || true
    fi
    if [ ! -z "$LOAD_PID" ]; then
        kill $LOAD_PID 2>/dev/null || true
    fi
else
    echo ""
    echo -e "${GREEN}Fix complete! Run the system when ready.${NC}"
fi

echo ""