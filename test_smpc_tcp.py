#!/usr/bin/env python3
"""
Comprehensive test suite for the SMPC (Secure Multi-Party Computation) system.
Tests communication layer, party servers, and the TCP controller.
"""

import unittest
import threading
import time
import socket
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict

RUN_NETWORK_TESTS = True

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from comm_layer import BaseServer, send_data
    from party_server import PartyServer
    from smpc_controller_tcp import SMPCControllerTCP
    from party import Party, Share
    from smpc_controller import SMPCController
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure all required files are in the same directory as this test file.")
    sys.exit(1)


class TestCommLayer(unittest.TestCase):
    """Test the communication layer functionality"""
    
    def test_send_data(self):
        """Test basic data sending functionality"""
        received_data = []
        
        def mock_handler(data):
            received_data.append(data)
        
        # Start a simple server in a thread
        def start_server():
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(('localhost', 12345))
                s.listen(1)
                s.settimeout(2.0)  # Timeout after 2 seconds
                try:
                    conn, _ = s.accept()
                    with conn:
                        data = b""
                        while True:
                            chunk = conn.recv(4096)
                            if not chunk:
                                break
                            data += chunk
                        import pickle
                        obj = pickle.loads(data)
                        mock_handler(obj)
                except socket.timeout:
                    pass
        
        server_thread = threading.Thread(target=start_server)
        server_thread.start()
        time.sleep(0.1)  # Give server time to start
        
        # Send test data
        test_data = {"test": "message", "number": 42}
        send_data('localhost', 12345, test_data)
        
        server_thread.join(timeout=3)
        
        self.assertEqual(len(received_data), 1)
        self.assertEqual(received_data[0], test_data)


class TestPartyServer(unittest.TestCase):
    """Test PartyServer functionality"""
    
    def setUp(self):
        self.party_server = PartyServer(party_id=1)
    
    def test_party_server_initialization(self):
        """Test that PartyServer initializes correctly"""
        self.assertEqual(self.party_server.id, 1)
        self.assertEqual(self.party_server.host, '0.0.0.0')
        self.assertEqual(self.party_server.port, 8001)
        self.assertIn("Party_A", self.party_server.name)
    
    @patch.object(PartyServer, 'send_data')
    @patch.object(PartyServer, 'compute_sum')
    @patch.object(PartyServer, 'unpack_compute_sum_request')
    def test_handle_incoming_compute_sum(self, mock_unpack, mock_compute, mock_send):
        """Test handling of compute_sum action"""
        # Setup mocks
        mock_shares = [Mock(spec=Share), Mock(spec=Share)]
        mock_prime = 2**31 - 1
        mock_unpack.return_value = (mock_shares, mock_prime)
        mock_compute.return_value = 12345
        
        # Test data
        test_data = {
            'action': 'compute_sum',
            'shares': mock_shares,
            'prime': mock_prime
        }
        
        # Call the method
        self.party_server.handle_incoming(test_data)
        
        # Verify calls
        mock_unpack.assert_called_once_with(test_data)
        mock_compute.assert_called_once_with(mock_shares, mock_prime)
        mock_send.assert_called_once_with(
            'localhost', 9000, 
            {'party_id': 1, 'sum': 12345}
        )
    
    def test_handle_incoming_unknown_action(self):
        """Test handling of unknown action"""
        test_data = {'action': 'unknown_action'}
        
        # Should not raise an exception
        try:
            self.party_server.handle_incoming(test_data)
        except Exception as e:
            self.fail(f"handle_incoming raised an exception for unknown action: {e}")


class MockPartyServer:
    """Mock party server for testing without network"""
    
    def __init__(self, party_id: int):
        self.party_id = party_id
        self.received_data = []
    
    def receive_data(self, data):
        self.received_data.append(data)
        # Simulate computation and return result
        if data.get('action') == 'compute_sum':
            # Mock computation result
            return {
                'party_id': self.party_id,
                'sum': 100 + self.party_id  # Simple mock result
            }


