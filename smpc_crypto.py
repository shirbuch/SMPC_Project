"""
Stateless Cryptographic Library for SMPC using Shamir's Secret Sharing.

This module provides core primitives for secret sharing and reconstruction
in a finite field, using Shamir's (t,n)-threshold scheme. It also includes
homomorphic addition of shares for secure multi-party computation (SMPC).

Fixed version with improved error handling and better field operations.
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


def _mod_inverse(a: int, m: int) -> int:
    """
    Calculate modular inverse using extended euclidean algorithm.

    Args:
        a (int): Number to find inverse of
        m (int): Modulus

    Returns:
        int: Modular inverse of a mod m

    Raises:
        ValueError: If modular inverse doesn't exist
    """

    def extended_gcd(a, b):
        if a == 0:
            return b, 0, 1
        gcd, x1, y1 = extended_gcd(b % a, a)
        x = y1 - (b // a) * x1
        y = x1
        return gcd, x, y

    if a < 0:
        a = (a % m + m) % m
    gcd, x, _ = extended_gcd(a, m)
    if gcd != 1:
        raise ValueError('Modular inverse does not exist')
    return x % m


def _evaluate_polynomial(coefficients: List[int], x: int, prime: int) -> int:
    """
    Evaluate a polynomial at a given x using Horner's method modulo prime.

    Horner's method reduces the number of modular multiplications,
    which is efficient and numerically stable for secret sharing.

    Args:
        coefficients (List[int]): Coefficients of the polynomial, ordered from a₀ (constant term) to aₙ.
        x (int): Point at which to evaluate the polynomial.
        prime (int): Prime modulus for finite field operations.

    Returns:
        int: Evaluated polynomial value modulo prime.
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
                inv_denominator = _mod_inverse(denominator, prime)
                term = (term * numerator * inv_denominator) % prime
        result = (result + term) % prime

    return result


def create_shares(secret: int, threshold: int, num_shares: int, prime: int) -> List[Tuple[int, int]]:
    """
    Split a secret into multiple shares using Shamir's Secret Sharing scheme.
    The polynomial is randomly generated with uniformly chosen coefficients in Z_p\\{0},
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
    if prime <= 1:
        raise ValueError("Prime must be greater than 1")

    secret = secret % prime  # Normalize into field

    # Generate random coefficients (avoid 0 for non-constant terms)
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
        ValueError: If the number of shares is insufficient for reconstruction.
    """
    if len(shares) < 2:
        raise ValueError("At least 2 shares required for reconstruction")
    return _lagrange_interpolation(shares, prime)


def add_shares(values: List[int], prime: int) -> int:
    """
    Compute the modular sum of share values.

    This function performs homomorphic addition over a finite field.
    In SMPC, parties can add their corresponding shares to compute
    shares of the sum without revealing individual secrets.

    Args:
        values (List[int]): List of individual share values.
        prime (int): The prime modulus defining the finite field.

    Returns:
        int: The result of summing all values modulo prime.

    Example:
        >>> add_shares([123, 456, 789], 104729)
        1368
    """
    return sum(values) % prime


def multiply_share_by_constant(share_value: int, constant: int, prime: int) -> int:
    """
    Multiply a share by a constant (homomorphic scalar multiplication).

    Args:
        share_value (int): The share value to multiply
        constant (int): The constant to multiply by
        prime (int): The prime modulus

    Returns:
        int: The result of multiplying the share by the constant
    """
    return (share_value * constant) % prime


if __name__ == "__main__":
    # Example usage: quick local validation
    secret = 12345
    threshold = 3
    num_shares = 5
    prime = get_prime(512)

    print(f"Original Secret: {secret}")
    print(f"Prime: {prime}")

    shares = create_shares(secret, threshold, num_shares, prime)
    print(f"Generated Shares: {shares}")

    selected = shares[:threshold]
    print(f"Using Shares: {selected}")

    recovered = reconstruct_secret(selected, prime)
    print(f"Recovered Secret: {recovered}")

    # Test homomorphic addition
    secret2 = 67890
    shares2 = create_shares(secret2, threshold, num_shares, prime)

    # Add corresponding shares
    sum_shares = [(x1, add_shares([y1, y2], prime)) for (x1, y1), (x2, y2) in zip(shares, shares2)]

    # Reconstruct sum
    recovered_sum = reconstruct_secret(sum_shares[:threshold], prime)
    expected_sum = (secret + secret2) % prime

    print(f"\nHomomorphic Addition Test:")
    print(f"Secret 1: {secret}")
    print(f"Secret 2: {secret2}")
    print(f"Expected Sum: {expected_sum}")
    print(f"Recovered Sum: {recovered_sum}")
    print(f"Test {'PASSED' if recovered_sum == expected_sum else 'FAILED'}")