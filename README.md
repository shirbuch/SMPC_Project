# Healthcare Analytics SMPC Project

A privacy-preserving healthcare analytics system using Secure Multi-Party Computation (SMPC) to enable hospitals to collaboratively analyze patient data without revealing individual hospital information.

## 🏥 Project Overview

This project demonstrates how multiple hospitals can securely compute aggregate statistics on their combined patient data without sharing raw patient information. Using MP-SPDZ (Multi-Party SPDZ), the system enables:

- **Privacy-preserving collaboration** between 4 hospitals
- **Secure computation** of healthcare statistics
- **No data sharing** - hospitals keep their data private
- **Verifiable results** with expected outcome validation

## 🎯 Features

### Supported Analytics
- **Basic Statistics**: Average age, treatment costs, recovery times, success rates
- **Age Distribution**: Patient counts across age groups (18-40, 41-60, 61+)
- **Cost Analysis**: Distribution across cost categories (low, medium, high)
- **Aggregate Metrics**: Total patients, spending, and success rates

### Hospital Profiles
- **Metropolitan General Hospital**: Large urban hospital (higher costs, better outcomes)
- **Regional Medical Center**: Medium regional hospital (average costs and outcomes)
- **University Research Hospital**: Research facility (highest costs, best outcomes)
- **Community Healthcare Center**: Small community hospital (lowest costs)

## 🛠️ Technical Stack

- **MP-SPDZ**: Secure multi-party computation framework
- **Python 3**: Data generation and input preparation
- **MPC Language**: Custom SMPC programs
- **JSON**: Data storage and configuration

## 📁 Project Structure

```
healthcare-smpc/
├── src/
│   ├── data_generator.py           # Generate realistic hospital data
│   ├── create_simple_inputs.py     # Create simple test inputs
│   ├── create_medium_inputs.py     # Create medium complexity inputs
│   ├── prepare_inputs.py           # General input preparation
│   ├── show_expected_medium.py     # Display expected results
│   ├── simple_test.mpc            # Basic SMPC test program
│   └── healthcare_analytics_medium.mpc  # Full analytics program
├── data/
│   ├── private/                   # Private hospital data (JSON)
│   └── public/                    # Public verification data
├── inputs_simple/                 # Simple test inputs
├── inputs_medium/                 # Medium complexity inputs
└── results/                       # Expected results and outputs
```

## 🚀 Quick Start

### Prerequisites

1. **Set up Python Environment**:
   ```bash
   # Create a virtual environment
   python3 -m venv healthcare-smpc-env

   # Activate the virtual environment
   # On Linux/macOS:
   source healthcare-smpc-env/bin/activate

   # On Windows:
   # healthcare-smpc-env\Scripts\activate
   ```

2. **Install Python dependencies**:
   ```bash
   # Make sure virtual environment is activated
   pip install --upgrade pip
   pip install numpy
   ```

3. **Install MP-SPDZ** (in linux/wsl):
   ```bash
   git clone https://github.com/data61/MP-SPDZ.git
   cd MP-SPDZ
   make -j 8 tldr
   ```

   **Note**: MP-SPDZ requires additional dependencies like GMP, MPIR, libsodium, etc. Follow the [MP-SPDZ installation guide](https://mp-spdz.readthedocs.io/en/latest/readme.html#requirements) for your specific system.

### Step 1: Generate Healthcare Data

**Important**: Make sure your Python virtual environment is activated before running any Python scripts.

```bash
# Activate environment if not already active
source healthcare-smpc-env/bin/activate  # Linux/macOS
# or: healthcare-smpc-env\Scripts\activate  # Windows

cd src/
python3 data_generator.py
```

This creates realistic patient data for 4 hospitals:
- **Hospital A**: 180 patients (Metropolitan General)
- **Hospital B**: 150 patients (Regional Medical)
- **Hospital C**: 220 patients (University Research)
- **Hospital D**: 120 patients (Community Healthcare)

### Step 2: Run Simple Test

For a quick verification that SMPC works:

```bash
# Create simple inputs (3 values per hospital)
python3 create_simple_inputs.py

# Run SMPC computation
cd ~/MP-SPDZ
./compile.py simple_test
./mascot-party.x 0 simple_test -N 4 -h localhost &
./mascot-party.x 1 simple_test -N 4 -h localhost &
./mascot-party.x 2 simple_test -N 4 -h localhost &
./mascot-party.x 3 simple_test -N 4 -h localhost
```

### Step 3: Run Medium Analytics

For comprehensive healthcare analytics:

```bash
# Create medium inputs (75 patients per hospital)
cd src/
python3 create_medium_inputs.py

# See expected results
python3 show_expected_medium.py

# Run SMPC computation
cd ~/MP-SPDZ
./compile.py healthcare_analytics_medium
./mascot-party.x 0 healthcare_analytics_medium -N 4 -h localhost &
./mascot-party.x 1 healthcare_analytics_medium -N 4 -h localhost &
./mascot-party.x 2 healthcare_analytics_medium -N 4 -h localhost &
./mascot-party.x 3 healthcare_analytics_medium -N 4 -h localhost
```

## 📊 Expected Results (Medium Version)

When you run the medium analytics, you should see results similar to:

```
=== BASIC STATISTICS ===
Total patients: 300
Average age: 54.23 years
Average cost: $12,458
Success rate: 87.45%
Total spending: $3,737,400

=== AGE DISTRIBUTION ===
Young (18-40): 89 patients
Middle (41-60): 127 patients
Senior (61+): 84 patients

=== COST ANALYSIS ===
Low cost (< $8,000): 98 patients
Medium cost ($8,000-$20,000): 156 patients
High cost (> $20,000): 46 patients
```

## 💡 Environment Management

### Virtual Environment Commands

```bash
# Create environment (first time only)
python3 -m venv healthcare-smpc-env

# Activate environment (every time you work on the project)
source healthcare-smpc-env/bin/activate  # Linux/macOS
# or: healthcare-smpc-env\Scripts\activate  # Windows

# Deactivate environment (when done working)
deactivate

# Check if environment is active (should show path to virtual env)
which python3  # Linux/macOS
# or: where python  # Windows
```
