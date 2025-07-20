from smpc_controller import SMPCController
from comm_layer import send_data, receive_data
from typing import List, Dict, Tuple
import threading
import time


def short(val: int) -> str:
    s = str(val)
    return s[:5] + "..." if len(s) > 5 else s


class SMPCControllerTCP:
    def __init__(self, num_parties: int = 3, threshold: int = 2):
        self.controller = SMPCController(num_parties=num_parties, threshold=threshold)
        self.party_hosts: List[Tuple[str, int]] = [("localhost", 8000 + i + 1) for i in range(num_parties)]
        self.party_sums: Dict[int, int] = {}

    def start_listener(self):
        thread = threading.Thread(
            target=receive_data,
            args=('0.0.0.0', 9000, self.receive_party_sum),
            daemon=True
        )
        thread.start()

    def distribute_shares(self, secrets: List[int]) -> None:
        print("[Controller] Creating and distributing shares...")
        share_map = self.controller.create_shares_for_parties(secrets)

        for party in self.controller.parties:
            shares = share_map[party.id]
            host, port = self.party_hosts[party.id - 1]
            print(f"[Controller] → {party.get_name()} at {host}:{port}: {[s.name for s in shares]}")
            send_data(host, port, {
                'action': 'compute_sum',
                'shares': shares,                # list of Share objects
                'prime': self.controller.prime   # send prime explicitly
            })

    def receive_party_sum(self, data: dict):
        pid = data['party_id']
        val = data['sum']
        self.party_sums[pid] = val
        print(f"[Controller] Received sum from Party {pid}: {short(val)}")

    def reconstruct_sum(self) -> int:
        if len(self.party_sums) < self.controller.threshold:
            raise ValueError("Not enough party sums to reconstruct")

        selected = sorted(self.party_sums.items())[:self.controller.threshold]
        print("[Controller] Reconstructing final result from:")
        for pid, val in selected:
            print(f"   Party {pid}: {short(val)}")

        return self.controller.reconstruct_final_result(dict(selected))

    def run(self, secrets: List[int]) -> int:
        print("[Controller] Starting secure computation")
        self.party_sums.clear()
        self.start_listener()

        self.distribute_shares(secrets)
        time.sleep(1)  # allow parties to receive and compute

        print("[Controller] Waiting for results...")
        while len(self.party_sums) < self.controller.threshold:
            time.sleep(0.2)

        result = self.reconstruct_sum()
        expected = sum(secrets) % self.controller.prime
        print(f"[Controller] Final Result: {result}")
        print(f"[Controller] Expected    : {expected}")
        print("MATCH" if result == expected else "MISMATCH")
        return result