class TestSMPCControllerTCP(unittest.TestCase):
    """Test SMPCControllerTCP functionality"""
    
    def setUp(self):
        self.controller = SMPCControllerTCP(num_parties=3, threshold=2)
    
    def test_controller_initialization(self):
        """Test controller initialization"""
        self.assertEqual(self.controller.host, '0.0.0.0')
        self.assertEqual(self.controller.port, 9000)
        self.assertEqual(len(self.controller.party_hosts), 3)
        self.assertEqual(self.controller.controller.num_parties, 3)
        self.assertEqual(self.controller.controller.threshold, 2)
    
    def test_handle_incoming(self):
        """Test handling incoming party results"""
        test_data = {
            'party_id': 1,
            'sum': 12345
        }
        
        self.controller.handle_incoming(test_data)
        
        self.assertIn(1, self.controller.party_sums)
        self.assertEqual(self.controller.party_sums[1], 12345)
    
    def test_handle_incoming_invalid_data(self):
        """Test handling invalid incoming data"""
        invalid_data = {'invalid': 'data'}
        
        # Should not raise an exception
        try:
            self.controller.handle_incoming(invalid_data)
        except Exception as e:
            self.fail(f"handle_incoming raised an exception for invalid data: {e}")
        
        # Should not add anything to party_sums
        self.assertEqual(len(self.controller.party_sums), 0)
    
    @patch.object(SMPCControllerTCP, 'send_data')
    def test_distribute_shares(self, mock_send):
        """Test share distribution to parties"""
        secrets = [100, 200, 300]
        
        self.controller.distribute_shares(secrets)
        
        # Should send data to all parties
        self.assertEqual(mock_send.call_count, 3)
        
        # Check that each call has the right structure
        for call in mock_send.call_args_list:
            args, kwargs = call
            host, port, data = args
            self.assertEqual(host, "localhost")
            self.assertIn(port, [8001, 8002, 8003])
            self.assertEqual(data['action'], 'compute_sum')
            self.assertIn('shares', data)
            self.assertIn('prime', data)
    
    def test_reconstruct_sum_insufficient_parties(self):
        """Test reconstruction with insufficient parties"""
        self.controller.party_sums = {1: 100}  # Only one party
        
        with self.assertRaises(ValueError):
            self.controller.reconstruct_sum()
    
    @patch.object(SMPCController, 'reconstruct_final_result')
    def test_reconstruct_sum_success(self, mock_reconstruct):
        """Test successful sum reconstruction"""
        mock_reconstruct.return_value = 42
        
        self.controller.party_sums = {1: 100, 2: 200, 3: 300}
        
        result = self.controller.reconstruct_sum()
        
        self.assertEqual(result, 42)
        mock_reconstruct.assert_called_once()


class TestIntegrationMocked(unittest.TestCase):
    """Integration tests using mocked network communication"""
    
    @patch('smpc_controller_tcp.time.sleep')
    @patch.object(SMPCControllerTCP, 'send_data')
    @patch.object(SMPCControllerTCP, 'start_listener')
    def test_full_computation_flow(self, mock_start_listener, mock_send_data, mock_sleep):
        """Test the complete computation flow with mocked network"""
        controller = SMPCControllerTCP(num_parties=3, threshold=2)
        
        # Track when distribution happens so we can send responses after
        original_distribute = controller.distribute_shares
        distribution_done = threading.Event()
        
        def mock_distribute_shares(secrets):
            original_distribute(secrets)
            distribution_done.set()
        
        controller.distribute_shares = mock_distribute_shares
        
        # Mock the party responses - send them after distribution is complete
        def simulate_party_responses():
            distribution_done.wait(timeout=5)  # Wait for distribution to complete
            time.sleep(0.1)  # Small delay to ensure controller is waiting
            controller.handle_incoming({'party_id': 1, 'sum': 150})
            controller.handle_incoming({'party_id': 2, 'sum': 250})
        
        # Start simulation in background
        response_thread = threading.Thread(target=simulate_party_responses)
        response_thread.start()
        
        # Run the computation
        secrets = [50, 100, 150]
        result = controller.run(secrets)
        
        response_thread.join()
        
        # Verify that distribution was called
        mock_send_data.assert_called()
        self.assertEqual(mock_send_data.call_count, 3)  # Should send to 3 parties
        
        # Verify listener was started
        mock_start_listener.assert_called_once()
        
        # Result should be computed (exact value depends on the reconstruction logic)
        self.assertIsInstance(result, int)


