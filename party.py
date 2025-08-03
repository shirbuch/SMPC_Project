"""
Decentralized Party Module for Real SMPC

This module implements a truly decentralized party that:
1. Creates and distributes shares of its own secret
2. Receives shares from other parties
3. Computes on shares locally without revealing secrets
4. Participates in secure sum computation

Based on the improved design from SMPC_Project.py
"""

import time
import secrets
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Set
from collections import defaultdict
import threading
import queue

import smpc_crypto as crypto

@dataclass
class SecureMessage:
    """Represents a secure message between parties"""
    sender_id: int
    receiver_id: int
    message_type: str  # 'share_distribution', 'sum_share', etc.
    payload: dict
    timestamp: float = field(default_factory=time.time)
    message_id: str = field(default_factory=lambda: secrets.token_hex(8))

class SecureChannel:
    """Simulates secure point-to-point communication channels between parties"""

    def __init__(self):
        self.message_queues = defaultdict(queue.Queue)  # receiver_id -> queue
        self.message_log = []
        self.total_messages = 0
        self.lock = threading.Lock()

    def send_message(self, message: SecureMessage):
        """Send a message through secure channel"""
        with self.lock:
            self.message_queues[message.receiver_id].put(message)
            self.message_log.append(message)
            self.total_messages += 1

    def receive_messages(self, party_id: int) -> List[SecureMessage]:
        """Receive all pending messages for a party"""
        messages = []
        queue_obj = self.message_queues[party_id]

        while not queue_obj.empty():
            try:
                message = queue_obj.get_nowait()
                messages.append(message)
            except queue.Empty:
                break
        return messages

    def get_communication_stats(self):
        """Get communication statistics"""
        with self.lock:
            return {
                'total_messages': self.total_messages,
                'queues_status': {pid: q.qsize() for pid, q in self.message_queues.items()}
            }

@dataclass
class Share:
    """
    Represents a single share in the SMPC protocol.
    Contains both the share value and metadata about its origin.
    """
    value: int  # The actual share value
    x_coord: int  # X-coordinate in Shamir's scheme (party position)
    secret_owner_id: int  # Which party's secret this is a share of
    share_holder_id: int  # Which party holds this share

    def __str__(self) -> str:
        return f"Share[owner={self.secret_owner_id}, holder={self.share_holder_id}, x={self.x_coord}, value={str(self.value)[:8]}...]"

