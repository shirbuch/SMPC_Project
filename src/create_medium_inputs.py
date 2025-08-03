#!/usr/bin/env python3
"""
Create correctly formatted medium inputs
"""

import json
import os

def create_medium_inputs():
    """Create properly formatted medium inputs"""
    
    MAX_PATIENTS = 75
    
    print("Creating medium inputs...")
    print(f"Max patients per hospital: {MAX_PATIENTS}")
    print("-" * 40)
    
    os.makedirs('inputs_medium', exist_ok=True)
    
    for i, hospital_id in enumerate(['hospital_a', 'hospital_b', 'hospital_c', 'hospital_d']):
        # Load hospital data
        with open(f'data/private/{hospital_id}_private.json', 'r') as f:
            data = json.load(f)
        
        patient_data = data['patient_data']
        actual_patients = len(patient_data['ages'])
        patients_to_use = min(actual_patients, MAX_PATIENTS)
        
        inputs = []
        
        # 1. Patient count
        inputs.append(patients_to_use)
        
        # 2. Ages (padded to MAX_PATIENTS)
        ages = patient_data['ages'][:patients_to_use]
        ages_padded = ages + [0] * (MAX_PATIENTS - len(ages))
        inputs.extend(ages_padded)
        
        # 3. Costs (padded to MAX_PATIENTS)
        costs = patient_data['treatment_costs'][:patients_to_use]
        costs_padded = costs + [0] * (MAX_PATIENTS - len(costs))
        inputs.extend(costs_padded)
        
        # 4. Recovery times (padded to MAX_PATIENTS)
        recovery = patient_data['recovery_times'][:patients_to_use]
        recovery_padded = recovery + [0] * (MAX_PATIENTS - len(recovery))
        inputs.extend(recovery_padded)
        
        # 5. Success rates (padded to MAX_PATIENTS)
        success = patient_data['success_rates'][:patients_to_use]
        success_padded = success + [0] * (MAX_PATIENTS - len(success))
        inputs.extend(success_padded)
        
        # 6. Severity scores (padded to MAX_PATIENTS)
        severity = patient_data['severity_scores'][:patients_to_use]
        severity_padded = severity + [0] * (MAX_PATIENTS - len(severity))
        inputs.extend(severity_padded)
        
        # Save input file
        input_file = f'inputs_medium/Player-Data-P{i}.txt'
        with open(input_file, 'w') as f:
            for value in inputs:
                f.write(f"{value}\n")
        
        print(f"Party {i} ({data['hospital_name']}):")
        print(f"  Using {patients_to_use} patients")
        print(f"  Total inputs: {len(inputs)}")
        print(f"  Expected: {1 + 5 * MAX_PATIENTS}")
        print()
        
        # Verify input structure
        expected = 1 + (5 * MAX_PATIENTS)  # 1 count + 5 data arrays * 75 patients
        if len(inputs) != expected:
            print(f"❌ ERROR: Expected {expected} inputs, got {len(inputs)}")
        else:
            print(f"✅ Correct input size")
    
    return True

def copy_to_mp_spdz():
    """Copy to MP-SPDZ format"""
    
    mp_spdz_dir = os.path.expanduser('~/MP-SPDZ/Player-Data')
    os.makedirs(mp_spdz_dir, exist_ok=True)
    
    print("\nCopying to MP-SPDZ...")
    for i in range(4):
        src = f'inputs_medium/Player-Data-P{i}.txt'
        dst = os.path.join(mp_spdz_dir, f'Input-P{i}-0')
        
        if os.path.exists(src):
            with open(src, 'r') as f:
                content = f.read()
            with open(dst, 'w') as f:
                f.write(content)
            
            lines = len(content.strip().split('\n'))
            print(f"✅ Party {i}: {lines} inputs")
        else:
            print(f"❌ Missing: {src}")
            return False
    
    return True

if __name__ == "__main__":
    if create_medium_inputs():
        if copy_to_mp_spdz():
            print("\n🚀 Ready to run medium version!")
        else:
            print("❌ Failed to copy to MP-SPDZ")
    else:
        print("❌ Failed to create inputs")
