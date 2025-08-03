#!/usr/bin/env python3
"""
Unit Tests for SMPC Crypto module

Covers:
- SMPC cryptographic primitives (sharing, reconstruction, homomorphic addition)

To run:
    python test_smpc_crypto.py
"""

import unittest
import random
import smpc_crypto as smpc_crypto


class TestSMPCCrypto(unittest.TestCase):
    """Test core SMPC cryptographic operations"""

    def setUp(self):
        self.prime = smpc_crypto.get_prime()
        self.secret = 12345
        self.threshold = 3
        self.num_shares = 5

    def test_create_shares_valid(self):
        """Should generate correct number of unique shares"""
        shares = smpc_crypto.create_shares(self.secret, self.threshold, self.num_shares, self.prime)
        self.assertEqual(len(shares), self.num_shares)
        self.assertEqual(len(set(x for x, _ in shares)), self.num_shares)

    def test_create_shares_invalid(self):
        """Should raise error when threshold > num_shares"""
        with self.assertRaises(ValueError):
            smpc_crypto.create_shares(42, 6, 5, self.prime)

    def test_reconstruct_secret_success(self):
        """Should recover the original secret from threshold shares"""
        shares = smpc_crypto.create_shares(self.secret, self.threshold, self.num_shares, self.prime)
        random.shuffle(shares)
        rec = smpc_crypto.reconstruct_secret(shares[:self.threshold], self.prime)
        self.assertEqual(rec, self.secret)

    def test_reconstruct_secret_failure(self):
        """Should raise error with insufficient shares"""
        shares = smpc_crypto.create_shares(self.secret, self.threshold, self.num_shares, self.prime)
        with self.assertRaises(ValueError):
            smpc_crypto.reconstruct_secret(shares[:1], self.prime)
        with self.assertRaises(ValueError):
            smpc_crypto.reconstruct_secret([], self.prime)

    def test_add_shares_valid(self):
        """Should correctly add shares using crypto.add_shares and reconstruct sum"""
        s1, s2 = 100, 200
        shares1 = smpc_crypto.create_shares(s1, self.threshold, self.num_shares, self.prime)
        shares2 = smpc_crypto.create_shares(s2, self.threshold, self.num_shares, self.prime)

        # Add corresponding y-values (shares) with modular addition
        added_shares = [
            (x[0], smpc_crypto.add_shares([x[1], y[1]], self.prime))
            for x, y in zip(shares1, shares2)
        ]

        # Reconstruct the secret sum from any threshold number of added shares
        result = smpc_crypto.reconstruct_secret(added_shares[:self.threshold], self.prime)
        expected = (s1 + s2) % self.prime
        self.assertEqual(result, expected)


    def test_threshold_security(self):
        """Should fail below threshold, succeed at or above it"""
        shares = smpc_crypto.create_shares(self.secret, threshold=3, num_shares=5, prime=self.prime)
        rec = smpc_crypto.reconstruct_secret(shares[:2], self.prime)
        self.assertNotEqual(rec, self.secret)
        rec = smpc_crypto.reconstruct_secret(shares[:3], self.prime)
        self.assertEqual(rec, self.secret)
        rec = smpc_crypto.reconstruct_secret(shares[:4], self.prime)
        self.assertEqual(rec, self.secret)


def run_tests():
    """
    Run all SMPC_crypto related tests and print a summary.

    Returns:
        bool: True if all tests passed, else False
    """
    loader = unittest.TestLoader()
    runner = unittest.TextTestRunner(verbosity=2)

    print("\n" + "=" * 60)
    print("🔐 Running SMPCCrypto Tests")
    print("=" * 60)
    suite_crypto = loader.loadTestsFromTestCase(TestSMPCCrypto)
    result_crypto = runner.run(suite_crypto)

    total = (
        result_crypto.testsRun
    )
    failures = (
        len(result_crypto.failures)
    )
    errors = (
        len(result_crypto.errors)
    )
    passed = total - failures - errors

    print("\n" + "=" * 60)
    print(f"📊 Total Tests Run: {total}")
    print(f"✅ Passed        : {passed}")
    print(f"❌ Failures      : {failures}")
    print(f"❗ Errors        : {errors}")
    print("=" * 60)

    return failures == 0 and errors == 0


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
