from dataclasses import dataclass
from typing import List, Dict, Tuple

from smpc_crypto import add_shares


class Share:
    """
    Represents a single share assigned to a party.
    Each share belongs to a party and corresponds to a specific secret.
    """
    name: str # e.g. "A_1", "B_2"
    value: int
    party_id: int
    secret_idx: int

    def __init__(self, value: int, party_id: int, secret_idx: int):
        self.name = f"{Party.id_to_letter(party_id)}_{secret_idx}"
        self.value = value
        self.party_id = party_id
        self.secret_idx = secret_idx

    @staticmethod
    def short(val: int) -> str:
        """Return truncated string representation of a value for display."""
        s = str(val)
        return s[:5] + "..." if len(s) > 5 else s

    def __str__(self) -> str:
        return f"{self.name}: {Share.short(self.value)}"


@dataclass
class Party:
    """
    Stateless local party in SMPC system.
    Can receive shares and compute the local computation (mod prime).
    """
    id: int

    def compute_sum(self, shares: List[Share], prime: int) -> int:
        """Compute sum of given shares mod prime."""
        result = add_shares([share.value for share in shares], prime)
        return result

    def get_name(self):
        return f"Party_{Party.id_to_letter(self.id)}"

    @staticmethod
    def id_to_letter(id: int) -> str:
        """Convert party ID (1-indexed) to uppercase letter (1 -> A)."""
        return f"{chr(64 + id)}"
    
    def unpack_compute_sum_request(self, data: dict) -> Tuple[List[Share], int]:
        """Unpack compute_sum request data and validate"""
        raw_shares = data.get('shares', [])
        prime = data.get('prime')
        
        if not isinstance(prime, int):
            raise ValueError("Missing or invalid prime field")
        
        if not isinstance(raw_shares, list) or not all(isinstance(s, Share) for s in raw_shares):
            raise ValueError("Invalid share data received")
        
        return raw_shares, prime
