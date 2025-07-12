# test_smpc_tcp.py
import subprocess
import time
import unittest

class TestDistributedSMPC(unittest.TestCase):
    def setUp(self):
        self.party_procs = [
            subprocess.Popen(["python3", "party_server.py", str(i+1)])
            for i in range(3)
        ]
        time.sleep(2)

    def tearDown(self):
        for proc in self.party_procs:
            proc.terminate()

    def test_tcp_end_to_end(self):
        result = subprocess.run(["python3", "-c", "from smpc_system_tcp import SMPCSystemTCP; smpc=SMPCSystemTCP(); smpc.run([100, 250], 'test1')"],
                                 capture_output=True, text=True)
        self.assertIn("✅ SUCCESS", result.stdout)

if __name__ == '__main__':
    unittest.main()
