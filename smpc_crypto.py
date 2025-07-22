"""
Stateless Cryptographic Library for SMPC using Shamir's Secret Sharing.

This module provides core primitives for secret sharing and reconstruction
in a finite field, using Shamir's (t,n)-threshold scheme. It also includes
homomorphic addition of shares for secure multiparty computation (SMPC).
"""

import secrets
from typing import List, Optional, Tuple
from Crypto.Util import number


def get_prime(bits: int = 512) -> int:
    """
    Generate a prime number suitable for cryptographic use.

    Uses PyCryptodome's `getPrime`, which applies a strong random number generator
    and probabilistic primality testing (e.g., Miller-Rabin) to generate a large prime.

    Args:
        bits (int): Bit length of the prime. Default is 512.

    Returns:
        int: A probable prime number suitable for finite field operations.
    """
    return number.getPrime(bits)


def _evaluate_polynomial(coefficients: List[int], x: int, prime: int) -> int:
    """
    Evaluate a polynomial at a given x using Horner's method modulo prime.

    Horner's method reduces the number of modular multiplications,
    which is efficient and numerically stable for secret sharing.

    Args:
        coefficients (List[int]): Coefficients of the polynomial, ordered from a₀ (constant term) to aₙ.
    """
    result = 0
    for coeff in reversed(coefficients):
        result = (result * x + coeff) % prime
    return result


def _lagrange_interpolation(points: List[Tuple[int, int]], prime: int, x: int = 0) -> int:
    """
    Reconstruct a secret at a given x (default 0) using Lagrange interpolation.
    This implementation works over a prime field ℤ_p using modular inverses.

    Args:
        points (List[Tuple[int, int]]): List of (x, y) share points.
        prime (int): Prime modulus for field operations.
        x (int): The x-coordinate at which to interpolate. Default is 0 (the secret).

    Returns:
        int: The reconstructed secret or interpolated value at x.

    Raises:
        ValueError: If duplicate x-values are found in the shares.
    """
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


def create_shares(secret: int, threshold: int, num_shares: int, prime: int) -> List[Tuple[int, int]]:
    """
    Split a secret into multiple shares using Shamir's Secret Sharing scheme.
    The polynomial is randomly generated with uniformly chosen coefficients in ℤ_p \ {0},
    with the secret as the constant term.

    Note:
        The secret will be reduced modulo `prime` if it exceeds the field size.

    Args:
        secret (int): The secret to be split (must be in range [0, prime)).
        threshold (int): Minimum number of shares required to reconstruct the secret.
        num_shares (int): Total number of shares to generate.
        prime (int): Prime modulus defining the finite field.

    Returns:
        List[Tuple[int, int]]: List of (x, y) points representing the shares.

    Raises:
        ValueError: If threshold > num_shares, or if inputs are invalid.
    """
    if threshold > num_shares:
        raise ValueError("Threshold cannot be greater than number of shares")
    if threshold < 1 or num_shares < 1:
        raise ValueError("Threshold and num_shares must be positive")
    secret = secret % prime  # Normalize into field

    coefficients = [secret] + [secrets.randbelow(prime - 1) + 1 for _ in range(threshold - 1)]
    return [(i, _evaluate_polynomial(coefficients, i, prime)) for i in range(1, num_shares + 1)]


def reconstruct_secret(shares: List[Tuple[int, int]], prime: int) -> int:
    """
    Reconstruct the original secret from a list of shares.

    Args:
        shares (List[Tuple[int, int]]): List of (x, y) share points.
        prime (int): Prime modulus for finite field operations.

    Returns:
        int: The reconstructed secret.

    Raises:
        ValueError: If the number of shares is less than the reconstruction of line.
    """
    if len(shares) < 2:
        raise ValueError("At least 2 shares required for reconstruction")
    return _lagrange_interpolation(shares, prime)


def add_shares(values: List[int], prime: int) -> int:
    """
    Compute the modular sum of share values.

    This function performs a simple homomorphic addition over a finite field.
    It is typically used by a party to locally compute the sum of its received shares,
    without revealing individual values.

    Note:
        This does not reconstruct the final secret. It only adds local share values
        under the field's modulus — a key step in homomorphic addition.

    Args:
        values (List[int]): List of individual share values held by the party.
        prime (int): The prime modulus defining the finite field.

    Returns:
        int: The result of summing all values modulo prime.

    Example:
        >>> add_shares([123, 456, 789], 104729)
        1368
    """
    return sum(values) % prime


# ----------------------------
# Example Usage (for testing)
# ----------------------------
if __name__ == "__main__":
    secret = 12345
    threshold = 3
    num_shares = 5
    prime = get_prime(512)

    print(f"Original Secret: {secret}")
    shares = create_shares(secret, threshold, num_shares, prime)
    print(f"Generated Shares: {shares}")

    selected = shares[:threshold]
    print(f"Using Shares: {selected}")

    recovered = reconstruct_secret(selected, prime)
    print(f"Recovered Secret: {recovered}")
