#!/bin/bash
set -e

echo "════════════════════════════════════════════════════════════"
echo "  CPU SCHEDULER OPTIMIZER - LIVE SYSTEM"
echo "════════════════════════════════════════════════════════════"
echo ""

source venv/bin/activate
rm -f /tmp/scheduler_*.{csv,log,json} /tmp/rl_*.json 2>/dev/null

if command -v tmux >/dev/null; then
  tmux kill-session -t scheduler 2>/dev/null || true
  tmux new-session -d -s scheduler -n main
  tmux split-window -h
  tmux split-window -v -t scheduler:main.1

  tmux send-keys -t scheduler:main.0 \
    "sudo ./rust/target/release/cpu_scheduler_optimizer | tee data/logs/rust_monitor.log" C-m

  tmux send-keys -t scheduler:main.1 \
    "sleep 5 && python3 python/advanced_dqn_agent.py | tee data/logs/python_agent.log" C-m

  tmux send-keys -t scheduler:main.2 \
    "sleep 8 && python3 python/realtime_monitor.py -d 600 -b 60" C-m

  tmux attach -t scheduler
else
  sudo ./rust/target/release/cpu_scheduler_optimizer > data/logs/rust_monitor.log &
  echo $! > .pids

  sleep 5
  python3 python/advanced_dqn_agent.py > data/logs/python_agent.log &
  echo $! >> .pids

  python3 python/realtime_monitor.py -d 600 -b 60
fi
