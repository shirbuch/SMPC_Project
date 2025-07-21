import sys
from smpc_controller import SMPCController
from comm_layer import BaseServer
from typing import List, Dict, Tuple
import threading
import time
import socket
from party import Share


class SMPCControllerTCP(BaseServer):
    def __init__(self, num_parties: int = 3, threshold: int = 2):
        super().__init__('0.0.0.0', 9000, "Controller")
        self.controller = SMPCController(num_parties=num_parties, threshold=threshold)
        self.party_hosts: List[Tuple[str, int]] = [("localhost", 8000 + i + 1) for i in range(num_parties)]
        self.party_sums: Dict[int, int] = {}
   
    def distribute_shares(self, secrets: List[int]) -> None:
        print(f"[{self.name}] Creating and distributing shares...")
        share_map = self.controller.create_shares_for_parties(secrets)

        for party in self.controller.parties:
            shares = share_map[party.id]
            host, port = self.party_hosts[party.id - 1]
            print(f"[{self.name}] → {party.get_name()} at {host}:{port}: {[s.name for s in shares]}")
            self.send_data(host, port, {
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

    def reconstruct_sum(self) -> int:
        if len(self.party_sums) < self.controller.threshold:
            raise ValueError("Not enough party sums to reconstruct")

        selected = sorted(self.party_sums.items())[:self.controller.threshold]
        print(f"[{self.name}] Reconstructing final result from:")
        for pid, val in selected:
            print(f"   Party {pid}: {Share.short(val)}")

        return self.controller.reconstruct_final_result(dict(selected))

    def run(self, secrets: List[int]) -> int:
        print(f"[{self.name}] Starting secure computation")
        self.party_sums.clear()
        self.start_listener()

        self.distribute_shares(secrets)
        time.sleep(1)  # allow parties to receive and compute

        print(f"[{self.name}] Waiting for results...")
        try:
            while len(self.party_sums) < self.controller.threshold:
                time.sleep(0.2)
        except KeyboardInterrupt:
            self.signal_handler(None, None)

        result = self.reconstruct_sum()
        expected = sum(secrets) % self.controller.prime
        print(f"[{self.name}] Final Result: {result}")
        print(f"[{self.name}] Expected    : {expected}")
        print("MATCH" if result == expected else "MISMATCH")
        return result


def main():
    """Run TCP-based SMPC computation"""
    secrets = [100, 250, 40]
    controller = SMPCControllerTCP(num_parties=3, threshold=2)
    
    try:
        result = controller.run(secrets)
        print(f"\n✅ Computation completed! Result: {result}")
    except Exception as e:
        print(f"\n❌ Computation failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()