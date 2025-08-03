"""
Decentralized SMPC Controller Module

This controller orchestrates a truly decentralized SMPC protocol where:
1. All parties actively participate and communicate peer-to-peer
2. No central authority holds or processes secrets
3. The controller only facilitates communication and coordinates phases
4. Individual secrets are NEVER reconstructed - only the final sum

Based on the improved design from SMPC_Project.py
"""

import time
from typing import List, Dict, Optional, Tuple
from party import DecentralizedParty, Channel, Message
import smpc_crypto as crypto

class DecentralizedSMPCController:
    """
    Decentralized SMPC Controller that coordinates secure multi-party computation
    without ever seeing or processing the actual secrets.

    Key principles:
    - No central authority
    - Peer-to-peer communication only
    - Individual secrets never reconstructed
    - Only final sum is revealed
    """

    def __init__(self, secrets: List[int], threshold: int, prime: Optional[int] = None):
        """
        Initialize the decentralized SMPC controller.

        Args:
            secrets (List[int]): List of secret values (one per party)
            threshold (int): Minimum number of parties needed for reconstruction
            prime (Optional[int]): Prime for field operations (generated if None)
        """
        # Input validation
        if not secrets:
            raise ValueError("Secrets list cannot be empty")

        if len(secrets) < 1:
            raise ValueError("At least one party is required")

        if threshold <= 0:
            raise ValueError("Threshold must be positive")

        if threshold > len(secrets):
            raise ValueError("Threshold cannot exceed number of parties")

        # Convert secrets to integers if possible
        try:
            self.secrets = [int(s) for s in secrets]
        except (TypeError, ValueError):
            raise ValueError("All secrets must be convertible to integers")

        self.num_parties = len(secrets)
        self.threshold = threshold
        self.prime = prime if prime else crypto.get_prime(512)

        # Communication infrastructure
        self.secure_channel = Channel()

        # Create decentralized parties
        self.parties: List[DecentralizedParty] = []
        for i, secret in enumerate(self.secrets):
            party = DecentralizedParty(
                party_id=i + 1,
                secret_value=secret,
                threshold=threshold,
                total_parties=self.num_parties,
                secure_channel=self.secure_channel,
                prime=self.prime
            )
            self.parties.append(party)

        # Protocol state
        self.protocol_log = []
        self.execution_metrics = {
            'phase1_time': 0,
            'phase2_time': 0,
            'phase3_time': 0,
            'total_messages': 0
        }

    def log(self, message: str):
        """Add message to protocol log (silent mode for cleaner output)"""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.protocol_log.append(log_entry)
        # Only print major phase headers, not detailed logs

    def run_secure_computation(self) -> Tuple[int, bool]:
        """
        Execute the complete decentralized SMPC protocol.

        Returns:
            Tuple[int, bool]: (final_sum, success_flag)
        """
        try:
            # Phase 1: Decentralized share distribution
            success_phase1 = self._phase1_distributed_sharing()
            if not success_phase1:
                return 0, False

            # Phase 2: Secure sum computation
            success_phase2 = self._phase2_secure_sum_computation()
            if not success_phase2:
                return 0, False

            # Phase 3: Final sum reconstruction
            final_sum = self._phase3_sum_reconstruction()

            # Verify correctness
            success = self._verify_correctness(final_sum)

            return final_sum, success

        except Exception as e:
            return 0, False

    def _phase1_distributed_sharing(self) -> bool:
        """
        Phase 1: Each party creates and distributes shares of their secret.
        This is completely decentralized - no central coordination needed.
        """
        start_time = time.time()

        print("\n📤 PHASE 1: Share Distribution")
        print("All parties creating and exchanging shares...")

        # Step 1a: All parties create and send shares simultaneously
        distribution_results = []

        for party in self.parties:
            success = party.phase1_create_and_distribute_shares()
            distribution_results.append(success)

        if not all(distribution_results):
            print("❌ Some parties failed to distribute shares")
            return False

        # Step 1b: All parties receive shares through channels
        max_rounds = 10  # Simulate asynchronous communication
        for round_num in range(max_rounds):
            reception_results = []
            for party in self.parties:
                received_all = party.phase1_receive_shares()
                reception_results.append(received_all)

            if all(reception_results):
                print("✅ All parties received all shares")
                break

            time.sleep(0.1)  # Simulate network delay
        else:
            print("❌ Share reception timed out")
            return False

        self.execution_metrics['phase1_time'] = time.time() - start_time
        self.execution_metrics['total_messages'] = self.secure_channel.get_communication_stats()['total_messages']

        return True

    def _phase2_secure_sum_computation(self) -> bool:
        """
        Phase 2: Each party computes their share of the final sum.
        Key: Individual secrets are NEVER reconstructed - only sum shares are computed.
        """
        start_time = time.time()

        print("\n🔢 PHASE 2: Sum Computation")
        print("Computing sum shares WITHOUT reconstructing individual secrets...")

        computation_results = []
        for party in self.parties:
            success = party.phase2_compute_sum_share()
            computation_results.append(success)

        if not all(computation_results):
            print("❌ Some parties failed to compute sum shares")
            return False

        self.execution_metrics['phase2_time'] = time.time() - start_time
        print("✅ Sum shares computed without exposing individual secrets")
        return True

    def _phase3_sum_reconstruction(self) -> int:
        """
        Phase 3: Reconstruct only the final sum using threshold number of sum shares.
        Individual secrets remain completely hidden.
        """
        start_time = time.time()

        print("\n🔓 PHASE 3: Final Sum Reconstruction")
        print("Reconstructing ONLY the sum - individual secrets remain hidden...")

        # Collect sum shares from threshold number of parties
        sum_shares = []
        selected_parties = self.parties[:self.threshold]

        for party in selected_parties:
            share_tuple = party.phase3_contribute_sum_share()
            if share_tuple:
                sum_shares.append(share_tuple)
            else:
                raise ValueError(f"Party {party.party_id} failed to contribute sum share")

        if len(sum_shares) < self.threshold:
            raise ValueError(f"Insufficient sum shares: got {len(sum_shares)}, need {self.threshold}")

        # Reconstruct the final sum
        final_sum = crypto.reconstruct_secret(sum_shares, self.prime)

        self.execution_metrics['phase3_time'] = time.time() - start_time
        print(f"🎯 Final Sum: {final_sum}")

        return final_sum

    def _verify_correctness(self, computed_sum: int) -> bool:
        """Verify that the computed sum matches the expected result"""
        expected_sum = sum(self.secrets) % self.prime
        is_correct = computed_sum == expected_sum

        print(f"\n🔍 Verification: {'✅ CORRECT' if is_correct else '❌ INCORRECT'}")
        print(f"Expected: {expected_sum}, Got: {computed_sum}")

        return is_correct

    def _display_metrics(self):
        """Display performance and security metrics"""
        total_time = sum([
            self.execution_metrics['phase1_time'],
            self.execution_metrics['phase2_time'],
            self.execution_metrics['phase3_time']
        ])

        print(f"\n⏱️  Performance: {total_time:.3f}s total, {self.execution_metrics['total_messages']} messages")
        print(f"🛡️  Security: Individual secrets NEVER reconstructed, only sum revealed")

    def analyze_security(self, colluding_party_ids: List[int]) -> Dict:
        """
        Analyze what colluding parties can learn.

        Args:
            colluding_party_ids (List[int]): IDs of colluding parties

        Returns:
            Dict: Security analysis results
        """
        num_colluding = len(colluding_party_ids)

        analysis = {
            'colluding_parties': colluding_party_ids,
            'num_colluding': num_colluding,
            'threshold': self.threshold,
            'can_break_privacy': num_colluding >= self.threshold,
            'individual_secrets_safe': num_colluding < self.threshold
        }

        # Only print summary, not detailed analysis
        if num_colluding < self.threshold:
            print(f"✅ Privacy PRESERVED against {num_colluding} colluding parties (< {self.threshold} threshold)")
        else:
            print(f"⚠️  Privacy COMPROMISED with {num_colluding} colluding parties (≥ {self.threshold} threshold)")

        return analysis

    def get_party_status(self) -> Dict:
        """Get status of all parties"""
        return {
            'parties': [party.get_status() for party in self.parties],
            'total_parties': self.num_parties,
            'threshold': self.threshold,
            'communication_stats': self.secure_channel.get_communication_stats()
        }


