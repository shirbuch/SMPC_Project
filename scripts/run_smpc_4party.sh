#!/bin/bash

set -e

PROJECT_DIR="$HOME/smpc-healthcare-project"
MP_SPDZ_DIR="$HOME/MP-SPDZ"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_step() {
    echo -e "\n${YELLOW}$1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

cd "$PROJECT_DIR"

# Ensure files are in place
print_step "Setting up MP-SPDZ environment..."
mkdir -p "$MP_SPDZ_DIR/Programs/Source"
cp src/healthcare_analytics.mpc "$MP_SPDZ_DIR/Programs/Source/"
cp inputs/Player-Data-P*.txt "$MP_SPDZ_DIR/"
print_success "Files copied"

# Compile if needed
cd "$MP_SPDZ_DIR"
if [ ! -f "Programs/Bytecode/healthcare_analytics-0.bc" ]; then
    print_step "Compiling MPC program..."
    ./compile.py healthcare_analytics
    print_success "Compiled"
fi

# Run with 4 parties
print_step "Running secure computation with 4 parties..."
echo "🔒 Starting MASCOT protocol with 4 hospitals..."

# Kill any existing processes
pkill -f mascot-party.x || true
sleep 1

# Method 1: Run all in background except last
for i in 0 1 2; do
    ./mascot-party.x $i healthcare_analytics -N 4 -h localhost &
done

# Run party 3 in foreground to see output
if ./mascot-party.x 3 healthcare_analytics -N 4 -h localhost; then
    print_success "🎉 SMPC computation completed successfully!"
else
    print_error "Computation failed"
    # Kill background processes
    pkill -f mascot-party.x || true
    exit 1
fi

# Wait for background processes to finish
wait

print_success "All parties completed successfully!"
