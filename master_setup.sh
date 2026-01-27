#!/bin/bash
# Master Setup Script - Sets up everything and tests the system

set -e

echo "════════════════════════════════════════════════════════════"
echo "  CPU SCHEDULER OPTIMIZER - MASTER SETUP"
echo "  Research-Grade System - Complete Installation"
echo "════════════════════════════════════════════════════════════"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Step 1: Create directory structure
echo -e "${BLUE}[1/8] Creating directory structure...${NC}"
mkdir -p rust/src
mkdir -p python/{models,config}
mkdir -p web/static
mkdir -p config
mkdir -p data/{metrics/{baseline,rl_controlled},models,logs}
mkdir -p results/{plots,reports,exports,live}
mkdir -p checkpoints
mkdir -p scripts
echo -e "${GREEN}✓${NC} Directory structure created"

# Step 2: Check prerequisites
echo ""
echo -e "${BLUE}[2/8] Checking prerequisites...${NC}"

if ! command -v rustc &> /dev/null; then
    echo -e "${RED}❌ Rust not installed!${NC}"
    echo "Install with: curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not installed!${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Rust: $(rustc --version)"
echo -e "${GREEN}✓${NC} Python: $(python3 --version)"
echo -e "${GREEN}✓${NC} CPU Cores: $(nproc)"

# Step 3: Create Python virtual environment
echo ""
echo -e "${BLUE}[3/8] Setting up Python environment...${NC}"

if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓${NC} Virtual environment created"
else
    echo -e "${YELLOW}⚠${NC}  Virtual environment already exists"
fi

source venv/bin/activate

# Create requirements.txt if it doesn't exist
if [ ! -f "python/requirements.txt" ]; then
    cat > python/requirements.txt << 'REQ_EOF'
torch>=2.0.0
numpy>=1.24.0
pandas>=2.0.0
matplotlib>=3.7.0
seaborn>=0.12.0
scipy>=1.10.0
flask>=2.3.0
pyyaml>=6.0
REQ_EOF
    echo -e "${GREEN}✓${NC} Created requirements.txt"
fi

echo -e "${CYAN}Installing Python packages (this may take a few minutes)...${NC}"
pip install --quiet --upgrade pip
pip install --quiet -r python/requirements.txt

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Python dependencies installed"
else
    echo -e "${RED}❌ Failed to install dependencies${NC}"
    exit 1
fi

# Step 4: Create Cargo.toml if it doesn't exist
echo ""
echo -e "${BLUE}[4/8] Setting up Rust project...${NC}"

if [ ! -f "rust/Cargo.toml" ]; then
    cat > rust/Cargo.toml << 'CARGO_EOF'
[package]
name = "cpu_scheduler_optimizer"
version = "0.1.0"
edition = "2021"

[[bin]]
name = "cpu_scheduler_optimizer"
path = "src/main.rs"

[dependencies]
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
chrono = "0.4"

[profile.release]
opt-level = 3
lto = true
codegen-units = 1
CARGO_EOF
    echo -e "${GREEN}✓${NC} Created Cargo.toml"
fi

# Check if Rust source files exist
if [ -f "rust/src/main.rs" ] && [ -f "rust/src/logger.rs" ] && [ -f "rust/src/controller.rs" ]; then
    echo -e "${CYAN}Building Rust components...${NC}"
    cd rust
    cargo build --release
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} Rust binary compiled successfully"
    else
        echo -e "${RED}❌ Rust compilation failed${NC}"
        echo "Make sure all Rust source files are in rust/src/"
        exit 1
    fi
    cd ..
else
    echo -e "${YELLOW}⚠${NC}  Rust source files not found - skipping compilation"
    echo "Place the following files in rust/src/:"
    echo "  - main.rs"
    echo "  - logger.rs"
    echo "  - controller.rs"
fi

# Step 5: Create configuration files
echo ""
echo -e "${BLUE}[5/8] Creating configuration files...${NC}"

cat > config/scheduler.yaml << 'CONFIG_EOF'
scheduler:
  baseline_duration: 60
  optimization_duration: 300
  metrics_interval: 1.0

actions:
  enabled:
    - set_nice
    - set_scheduler
  
  nice_values:
    high_priority: -5
    normal_priority: 0
    low_priority: 10

safety:
  max_actions_per_minute: 30
  min_action_interval: 2.0
CONFIG_EOF

cat > python/config/hyperparameters.yaml << 'HYPER_EOF'
model:
  state_dim: 12
  action_dim: 5
  hidden_dim: 256

training:
  learning_rate: 0.0001
  gamma: 0.99
  batch_size: 128
  memory_size: 50000
  target_update_freq: 500

exploration:
  epsilon_start: 1.0
  epsilon_end: 0.01
  epsilon_decay: 0.9995

