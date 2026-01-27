#!/bin/bash

source venv/bin/activate

if [ ! -f /tmp/scheduler_metrics.csv ]; then
  echo "❌ No metrics found. Run run_research.sh first."
  exit 1
fi

python3 python/research_evaluation.py
ls -lh results/*.png