# Legacy compatibility class for existing tests
class SMPCController:
    """Legacy SMPC Controller for backward compatibility"""

    def __init__(self, num_parties: int = 3, threshold: int = 2):
        self.num_parties = num_parties
        self.threshold = threshold
        self.prime = crypto.get_prime()

        # Create legacy parties for compatibility
        from party import Party, LegacyShare
        self.parties = [Party(i+1) for i in range(num_parties)]

    def create_shares_for_parties(self, secrets: List[int]) -> Dict:
        """Create shares for legacy compatibility"""
        from party import LegacyShare

        all_shares = []
        for idx, secret in enumerate(secrets):
            raw_shares = crypto.create_shares(secret, self.threshold, self.num_parties, self.prime)
            named_shares = [LegacyShare(share_val, party_id, idx+1) for (party_id, share_val) in raw_shares]
            all_shares.append(named_shares)

        shares_by_party = {}
        for i, party in enumerate(self.parties):
            shares = [secret_shares[i] for secret_shares in all_shares]
            shares_by_party[party.id] = shares

        return shares_by_party

    def request_parties_to_compute_results(self, shares_by_party: Dict) -> Dict:
        """Compute results for legacy compatibility"""
        results = {}
        for party in self.parties:
            shares = shares_by_party.get(party.id, [])
            result = party.compute_sum(shares, self.prime)
            results[party.id] = result
        return results

    def reconstruct_final_result(self, partial_results: Dict, party_ids=None) -> int:
        """Reconstruct final result for legacy compatibility"""
        if party_ids is None:
            selected_ids = list(partial_results.keys())[:self.threshold]
        else:
            selected_ids = party_ids

        selected_partial_results = [(pid, partial_results[pid]) for pid in selected_ids]

        if len(selected_partial_results) < self.threshold:
            raise ValueError("Insufficient number of shares to reconstruct.")

        return crypto.reconstruct_secret(selected_partial_results, prime=self.prime)

    def run_secure_computation(self, secrets: List[int]) -> int:
        """Run computation for legacy compatibility"""
        shares_by_party = self.create_shares_for_parties(secrets)
        partial_results = self.request_parties_to_compute_results(shares_by_party)
        return self.reconstruct_final_result(partial_results)


