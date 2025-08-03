#!/usr/bin/env python3
"""
Create simple inputs for quick SMPC test
Each hospital provides just 3 summary values
"""

import json
import os

def create_simple_inputs():
    """Create simple test inputs from existing hospital data"""
    
    # Load existing hospital data
    hospitals_data = []
    for hospital_id in ['hospital_a', 'hospital_b', 'hospital_c', 'hospital_d']:
        with open(f'data/private/{hospital_id}_private.json', 'r') as f:
            hospitals_data.append(json.load(f))
    
    # Create simple input files
    os.makedirs('inputs_simple', exist_ok=True)
    
    print("Creating simple test inputs...")
    print("-" * 40)
    
    for i, hospital_data in enumerate(hospitals_data):
        patient_data = hospital_data['patient_data']
        
        # Calculate simple aggregates
        patient_count = len(patient_data['ages'])
        total_age = sum(patient_data['ages'])
        total_cost = sum(patient_data['treatment_costs'])
        
        # Create input file with just 3 values
        inputs = [patient_count, total_age, total_cost]
        
        input_file = f'inputs_simple/Player-Data-P{i}.txt'
        with open(input_file, 'w') as f:
            for value in inputs:
                f.write(f"{value}\n")
        
        print(f"Party {i} ({hospital_data['hospital_name']}):")
        print(f"  Patients: {patient_count}")
        print(f"  Total age: {total_age}")
        print(f"  Total cost: ${total_cost:,}")
        print(f"  File: {input_file}")
        print()
    
    print("✅ Simple test inputs created!")
    print("These will test basic SMPC functionality quickly.")

def create_mp_spdz_inputs():
    """Copy simple inputs to MP-SPDZ format"""
    
    mp_spdz_dir = os.path.expanduser('~/MP-SPDZ')
    player_data_dir = os.path.join(mp_spdz_dir, 'Player-Data')
    
    os.makedirs(player_data_dir, exist_ok=True)
    
    for i in range(4):
        src_file = f'inputs_simple/Player-Data-P{i}.txt'
        dst_file = os.path.join(player_data_dir, f'Input-P{i}-0')
        
        if os.path.exists(src_file):
            with open(src_file, 'r') as f:
                content = f.read()
            with open(dst_file, 'w') as f:
                f.write(content)
            print(f"✅ Created {dst_file}")
        else:
            print(f"❌ Missing {src_file}")

if __name__ == "__main__":
    # Check if hospital data exists
    required_files = [f'data/private/hospital_{h}_private.json' 
                     for h in ['a', 'b', 'c', 'd']]
    
    missing_files = [f for f in required_files if not os.path.exists(f)]
    if missing_files:
        print("❌ Missing hospital data files:")
        for f in missing_files:
            print(f"  {f}")
        print("Run data_generator.py first!")
        exit(1)
    
    create_simple_inputs()
    create_mp_spdz_inputs()
    
    print("\n🚀 Ready to test! Run:")
    print("cd ~/MP-SPDZ")
    print("./compile.py simple_test")
    print("./mascot-party.x 0 simple_test -N 4 -h localhost &")
    print("./mascot-party.x 1 simple_test -N 4 -h localhost &") 
    print("./mascot-party.x 2 simple_test -N 4 -h localhost &")
    print("./mascot-party.x 3 simple_test -N 4 -h localhost")
