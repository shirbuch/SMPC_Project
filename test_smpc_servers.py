#!/usr/bin/env python3
"""
Comprehensive test suite for the SMPC (Secure Multi-Party Computation) system.
Tests cover the party server, TCP-based controller, communication flow, and both
mocked and real network integration scenarios.

This suite ensures correctness of server behavior, share distribution,
result aggregation, and interaction between distributed SMPC components.
"""

import unittest
import threading
import time
import socket
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from comm_layer import BaseServer
    from party_server import PartyServer
    from smpc_controller_server import SMPCControllerServer
    from party import Party, Share
    from smpc_controller import SMPCController
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure all required files are in the same directory as this test file.")
    sys.exit(1)


class TestPartyServer(unittest.TestCase):
    """
    Unit tests for the PartyServer class, verifying initialization,
    handling of valid and invalid incoming actions, and integration
    with share computation and messaging.
    """
    
    def setUp(self):
        """
        Initialize a PartyServer instance with party_id=1 before each test.
        """
        self.party_server = PartyServer(party_id=1)
    
    def test_party_server_initialization(self):
        """
        Test that PartyServer initializes its attributes correctly.

        Asserts:
            - ID, host, port, and name are correctly set.
        """
        self.assertEqual(self.party_server.id, 1)
        self.assertEqual(self.party_server.host, '0.0.0.0')
        self.assertEqual(self.party_server.port, 8001)
        self.assertIn("Party_A", self.party_server.name)
    
    @patch.object(PartyServer, 'send_data')
    @patch.object(PartyServer, 'compute_sum')
    @patch.object(PartyServer, 'unpack_compute_sum_request')
    def test_handle_incoming_compute_sum(self, mock_unpack, mock_compute, mock_send):
        """
        Test PartyServer's ability to handle the 'compute_sum' action.

        Mocks:
            - Share unpacking
            - Local computation
            - Response transmission

        Asserts:
            - That each mocked method is called with expected arguments.
        """
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
        """
        Verify that PartyServer does not crash when receiving an unknown action.

        Asserts:
            - No exception is raised during execution.
        """
        test_data = {'action': 'unknown_action'}
        
        # Should not raise an exception
        try:
            self.party_server.handle_incoming(test_data)
        except Exception as e:
            self.fail(f"handle_incoming raised an exception for unknown action: {e}")


class MockPartyServer:
    """
    Mock implementation of a party server for testing purposes
    without actual network or computation logic.
    """
    
    def __init__(self, party_id: int):
        """
        Initialize the mock server with a given party ID.

        Args:
            party_id (int): Unique identifier for the party.
        """
        self.party_id = party_id
        self.received_data = []
    
    def receive_data(self, data):
        """
        Simulate receiving data and computing a fixed result
        when the action is 'compute_sum'.

        Args:
            data (dict): Incoming data dictionary.

        Returns:
            dict: Mock computation result with party_id and fixed sum.
        """
        self.received_data.append(data)
        # Simulate computation and return result
        if data.get('action') == 'compute_sum':
            # Mock computation result
            return {
                'party_id': self.party_id,
                'sum': 100 + self.party_id  # Simple mock result
            }


