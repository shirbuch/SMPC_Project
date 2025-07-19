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
            named_shares = [Share(share_val, party_id, idx+1) for (party_id, share_val) in raw_shares]
            all_shares.append(named_shares)

        # Bundle shares per party
        shares_by_party: Dict[int, List[Share]] = {}
        for i, party in enumerate(self.parties):
            shares = [secret_shares[i] for secret_shares in all_shares]
            shares_by_party[party.id] = shares

        return shares_by_party

    def request_parties_to_compute_results(self, shares_by_party: Dict[int, List[Share]]) -> Dict[int, int]:
        results = {}
        for party in self.parties:
            shares = shares_by_party.get(party.id, [])
            result = party.compute_sum(shares, self.prime)
            results[party.id] = result
        return results

    def reconstruct_final_result(self, partial_results: Dict[int, int], party_ids: Optional[List[int]] = None) -> int:
        if party_ids is None:
            selected_ids = list(partial_results.keys())[:self.threshold]
        else:
            selected_ids = party_ids

        selected_partial_results = [(pid, partial_results[pid]) for pid in selected_ids]

        if len(selected_partial_results) < self.threshold:
            raise ValueError("Insufficient number of shares to reconstruct.")

        return crypto.reconstruct_secret(selected_partial_results, prime=self.prime)

    def run_secure_computation(self, secrets: List[int]) -> int:
        shares_by_party = self.create_shares_for_parties(secrets)
        partial_results = self.request_parties_to_compute_results(shares_by_party)
        return self.reconstruct_final_result(partial_results)


def run_basic_functionality():
    print("=" * 50)
    print("======== SMPC System Basic Functionality =========")
    print("=" * 50)

    try:
        secrets = [100, 250, 40]
        expected_result = sum(secrets)

        smpc = SMPCController(num_parties=3, threshold=2)

        print(f"\nTesting with secrets: {secrets}")
        print(f"   Expected result: {expected_result}")

        print("\n1. Creating shares and assigning to parties...")
        shares_by_party = smpc.create_shares_for_parties(secrets)
        print("   Created shares.")

        print("\n2. Share distribution:")
        for party_id, shares in shares_by_party.items():
            names = [s.name for s in shares]
            print(f"   Party {party_id}: {names}")

        print("\n3. Requesting party results...")
        partial_results = smpc.request_parties_to_compute_results(shares_by_party)
        for pid, val in partial_results.items():
            print(f"   Party {pid}: {str(val)[:5]}...")

        print("\n4. Reconstructing final result...")
        result = smpc.reconstruct_final_result(partial_results)
        print(f"   Final result: {result}")

        if result == expected_result:
            print("   ✅ SUCCESS: Computation result is correct!")
        else:
            print(f"   ❌ ERROR: Expected {expected_result}, got {result}")

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_basic_functionality()
