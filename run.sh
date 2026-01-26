#!/bin/bash
set -e

echo "════════════════════════════════════════════════════════════"
echo "  CPU SCHEDULER OPTIMIZER - Deep RL System"
echo "════════════════════════════════════════════════════════════"
echo ""

# Activate virtual environment
source venv/bin/activate

# Clean previous runs
rm -f /tmp/scheduler_*.{csv,log,json}
rm -f /tmp/rl_*.json

# Check if tmux is available
if command -v tmux &> /dev/null; then
    echo "Using tmux for multi-pane management..."
    
    # Kill existing session
    tmux kill-session -t scheduler 2>/dev/null || true
    
    # Create new session with 4 panes
    tmux new-session -d -s scheduler -n main
    tmux split-window -h -t scheduler:main
    tmux split-window -v -t scheduler:main.0
    tmux split-window -v -t scheduler:main.1
    
    # Pane 0 (top-left): Rust monitor
    tmux send-keys -t scheduler:main.0 \
        "cd $(pwd) && ./rust/target/release/cpu_scheduler_optimizer 2>&1 | tee data/logs/rust_monitor.log" C-m
    
    # Pane 1 (bottom-left): Python DQN agent
    tmux send-keys -t scheduler:main.1 \
        "cd $(pwd) && source venv/bin/activate && sleep 5 && python3 python/dqn_agent.py 2>&1 | tee data/logs/python_agent.log" C-m
    
    # Pane 2 (top-right): Real-time monitor
    tmux send-keys -t scheduler:main.2 \
        "cd $(pwd) && source venv/bin/activate && sleep 8 && python3 python/realtime_monitor.py" C-m
    
    # Pane 3 (bottom-right): Web server
    tmux send-keys -t scheduler:main.3 \
        "cd $(pwd) && source venv/bin/activate && sleep 10 && python3 python/web_server.py" C-m
    
    echo "✅ All components launched!"
    echo ""
    echo "Commands:"
    echo "  • Attach to session:  tmux attach -t scheduler"
    echo "  • Detach:             Ctrl+B, then D"
    echo "  • Stop:               ./stop.sh"
    echo "  • Web dashboard:      http://localhost:5000"
    echo ""
    
    # Attach to session
    tmux attach -t scheduler
    
else
    echo "tmux not available - launching in background..."
    
    # Launch components
    ./rust/target/release/cpu_scheduler_optimizer > data/logs/rust_monitor.log 2>&1 &
    RUST_PID=$!
    echo "✓ Rust monitor started (PID: $RUST_PID)"
    
    sleep 5
    python3 python/dqn_agent.py > data/logs/python_agent.log 2>&1 &
    AGENT_PID=$!
    echo "✓ DQN agent started (PID: $AGENT_PID)"
    
    sleep 3
    python3 python/web_server.py > data/logs/web_server.log 2>&1 &
    WEB_PID=$!
    echo "✓ Web server started (PID: $WEB_PID)"
    
    # Save PIDs
    echo "$RUST_PID $AGENT_PID $WEB_PID" > .pids
    
    echo ""
    echo "✅ System running!"
    echo "   Web dashboard: http://localhost:5000"
    echo "   Stop with: ./stop.sh"
    
    # Run real-time monitor in foreground
    python3 python/realtime_monitor.py
fi