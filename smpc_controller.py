from typing import List, Dict, Optional
from party import Party, Share
import smpc_crypto as crypto

class SMPCController:
    """Secure Multi-Party Computation Controller using Shamir's Secret Sharing."""

    def __init__(self, num_parties: int = 3, threshold: int = 2):
        if threshold > num_parties:
            raise ValueError("Threshold cannot exceed number of parties")

        self.num_parties = num_parties
        self.threshold = threshold
        self.prime = crypto.get_prime()
        self.parties: List[Party] = [
            Party(id=i+1, name=f"Party_{i+1}") for i in range(num_parties)
        ]

    def submit_secret_values(self, user_values: List[int], computation_id: str = "default") -> bool:
        if len(user_values) != 2:
            return False

        try:
            party_letters = ['A', 'B', 'C', 'D', 'E']
            all_shares: List[List[Share]] = []

            for idx, secret in enumerate(user_values):
                raw_shares = crypto.create_shares(secret, self.threshold, self.num_parties, prime=self.prime)
                named = [
                    Share(
                        name=f"{idx + 1}_{party_letters[i]}",
                        value=share_val,
                        party_id=party_id
                    )
                    for i, (party_id, share_val) in enumerate(raw_shares)
                ]
                all_shares.append(named)

            for i, party in enumerate(self.parties):
                shares = [all_shares[0][i], all_shares[1][i]]
                party.receive_shares(computation_id, shares)

            return True

        except Exception as e:
            return False

    def compute_party_sums(self, computation_id: str = "default") -> Dict[int, int]:
        results = {}
        for party in self.parties:
            party.compute_and_store_local_sum(computation_id, self.prime)
            share = party.local_sum_shares[computation_id]
            results[party.id] = share.value
        return results

    def reconstruct_final_sum(self, computation_id: str = "default", party_ids: Optional[List[int]] = None) -> int:
        computed_share = []

        if party_ids is None:
            selected_parties = self.parties[:self.threshold]
        else:
            selected_parties = [p for p in self.parties if p.id in party_ids]

        for party in selected_parties:
            share = party.local_sum_shares.get(computation_id)
            if share is None:
                raise ValueError(f"{party.name} missing local sum for '{computation_id}'")
            computed_share.append((party.id, share.value))

        if len(computed_share) < self.threshold:
            raise ValueError(f"Insufficient shares: {len(computed_share)} provided, need {self.threshold}")

        final_sum = crypto.reconstruct_secret(computed_share, prime=self.prime)
        return final_sum

    def run_secure_computation(self, value1: int, value2: int, computation_id: str = "default") -> int:
        if not self.submit_secret_values([value1, value2], computation_id):
            raise RuntimeError("Failed to submit secret values")

        self.compute_party_sums(computation_id)
        result = self.reconstruct_final_sum(computation_id)

        return result

    def get_party_info(self, party_id: int) -> Optional[Party]:
        return next((p for p in self.parties if p.id == party_id), None)

    def reset_computation(self, computation_id: str = "default") -> None:
        for party in self.parties:
            party.shares.pop(computation_id, None)
            party.local_sum_shares.pop(computation_id, None)

def run_basic_functionality():
    print("=" * 50)
    print("======== SMPC System Basic Functionality =========")
    print("=" * 50)

    try:
        secret1, secret2 = 100, 250
        expected_sum = secret1 + secret2

        smpc = SMPCController(num_parties=3, threshold=2)

        print(f"\nTesting with secrets: {secret1}, {secret2}")
        print(f"   Expected sum: {expected_sum}")

        print("\n1. Submitting secrets and creating shares...")
        success = smpc.submit_secret_values([secret1, secret2], "test")
        if not success:
            raise RuntimeError("Failed to submit secrets")
        print("   ✅ Secrets submitted successfully")

        print("\n2. Share distribution:")
        for party in smpc.parties:
            shares = party.shares["test"]
            share_names = [share.name for share in shares]
            print(f"   {party.name}: {share_names}")

        print("\n3. Computing party sums...")
        smpc.compute_party_sums("test")
        print("   ✅ Party sums computed successfully")

        print("\n4. Reconstructing final sum...")
        final_result = smpc.reconstruct_final_sum("test")
        print(f"   Final result: {final_result}")

        if final_result == expected_sum:
            print("   ✅ SUCCESS: Computation result is correct!")
            return True
        else:
            print(f"   ❌ FAILED: Expected {expected_sum}, got {final_result}")
            return False

    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    run_basic_functionality()
