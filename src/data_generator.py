#!/usr/bin/env python3
"""
Healthcare Data Generator for SMPC Project
Generates realistic healthcare data for 4 hospitals
"""
import random
import json
import numpy as np
import os
from typing import Dict, List, Tuple
from datetime import datetime

class HealthcareDataGenerator:
    def __init__(self, seed=42):
        random.seed(seed)
        np.random.seed(seed)
        
        # Hospital characteristics
        self.hospital_profiles = {
            'hospital_a': {
                'name': 'Metropolitan General Hospital',
                'type': 'General',
                'cost_multiplier': 1.2,  # Higher costs (urban)
                'success_boost': 0.05    # Better outcomes
            },
            'hospital_b': {
                'name': 'Regional Medical Center', 
                'type': 'Regional',
                'cost_multiplier': 0.9,  # Lower costs
                'success_boost': 0.0     # Average outcomes
            },
            'hospital_c': {
                'name': 'University Research Hospital',
                'type': 'Research',
                'cost_multiplier': 1.4,  # Highest costs (research)
                'success_boost': 0.08    # Best outcomes
            },
            'hospital_d': {
                'name': 'Community Healthcare Center',
                'type': 'Community',
                'cost_multiplier': 0.8,  # Lowest costs
                'success_boost': -0.02   # Slightly lower outcomes
            }
        }
    
    def generate_hospital_data(self, hospital_id: str, num_patients: int) -> Dict:
        """Generate realistic healthcare data for a hospital"""
        
        profile = self.hospital_profiles[hospital_id]
        
        # Age distribution (realistic healthcare demographics)
        # Different hospitals see different age distributions
        if profile['type'] == 'Community':
            ages = np.random.normal(45, 18, num_patients).clip(18, 85)
        elif profile['type'] == 'Research':
            ages = np.random.normal(60, 15, num_patients).clip(25, 90)
        else:
            ages = np.random.normal(55, 20, num_patients).clip(18, 90)
        
        ages = ages.astype(int)
        
        # Treatment costs (log-normal distribution with hospital-specific multiplier)
        base_costs = np.random.lognormal(8.5, 1.3, num_patients)
        treatment_costs = (base_costs * profile['cost_multiplier']).astype(int)
        treatment_costs = np.clip(treatment_costs, 500, 100000)  # Reasonable bounds
        
        # Recovery times (gamma distribution, age-dependent)
        age_factor = (ages - 18) / 72  # Normalize age impact
        recovery_base = np.random.gamma(2, 4, num_patients)
        recovery_times = (recovery_base * (1 + age_factor * 0.5)).astype(int)
        recovery_times = np.clip(recovery_times, 1, 365)  # 1 day to 1 year
        
        # Success rates (bernoulli with age and hospital dependency)
        base_success_prob = 0.85 + profile['success_boost']
        age_penalty = (ages - 18) * 0.003  # Success decreases with age
        success_probs = base_success_prob - age_penalty
        success_probs = np.clip(success_probs, 0.4, 0.98)
        success_rates = np.random.binomial(1, success_probs)
        
        # Treatment types with hospital-specific distributions
        if profile['type'] == 'Research':
            treatment_types = np.random.choice(
                ['Surgery', 'Medication', 'Therapy', 'Experimental'], 
                num_patients, p=[0.4, 0.3, 0.2, 0.1]
            )
        else:
            treatment_types = np.random.choice(
                ['Surgery', 'Medication', 'Therapy'], 
                num_patients, p=[0.35, 0.45, 0.2]
            )
        
        # Severity scores (1-10 scale)
        severity_scores = np.random.randint(1, 11, num_patients)
        
        # Length of stay (related to recovery time and severity)
        length_of_stay = (recovery_times * 0.3 + severity_scores * 0.5).astype(int)
        length_of_stay = np.clip(length_of_stay, 1, 60)  # 1-60 days
        
        return {
            'hospital_id': hospital_id,
            'hospital_name': profile['name'],
            'hospital_type': profile['type'],
            'num_patients': num_patients,
            'generation_timestamp': datetime.now().isoformat(),
            'patient_data': {
                'ages': ages.tolist(),
                'treatment_costs': treatment_costs.tolist(),
                'recovery_times': recovery_times.tolist(),
                'success_rates': success_rates.tolist(),
                'treatment_types': treatment_types.tolist(),
                'severity_scores': severity_scores.tolist(),
                'length_of_stay': length_of_stay.tolist()
            },
            # Pre-computed local statistics (for verification)
            'local_stats': {
                'avg_age': float(np.mean(ages)),
                'avg_cost': float(np.mean(treatment_costs)),
                'avg_recovery': float(np.mean(recovery_times)),
                'success_rate': float(np.mean(success_rates)),
                'avg_severity': float(np.mean(severity_scores)),
                'avg_length_of_stay': float(np.mean(length_of_stay)),
                'total_patients': num_patients,
                'total_cost': float(np.sum(treatment_costs)),
                'cost_std': float(np.std(treatment_costs)),
                'age_distribution': {
                    '18-30': int(np.sum((ages >= 18) & (ages <= 30))),
                    '31-50': int(np.sum((ages >= 31) & (ages <= 50))),
                    '51-70': int(np.sum((ages >= 51) & (ages <= 70))),
                    '71+': int(np.sum(ages >= 71))
                }
            }
        }
    
    def generate_all_hospitals_data(self) -> Dict:
        """Generate data for all 4 hospitals with different patient counts"""
        
        # Different hospitals have different patient volumes
        patient_counts = {
            'hospital_a': 180,  # Large urban hospital
            'hospital_b': 150,  # Medium regional hospital  
            'hospital_c': 220,  # Large research hospital
            'hospital_d': 120   # Small community hospital
        }
        
        hospitals = {}
        
        for hospital_id, num_patients in patient_counts.items():
            print(f"Generating data for {hospital_id} with {num_patients} patients...")
            hospital_data = self.generate_hospital_data(hospital_id, num_patients)
            hospitals[hospital_id] = hospital_data
            
            # Save individual hospital data (private) - FIXED PATH
            os.makedirs('../data/private', exist_ok=True)
            with open(f'../data/private/{hospital_id}_private.json', 'w') as f:
                json.dump(hospital_data, f, indent=2)
        
        # Create aggregated statistics for verification (public) - FIXED PATH
        os.makedirs('../data/public', exist_ok=True)
        aggregate_stats = self.compute_true_aggregates(hospitals)
        with open('../data/public/true_aggregates.json', 'w') as f:
            json.dump(aggregate_stats, f, indent=2)
        
        return hospitals
    
    def compute_true_aggregates(self, hospitals: Dict) -> Dict:
        """Compute true aggregate statistics for verification"""
        
        all_ages = []
        all_costs = []
        all_recovery = []
        all_success = []
        all_severity = []
        all_los = []
        total_patients = 0
        total_cost = 0
        
        for hospital_data in hospitals.values():
            patient_data = hospital_data['patient_data']
            all_ages.extend(patient_data['ages'])
            all_costs.extend(patient_data['treatment_costs'])
            all_recovery.extend(patient_data['recovery_times'])
            all_success.extend(patient_data['success_rates'])
            all_severity.extend(patient_data['severity_scores'])
            all_los.extend(patient_data['length_of_stay'])
            total_patients += hospital_data['num_patients']
            total_cost += hospital_data['local_stats']['total_cost']
        
        return {
            'total_patients': total_patients,
            'avg_age': float(np.mean(all_ages)),
            'avg_cost': float(np.mean(all_costs)),
            'avg_recovery': float(np.mean(all_recovery)),
            'overall_success_rate': float(np.mean(all_success)),
            'avg_severity': float(np.mean(all_severity)),
            'avg_length_of_stay': float(np.mean(all_los)),
            'total_healthcare_cost': float(total_cost),
            'cost_std': float(np.std(all_costs)),
            'age_distribution': {
                '18-30': int(np.sum((np.array(all_ages) >= 18) & (np.array(all_ages) <= 30))),
                '31-50': int(np.sum((np.array(all_ages) >= 31) & (np.array(all_ages) <= 50))),
                '51-70': int(np.sum((np.array(all_ages) >= 51) & (np.array(all_ages) <= 70))),
                '71+': int(np.sum(np.array(all_ages) >= 71))
            },
            'cost_distribution': {
                'low_cost_<5000': int(np.sum(np.array(all_costs) < 5000)),
                'medium_cost_5000-15000': int(np.sum((np.array(all_costs) >= 5000) & 
                                                   (np.array(all_costs) <= 15000))),
                'high_cost_>15000': int(np.sum(np.array(all_costs) > 15000))
            }
        }
    
    def print_data_summary(self, hospitals: Dict):
        """Print a summary of generated data"""
        print("\n" + "="*60)
        print("HEALTHCARE DATA GENERATION SUMMARY")
        print("="*60)
        
        for hospital_id, data in hospitals.items():
            stats = data['local_stats']
            print(f"\n{data['hospital_name']} ({hospital_id.upper()})")
            print(f"  Type: {data['hospital_type']}")
            print(f"  Patients: {stats['total_patients']}")
            print(f"  Avg Age: {stats['avg_age']:.1f} years")
            print(f"  Avg Cost: ${stats['avg_cost']:,.0f}")
            print(f"  Success Rate: {stats['success_rate']:.1%}")
            print(f"  Total Revenue: ${stats['total_cost']:,.0f}")

def main():
    """Main function to generate all healthcare data"""
    
    print("Healthcare SMPC Data Generator")
    print("="*40)
    
    # Create directories in parent folder
    os.makedirs('../data/private', exist_ok=True)
    os.makedirs('../data/public', exist_ok=True)
    
    # Generate data
    generator = HealthcareDataGenerator()
    hospitals = generator.generate_all_hospitals_data()
    
    # Print summary
    generator.print_data_summary(hospitals)
    
    print(f"\n✅ Data generation complete!")
    print(f"Private data saved in: ../data/private/")
    print(f"Verification data saved in: ../data/public/")
    print(f"Total hospitals: {len(hospitals)}")
    print(f"Total patients: {sum(h['num_patients'] for h in hospitals.values())}")

if __name__ == "__main__":
    main()