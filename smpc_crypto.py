"""
Stateless Cryptographic Library for SMPC using Shamir's Secret Sharing
"""

import random
from typing import List, Optional, Tuple
from Crypto.Util import number

DEFAULT_PRIME = number.getPrime(256)


def get_prime() -> int:
    """Return a default 256-bit prime for field operations."""
    return DEFAULT_PRIME


def _evaluate_polynomial(coefficients: List[int], x: int, prime: int) -> int:
    """Evaluate a polynomial at point x using Horner's method (mod prime)."""
    result = 0
    for coeff in reversed(coefficients):
        result = (result * x + coeff) % prime
    return result


def _lagrange_interpolation(points: List[Tuple[int, int]], x: int = 0, prime: int = DEFAULT_PRIME) -> int:
    """Reconstruct secret using Lagrange interpolation."""
    result = 0
    n = len(points)

    for i in range(n):
        xi, yi = points[i]
        term = yi
        for j in range(n):
            if i != j:
                xj, _ = points[j]
                numerator = (x - xj) % prime
                denominator = (xi - xj) % prime
                inv_denominator = pow(denominator, prime - 2, prime)
                term = (term * numerator * inv_denominator) % prime
        result = (result + term) % prime

    return result


def create_shares(secret: int, threshold: int, num_shares: int, prime: Optional[int] = None) -> List[Tuple[int, int]]:
    """Split secret into shares using Shamir's scheme."""
    prime = prime or DEFAULT_PRIME
    if threshold > num_shares:
        raise ValueError("Threshold cannot be greater than number of shares")
    if threshold < 1 or num_shares < 1:
        raise ValueError("Threshold and num_shares must be positive")

    secret = secret % prime
    coefficients = [secret] + [random.randint(1, prime - 1) for _ in range(threshold - 1)]
    return [(i, _evaluate_polynomial(coefficients, i, prime)) for i in range(1, num_shares + 1)]


def reconstruct_secret(shares: List[Tuple[int, int]], prime: Optional[int] = None) -> int:
    """Reconstruct the secret from shares."""
    if len(shares) < 2:
        raise ValueError("At least 2 shares required for reconstruction")
    return _lagrange_interpolation(shares, prime=prime or DEFAULT_PRIME)


def add_shares(shares1: List[Tuple[int, int]], shares2: List[Tuple[int, int]], prime: Optional[int] = None) -> List[Tuple[int, int]]:
    """Add two share sets homomorphically."""
    if len(shares1) != len(shares2):
        raise ValueError("Share sets must have same length")
    prime = prime or DEFAULT_PRIME

    result = []
    for (id1, val1), (id2, val2) in zip(shares1, shares2):
        if id1 != id2:
            raise ValueError(f"Party ID mismatch: {id1} != {id2}")
        result.append((id1, (val1 + val2) % prime))

    return result
