#!/bin/bash
set -e

echo "════════════════════════════════════════════════════════════"
echo "  FULL RL RESEARCH EXPERIMENT"
echo "════════════════════════════════════════════════════════════"
echo ""

source venv/bin/activate
rm -f /tmp/scheduler_*.{csv,log,json} /tmp/rl_*.json 2>/dev/null

DURATION=1800
BASELINE=300

sudo ./rust/target/release/cpu_scheduler_optimizer > data/logs/rust_monitor.log &
RUST_PID=$!

sleep 5
python3 python/advanced_dqn_agent.py > data/logs/python_agent.log &
AGENT_PID=$!

python3 python/realtime_monitor.py -d $DURATION -b $BASELINE

sudo kill $RUST_PID
kill $AGENT_PID

python3 python/research_evaluation.py

echo "✅ Research experiment completed"
