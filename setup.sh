#!/bin/bash
set -e

echo "════════════════════════════════════════════════════════════"
echo "  CPU SCHEDULER OPTIMIZER - Research-Grade Setup"
echo "════════════════════════════════════════════════════════════"
echo ""

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Checking dependencies...${NC}"

command -v rustc >/dev/null || {
  echo -e "${RED}❌ Rust not installed${NC}"
  echo "Install from https://rustup.rs/"
  exit 1
}

command -v python3 >/dev/null || {
  echo -e "${RED}❌ Python3 not installed${NC}"
  exit 1
}

echo -e "${GREEN}✓${NC} Rust: $(rustc --version)"
echo -e "${GREEN}✓${NC} Python: $(python3 --version)"

echo ""
echo -e "${BLUE}Checking system tools...${NC}"
for tool in renice chrt; do
  command -v $tool >/dev/null \
    && echo -e "${GREEN}✓${NC} $tool available" \
    || echo -e "${YELLOW}⚠${NC}  $tool missing"
done

echo ""
echo -e "${BLUE}Setting up Python environment...${NC}"

if [ ! -d venv ]; then
  python3 -m venv venv
  echo -e "${GREEN}✓${NC} Virtual env created"
fi

source venv/bin/activate
pip install --upgrade pip
pip install -r python/requirements.txt

echo ""
echo -e "${BLUE}Building Rust binary...${NC}"
cd rust
cargo build --release
cd ..

mkdir -p data/{logs,metrics/{baseline,rl_controlled},models}
mkdir -p results/{plots,reports,exports,live}
mkdir -p checkpoints

touch data/logs/{rust_monitor.log,python_agent.log}

echo ""
echo -e "${GREEN}✅ Setup complete${NC}"
