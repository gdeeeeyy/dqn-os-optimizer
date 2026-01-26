#!/bin/bash

echo "Stopping CPU Scheduler Optimizer..."

if command -v tmux &> /dev/null; then
    tmux kill-session -t scheduler 2>/dev/null || true
    echo "✓ Tmux session stopped"
fi

if [ -f .pids ]; then
    read -r RUST_PID AGENT_PID WEB_PID < .pids
    kill $RUST_PID $AGENT_PID $WEB_PID 2>/dev/null || true
    rm .pids
    echo "✓ Background processes stopped"
fi

echo "✅ System stopped"