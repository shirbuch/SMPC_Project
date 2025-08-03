#!/usr/bin/env python3
"""
Show Expected Medium Results Script
Displays exactly what the medium SMPC computation should produce
"""

import json
import numpy as np
import os

def load_hospital_data():
    """Load all hospital data"""
    hospitals = {}
    for hospital_id in ['hospital_a', 'hospital_b', 'hospital_c', 'hospital_d']:
        with open(f'data/private/{hospital_id}_private.json', 'r') as f:
            hospitals[hospital_id] = json.load(f)
    return hospitals

def compute_expected_medium_results():
    """Compute exactly what the medium SMPC should produce"""
    
    print("📊 COMPUTING EXPECTED MEDIUM RESULTS")
    print("=" * 60)
    print("These are the exact results your medium SMPC should produce")
    print("(75 patients per hospital = 300 total patients)")
    print()
    
    hospitals = load_hospital_data()
    MAX_PATIENTS = 75
    
    # Show hospital breakdown
    print("🏥 HOSPITAL DATA USED IN MEDIUM VERSION:")
    print("-" * 50)
    
    hospital_summaries = []
    total_patients_used = 0
    
    for i, (hospital_id, data) in enumerate(hospitals.items()):
        patient_data = data['patient_data']
        actual_patients = len(patient_data['ages'])
        patients_to_use = min(actual_patients, MAX_PATIENTS)
        
        print(f"Hospital {i}: {data['hospital_name']}")
        print(f"  Total patients available: {actual_patients}")
        print(f"  Patients used in medium: {patients_to_use}")
        print(f"  Hospital type: {data['hospital_type']}")
        
        hospital_summaries.append({
            'id': i,
            'name': data['hospital_name'],
            'patients_used': patients_to_use,
            'total_available': actual_patients
        })
        
        total_patients_used += patients_to_use
        print()
    
    print(f"📊 TOTAL PATIENTS IN MEDIUM VERSION: {total_patients_used}")
    print()
    
    # Collect data from medium subset (75 patients per hospital)
    all_ages = []
    all_costs = []
    all_recovery = []
    all_success = []
    all_severity = []
    
    for hospital_id, data in hospitals.items():
        patient_data = data['patient_data']
        patients_to_use = min(len(patient_data['ages']), MAX_PATIENTS)
        
        # Take only the first patients_to_use patients
        all_ages.extend(patient_data['ages'][:patients_to_use])
        all_costs.extend(patient_data['treatment_costs'][:patients_to_use])
        all_recovery.extend(patient_data['recovery_times'][:patients_to_use])
        all_success.extend(patient_data['success_rates'][:patients_to_use])
        all_severity.extend(patient_data['severity_scores'][:patients_to_use])
    
    # Compute comprehensive statistics
    expected_results = {
        'total_patients': int(total_patients_used),
        'avg_age': float(np.mean(all_ages)),
        'avg_cost': float(np.mean(all_costs)),
        'avg_recovery': float(np.mean(all_recovery)),
        'success_rate': float(np.mean(all_success) * 100),
        'avg_severity': float(np.mean(all_severity)),
        'total_spending': float(np.sum(all_costs)),
        
        # Age distribution
        'young_18_40': int(np.sum((np.array(all_ages) >= 18) & (np.array(all_ages) <= 40))),
        'middle_41_60': int(np.sum((np.array(all_ages) >= 41) & (np.array(all_ages) <= 60))),
        'senior_61_plus': int(np.sum(np.array(all_ages) >= 61)),
        
        # Cost distribution
        'low_cost_under_8k': int(np.sum(np.array(all_costs) < 8000)),
        'med_cost_8k_20k': int(np.sum((np.array(all_costs) >= 8000) & (np.array(all_costs) <= 20000))),
        'high_cost_over_20k': int(np.sum(np.array(all_costs) > 20000)),
    }
    
    return expected_results, hospital_summaries

def display_expected_results(results, hospital_summaries):
    """Display the expected results in SMPC output format"""
    
    print("🎯 EXPECTED MEDIUM SMPC OUTPUT:")
    print("=" * 60)
    print("This is exactly what your SMPC computation should show:")
    print()
    
    # Mimic SMPC output format
    print("==================================================")
    print("HEALTHCARE ANALYTICS - MEDIUM VERSION (FIXED)")
    print("Multi-Party Computation across 4 hospitals")
    print("Max patients per hospital: 75")
    print("==================================================")
    print()
    
    print("Phase 1: Collecting private data from hospitals...")
    for i, hospital in enumerate(hospital_summaries):
        print(f"Hospital {i} ({hospital['name']}) inputting private data...")
    print("✅ All hospitals have securely input their private data")
    print()
    
    print("Phase 2: Computing basic aggregate statistics...")
    print("--- BASIC STATISTICS ---")
    print(f"Total patients: {results['total_patients']}")
    print(f"Average age: {results['avg_age']:.4f} years")
    print(f"Average cost: ${results['avg_cost']:.4f}")
    print(f"Average recovery: {results['avg_recovery']:.4f} days")
    print(f"Success rate: {results['success_rate']:.4f}%")
    print(f"Average severity: {results['avg_severity']:.4f}/10")
    print(f"Total spending: ${results['total_spending']:.0f}")
    print()
    
    print("Phase 3: Computing advanced analytics...")
    print()
    print("--- AGE DISTRIBUTION ---")
    print(f"Young (18-40): {results['young_18_40']} patients")
    print(f"Middle (41-60): {results['middle_41_60']} patients")
    print(f"Senior (61+): {results['senior_61_plus']} patients")
    print()
    
    print("--- COST ANALYSIS ---")
    print(f"Low cost (< $8,000): {results['low_cost_under_8k']} patients")
    print(f"Medium cost ($8,000-$20,000): {results['med_cost_8k_20k']} patients")
    print(f"High cost (> $20,000): {results['high_cost_over_20k']} patients")
    print()
    
    print("==================================================")
    print("SECURE COMPUTATION COMPLETED SUCCESSFULLY")
    print("==================================================")

