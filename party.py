from dataclasses import dataclass
from typing import List


@dataclass
class Share:
    """Represents a single share assigned to a party."""
    name: str
    value: int
    party_id: int

    def short(self) -> str:
        s = str(self.value)
        return s[:5] + "..." if len(s) > 5 else s

    def __str__(self) -> str:
        return f"{self.name}: {self.short()}"


@dataclass
class Party:
    """Stateless party: receives shares + prime, returns result."""
    id: int
    name: str

    def recieve_shares_and_compute_sum(self, shares: List[Share], prime: int) -> int:
        """Compute sum of given shares mod prime."""
        total = sum(share.value for share in shares) % prime
        return total
