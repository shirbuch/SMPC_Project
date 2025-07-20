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

    def start_listener(self):
        thread = threading.Thread(
            target=self.start_server,
            daemon=True
        )
        thread.start()

    def stop_listener(self):
        try:
            # Attempt to close the socket if it's still open
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(('localhost', 9000))
                s.close()
        except Exception as e:
            print(f"[Controller] Error stopping listener: {e}")
        print("[Controller] Listener stopped.")
        
    def distribute_shares(self, secrets: List[int]) -> None:
        print("[Controller] Creating and distributing shares...")
        share_map = self.controller.create_shares_for_parties(secrets)

        for party in self.controller.parties:
            shares = share_map[party.id]
            host, port = self.party_hosts[party.id - 1]
            print(f"[Controller] → {party.get_name()} at {host}:{port}: {[s.name for s in shares]}")
            self.send_data(host, port, {
                'action': 'compute_sum',
                'shares': shares,                # list of Share objects
                'prime': self.controller.prime   # send prime explicitly
            })

    def handle_incoming(self, data: dict):
        pid = data.get('party_id')
        val = data.get('sum')
        if pid is None or val is None:
            print("[Controller] Invalid data received.")
            return
        self.party_sums[pid] = val
        print(f"[Controller] Received sum from Party {pid}: {Share.short(val)}")

    def reconstruct_sum(self) -> int:
        if len(self.party_sums) < self.controller.threshold:
            raise ValueError("Not enough party sums to reconstruct")

        selected = sorted(self.party_sums.items())[:self.controller.threshold]
        print("[Controller] Reconstructing final result from:")
        for pid, val in selected:
            print(f"   Party {pid}: {Share.short(val)}")

        return self.controller.reconstruct_final_result(dict(selected))

    def run(self, secrets: List[int]) -> int:
        print("[Controller] Starting secure computation")
        self.party_sums.clear()
        self.start_listener()

        self.distribute_shares(secrets)
        time.sleep(1)  # allow parties to receive and compute

        print("[Controller] Waiting for results...")
        try:
            while len(self.party_sums) < self.controller.threshold:
                time.sleep(0.2)
        except KeyboardInterrupt:
            self.signal_handler(None, None)

        result = self.reconstruct_sum()
        expected = sum(secrets) % self.controller.prime
        print(f"[Controller] Final Result: {result}")
        print(f"[Controller] Expected    : {expected}")
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