from typing import List, Dict, Optional
from party import Party, Share
import smpc_crypto as crypto
from dataclasses import dataclass


class SMPCController:
    """Secure Multi-Party Computation Controller using Shamir's Secret Sharing."""

    def __init__(self, num_parties: int = 3, threshold: int = 2):
        if threshold > num_parties:
            raise ValueError("Threshold cannot exceed number of parties")

        self.num_parties = num_parties
        self.threshold = threshold
        self.prime = crypto.get_prime()
        self.parties: List[Party] = [
            Party(i+1) for i in range(num_parties)
        ]

    def create_shares_for_parties(self, secrets: List[int]) -> Dict[int, List[Share]]:
        all_shares: List[List[Share]] = []

        # Create named shares for each secret
        for idx, secret in enumerate(secrets):
            raw_shares = crypto.create_shares(secret, self.threshold, self.num_parties, prime=self.prime)
            named = [Share(share_val, party_id, idx+1) for (party_id, share_val) in raw_shares]
            all_shares.append(named)

        # Bundle shares per party
        party_share_map: Dict[int, List[Share]] = {}
        for i, party in enumerate(self.parties):
            shares = [secret_shares[i] for secret_shares in all_shares]
            party_share_map[party.id] = shares

        return party_share_map

    def request_party_sums(self, party_share_map: Dict[int, List[Share]]) -> Dict[int, int]:
        results = {}
        for party in self.parties:
            shares = party_share_map.get(party.id, [])
            result = party.recieve_shares_and_compute_sum(shares, self.prime)
            results[party.id] = result
        return results

    def reconstruct_final_sum(self, partial_sums: Dict[int, int], party_ids: Optional[List[int]] = None) -> int:
        if party_ids is None:
            selected_ids = list(partial_sums.keys())[:self.threshold]
        else:
            selected_ids = party_ids

        selected_shares = [(pid, partial_sums[pid]) for pid in selected_ids]

        if len(selected_shares) < self.threshold:
            raise ValueError("Insufficient number of shares to reconstruct.")

        return crypto.reconstruct_secret(selected_shares, prime=self.prime)

    def run_secure_computation(self, secrets: List[int]) -> int:
        party_share_map = self.create_shares_for_parties(secrets)
        sum_shares = self.request_party_sums(party_share_map)
        return self.reconstruct_final_sum(sum_shares)


def run_basic_functionality():
    print("=" * 50)
    print("======== SMPC System Basic Functionality =========")
    print("=" * 50)

    try:
        secrets = [100, 250, 40]
        expected_sum = sum(secrets)

        smpc = SMPCController(num_parties=3, threshold=2)

        print(f"\nTesting with secrets: {secrets}")
        print(f"   Expected sum: {expected_sum}")

        print("\n1. Creating shares and assigning to parties...")
        share_map = smpc.create_shares_for_parties(secrets)
        print("   Created shares.")

        print("\n2. Share distribution:")
        for party_id, shares in share_map.items():
            names = [s.name for s in shares]
            print(f"   Party {party_id}: {names}")

        print("\n3. Requesting party sums...")
        sum_shares = smpc.request_party_sums(share_map)
        for pid, val in sum_shares.items():
            print(f"   Party {pid}: {str(val)[:5]}...")

        print("\n4. Reconstructing final sum...")
        result = smpc.reconstruct_final_sum(sum_shares)
        print(f"   Final result: {result}")

        if result == expected_sum:
            print("   ✅ SUCCESS: Computation result is correct!")
        else:
            print(f"   ❌ ERROR: Expected {expected_sum}, got {result}")

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_basic_functionality()
