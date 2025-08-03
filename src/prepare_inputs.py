#!/usr/bin/env python3
"""
Input Preparation Script for SMPC Healthcare Analytics
Converts JSON data to MP-SPDZ input format
"""

import json
import os
from typing import Dict, List

class SMPCInputPreparator:
    def __init__(self, data_dir='data/private', max_patients=250):
        self.data_dir = data_dir
        self.max_patients = max_patients
    
    def load_hospital_data(self, hospital_id: str) -> Dict:
        """Load hospital data from JSON file"""
        filepath = os.path.join(self.data_dir, f'{hospital_id}_private.json')
        with open(filepath, 'r') as f:
            return json.load(f)
    
    def prepare_hospital_inputs(self, hospital_data: Dict) -> List[int]:
        """Prepare input data for a specific hospital"""
        patient_data = hospital_data['patient_data']
        num_patients = len(patient_data['ages'])
        
        inputs = []
        
        # First input: number of patients
        inputs.append(num_patients)
        
        # Prepare each data type, padded to max_patients
        data_types = ['ages', 'treatment_costs', 'recovery_times', 
                     'success_rates', 'severity_scores', 'length_of_stay']
        
        for data_type in data_types:
            data = patient_data[data_type]
            # Pad with zeros if needed
            padded_data = data + [0] * (self.max_patients - len(data))
            inputs.extend(padded_data)
        
        return inputs
    
    def create_input_files(self):
        """Create input files for all hospitals"""
        hospital_ids = ['hospital_a', 'hospital_b', 'hospital_c', 'hospital_d']
        
        os.makedirs('inputs', exist_ok=True)
        
        for i, hospital_id in enumerate(hospital_ids):
            print(f"Preparing inputs for {hospital_id} (Party {i})...")
            
            # Load hospital data
            hospital_data = self.load_hospital_data(hospital_id)
            
            # Prepare inputs
            inputs = self.prepare_hospital_inputs(hospital_data)
            
            # Save to input file
            input_filename = f'inputs/Player-Data-P{i}.txt'
            with open(input_filename, 'w') as f:
                for value in inputs:
                    f.write(f"{value}\n")
            
            print(f"  Created {input_filename} with {len(inputs)} values")
        
        print("✅ All input files created successfully!")
        
    def print_input_summary(self):
        """Print summary of input files"""
        hospital_ids = ['hospital_a', 'hospital_b', 'hospital_c', 'hospital_d']
        
        print("\n" + "="*50)
        print("INPUT FILES SUMMARY")
        print("="*50)
        
        for i, hospital_id in enumerate(hospital_ids):
            hospital_data = self.load_hospital_data(hospital_id)
            input_file = f'inputs/Player-Data-P{i}.txt'
            
            if os.path.exists(input_file):
                with open(input_file, 'r') as f:
                    lines = f.readlines()
                
                print(f"\nParty {i} ({hospital_data['hospital_name']}):")
                print(f"  File: {input_file}")
                print(f"  Patients: {lines[0].strip()}")
                print(f"  Total inputs: {len(lines)}")
            else:
                print(f"\n❌ Missing input file: {input_file}")

def main():
    """Main function to prepare all inputs"""
    print("SMPC Input Preparation")
    print("="*30)
    
    preparator = SMPCInputPreparator()
    
    # Check if data files exist
    required_files = ['hospital_a_private.json', 'hospital_b_private.json',
                     'hospital_c_private.json', 'hospital_d_private.json']
    
    missing_files = []
    for filename in required_files:
        if not os.path.exists(f'data/private/{filename}'):
            missing_files.append(filename)
    
    if missing_files:
        print("❌ Missing data files:")
        for filename in missing_files:
            print(f"  - data/private/{filename}")
        print("\nPlease run data_generator.py first!")
        return
    
    # Create input files
    preparator.create_input_files()
    preparator.print_input_summary()

if __name__ == "__main__":
    main()
