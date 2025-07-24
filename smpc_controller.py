"""
SMPC Controller Module

Defines the `SMPCController` class responsible for coordinating secret sharing,
local computation delegation, and secure reconstruction using Shamir's Secret Sharing.
Also includes a `run_basic_functionality` diagnostic function.
"""

from typing import List, Dict, Optional
from party import Party, Share
import smpc_crypto as crypto


class SMPCController:
    """
    Secure Multi-Party Computation Controller using Shamir's Secret Sharing.

    Responsibilities:
    - Generate shares for secrets
    - Distribute shares to parties
    - Collect local computation results
    - Reconstruct the final result
    """

    def __init__(self, num_parties: int = 3, threshold: int = 2):
        """
        Initialize controller with parties and threshold.

        Args:
            num_parties (int): Total number of parties.
            threshold (int): Minimum number of parties required to reconstruct.

        Raises:
            ValueError: If threshold > num_parties
        """
        if threshold > num_parties:
            raise ValueError("Threshold cannot exceed number of parties")

        self.num_parties = num_parties
        self.threshold = threshold
        self.prime = crypto.get_prime()
        self.parties: List[Party] = [Party(i+1) for i in range(num_parties)]

    def create_shares_for_parties(self, secrets: List[int]) -> Dict[int, List[Share]]:
        """
        Create shares for each secret and assign them to parties.

        Args:
            secrets (List[int]): List of input secrets.

        Returns:
            Dict[int, List[Share]]: Mapping from party ID to list of Share objects.
        """
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
        """
        Request each party to compute the sum of their shares.

        Args:
            shares_by_party (Dict[int, List[Share]]): Share assignments.

        Returns:
            Dict[int, int]: Mapping from party ID to their partial result.
        """
        results = {}
        for party in self.parties:
            shares = shares_by_party.get(party.id, [])
            result = party.compute_sum(shares, self.prime)
            results[party.id] = result
        return results

    def reconstruct_final_result(self, partial_results: Dict[int, int], party_ids: Optional[List[int]] = None) -> int:
        """
        Reconstruct the full result using Lagrange interpolation.

        Args:
            partial_results (Dict[int, int]): Party ID to sum mappings.
            party_ids (Optional[List[int]]): Specific party IDs to use (default: first `threshold`).

        Returns:
            int: Final reconstructed result.

        Raises:
            ValueError: If fewer than threshold results are provided.
        """
        if party_ids is None:
            selected_ids = list(partial_results.keys())[:self.threshold]
        else:
            selected_ids = party_ids

        selected_partial_results = [(pid, partial_results[pid]) for pid in selected_ids]

        if len(selected_partial_results) < self.threshold:
            raise ValueError("Insufficient number of shares to reconstruct.")

        return crypto.reconstruct_secret(selected_partial_results, prime=self.prime)

    def run_secure_computation(self, secrets: List[int]) -> int:
        """
        End-to-end secure computation: share, compute, and reconstruct.

        Args:
            secrets (List[int]): Secrets to compute the sum of.

        Returns:
            int: Final reconstructed secure result.
        """
        shares_by_party = self.create_shares_for_parties(secrets)
        partial_results = self.request_parties_to_compute_results(shares_by_party)
        return self.reconstruct_final_result(partial_results)


def run_basic_functionality():
    """
    Run a sample SMPC computation for debugging or demonstration.
    """
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
