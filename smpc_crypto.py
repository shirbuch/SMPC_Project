"""
Stateless Cryptographic Library for SMPC using Shamir's Secret Sharing
"""

import secrets
from typing import List, Optional, Tuple
from Crypto.Util import number

def get_prime(bits: int = 512) -> int:
    """
    Generate a cryptographically secure prime number using OpenSSL (via PyCryptodome).

    Args:
        bits (int): Bit length of the prime. Default is 512.

    Returns:
        int: A cryptographically secure prime number.
    """
    return number.getPrime(bits)

DEFAULT_PRIME = get_prime()


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
                if denominator == 0:
                    raise ValueError("Duplicate x-values in shares detected")
                inv_denominator = pow(denominator, prime - 2, prime)
                term = (term * numerator * inv_denominator) % prime
        result = (result + term) % prime

    return result


def create_shares(secret: int, threshold: int, num_shares: int, prime: Optional[int] = None) -> List[Tuple[int, int]]:
    """
    Split a secret into shares using Shamir's Secret Sharing.

    Args:
        secret (int): The secret to be shared.
        threshold (int): Minimum number of shares needed to reconstruct.
        num_shares (int): Total number of shares to generate.
        prime (Optional[int]): Prime modulus for finite field. Optional.

    Returns:
        List[Tuple[int, int]]: List of (x, y) share points.

    Raises:
        ValueError: If threshold > num_shares or inputs are invalid.
    """
    prime = prime or DEFAULT_PRIME
    if threshold > num_shares:
        raise ValueError("Threshold cannot be greater than number of shares")
    if threshold < 1 or num_shares < 1:
        raise ValueError("Threshold and num_shares must be positive")
    secret = secret % prime  # Normalize into field

    coefficients = [secret] + [secrets.randbelow(prime - 1) + 1 for _ in range(threshold - 1)]
    return [(i, _evaluate_polynomial(coefficients, i, prime)) for i in range(1, num_shares + 1)]


def reconstruct_secret(shares: List[Tuple[int, int]], prime: Optional[int] = None) -> int:
    """
    Reconstruct the secret from a list of shares.

    Args:
        shares (List[Tuple[int, int]]): List of (x, y) share points.
        prime (Optional[int]): Prime modulus for field operations.

    Returns:
        int: The reconstructed secret.

    Raises:
        ValueError: If fewer than 2 shares are provided.
    """
    if len(shares) < 2:
        raise ValueError("At least 2 shares required for reconstruction")
    return _lagrange_interpolation(shares, prime=prime or DEFAULT_PRIME)


def add_shares(values: List[int], prime: int) -> int:
    """
    Compute the modular sum of share values.

    This function performs a simple homomorphic addition over a finite field.
    It is typically used by a party to locally compute the sum of its received shares,
    without revealing individual values.

    Args:
        values (List[int]): List of individual share values held by the party.
        prime (int): The prime modulus defining the finite field.

    Returns:
        int: The result of summing all values modulo prime.

    Example:
        >>> add_shares([123, 456, 789], 104729)
        1368
    """
    result = sum(value for value in values) % prime
    return result

# ----------------------------
# Example Usage (for testing)
# ----------------------------
if __name__ == "__main__":
    secret = 12345
    threshold = 3
    num_shares = 5

    print(f"Original Secret: {secret}")
    shares = create_shares(secret, threshold, num_shares)
    print(f"Generated Shares: {shares}")

    selected = shares[:threshold]
    print(f"Using Shares: {selected}")

    recovered = reconstruct_secret(selected)
    print(f"Recovered Secret: {recovered}")
