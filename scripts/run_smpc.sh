#!/bin/bash

# SMPC Healthcare Analytics Runner Script
# Automates the entire SMPC computation process

set -e  # Exit on any error

PROJECT_DIR="$HOME/smpc-healthcare-project"
MP_SPDZ_DIR="$HOME/MP-SPDZ"

echo "=================================="
echo "SMPC Healthcare Analytics Runner"
echo "=================================="

# Check if we're in the right directory
if [ ! -d "$PROJECT_DIR" ]; then
    echo "❌ Project directory not found: $PROJECT_DIR"
    exit 1
fi

cd "$PROJECT_DIR"

# Step 1: Generate healthcare data
echo "Step 1: Generating healthcare data..."
python3 src/data_generator.py

# Step 2: Prepare SMPC inputs
echo -e "\nStep 2: Preparing SMPC inputs..."
python3 src/prepare_inputs.py

# Step 3: Copy files to MP-SPDZ directory
echo -e "\nStep 3: Setting up MP-SPDZ environment..."
cp src/healthcare_analytics.mpc "$MP_SPDZ_DIR/"
cp -r inputs/* "$MP_SPDZ_DIR/"

# Step 4: Compile the MPC program
echo -e "\nStep 4: Compiling MPC program..."
cd "$MP_SPDZ_DIR"
./compile.py healthcare_analytics

# Step 5: Run the secure computation
echo -e "\nStep 5: Running secure multi-party computation..."
echo "This will simulate 4 hospitals computing joint statistics..."
./Scripts/mascot.sh healthcare_analytics

# Step 6: Save results
echo -e "\nStep 6: Saving results..."
cd "$PROJECT_DIR"
mkdir -p results/outputs
cp "$MP_SPDZ_DIR"/*.log results/outputs/ 2>/dev/null || true

echo -e "\n✅ SMPC computation completed successfully!"
echo "Results saved in: results/outputs/"
echo "Check the terminal output above for the computed statistics."
