# test_smpc_tcp.py
import subprocess
import time
import unittest
from smpc_system_tcp import SMPCSystemTCP


class TestDistributedSMPC(unittest.TestCase):
    def setUp(self):
        """Start 3 party servers before each test"""
        self.party_procs = [
            subprocess.Popen(["python", "party_server.py", str(i + 1)])
            for i in range(3)
        ]
        time.sleep(2)  # Give time for the servers to bind

    def tearDown(self):
        """Terminate all party servers after each test"""
        for proc in self.party_procs:
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()

    def run_smpc(self, values, computation_id="test"):
        """Helper to run SMPC controller and return result"""
        smpc = SMPCSystemTCP(num_parties=3, threshold=2)
        result = smpc.run(values, computation_id)
        return result, smpc

    def test_basic_sum(self):
        """Test TCP SMPC with small known inputs"""
        values = [100, 250]
        expected = sum(values)
        result, smpc = self.run_smpc(values, "basic_sum")
        self.assertEqual(result, expected % smpc.crypto.get_prime())

    def test_large_values(self):
        """Test TCP SMPC with large integers"""
        values = [123456789012345, 987654321098765]
        expected = sum(values)
        result, smpc = self.run_smpc(values, "large_sum")
        self.assertEqual(result, expected % smpc.crypto.get_prime())

    def test_zero_values(self):
        """Test TCP SMPC with zeroes"""
        values = [0, 0]
        result, _ = self.run_smpc(values, "zero_sum")
        self.assertEqual(result, 0)

    def test_one_value_zero(self):
        """Test one zero and one positive"""
        values = [0, 1234]
        result, smpc = self.run_smpc(values, "zero_and_positive")
        self.assertEqual(result, 1234 % smpc.crypto.get_prime())

    def test_all_parties_send_back(self):
        """Verify all party sums are received"""
        values = [1, 2]
        _, smpc = self.run_smpc(values, "check_sums")
        self.assertEqual(len(smpc.party_sums), 3)
        for pid in [1, 2, 3]:
            self.assertIn(pid, smpc.party_sums)


if __name__ == "__main__":
    unittest.main()