class TestRealNetworkIntegration(unittest.TestCase):
    """Real network integration tests (optional, may be slow)"""
    
    def setUp(self):
        """Check if ports are available for testing"""
        self.ports_available = True
        test_ports = [9001, 8004, 8005, 8006]  # Use different ports to avoid conflicts
        
        for port in test_ports:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('localhost', port))
            except OSError:
                self.ports_available = False
                break
    
    @unittest.skipUnless(RUN_NETWORK_TESTS, "Skipping real network tests unless RUN_NETWORK_TESTS is set")
    def test_real_network_communication(self):
        """Test actual network communication between components"""
        if not self.ports_available:
            self.skipTest("Required ports not available")
        
        # Create a simple test server
        received_messages = []
        
        def test_server():
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    s.bind(('localhost', 9001))
                    s.listen(1)
                    s.settimeout(5.0)
                    
                    conn, _ = s.accept()
                    with conn:
                        data = b""
                        while True:
                            chunk = conn.recv(4096)
                            if not chunk:
                                break
                            data += chunk
                        import pickle
                        obj = pickle.loads(data)
                        received_messages.append(obj)
            except Exception as e:
                print(f"Test server error: {e}")
        
        server_thread = threading.Thread(target=test_server)
        server_thread.start()
        time.sleep(0.2)  # Let server start
        
        # Send test message
        test_message = {'test': 'real_network', 'value': 123}
        send_data('localhost', 9001, test_message)
        
        server_thread.join(timeout=6)
        
        self.assertEqual(len(received_messages), 1)
        self.assertEqual(received_messages[0], test_message)


def run_system_validation():
    """
    Run a basic system validation to check if all components can be imported
    and basic functionality works
    """
    print("Running system validation...")
    
    try:
        # Test basic imports
        print("✓ All modules imported successfully")
        
        # Test party creation
        party = Party(1)
        print(f"✓ Party created: {party.get_name()}")
        
        # Test share creation
        share = Share(value=123, party_id=1, secret_idx=1)
        print(f"✓ Share created: {share}")
        
        # Test controller creation
        controller = SMPCController(num_parties=3, threshold=2)
        print("✓ SMPC Controller created")
        
        # Test TCP controller creation
        tcp_controller = SMPCControllerTCP(num_parties=3, threshold=2)
        print("✓ TCP Controller created")
        
        # Test party server creation
        party_server = PartyServer(party_id=1)
        print(f"✓ Party Server created: {party_server.get_name()}")
        
        print("\n✅ System validation completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ System validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("SMPC System Test Suite")
    print("=" * 50)
    
    # First run system validation
    if not run_system_validation():
        print("System validation failed. Cannot proceed with tests.")
        sys.exit(1)
    
    print("\nRunning unit tests...")
    print("-" * 30)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestCommLayer,
        TestPartyServer, 
        TestSMPCControllerTCP,
        TestIntegrationMocked,
        TestRealNetworkIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"  {test}: {traceback}")
    
    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"  {test}: {traceback}")
    
    if result.wasSuccessful():
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed!")
    
    print("\nNOTE: To not run network integration tests, set const at top of tests:")
    print("RUN_NETWORK_TESTS=False")