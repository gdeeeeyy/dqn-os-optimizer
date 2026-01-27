#!/bin/bash

echo "Stopping CPU Scheduler Optimizer..."

tmux kill-session -t scheduler 2>/dev/null || true
sudo pkill -f cpu_scheduler_optimizer 2>/dev/null
pkill -f advanced_dqn_agent.py 2>/dev/null
pkill -f realtime_monitor.py 2>/dev/null

if [ -f .pids ]; then
  xargs sudo kill -9 < .pids
  rm .pids
fi

echo "✅ System stopped"