class DecentralizedParty:
    """
    A truly decentralized party in SMPC that communicates only through secure channels.

    Key features:
    - Creates and distributes shares of its own secret
    - Receives shares from other parties
    - Computes on shares without reconstructing individual secrets
    - Participates in secure sum computation
    """

    def __init__(self, party_id: int, secret_value: int, threshold: int, total_parties: int,
                 secure_channel: SecureChannel, prime: int):
        """
        Initialize a decentralized party.

        Args:
            party_id (int): Unique identifier for this party (1-indexed)
            secret_value (int): This party's private input
            threshold (int): Minimum shares needed for reconstruction
            total_parties (int): Total number of parties in the protocol
            secure_channel (SecureChannel): Communication channel
            prime (int): Prime for field operations
        """
        self.party_id = party_id
        self.secret_value = secret_value % prime  # Normalize to field
        self.threshold = threshold
        self.total_parties = total_parties
        self.secure_channel = secure_channel
        self.prime = prime

        # Protocol state
        self.my_secret_shares: List[Share] = []  # Shares of my secret
        self.received_shares: Dict[int, Share] = {}  # secret_owner_id -> share
        self.sum_share: Optional[Share] = None  # My share of the final sum

        # Status tracking
        self.shares_distributed = False
        self.all_shares_received = False
        self.sum_computed = False

        print(f"Party {self.party_id}: Initialized with secret (hidden)")

    def phase1_create_and_distribute_shares(self) -> bool:
        """
        Phase 1: Create shares of own secret and distribute to all parties.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create shares using Shamir's secret sharing
            raw_shares = crypto.create_shares(
                self.secret_value,
                self.threshold,
                self.total_parties,
                self.prime
            )

            # Convert to Share objects and store
            self.my_secret_shares = []
            for x_coord, share_value in raw_shares:
                share = Share(
                    value=share_value,
                    x_coord=x_coord,
                    secret_owner_id=self.party_id,
                    share_holder_id=x_coord  # x_coord corresponds to party ID
                )
                self.my_secret_shares.append(share)

            # Distribute shares to all parties (including self)
            for share in self.my_secret_shares:
                message = SecureMessage(
                    sender_id=self.party_id,
                    receiver_id=share.share_holder_id,
                    message_type='share_distribution',
                    payload={'share': share}
                )

                self.secure_channel.send_message(message)

            self.shares_distributed = True
            return True

        except Exception as e:
            print(f"Party {self.party_id}: Share distribution failed - {e}")
            return False

    def phase1_receive_shares(self) -> bool:
        """
        Phase 1: Receive shares from other parties.

        Returns:
            bool: True if all shares received, False if still waiting
        """
        # Process incoming messages
        messages = self.secure_channel.receive_messages(self.party_id)

        for message in messages:
            if message.message_type == 'share_distribution':
                share = message.payload['share']

                # Store the share
                self.received_shares[share.secret_owner_id] = share

        # Check if we have shares from all parties
        expected_senders = set(range(1, self.total_parties + 1))
        received_senders = set(self.received_shares.keys())

        if expected_senders == received_senders:
            self.all_shares_received = True
            return True
        else:
            # For single party case, we should have received our own share
            if self.total_parties == 1 and self.party_id in received_senders:
                self.all_shares_received = True
                return True
            return False

    def phase2_compute_sum_share(self) -> bool:
        """
        Phase 2: Compute this party's share of the final sum.

        Key insight: We can compute shares of the sum by adding corresponding shares
        without ever reconstructing individual secrets.

        Returns:
            bool: True if computation successful, False otherwise
        """
        if not self.all_shares_received:
            return False

        try:
            # Sum all the share values (homomorphic addition)
            sum_value = 0
            for secret_owner_id, share in self.received_shares.items():
                sum_value = crypto.add_shares([sum_value, share.value], self.prime)

            # Create sum share
            self.sum_share = Share(
                value=sum_value,
                x_coord=self.party_id,
                secret_owner_id=0,  # 0 indicates this is a sum share
                share_holder_id=self.party_id
            )

            self.sum_computed = True
            return True

        except Exception as e:
            print(f"Party {self.party_id}: Sum computation failed - {e}")
            return False

    def phase3_contribute_sum_share(self) -> Optional[Tuple[int, int]]:
        """
        Phase 3: Contribute this party's sum share for final reconstruction.

        Returns:
            Optional[Tuple[int, int]]: (x_coord, share_value) or None if not ready
        """
        if not self.sum_computed or self.sum_share is None:
            return None

        return (self.sum_share.x_coord, self.sum_share.value)

    def get_status(self) -> Dict:
        """Get current status of this party"""
        return {
            'party_id': self.party_id,
            'shares_distributed': self.shares_distributed,
            'shares_received': len(self.received_shares),
            'expected_shares': self.total_parties,
            'all_shares_received': self.all_shares_received,
            'sum_computed': self.sum_computed,
            'ready_for_reconstruction': self.sum_computed
        }

    def get_name(self) -> str:
        """Get human-readable name for this party"""
        return f"Party_{chr(64 + self.party_id)}"

# Compatibility classes for existing code
class Party:
    """Compatibility wrapper for existing code"""

    def __init__(self, party_id: int):
        self.id = party_id

    def get_name(self) -> str:
        return f"Party_{chr(64 + self.id)}"

    def compute_sum(self, shares: List, prime: int) -> int:
        """Compute sum of share values"""
        return crypto.add_shares([s.value if hasattr(s, 'value') else s for s in shares], prime)

    @staticmethod
    def id_to_letter(party_id: int) -> str:
        return chr(64 + party_id)

# For backward compatibility, keep the old Share class as well
class LegacyShare:
    """Legacy share class for backward compatibility"""

    def __init__(self, value: int, party_id: int, secret_idx: int):
        self.value = value
        self.party_id = party_id
        self.secret_idx = secret_idx
        self.name = f"{Party.id_to_letter(party_id)}_{secret_idx}"

    def __str__(self) -> str:
        return f"{self.name}: {str(self.value)[:5]}..."

    @staticmethod
    def short(val: int) -> str:
        s = str(val)
        return s[:5] + "..." if len(s) > 5 else s

if __name__ == "__main__":
    # Test the decentralized party system
    print("Testing Decentralized SMPC Party System")
    print("=" * 50)

    # Setup
    num_parties = 3
    threshold = 2
    prime = crypto.get_prime(256)  # Smaller prime for testing
    secrets = [100, 200, 300]

    # Create secure channel
    channel = SecureChannel()

    # Create parties
    parties = []
    for i in range(num_parties):
        party = DecentralizedParty(
            party_id=i + 1,
            secret_value=secrets[i],
            threshold=threshold,
            total_parties=num_parties,
            secure_channel=channel,
            prime=prime
        )
        parties.append(party)

    print(f"\nCreated {len(parties)} parties with secrets: {secrets}")
    print(f"Expected sum: {sum(secrets)}")

    # Phase 1: Share distribution and collection
    print("\n--- Phase 1: Share Distribution ---")

    # All parties create and distribute shares
    for party in parties:
        party.phase1_create_and_distribute_shares()

    # All parties receive shares (simulate async communication)
    max_rounds = 5
    for round_num in range(max_rounds):
        print(f"\nCommunication round {round_num + 1}:")
        all_ready = True

        for party in parties:
            if not party.phase1_receive_shares():
                all_ready = False

        if all_ready:
            print("All parties have received all shares!")
            break

    # Phase 2: Sum computation
    print("\n--- Phase 2: Sum Computation ---")
    for party in parties:
        party.phase2_compute_sum_share()

    # Phase 3: Reconstruction
    print("\n--- Phase 3: Final Reconstruction ---")
    sum_shares = []

    for i, party in enumerate(parties):
        if i < threshold:  # Only need threshold parties
            share_tuple = party.phase3_contribute_sum_share()
            if share_tuple:
                sum_shares.append(share_tuple)

    # Reconstruct the final sum
    if len(sum_shares) >= threshold:
        final_sum = crypto.reconstruct_secret(sum_shares, prime)
        expected_sum = sum(secrets) % prime

        print(f"\nFinal Results:")
        print(f"Reconstructed sum: {final_sum}")
        print(f"Expected sum: {expected_sum}")
        print(f"Success: {'YES' if final_sum == expected_sum else 'NO'}")
    else:
        print("Not enough sum shares for reconstruction!")

    # Show communication stats
    stats = channel.get_communication_stats()
    print(f"\nCommunication Statistics:")
    print(f"Total messages: {stats['total_messages']}")