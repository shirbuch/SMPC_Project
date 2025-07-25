from dataclasses import dataclass
from typing import List, Dict, Tuple

from smpc_crypto import add_shares

class Share:
    """
    Represents a single share assigned to a party.

    Each share:
    - Has a name encoding the party and secret index (e.g., "A_1")
    - Stores its numerical value
    - Is associated with a specific party and secret index
    """
    name: str  # e.g. "A_1", "B_2"
    value: int
    party_id: int
    secret_idx: int

    def __init__(self, value: int, party_id: int, secret_idx: int):
        """
        Initialize a share.

        Args:
            value (int): The numeric value of the share.
            party_id (int): ID of the party that owns this share.
            secret_idx (int): Index of the secret this share corresponds to.
        """
        self.name = f"{Party.id_to_letter(party_id)}_{secret_idx}"
        self.value = value
        self.party_id = party_id
        self.secret_idx = secret_idx

    @staticmethod
    def short(val: int) -> str:
        """
        Return a truncated string representation of a value.

        Args:
            val (int): Value to be shortened.

        Returns:
            str: First 5 digits followed by ellipsis if long, else raw string.
        """
        s = str(val)
        return s[:5] + "..." if len(s) > 5 else s

    def __str__(self) -> str:
        """
        Return a display-friendly representation of the share.

        Returns:
            str: Formatted name and shortened value.
        """
        return f"{self.name}: {Share.short(self.value)}"


@dataclass
class Party:
    """
    Stateless local party in SMPC system.

    Each party:
    - Has a unique ID
    - Can compute a sum of shares modulo a given prime
    - Converts ID to a user-friendly name
    """
    id: int

    def compute_sum(self, shares: List[Share], prime: int) -> int:
        """
        Compute the modular sum of the provided shares.

        Args:
            shares (List[Share]): Shares assigned to this party.
            prime (int): Prime modulus for computation.

        Returns:
            int: Sum of share values modulo prime.
        """
        result = add_shares([share.value for share in shares], prime)
        return result

    def get_name(self) -> str:
        """
        Return the human-readable name of the party (e.g., "Party_A").

        Returns:
            str: Name of the party.
        """
        return f"Party_{Party.id_to_letter(self.id)}"

    @staticmethod
    def id_to_letter(id: int) -> str:
        """
        Convert a party ID (1-indexed) to a corresponding uppercase letter.

        Args:
            id (int): Numeric ID starting at 1.

        Returns:
            str: Corresponding uppercase letter (1 -> A).
        """
        return f"{chr(64 + id)}"

    def unpack_compute_sum_request(self, data: dict) -> Tuple[List[Share], int]:
        """
        Extract shares and prime value from a compute request payload.

        Args:
            data (dict): Incoming compute request with 'shares' and 'prime'.

        Returns:
            Tuple[List[Share], int]: List of Share objects and the prime.

        Raises:
            ValueError: If data is malformed or missing required fields.
        """
        raw_shares = data.get('shares', [])
        prime = data.get('prime')
        
        if not isinstance(prime, int):
            raise ValueError("Missing or invalid prime field")
        
        if not isinstance(raw_shares, list) or not all(isinstance(s, Share) for s in raw_shares):
            raise ValueError("Invalid share data received")
        
        return raw_shares, prime
