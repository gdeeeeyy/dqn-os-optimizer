#!/bin/bash

echo "Cleaning temporary files..."

rm -f /tmp/scheduler_*.{csv,log,json}
rm -f /tmp/rl_*.json
rm -f .pids

echo "✅ Cleanup complete"
