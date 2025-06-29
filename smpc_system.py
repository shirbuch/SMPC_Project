"""
Secure Multi-Party Computation (SMPC) System

This module implements a complete SMPC system that allows multiple parties
to securely compute the sum of their private inputs without revealing
individual values to each other.
"""

from typing import List, Tuple, Dict, Optional
import logging
from dataclasses import dataclass
from smpc_crypto import SMPCCrypto


@dataclass
class Party:
    """Represents a party in the SMPC protocol."""
    id: int
    name: str
    shares: Dict[str, List[Tuple[str, int]]]  # Maps computation_id to list of (share_name, share_value)
    
    def __post_init__(self):
        if not self.shares:
            self.shares = {}


class SMPCSystem:
    """
    Secure Multi-Party Computation System.
    
    Coordinates secure computation between multiple parties using secret sharing.
    """
    
    def __init__(self, num_parties: int = 3, threshold: int = 2):
        """
        Initialize SMPC system.
        
        Args:
            num_parties: Number of parties participating in computation
            threshold: Minimum shares needed to reconstruct secret
        """
        if threshold > num_parties:
            raise ValueError("Threshold cannot exceed number of parties")
        
        self.num_parties = num_parties
        self.threshold = threshold
        self.crypto = SMPCCrypto()
        self.parties: List[Party] = []
        self.computations: Dict[str, Dict] = {}
        
        # Initialize parties
        for i in range(num_parties):
            party = Party(id=i+1, name=f"Party_{i+1}", shares={})
            self.parties.append(party)
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def submit_secret_values(self, user_values: List[int], computation_id: str = "default") -> bool:
        """
        Submit secret values to be shared among parties.
        Creates shares with names like 1_A, 1_B, 1_C and 2_A, 2_B, 2_C
        
        Args:
            user_values: List of secret values from user
            computation_id: Unique identifier for this computation
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if len(user_values) != 2:
                raise ValueError("Exactly 2 values must be provided")
            
            self.logger.info(f"Starting computation '{computation_id}' with {len(user_values)} values")
            
            # Create shares for each secret value
            all_shares = []
            party_letters = ['A', 'B', 'C', 'D', 'E']  # Support up to 5 parties
            
            for secret_idx, secret in enumerate(user_values):
                shares = self.crypto.create_shares(secret, self.threshold, self.num_parties)
                # Add share names: secret_idx+1 + party_letter
                named_shares = []
                for party_idx, (party_id, share_value) in enumerate(shares):
                    share_name = f"{secret_idx + 1}_{party_letters[party_idx]}"
                    named_shares.append((share_name, share_value, party_id))
                
                all_shares.append(named_shares)
                self.logger.info(f"Created {len(named_shares)} shares for secret {secret_idx + 1}")
            
            # Distribute shares to parties
            for party_idx, party in enumerate(self.parties):
                # Each party gets one share from each secret
                party_shares = []
                for secret_idx in range(len(user_values)):
                    share_name, share_value, party_id = all_shares[secret_idx][party_idx]
                    party_shares.append((share_name, share_value))
                
                # Store shares with computation ID
                party.shares[computation_id] = party_shares
                share_names = [name for name, _ in party_shares]
                self.logger.info(f"Distributed shares {share_names} to {party.name}")
            
            # Store computation metadata
            self.computations[computation_id] = {
                'num_secrets': len(user_values),
                'original_values': user_values,  # Only for verification
                'status': 'shares_distributed',
                'all_shares': all_shares  # Store for reconstruction
            }
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error in submit_secret_values: {e}")
            return False
    
    def compute_party_sums(self, computation_id: str = "default") -> Dict[int, int]:
        """
        Each party computes the sum of their shares locally.
        
        Args:
            computation_id: Computation identifier
            
        Returns:
            Dictionary mapping party_id to their local sum of shares
        """
        if computation_id not in self.computations:
            raise ValueError(f"Computation '{computation_id}' not found")
        
        party_sums = {}
        
        for party in self.parties:
            if computation_id not in party.shares:
                raise ValueError(f"Party {party.name} missing shares for computation '{computation_id}'")
            
            # Sum all share values held by this party
            shares = party.shares[computation_id]
            local_sum = sum(share_value for _, share_value in shares) % self.crypto.get_prime()
            
            party_sums[party.id] = local_sum
            share_names = [name for name, _ in shares]
            self.logger.info(f"{party.name} computed sum of shares {share_names}: {local_sum}")
        
        # Update computation status
        self.computations[computation_id]['party_sums'] = party_sums
        self.computations[computation_id]['status'] = 'party_sums_computed'
        
        return party_sums
    
    def reconstruct_final_sum(self, computation_id: str = "default") -> int:
        """
        Reconstruct the final sum from party sums.
        
        Args:
            computation_id: Computation identifier
            
        Returns:
            Final sum of all original secret values
        """
        if computation_id not in self.computations:
            raise ValueError(f"Computation '{computation_id}' not found")
        
        comp_data = self.computations[computation_id]
        if 'party_sums' not in comp_data:
            raise ValueError("Party sums not computed yet")
        
        # Create shares from party sums for reconstruction
        party_sums = comp_data['party_sums']
        reconstruction_shares = [(party_id, sum_value) for party_id, sum_value in party_sums.items()]
        
        # Reconstruct the final sum
        final_sum = self.crypto.reconstruct_secret(reconstruction_shares[:self.threshold])
        
        self.logger.info(f"Reconstructed final sum: {final_sum}")
        
        # Update computation status
        self.computations[computation_id]['final_sum'] = final_sum
        self.computations[computation_id]['status'] = 'completed'
        
        return final_sum
    
    def run_secure_computation(self, value1: int, value2: int, computation_id: str = "default") -> int:
        """
        Run complete secure computation workflow.
        
        Args:
            value1: First secret value
            value2: Second secret value
            computation_id: Computation identifier
            
        Returns:
            Sum of the two secret values
        """
        self.logger.info("Starting secure multi-party computation")
        
        # Step 1: Submit and distribute secret shares
        if not self.submit_secret_values([value1, value2], computation_id):
            raise RuntimeError("Failed to submit secret values")
        
        # Step 2: Each party computes sum of their shares
        party_sums = self.compute_party_sums(computation_id)
        
        # Step 3: Reconstruct final sum
        final_sum = self.reconstruct_final_sum(computation_id)
        
        # Verify correctness (only for demonstration)
        expected_sum = (value1 + value2) % self.crypto.get_prime()
        if final_sum == expected_sum:
            self.logger.info("✓ Secure computation completed successfully")
        else:
            self.logger.error(f"✗ Computation error: expected {expected_sum}, got {final_sum}")
        
        return final_sum
    
    def get_computation_status(self, computation_id: str = "default") -> Optional[Dict]:
        """Get status of a computation."""
        return self.computations.get(computation_id)
    
    def get_party_info(self, party_id: int) -> Optional[Party]:
        """Get information about a specific party."""
        for party in self.parties:
            if party.id == party_id:
                return party
        return None
    
    def reset_computation(self, computation_id: str = "default") -> None:
        """Reset a computation and clear all related data."""
        if computation_id in self.computations:
            del self.computations[computation_id]
        
        for party in self.parties:
            if computation_id in party.shares:
                del party.shares[computation_id]
        
        self.logger.info(f"Reset computation '{computation_id}'")


def main():
    """Example usage of the SMPC system."""
    print("=== Secure Multi-Party Computation Demo ===")
    
    # Initialize SMPC system with 3 parties, threshold of 2
    smpc = SMPCSystem(num_parties=3, threshold=2)
    
    # User's secret values
    secret1 = 100
    secret2 = 250
    
    print(f"User's secret values: {secret1}, {secret2}")
    print(f"Expected sum: {secret1 + secret2}")
    print()
    
    # Run secure computation
    try:
        result = smpc.run_secure_computation(secret1, secret2)
        print(f"Secure computation result: {result}")
        
        # Show computation details
        status = smpc.get_computation_status()
        if status:
            print(f"Computation status: {status['status']}")
            if 'party_sums' in status:
                print("Party sums:", status['party_sums'])
            
            # Show share distribution details
            print("\nShare Distribution:")
            for party in smpc.parties:
                if 'default' in party.shares:
                    shares = party.shares['default']
                    share_info = [(name, val) for name, val in shares]
                    print(f"  {party.name}: {share_info}")
        
    except Exception as e:
        print(f"Error during computation: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()