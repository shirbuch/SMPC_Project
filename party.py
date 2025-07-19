
from dataclasses import dataclass, field
from typing import List, Dict

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
    """Represents a party in the SMPC protocol."""
    id: int
    name: str
    shares: Dict[str, List[Share]] = field(default_factory=dict)
    local_sum_shares: Dict[str, Share] = field(default_factory=dict)

    def receive_shares(self, computation_id: str, shares: List[Share]):
        self.shares[computation_id] = shares

    def compute_and_store_local_sum(self, computation_id: str, prime: int):
        if computation_id not in self.shares:
            raise ValueError(f"{self.name} missing shares for '{computation_id}'")
        total = sum(share.value for share in self.shares[computation_id]) % prime
        letter = chr(64 + self.id)  # 1 → A, 2 → B, ...
        share = Share(name=f"sum_{letter}", value=total, party_id=self.id)
        self.local_sum_shares[computation_id] = share
