"""
Test suite for Secure Multi-Party Computation (SMPC) implementation.

This module contains comprehensive tests for both the cryptographic components
and the SMPC system functionality.
"""

import unittest
import random
from typing import List, Tuple
from smpc_crypto import SMPCCrypto
from smpc_system import SMPCSystem, Party


class TestSMPCCrypto(unittest.TestCase):
    """Test cases for SMPC cryptographic operations."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.crypto = SMPCCrypto()
        self.test_secret = 12345
        self.threshold = 3
        self.num_shares = 5
    
    def test_secret_sharing_basic(self):
        """Test basic secret sharing functionality."""
        shares = self.crypto.create_shares(self.test_secret, self.threshold, self.num_shares)
        
        # Check correct number of shares
        self.assertEqual(len(shares), self.num_shares)
        
        # Check share format
        for party_id, share_value in shares:
            self.assertIsInstance(party_id, int)
            self.assertIsInstance(share_value, int)
            self.assertGreater(party_id, 0)
    
    def test_secret_reconstruction(self):
        """Test secret reconstruction from shares."""
        shares = self.crypto.create_shares(self.test_secret, self.threshold, self.num_shares)
        
        # Reconstruct with exact threshold
        subset_shares = shares[:self.threshold]
        reconstructed = self.crypto.reconstruct_secret(subset_shares)
        self.assertEqual(reconstructed, self.test_secret)
        
        # Reconstruct with more than threshold
        subset_shares = shares[:self.threshold + 1]
        reconstructed = self.crypto.reconstruct_secret(subset_shares)
        self.assertEqual(reconstructed, self.test_secret)
    
    def test_insufficient_shares(self):
        """Test that reconstruction fails with insufficient shares."""
        shares = self.crypto.create_shares(self.test_secret, self.threshold, self.num_shares)
        
        with self.assertRaises(ValueError):
            self.crypto.reconstruct_secret([])
        
        with self.assertRaises(ValueError):
            self.crypto.reconstruct_secret(shares[:1])
    
    def test_threshold_validation(self):
        """Test validation of threshold parameters."""
        with self.assertRaises(ValueError):
            self.crypto.create_shares(123, 6, 5)  # threshold > num_shares
        
        with self.assertRaises(ValueError):
            self.crypto.create_shares(123, 0, 5)  # invalid threshold
        
        with self.assertRaises(ValueError):
            self.crypto.create_shares(123, 3, 0)  # invalid num_shares
    
    def test_share_addition(self):
        """Test homomorphic addition of shares."""
        secret1 = 100
        secret2 = 200
        expected_sum = secret1 + secret2
        
        shares1 = self.crypto.create_shares(secret1, 3, 5)
        shares2 = self.crypto.create_shares(secret2, 3, 5)
        
        # Add shares
        sum_shares = self.crypto.add_shares(shares1, shares2)
        
        # Reconstruct sum
        reconstructed_sum = self.crypto.reconstruct_secret(sum_shares[:3])
        self.assertEqual(reconstructed_sum, expected_sum)
    
    def test_share_addition_validation(self):
        """Test validation in share addition."""
        shares1 = self.crypto.create_shares(100, 3, 5)
        shares2 = self.crypto.create_shares(200, 3, 4)  # Different length
        
        with self.assertRaises(ValueError):
            self.crypto.add_shares(shares1, shares2)
    
    def test_large_numbers(self):
        """Test with large numbers."""
        large_secret = 2**50 + 12345
        shares = self.crypto.create_shares(large_secret, 3, 5)
        reconstructed = self.crypto.reconstruct_secret(shares[:3])
        
        # Check modular arithmetic consistency
        expected = large_secret % self.crypto.get_prime()
        self.assertEqual(reconstructed, expected)
    
    def test_zero_secret(self):
        """Test with zero secret."""
        shares = self.crypto.create_shares(0, 3, 5)
        reconstructed = self.crypto.reconstruct_secret(shares[:3])
        self.assertEqual(reconstructed, 0)
    
    def test_random_subsets(self):
        """Test reconstruction with different random subsets of shares."""
        shares = self.crypto.create_shares(self.test_secret, 3, 7)
        
        # Test multiple random subsets
        for _ in range(10):
            random_subset = random.sample(shares, 3)
            reconstructed = self.crypto.reconstruct_secret(random_subset)
            self.assertEqual(reconstructed, self.test_secret)


class TestSMPCSystem(unittest.TestCase):
    """Test cases for SMPC system functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.smpc = SMPCSystem(num_parties=3, threshold=2)
        self.test_values = [100, 250]
        self.computation_id = "test_comp"
    
    def test_system_initialization(self):
        """Test SMPC system initialization."""
        self.assertEqual(len(self.smpc.parties), 3)
        self.assertEqual(self.smpc.threshold, 2)
        
        # Check party initialization
        for i, party in enumerate(self.smpc.parties):
            self.assertEqual(party.id, i + 1)
            self.assertEqual(party.name, f"Party_{i + 1}")
            self.assertEqual(len(party.shares), 0)
    
    def test_invalid_initialization(self):
        """Test invalid system initialization parameters."""
        with self.assertRaises(ValueError):
            SMPCSystem(num_parties=2, threshold=3)  # threshold > num_parties
    
    def test_submit_secret_values(self):
        """Test submitting secret values."""
        result = self.smpc.submit_secret_values(self.test_values, self.computation_id)
        self.assertTrue(result)
        
        # Check computation was registered
        self.assertIn(self.computation_id, self.smpc.computations)
        
        # Check parties received shares with proper naming
        expected_share_names = [
            ['1_A', '2_A'],  # Party 1 gets first share of each secret
            ['1_B', '2_B'],  # Party 2 gets second share of each secret  
            ['1_C', '2_C']   # Party 3 gets third share of each secret
        ]
        
        for party_idx, party in enumerate(self.smpc.parties):
            self.assertIn(self.computation_id, party.shares)
            shares = party.shares[self.computation_id]
            self.assertEqual(len(shares), len(self.test_values))
            
            # Check share names
            share_names = [name for name, _ in shares]
            self.assertEqual(share_names, expected_share_names[party_idx])
    
    def test_submit_invalid_values(self):
        """Test submitting invalid number of values."""
        # Too few values
        result = self.smpc.submit_secret_values([100], self.computation_id)
        self.assertFalse(result)
        
        # Too many values
        result = self.smpc.submit_secret_values([100, 200, 300], self.computation_id)
        self.assertFalse(result)
    
    def test_compute_party_sums(self):
        """Test computing party sums."""
        # Submit values first
        self.smpc.submit_secret_values(self.test_values, self.computation_id)
        
        # Compute party sums
        party_sums = self.smpc.compute_party_sums(self.computation_id)
        
        self.assertEqual(len(party_sums), 3)
        for party_id, sum_value in party_sums.items():
            self.assertIsInstance(party_id, int)
            self.assertIsInstance(sum_value, int)
            self.assertGreater(party_id, 0)
    
    def test_compute_party_sums_missing_computation(self):
        """Test computing party sums for non-existent computation."""
        with self.assertRaises(ValueError):
            self.smpc.compute_party_sums("non_existent")
    
    def test_reconstruct_final_sum(self):
        """Test reconstructing final sum."""
        # Submit values and compute party sums
        self.smpc.submit_secret_values(self.test_values, self.computation_id)
        self.smpc.compute_party_sums(self.computation_id)
        
        # Reconstruct final sum
        final_sum = self.smpc.reconstruct_final_sum(self.computation_id)
        
        expected_sum = sum(self.test_values)
        self.assertEqual(final_sum, expected_sum)
    
    def test_reconstruct_without_party_sums(self):
        """Test reconstruction without computing party sums first."""
        self.smpc.submit_secret_values(self.test_values, self.computation_id)
        
        with self.assertRaises(ValueError):
            self.smpc.reconstruct_final_sum(self.computation_id)
    
    def test_complete_workflow(self):
        """Test complete secure computation workflow."""
        value1, value2 = 123, 456
        expected_sum = value1 + value2
        
        result = self.smpc.run_secure_computation(value1, value2, self.computation_id)
        self.assertEqual(result, expected_sum)
        
        # Check computation status
        status = self.smpc.get_computation_status(self.computation_id)
        self.assertIsNotNone(status)
        self.assertEqual(status['status'], 'completed')
        self.assertEqual(status['final_sum'], expected_sum)
    
    def test_multiple_computations(self):
        """Test handling multiple computations simultaneously."""
        comp1_id = "comp1"
        comp2_id = "comp2"
        
        values1 = [100, 200]
        values2 = [50, 75]
        
        # Run two computations
        result1 = self.smpc.run_secure_computation(values1[0], values1[1], comp1_id)
        result2 = self.smpc.run_secure_computation(values2[0], values2[1], comp2_id)
        
        self.assertEqual(result1, sum(values1))
        self.assertEqual(result2, sum(values2))
        
        # Check both computations exist
        self.assertIn(comp1_id, self.smpc.computations)
        self.assertIn(comp2_id, self.smpc.computations)
    
    def test_get_party_info(self):
        """Test getting party information."""
        party = self.smpc.get_party_info(1)
        self.assertIsNotNone(party)
        self.assertEqual(party.id, 1)
        self.assertEqual(party.name, "Party_1")
        
        # Non-existent party
        party = self.smpc.get_party_info(999)
        self.assertIsNone(party)
    
    def test_reset_computation(self):
        """Test resetting a computation."""
        # Run a computation
        self.smpc.run_secure_computation(100, 200, self.computation_id)
        
        # Verify computation exists
        self.assertIn(self.computation_id, self.smpc.computations)
        
        # Verify parties have shares
        for party in self.smpc.parties:
            self.assertIn(self.computation_id, party.shares)
        
        # Reset computation
        self.smpc.reset_computation(self.computation_id)
        
        # Verify computation is removed
        self.assertNotIn(self.computation_id, self.smpc.computations)
        
        # Verify party shares are cleared
        for party in self.smpc.parties:
            self.assertNotIn(self.computation_id, party.shares)
    
    def test_edge_case_values(self):
        """Test edge case values."""
        test_cases = [
            (0, 0),      # Both zero
            (0, 100),    # One zero
            (1, 1),      # Small values
            (2**20, 2**21),  # Large values
        ]
        
        for i, (val1, val2) in enumerate(test_cases):
            comp_id = f"edge_case_{i}"
            result = self.smpc.run_secure_computation(val1, val2, comp_id)
            expected = (val1 + val2) % self.smpc.crypto.get_prime()
            self.assertEqual(result, expected, f"Failed for values {val1}, {val2}")


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete SMPC system."""
    
    def test_different_system_configurations(self):
        """Test SMPC with different party and threshold configurations."""
        configurations = [
            (3, 2),  # 3 parties, threshold 2
            (5, 3),  # 5 parties, threshold 3
            (4, 4),  # 4 parties, threshold 4 (all required)
        ]
        
        for num_parties, threshold in configurations:
            with self.subTest(parties=num_parties, threshold=threshold):
                smpc = SMPCSystem(num_parties=num_parties, threshold=threshold)
                result = smpc.run_secure_computation(100, 200, f"test_{num_parties}_{threshold}")
                self.assertEqual(result, 300)
    
    def test_consistency_across_runs(self):
        """Test that multiple runs with same inputs produce consistent results."""
        smpc = SMPCSystem()
        val1, val2 = 42, 58
        
        results = []
        for i in range(5):
            result = smpc.run_secure_computation(val1, val2, f"consistency_test_{i}")
            results.append(result)
        
        # All results should be the same
        self.assertTrue(all(r == results[0] for r in results))
        self.assertEqual(results[0], val1 + val2)


def run_tests():
    """Run all tests with detailed output."""
    # Create test suite
    test_classes = [TestSMPCCrypto, TestSMPCSystem, TestIntegration]
    
    suite = unittest.TestSuite()
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)