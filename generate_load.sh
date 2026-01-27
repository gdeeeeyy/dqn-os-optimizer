#!/bin/bash

# Workload Generator - Creates CPU load for testing the scheduler

echo "════════════════════════════════════════════════════════════"
echo "  WORKLOAD GENERATOR - Create CPU Load for Testing"
echo "════════════════════════════════════════════════════════════"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

NUM_CPUS=$(nproc)

echo -e "${BLUE}Available workload types:${NC}"
echo ""
echo "  1) CPU-intensive (stress CPU cores)"
echo "  2) Mixed workload (CPU + some I/O)"
echo "  3) Light background load"
echo "  4) Stop all workloads"
echo ""
echo -e -n "Select workload [1-4]: "
read -r choice

case $choice in
    1)
        echo ""
        echo -e "${GREEN}Starting CPU-intensive workload...${NC}"
        echo "  Using $((NUM_CPUS / 2)) CPU cores"
        echo "  This will create ~50-70% CPU load"
        echo ""
        
        # Use Python for CPU-intensive work (portable)
        for i in $(seq 1 $((NUM_CPUS / 2))); do
            python3 -c "
import time
import math
start = time.time()
while time.time() - start < 600:  # Run for 10 minutes
    # CPU-intensive calculation
    [math.sqrt(x) for x in range(10000)]
" &
        done
        
        echo -e "${GREEN}✓ Workload started (will run for 10 minutes)${NC}"
        echo "  PID: $!"
        echo ""
        echo "Monitor with:"
        echo "  top -H"
        echo "  htop"
        ;;
    
    2)
        echo ""
        echo -e "${GREEN}Starting mixed workload...${NC}"
        echo "  CPU + I/O operations"
        echo ""
        
        # CPU work
        for i in $(seq 1 $((NUM_CPUS / 4))); do
            python3 -c "
import time
import random
start = time.time()
while time.time() - start < 600:
    # Mix of CPU and I/O
    data = [random.random() for _ in range(5000)]
    sorted(data)
    time.sleep(0.01)
" &
        done
        
        # I/O work
        dd if=/dev/zero of=/tmp/test_io_$$.dat bs=1M count=100 oflag=sync &>/dev/null &
        
        echo -e "${GREEN}✓ Mixed workload started${NC}"
        ;;
    
    3)
        echo ""
        echo -e "${GREEN}Starting light background load...${NC}"
        echo "  Low CPU usage, simulates background tasks"
        echo ""
        
        python3 -c "
import time
import random
start = time.time()
while time.time() - start < 600:
    # Light processing
    x = sum([random.random() for _ in range(100)])
    time.sleep(0.1)
" &
        
        echo -e "${GREEN}✓ Background load started${NC}"
        ;;
    
    4)
        echo ""
        echo "Stopping all Python workloads..."
        pkill -f "math.sqrt" 2>/dev/null
        pkill -f "random.random" 2>/dev/null
        rm -f /tmp/test_io_*.dat 2>/dev/null
        echo -e "${GREEN}✓ Workloads stopped${NC}"
        ;;
    
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "═══════════════════════════════════════════════════════════"
echo ""

if [ "$choice" != "4" ]; then
    echo "Workload is running. The scheduler can now optimize it!"
    echo ""
    echo "Next steps:"
    echo "  1. In another terminal, run: ./run_with_dashboard.sh"
    echo "  2. Watch the dashboard optimize the workload"
    echo "  3. Stop workload with: ./generate_load.sh (option 4)"
    echo ""
fi