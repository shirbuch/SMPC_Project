#!/usr/bin/env python3
import unittest
import random
import time
import smpc_crypto as crypto
from smpc_controller import SMPCController


class TestSMPCCrypto(unittest.TestCase):
    def setUp(self):
        self.prime = crypto.get_prime()
        self.secret = 12345
        self.threshold = 3
        self.num_shares = 5

    def test_create_shares_valid(self):
        shares = crypto.create_shares(self.secret, self.threshold, self.num_shares, self.prime)
        self.assertEqual(len(shares), self.num_shares)
        self.assertEqual(len(set(x for x, _ in shares)), self.num_shares)

    def test_create_shares_invalid(self):
        with self.assertRaises(ValueError):
            crypto.create_shares(42, 6, 5, self.prime)

    def test_reconstruct_secret_success(self):
        shares = crypto.create_shares(self.secret, self.threshold, self.num_shares, self.prime)
        random.shuffle(shares)
        rec = crypto.reconstruct_secret(shares[:self.threshold], self.prime)
        self.assertEqual(rec, self.secret)

    def test_reconstruct_secret_failure(self):
        shares = crypto.create_shares(self.secret, self.threshold, self.num_shares, self.prime)
        with self.assertRaises(ValueError):
            crypto.reconstruct_secret(shares[:1], self.prime)
        with self.assertRaises(ValueError):
            crypto.reconstruct_secret([], self.prime)

    def test_add_shares_valid(self):
        s1, s2 = 100, 200
        shares1 = crypto.create_shares(s1, self.threshold, self.num_shares, self.prime)
        shares2 = crypto.create_shares(s2, self.threshold, self.num_shares, self.prime)
        added = crypto.add_shares(shares1, shares2, self.prime)
        result = crypto.reconstruct_secret(added[:self.threshold], self.prime)
        expected = (s1 + s2) % self.prime
        self.assertEqual(result, expected)

    def test_add_shares_mismatch(self):
        shares1 = crypto.create_shares(100, 3, 5, self.prime)
        shares2 = [(id + 1, val) for id, val in shares1]
        with self.assertRaises(ValueError):
            crypto.add_shares(shares1, shares2, self.prime)

    def test_prime_is_consistent(self):
        self.assertTrue(self.prime > 2**200)

    def test_threshold_security(self):
        shares = crypto.create_shares(self.secret, threshold=3, num_shares=5, prime=self.prime)
        rec = crypto.reconstruct_secret(shares[:2], self.prime)
        self.assertNotEqual(rec, self.secret)
        rec = crypto.reconstruct_secret(shares[:3], self.prime)
        self.assertEqual(rec, self.secret)
        rec = crypto.reconstruct_secret(shares[:4], self.prime)
        self.assertEqual(rec, self.secret)


class TestSMPCController(unittest.TestCase):
    def setUp(self):
        self.smpc = SMPCController(3, 2)

    def test_run_secure_computation(self):
        result = self.smpc.run_secure_computation(50, 60)
        self.assertEqual(result, 110)

    def test_multiple_runs(self):
        res1 = self.smpc.run_secure_computation(10, 20)
        res2 = self.smpc.run_secure_computation(5, 7)
        self.assertEqual(res1, 30)
        self.assertEqual(res2, 12)

    def test_compute_party_sums_and_reconstruction(self):
        shares = self.smpc.submit_secret_values([100, 200])
        sums = self.smpc.compute_party_sums(shares)
        result = self.smpc.reconstruct_final_sum(sums)
        expected = (100 + 200) % self.smpc.prime
        self.assertEqual(result, expected)

    def test_partial_ids(self):
        shares = self.smpc.submit_secret_values([10, 90])
        partials = self.smpc.compute_party_sums(shares)
        used_ids = list(partials.keys())[:2]
        result = self.smpc.reconstruct_final_sum(partials, party_ids=used_ids)
        self.assertEqual(result, 100)

    def test_insufficient_shares(self):
        shares = self.smpc.submit_secret_values([10, 15])
        partials = self.smpc.compute_party_sums(shares)
        only_one_id = [list(partials.keys())[0]]
        with self.assertRaises(ValueError):
            self.smpc.reconstruct_final_sum(partials, party_ids=only_one_id)

    def test_edge_cases(self):
        for val1, val2 in [(0, 0), (0, 10), (-5, 5), (10**8, 10**8)]:
            with self.subTest(val1=val1, val2=val2):
                expected = (val1 + val2) % self.smpc.prime
                result = self.smpc.run_secure_computation(val1, val2)
                self.assertEqual(result, expected)

    def test_all_configurations(self):
        configs = [(3, 2), (4, 2), (5, 3), (4, 4)]
        for num, thresh in configs:
            with self.subTest(parties=num, threshold=thresh):
                smpc = SMPCController(num, thresh)
                result = smpc.run_secure_computation(100, 200)
                self.assertEqual(result, 300)

    def test_performance_sizes(self):
        for a, b in [(10, 20), (1000, 2000), (10**6, 2*10**6), (10**9, 2*10**9)]:
            with self.subTest(val1=a, val2=b):
                start = time.time()
                result = self.smpc.run_secure_computation(a, b)
                duration = (time.time() - start) * 1000
                expected = (a + b) % self.smpc.prime
                self.assertEqual(result, expected)
                self.assertLess(duration, 1000)


def run_tests():
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
    suite_system = loader.loadTestsFromTestCase(TestSMPCController)
    result_system = runner.run(suite_system)

    total = result_crypto.testsRun + result_system.testsRun
    failures = len(result_crypto.failures) + len(result_system.failures)
    errors = len(result_crypto.errors) + len(result_system.errors)
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
