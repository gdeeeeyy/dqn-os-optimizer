#!/bin/bash
set -e

echo "🔧 Setting up CPU Scheduler Optimizer..."

# Check for Rust
if ! command -v rustc &> /dev/null; then
    echo "❌ Rust not found! Install from https://rustup.rs/"
    exit 1
fi

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found!"
    exit 1
fi

# Setup Python virtual environment
echo "📦 Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r python/requirements.txt

# Build Rust components
echo "🦀 Building Rust components..."
cd rust
cargo build --release
cd ..

# Create necessary directories
mkdir -p data/{metrics/{baseline,rl_controlled},models,logs}
mkdir -p results/{plots,reports,exports,live}

# Initialize log files
touch data/logs/{rust_monitor.log,python_agent.log,actions.log}

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Review config files in config/"
echo "  2. Run ./run.sh to start the system"