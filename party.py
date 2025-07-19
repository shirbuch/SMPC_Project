from dataclasses import dataclass
from typing import List


class Share:
    """Represents a single share assigned to a party."""
    name: str # e.g. "A_1", "B_2"
    value: int
    party_id: int
    secret_idx: int

    def __init__(self, value: int, party_id: int, secret_idx: int):
        self.name = f"{Party.id_to_name(party_id)}_{secret_idx}"
        self.value = value
        self.party_id = party_id
        self.secret_idx = secret_idx

    def short(self) -> str:
        s = str(self.value)
        return s[:5] + "..." if len(s) > 5 else s

    def __str__(self) -> str:
        return f"{self.name}: {self.short()}"


@dataclass
class Party:
    """Stateless party: receives shares + prime, returns result."""
    id: int

    def recieve_shares_and_compute_sum(self, shares: List[Share], prime: int) -> int:
        """Compute sum of given shares mod prime."""
        total = sum(share.value for share in shares) % prime
        return total

    def get_name(self):
        return Party.id_to_name(self.id)

    @staticmethod
    def id_to_name(id: int) -> str:
        return f"{chr(64 + id)}"  # 1 → A, etc.