#!/usr/bin/env python3
"""
Unit Tests for SMPC System

Covers:
- SMPC cryptographic primitives (sharing, reconstruction, homomorphic addition)
- SMPC controller logic (share distribution, secure computation)
- Party and Share behavior

To run:
    python test_smpc.py
"""

import unittest
import random
import time
import smpc_crypto as crypto
from smpc_controller import SMPCController
from party import Party, Share


class TestSMPCCrypto(unittest.TestCase):
    """Test core SMPC cryptographic operations"""

    def setUp(self):
        self.prime = crypto.get_prime()
        self.secret = 12345
        self.threshold = 3
        self.num_shares = 5

    def test_create_shares_valid(self):
        """Should generate correct number of unique shares"""
        shares = crypto.create_shares(self.secret, self.threshold, self.num_shares, self.prime)
        self.assertEqual(len(shares), self.num_shares)
        self.assertEqual(len(set(x for x, _ in shares)), self.num_shares)

    def test_create_shares_invalid(self):
        """Should raise error when threshold > num_shares"""
        with self.assertRaises(ValueError):
            crypto.create_shares(42, 6, 5, self.prime)

    def test_reconstruct_secret_success(self):
        """Should recover the original secret from threshold shares"""
        shares = crypto.create_shares(self.secret, self.threshold, self.num_shares, self.prime)
        random.shuffle(shares)
        rec = crypto.reconstruct_secret(shares[:self.threshold], self.prime)
        self.assertEqual(rec, self.secret)

    def test_reconstruct_secret_failure(self):
        """Should raise error with insufficient shares"""
        shares = crypto.create_shares(self.secret, self.threshold, self.num_shares, self.prime)
        with self.assertRaises(ValueError):
            crypto.reconstruct_secret(shares[:1], self.prime)
        with self.assertRaises(ValueError):
            crypto.reconstruct_secret([], self.prime)

    def test_add_shares_valid(self):
        """Should correctly add shares using crypto.add_shares and reconstruct sum"""
        s1, s2 = 100, 200
        shares1 = crypto.create_shares(s1, self.threshold, self.num_shares, self.prime)
        shares2 = crypto.create_shares(s2, self.threshold, self.num_shares, self.prime)

        # Add corresponding y-values (shares) with modular addition
        added_shares = [
            (x[0], crypto.add_shares([x[1], y[1]], self.prime))
            for x, y in zip(shares1, shares2)
        ]

        # Reconstruct the secret sum from any threshold number of added shares
        result = crypto.reconstruct_secret(added_shares[:self.threshold], self.prime)
        expected = (s1 + s2) % self.prime
        self.assertEqual(result, expected)


    def test_threshold_security(self):
        """Should fail below threshold, succeed at or above it"""
        shares = crypto.create_shares(self.secret, threshold=3, num_shares=5, prime=self.prime)
        rec = crypto.reconstruct_secret(shares[:2], self.prime)
        self.assertNotEqual(rec, self.secret)
        rec = crypto.reconstruct_secret(shares[:3], self.prime)
        self.assertEqual(rec, self.secret)
        rec = crypto.reconstruct_secret(shares[:4], self.prime)
        self.assertEqual(rec, self.secret)


class TestSMPCController(unittest.TestCase):
    """Test SMPCController functionality"""

    def setUp(self):
        self.smpc = SMPCController(3, 2)

    def test_run_secure_computation(self):
        result = self.smpc.run_secure_computation([50, 60])
        self.assertEqual(result, 110)

    def test_multiple_runs(self):
        res1 = self.smpc.run_secure_computation([10, 20])
        res2 = self.smpc.run_secure_computation([5, 7])
        self.assertEqual(res1, 30)
        self.assertEqual(res2, 12)

    def test_more_than_two_secrets(self):
        result = self.smpc.run_secure_computation([100, 250, 40])
        self.assertEqual(result, 390)

    def test_compute_partial_results_and_reconstruction(self):
        shares = self.smpc.create_shares_for_parties([100, 200, 300])
        results = self.smpc.request_parties_to_compute_results(shares)
        result = self.smpc.reconstruct_final_result(results)
        expected = sum([100, 200, 300]) % self.smpc.prime
        self.assertEqual(result, expected)

    def test_insufficient_shares(self):
        shares = self.smpc.create_shares_for_parties([10, 15])
        partials = self.smpc.request_parties_to_compute_results(shares)
        only_one_id = [list(partials.keys())[0]]
        with self.assertRaises(ValueError):
            self.smpc.reconstruct_final_result(partials, party_ids=only_one_id)

    def test_edge_cases(self):
        for secrets in [[0, 0], [0, 10], [-5, 5], [10**8, 10**8]]:
            with self.subTest(secrets=secrets):
                expected = sum(secrets) % self.smpc.prime
                result = self.smpc.run_secure_computation(secrets)
                self.assertEqual(result, expected)

    def test_all_configurations(self):
        configs = [(3, 2), (4, 2), (5, 3), (4, 4)]
        for num, thresh in configs:
            with self.subTest(parties=num, threshold=thresh):
                smpc = SMPCController(num, thresh)
                result = smpc.run_secure_computation([100, 200])
                self.assertEqual(result, 300)

    def test_performance_sizes(self):
        for secrets in [[10, 20], [1000, 2000], [10**6, 2*10**6], [10**9, 2*10**9]]:
            with self.subTest(secrets=secrets):
                start = time.time()
                result = self.smpc.run_secure_computation(secrets)
                duration = (time.time() - start) * 1000
                expected = sum(secrets) % self.smpc.prime
                self.assertEqual(result, expected)
                self.assertLess(duration, 1000)


class TestPartyAndShare(unittest.TestCase):
    """Test Party and Share behavior"""

    def setUp(self):
        self.prime = crypto.get_prime()

    def test_share_name_generation(self):
        s = Share(value=12345, party_id=1, secret_idx=2)
        self.assertEqual(s.name, "A_2")
        self.assertEqual(str(s), "A_2: 12345")

    def test_partial_result_correctness(self):
        p = Party(1)
        shares = [
            Share(value=100, party_id=1, secret_idx=1),
            Share(value=200, party_id=1, secret_idx=2),
            Share(value=300, party_id=1, secret_idx=3),
        ]
        result = p.compute_sum(shares, self.prime)
        expected = (100 + 200 + 300) % self.prime
        self.assertEqual(result, expected)


def run_tests():
    """
    Run all SMPC-related tests and print a summary.

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

    print("\n" + "=" * 60)
    print("🤝 Running SMPCController Tests")
    print("=" * 60)
    suite_controller = loader.loadTestsFromTestCase(TestSMPCController)
    result_controller = runner.run(suite_controller)

    print("\n" + "=" * 60)
    print("🧩 Running Party & Share Tests")
    print("=" * 60)
    suite_party = loader.loadTestsFromTestCase(TestPartyAndShare)
    result_party = runner.run(suite_party)

    total = (
        result_crypto.testsRun +
        result_controller.testsRun +
        result_party.testsRun
    )
    failures = (
        len(result_crypto.failures) +
        len(result_controller.failures) +
        len(result_party.failures)
    )
    errors = (
        len(result_crypto.errors) +
        len(result_controller.errors) +
        len(result_party.errors)
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