def display_verification_table(results):
    """Display results in verification table format"""
    
    print("\n📋 VERIFICATION TABLE FORMAT:")
    print("=" * 80)
    print("Use this table to check your SMPC results:")
    print()
    print(f"{'Metric':<30} {'Expected Value':<20} {'Your SMPC Value':<20} {'Status'}")
    print("-" * 80)
    
    metrics = [
        ('Total Patients', results['total_patients'], 'exact'),
        ('Average Age (years)', results['avg_age'], 'percentage'),
        ('Average Cost ($)', results['avg_cost'], 'percentage'),
        ('Average Recovery (days)', results['avg_recovery'], 'percentage'),
        ('Success Rate (%)', results['success_rate'], 'percentage'),
        ('Average Severity', results['avg_severity'], 'percentage'),
        ('Total Spending ($)', results['total_spending'], 'percentage'),
        ('Young Patients (18-40)', results['young_18_40'], 'exact'),
        ('Middle Patients (41-60)', results['middle_41_60'], 'exact'),
        ('Senior Patients (61+)', results['senior_61_plus'], 'exact'),
        ('Low Cost Patients', results['low_cost_under_8k'], 'exact'),
        ('Medium Cost Patients', results['med_cost_8k_20k'], 'exact'),
        ('High Cost Patients', results['high_cost_over_20k'], 'exact'),
    ]
    
    for name, expected_val, comparison_type in metrics:
        if comparison_type == 'exact':
            criteria = "Must match exactly"
        else:
            criteria = "Within 1% acceptable"
        
        print(f"{name:<30} {expected_val:<20.4f} {'[Your Value]':<20} {criteria}")
    
    print("-" * 80)

def display_summary(results):
    """Display key summary information"""
    
    print("\n📊 KEY EXPECTED VALUES SUMMARY:")
    print("=" * 40)
    print(f"🎯 Total Patients: {results['total_patients']}")
    print(f"👥 Average Age: {results['avg_age']:.2f} years")
    print(f"💰 Average Cost: ${results['avg_cost']:.2f}")
    print(f"✅ Success Rate: {results['success_rate']:.2f}%")
    print(f"💵 Total Spending: ${results['total_spending']:,.0f}")
    print()
    print(f"📈 Age Groups: {results['young_18_40']} | {results['middle_41_60']} | {results['senior_61_plus']}")
    print(f"💲 Cost Groups: {results['low_cost_under_8k']} | {results['med_cost_8k_20k']} | {results['high_cost_over_20k']}")

def save_expected_results(results):
    """Save expected results to file for reference"""
    
    import os
    os.makedirs('results', exist_ok=True)
    
    # Convert numpy types for JSON serialization
    json_results = {}
    for key, value in results.items():
        if isinstance(value, (np.integer, np.floating)):
            json_results[key] = float(value) if isinstance(value, np.floating) else int(value)
        else:
            json_results[key] = value
    
    output_data = {
        'computation_type': 'Medium Version Expected Results',
        'patients_per_hospital': 75,
        'total_patients': json_results['total_patients'],
        'expected_results': json_results,
        'usage_note': 'These are the exact values your medium SMPC should produce'
    }
    
    try:
        with open('results/expected_medium_results.json', 'w') as f:
            json.dump(output_data, f, indent=2)
        print(f"\n💾 Expected results saved to: results/expected_medium_results.json")
    except Exception as e:
        print(f"⚠️  Could not save results: {e}")

def main():
    """Main function to show expected medium results"""
    
    print("🎯 MEDIUM SMPC EXPECTED RESULTS CALCULATOR")
    print("=" * 60)
    print("This script shows exactly what your medium SMPC should produce")
    print()
    
    # Check if data files exist
    required_files = [f'data/private/hospital_{h}_private.json' 
                     for h in ['a', 'b', 'c', 'd']]
    
    missing_files = [f for f in required_files if not os.path.exists(f)]
    if missing_files:
        print("❌ Missing hospital data files:")
        for f in missing_files:
            print(f"   {f}")
        print("\nPlease run: python3 src/data_generator.py")
        return
    
    try:
        # Compute expected results
        results, hospital_summaries = compute_expected_medium_results()
        
        # Display in multiple formats
        display_expected_results(results, hospital_summaries)
        display_verification_table(results)
        display_summary(results)
        
        # Save for reference
        save_expected_results(results)
        
        print("\n" + "=" * 60)
        print("🎉 EXPECTED RESULTS CALCULATED!")
        print("=" * 60)
        print("✅ These are the exact values your medium SMPC should produce")
        print("📊 Use these to verify your SMPC computation is correct")
        print("🔍 Any significant differences indicate computation issues")
        print("📄 Results saved for future reference")
        
    except Exception as e:
        print(f"\n❌ Error calculating expected results: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
