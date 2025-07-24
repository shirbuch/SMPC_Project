"""
SMPC Controller Server Module

This module defines `SMPCControllerServer`, an interactive TCP-based controller for
Secure Multi-Party Computation using Shamir's Secret Sharing. It distributes shares,
collects results, and reconstructs the final computation securely over a network.
"""

import sys
from smpc_controller import SMPCController
from comm_layer import BaseServer
from typing import List, Dict, Tuple
import threading
import time
import socket
from party import Share


class SMPCControllerServer(BaseServer):
    """
    TCP-enabled controller server for secure distributed computation.

    Extends BaseServer to handle incoming data, manage party connections, and
    coordinate secret sharing, result collection, and reconstruction.
    """

    def __init__(self, num_parties: int = 3, threshold: int = 2):
        """
        Initialize the controller server.

        Args:
            num_parties (int): Number of party nodes.
            threshold (int): Minimum required for reconstruction.
        """
        super().__init__('0.0.0.0', 9000, "Controller")
        self.controller = SMPCController(num_parties=num_parties, threshold=threshold)
        self.party_hosts: List[Tuple[str, int]] = [("localhost", 8000 + i + 1) for i in range(num_parties)]
        self.party_sums: Dict[int, int] = {}

    def send_data_with_retry(self, host: str, port: int, data: dict, retries: int = 20, delay: float = 1.0):
        """
        Attempt to send data repeatedly to a party with retry logic.

        Args:
            host (str): Target host.
            port (int): Target port.
            data (dict): Payload to send.
            retries (int): Max retry attempts.
            delay (float): Delay between attempts (in seconds).
        """
        for attempt in range(1, retries + 1):
            try:
                self.send_data(host, port, data)
                return
            except (ConnectionRefusedError, socket.timeout, OSError):
                print(f"[{self.name}] Party at {host}:{port} not ready, retrying ({attempt}/{retries})...")
                time.sleep(delay)

        # After retries exhausted
        print(f"[{self.name}] ⏳ Party at {host}:{port} still not available.")
        input(f"[{self.name}] Press Enter to keep retrying, or Ctrl+C to abort.")
        self.send_data_with_retry(host, port, data, retries=retries, delay=delay)

    def distribute_shares(self, secrets: List[int]) -> None:
        """
        Generate and send secret shares to each party.

        Args:
            secrets (List[int]): Secret values to share.
        """
        print(f"[{self.name}] Creating and distributing shares...")
        share_map = self.controller.create_shares_for_parties(secrets)

        for party in self.controller.parties:
            shares = share_map[party.id]
            host, port = self.party_hosts[party.id - 1]
            print(f"[{self.name}] → {party.get_name()} at {host}:{port}: {[s.name for s in shares]}")
            self.send_data_with_retry(host, port, {
                'action': 'compute_sum',
                'shares': shares,
                'prime': self.controller.prime
            })

    def handle_incoming(self, data: dict):
        """
        Handle incoming results from parties.

        Args:
            data (dict): Expected to contain 'party_id' and 'sum' fields.
        """
        pid = data.get('party_id')
        val = data.get('sum')
        if pid is None or val is None:
            print(f"[{self.name}] Invalid data received.")
            return
        self.party_sums[pid] = val
        print(f"[{self.name}] Received sum from Party {pid}: {Share.short(val)}")

    def reconstruct_final_result(self) -> int:
        """
        Reconstruct the final sum using received partial sums.

        Returns:
            int: The reconstructed result.

        Raises:
            ValueError: If not enough results are available.
        """
        if len(self.party_sums) < self.controller.threshold:
            raise ValueError("Not enough party sums to reconstruct")

        selected = sorted(self.party_sums.items())[:self.controller.threshold]
        print(f"[{self.name}] Reconstructing final result from:")
        for pid, val in selected:
            print(f"   Party {pid}: {Share.short(val)}")

        result = self.controller.reconstruct_final_result(dict(selected))
        self.party_sums.clear()  # Clear after reconstruction
        return result

    def run(self, secrets: List[int]) -> int:
        """
        Run the full secure computation over TCP.

        Args:
            secrets (List[int]): Secret values to compute securely.

        Returns:
            int: The reconstructed final result.
        """
        print(f"[{self.name}] Starting secure computation")
        self.party_sums.clear()
        self.start_listener()

        self.distribute_shares(secrets)
        print(f"[{self.name}] Waiting for results...")

        try:
            while len(self.party_sums) < self.controller.threshold:
                time.sleep(0.2)
        except KeyboardInterrupt:
            self.signal_handler(None, None)

        result = self.reconstruct_final_result()
        expected = sum(secrets) % self.controller.prime
        print(f"[{self.name}] Final Result: {result}")
        print(f"[{self.name}] Expected    : {expected}")
        print("MATCH" if result == expected else "MISMATCH")
        return result


def main():
    """
    Command-line interface to launch the controller server.
    """
    import argparse
    parser = argparse.ArgumentParser(description="Run SMPC controller server.")
    parser.add_argument("secrets", nargs="+", type=int, help="List of secrets to compute securely.")
    parser.add_argument("-n", "--num_parties", type=int, default=3, help="Number of parties")
    parser.add_argument("-t", "--threshold", type=int, default=2, help="Threshold for reconstruction")
    args = parser.parse_args()

    controller = SMPCControllerServer(num_parties=args.num_parties, threshold=args.threshold)

    try:
        result = controller.run(args.secrets)
        print(f"\n✅ Computation completed! Result: {result}")
    except Exception as e:
        print(f"\n❌ Computation failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