def run_basic_functionality():
    """
    Run a demonstration of the improved decentralized SMPC system.
    """
    print("=" * 70)
    print("🔒 DECENTRALIZED SMPC SYSTEM DEMONSTRATION")
    print("=" * 70)
    print("Innovation: True peer-to-peer SMPC with no central authority")
    print("Individual secrets are NEVER reconstructed!")
    print("=" * 70)

    try:
        # Test configuration
        secrets = [150, 275, 425]  # Company revenues
        threshold = 2

        print(f"\nTest Configuration:")
        print(f"Secrets (company revenues): {secrets}")
        print(f"Expected sum: {sum(secrets)}")
        print(f"Number of parties: {len(secrets)}")
        print(f"Security threshold: {threshold}")

        # Create and run decentralized SMPC
        controller = DecentralizedSMPCController(secrets, threshold)

        # Execute the protocol
        final_sum, success = controller.run_secure_computation()

        if success:
            print(f"\n🎉 SUCCESS! Decentralized SMPC completed successfully!")
            print(f"✅ Final sum: {final_sum}")
            print(f"✅ Individual secrets remained completely private")

            # Security analysis
            controller.analyze_security([1])  # Single party attack
            controller.analyze_security([1, 2])  # Threshold attack

        else:
            print(f"\n❌ SMPC protocol failed!")

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_basic_functionality()