rewards:
  cpu_weight: 2.0
  stability_weight: 3.0
  fairness_weight: 1.5
  latency_weight: 2.0
  context_switch_weight: 1.0
  load_balance_weight: 1.0
HYPER_EOF

cat > .gitignore << 'GITIGNORE_EOF'
# Python
venv/
__pycache__/
*.pyc
*.pyo
*.egg-info/

# Rust
rust/target/
rust/Cargo.lock

# Data
data/
results/
checkpoints/
*.csv
*.log
*.json

# Models
*.pth

# IDE
.vscode/
.idea/
*.swp
GITIGNORE_EOF

echo -e "${GREEN}✓${NC} Configuration files created"

# Step 6: Create Python model files
echo ""
echo -e "${BLUE}[6/8] Creating Python model files...${NC}"

cat > python/models/__init__.py << 'INIT_EOF'
# Models package initialization
INIT_EOF

cat > python/models/dqn.py << 'DQN_EOF'
import torch
import torch.nn as nn

class DQN(nn.Module):
    def __init__(self, state_dim, action_dim, hidden_dim=128):
        super(DQN, self).__init__()
        self.network = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, action_dim)
        )
    
    def forward(self, state):
        return self.network(state)
DQN_EOF

cat > python/models/replay_buffer.py << 'BUFFER_EOF'
import random
from collections import deque

class ReplayBuffer:
    def __init__(self, capacity):
        self.buffer = deque(maxlen=capacity)
    
    def push(self, state, action, reward, next_state, done):
        self.buffer.append((state, action, reward, next_state, done))
    
    def sample(self, batch_size):
        batch = random.sample(self.buffer, min(batch_size, len(self.buffer)))
        states, actions, rewards, next_states, dones = zip(*batch)
        return states, actions, rewards, next_states, dones
    
    def __len__(self):
        return len(self.buffer)
BUFFER_EOF

echo -e "${GREEN}✓${NC} Model files created"

# Step 7: Make shell scripts executable
echo ""
echo -e "${BLUE}[7/8] Setting up shell scripts...${NC}"

if [ -f "setup.sh" ]; then chmod +x setup.sh; fi
if [ -f "run.sh" ]; then chmod +x run.sh; fi
if [ -f "run_research.sh" ]; then chmod +x run_research.sh; fi
if [ -f "stop.sh" ]; then chmod +x stop.sh; fi
if [ -f "clean.sh" ]; then chmod +x clean.sh; fi
if [ -f "generate_plots.sh" ]; then chmod +x generate_plots.sh; fi

echo -e "${GREEN}✓${NC} Shell scripts are executable"

# Step 8: Verify Python files
echo ""
echo -e "${BLUE}[8/8] Verifying Python files...${NC}"

PYTHON_FILES=(
    "python/process_profiler.py"
    "python/advanced_dqn_agent.py"
    "python/research_evaluation.py"
    "python/realtime_monitor.py"
)

MISSING_FILES=()
for file in "${PYTHON_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} Found: $file"
    else
        echo -e "${YELLOW}⚠${NC}  Missing: $file"
        MISSING_FILES+=("$file")
    fi
done

# Summary
echo ""
echo "════════════════════════════════════════════════════════════"
if [ ${#MISSING_FILES[@]} -eq 0 ]; then
    echo -e "${GREEN}✅ SETUP COMPLETE - ALL FILES PRESENT${NC}"
else
    echo -e "${YELLOW}⚠  SETUP COMPLETE - SOME FILES MISSING${NC}"
    echo ""
    echo "Missing files:"
    for file in "${MISSING_FILES[@]}"; do
        echo "  - $file"
    done
    echo ""
    echo "Copy these files from the artifacts provided."
fi
echo "════════════════════════════════════════════════════════════"

# Test data generation
echo ""
echo -e "${BLUE}Would you like to generate sample data for testing? (y/n)${NC}"
read -r response

if [[ "$response" =~ ^[Yy]$ ]]; then
    echo ""
    echo "Generating sample data..."
    python3 python/generate_sample_data.py
    
    echo ""
    echo "Generating test plots..."
    python3 python/research_evaluation.py
    
    echo ""
    echo -e "${GREEN}✅ Test complete! Check results/ directory for plots.${NC}"
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo "  NEXT STEPS"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "1. Verify all Python files are present:"
echo "   ls python/"
echo ""
echo "2. Generate sample data and test plots:"
echo "   python3 python/generate_sample_data.py"
echo "   python3 python/research_evaluation.py"
echo ""
echo "3. Run the full system:"
echo "   ./run_research.sh     # 30-min research experiment"
echo "   or"
echo "   ./run.sh              # Interactive session"
echo ""
echo "4. View results:"
echo "   ls results/           # Plots and reports"
echo ""
echo "════════════════════════════════════════════════════════════" 