class TestSMPCControllerTCP(unittest.TestCase):
    """
    Unit tests for the SMPCControllerServer class.
    Covers initialization, share distribution, result aggregation,
    and input validation.
    """
    
    def setUp(self):
        """
        Initialize an SMPCControllerServer with 3 parties and threshold=2.
        """
        self.controller = SMPCControllerServer(num_parties=3, threshold=2)
    
    def test_controller_initialization(self):
        """
        Verify that the controller initializes all expected attributes correctly.
        """
        self.assertEqual(self.controller.host, '0.0.0.0')
        self.assertEqual(self.controller.port, 9000)
        self.assertEqual(len(self.controller.party_hosts), 3)
        self.assertEqual(self.controller.controller.num_parties, 3)
        self.assertEqual(self.controller.controller.threshold, 2)
    
    def test_handle_incoming(self):
        """
        Test correct storage of valid party result upon receiving it.

        Asserts:
            - party_id is stored with the expected sum.
        """
        test_data = {
            'party_id': 1,
            'sum': 12345
        }
        
        self.controller.handle_incoming(test_data)
        
        self.assertIn(1, self.controller.party_sums)
        self.assertEqual(self.controller.party_sums[1], 12345)
    
    def test_handle_incoming_invalid_data(self):
        """
        Ensure controller does not crash on invalid input data and no results are stored.
        """
        invalid_data = {'invalid': 'data'}
        
        # Should not raise an exception
        try:
            self.controller.handle_incoming(invalid_data)
        except Exception as e:
            self.fail(f"handle_incoming raised an exception for invalid data: {e}")
        
        # Should not add anything to party_sums
        self.assertEqual(len(self.controller.party_sums), 0)
    
    @patch.object(SMPCControllerServer, 'send_data')
    def test_distribute_shares(self, mock_send):
        """
        Test whether controller correctly sends shares to all expected parties.

        Args:
            mock_send (Mock): Patched send_data method.

        Asserts:
            - Correct number of sends
            - Valid structure of each message (action, shares, prime)
        """
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
        """
        Ensure that attempting to reconstruct with insufficient party results
        raises a ValueError.

        Raises:
            ValueError: If fewer than `threshold` parties are present.
        """
        self.controller.party_sums = {1: 100}
        with self.assertRaises(ValueError):
            self.controller.reconstruct_final_result()
    
    @patch.object(SMPCController, 'reconstruct_final_result')
    def test_reconstruct_sum_success(self, mock_reconstruct):
        """
        Verify successful sum reconstruction using mock reconstruction logic.

        Args:
            mock_reconstruct (Mock): Patched reconstruct_final_result method.

        Asserts:
            - Returned result matches mock
            - Reconstruction method is called once
        """
        mock_reconstruct.return_value = 42
        self.controller.party_sums = {1: 100, 2: 200, 3: 300}
        
        result = self.controller.reconstruct_final_result()
        
        self.assertEqual(result, 42)
        mock_reconstruct.assert_called_once()


class TestIntegrationMocked(unittest.TestCase):
    """
    Integration-level tests for the SMPC system using mocks to simulate
    network behavior and computation responses from parties.
    """
    
    @patch('smpc_controller_server.time.sleep')
    @patch.object(SMPCControllerServer, 'send_data')
    @patch.object(SMPCControllerServer, 'start_listener')
    def test_full_computation_flow(self, mock_start_listener, mock_send_data, mock_sleep):
        """
        Simulates full end-to-end computation flow using mocked network and responses.

        Steps:
            - Controller distributes shares
            - Mocked parties send results after a delay
            - Controller reconstructs result

        Asserts:
            - Share distribution occurred
            - Listener was activated
            - Final result is an integer
        """
        controller = SMPCControllerServer(num_parties=3, threshold=2)
        
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
    """
    Integration test scaffold to verify availability of real network ports.
    Can be used as a base for future full-stack tests.
    """
    
    def setUp(self):
        """
        Verify that predefined ports (9001, 8004–8006) are available before running tests.

        Sets:
            self.ports_available (bool): Whether test can proceed.
        """
        self.ports_available = True
        test_ports = [9001, 8004, 8005, 8006]  # Use different ports to avoid conflicts
        
        for port in test_ports:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('localhost', port))
            except OSError:
                self.ports_available = False
                break


def run_system_validation():
    """
    Performs a series of basic validations to ensure system components
    can be created and interact without runtime errors.

    Returns:
        bool: True if all validations passed, False if any component fails.

    Prints:
        Step-by-step validation progress and success/failure status.
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
        tcp_controller = SMPCControllerServer(num_parties=3, threshold=2)
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
