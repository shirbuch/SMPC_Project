import sys
from smpc_controller import SMPCController
from comm_layer import SecureBaseServer as BaseServer
from typing import List, Dict, Tuple
import threading
import time
import socket
from party import Share


class SMPCControllerServer(BaseServer):
    def __init__(self, num_parties: int = 3, threshold: int = 2):
        super().__init__('0.0.0.0', 9000, "Controller")
        self.controller = SMPCController(num_parties=num_parties, threshold=threshold)
        self.party_hosts: List[Tuple[str, int]] = [("localhost", 8000 + i + 1) for i in range(num_parties)]
        self.party_sums: Dict[int, int] = {}

    def send_data_with_retry(self, host: str, port: int, data: dict, retries: int = 20, delay: float = 1.0):
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
        print(f"[{self.name}] Creating and distributing shares...")
        share_map = self.controller.create_shares_for_parties(secrets)

        for party in self.controller.parties:
            shares = share_map[party.id]
            host, port = self.party_hosts[party.id - 1]
            print(f"[{self.name}] → {party.get_name()} at {host}:{port}: {[s.name for s in shares]}")
            self.send_data_with_retry(host, port, {
                'action': 'compute_sum',
                'shares': shares,                # list of Share objects
                'prime': self.controller.prime   # send prime explicitly
            })

    def handle_incoming(self, data: dict):
        pid = data.get('party_id')
        val = data.get('sum')
        if pid is None or val is None:
            print(f"[{self.name}] Invalid data received.")
            return
        self.party_sums[pid] = val
        print(f"[{self.name}] Received sum from Party {pid}: {Share.short(val)}")

    def reconstruct_final_result(self) -> int:
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
