# smpc_system_tcp.py
from smpc_system import SMPCSystem
from comm_layer import send_data, receive_data
from typing import List, Dict, Tuple
import threading
import time

def _short(val: int) -> str:
    s = str(val)
    return s[:5] + "..." if len(s) > 5 else s

class SMPCSystemTCP:
    def __init__(self, num_parties: int = 3, threshold: int = 2):
        self.smpc = SMPCSystem(num_parties=num_parties, threshold=threshold)
        self.party_hosts: List[Tuple[str, int]] = [("localhost", 8000 + i + 1) for i in range(num_parties)]
        self.party_sums: Dict[int, int] = {}
        self.computation_id = "default"

    def start_listener(self):
        thread = threading.Thread(target=receive_data, args=('0.0.0.0', 9000, self.receive_party_sum), daemon=True)
        thread.start()

    def distribute_shares(self, values: List[int], computation_id: str = "default") -> None:
        print(f"[SMPC Controller] Creating shares using core logic...")
        success = self.smpc.submit_secret_values(values, computation_id)
        if not success:
            raise RuntimeError("Failed to submit secret values")

        for party, (host, port) in zip(self.smpc.parties, self.party_hosts):
            shares = party.shares[computation_id]
            serialized = [(share.name, share.value) for share in shares]
            print(f"[SMPC Controller] Sending to {party.name} at {host}:{port}: {[s[0] for s in serialized]}")
            send_data(host, port, {
                'action': 'store_shares',
                'computation_id': computation_id,
                'shares': serialized
            })

    def trigger_local_sums(self, computation_id: str = "default") -> None:
        for i, (host, port) in enumerate(self.party_hosts):
            print(f"[SMPC Controller] Triggering local sum at Party {i+1} ({host}:{port})")
            send_data(host, port, {
                'action': 'compute_sum',
                'computation_id': computation_id
            })

    def receive_party_sum(self, data):
        pid = data['party_id']
        comp_id = data['computation_id']
        if comp_id != self.computation_id:
            return
        self.party_sums[pid] = data['sum']
        print(f"[SMPC Controller] Received sum from Party {pid}: {_short(data['sum'])}")

    def reconstruct_sum(self):
        if len(self.party_sums) < self.smpc.threshold:
            raise ValueError("Not enough party sums to reconstruct")
        shares = [(pid, val) for pid, val in sorted(self.party_sums.items())[:self.smpc.threshold]]
        print("[SMPC Controller] Reconstructing using shares:")
        for pid, val in shares:
            print(f"   Party {pid}: {_short(val)}")
        return self.smpc.crypto.reconstruct_secret(shares)

    def run(self, values: List[int], computation_id: str = "default") -> int:
        print("[SMPC Controller] Starting computation")
        self.computation_id = computation_id
        self.party_sums.clear()
        self.start_listener()

        self.distribute_shares(values, computation_id)
        time.sleep(1)
        self.trigger_local_sums(computation_id)

        print("[SMPC Controller] Waiting for results...")
        while len(self.party_sums) < self.smpc.threshold:
            time.sleep(0.2)

        final_sum = self.reconstruct_sum()
        expected = sum(values) % self.smpc.crypto.get_prime()
        print(f"[SMPC Controller] Final result: {_short(final_sum)}")
        print(f"[SMPC Controller] Expected result: {_short(expected)}")
        print("✅ SUCCESS" if final_sum == expected else "❌ MISMATCH")
        return final_sum
