#!/bin/bash

# SMPC Healthcare Analytics - Fixed Runner Script
set -e

PROJECT_DIR="$HOME/smpc-healthcare-project"
MP_SPDZ_DIR="$HOME/MP-SPDZ"

# Colors
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

# Step 1: Generate data (if not already done)
if [ ! -f "data/private/hospital_a_private.json" ]; then
    print_step "Step 1: Generating healthcare data..."
    python3 src/data_generator.py
    print_success "Healthcare data generated"
fi

# Step 2: Prepare inputs (if not already done)
if [ ! -f "inputs/Player-Data-P0.txt" ]; then
    print_step "Step 2: Preparing SMPC inputs..."
    python3 src/prepare_inputs.py
    print_success "SMPC inputs prepared"
fi

# Step 3: Copy files to correct MP-SPDZ locations
print_step "Step 3: Setting up MP-SPDZ environment..."

# Create necessary directories
mkdir -p "$MP_SPDZ_DIR/Programs/Source"

# Copy MPC program to correct location
cp src/healthcare_analytics.mpc "$MP_SPDZ_DIR/Programs/Source/"
print_success "MPC program copied to Programs/Source/"

# Copy input files
cp inputs/Player-Data-P*.txt "$MP_SPDZ_DIR/"
print_success "Input files copied"

# Step 4: Compile
print_step "Step 4: Compiling MPC program..."
cd "$MP_SPDZ_DIR"

if ./compile.py healthcare_analytics; then
    print_success "MPC program compiled successfully"
else
    print_error "Compilation failed"
    exit 1
fi

# Step 5: Run computation
print_step "Step 5: Running secure computation..."
echo "🔒 Starting MASCOT protocol..."

if timeout 300 ./Scripts/mascot.sh healthcare_analytics; then
    print_success "SMPC computation completed!"
else
    print_error "Computation failed or timed out"
    exit 1
fi

print_success "🎉 Project completed successfully!"
