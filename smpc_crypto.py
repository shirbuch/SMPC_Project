"""
Secure Multi-Party Computation (SMPC) Cryptographic Module

This module implements Shamir's Secret Sharing scheme for secure multi-party computation.
It provides functionality to split secrets into shares and reconstruct them securely.
"""

import random
from typing import List, Tuple, Dict
from Crypto.Util import number
from Crypto.Random import get_random_bytes


class SMPCCrypto:
    """
    Secure Multi-Party Computation cryptographic operations using Shamir's Secret Sharing.
    
    This class provides methods to split secrets into shares and reconstruct them,
    enabling secure computation without revealing individual inputs.
    """
    
    def __init__(self, prime: int = None):
        """
        Initialize SMPC crypto with a large prime for finite field operations.
        
        Args:
            prime: Large prime number for finite field. If None, generates a 256-bit prime.
        """
        self.prime = prime or number.getPrime(256)
    
    def _evaluate_polynomial(self, coefficients: List[int], x: int) -> int:
        """
        Evaluate polynomial at point x using Horner's method.
        
        Args:
            coefficients: Polynomial coefficients [a0, a1, a2, ...]
            x: Point to evaluate at
            
        Returns:
            Polynomial value at x modulo prime
        """
        result = 0
        for coeff in reversed(coefficients):
            result = (result * x + coeff) % self.prime
        return result
    
    def _lagrange_interpolation(self, points: List[Tuple[int, int]], x: int = 0) -> int:
        """
        Perform Lagrange interpolation to reconstruct secret at x=0.
        
        Args:
            points: List of (x, y) coordinate tuples
            x: Point to interpolate at (default 0 for secret reconstruction)
            
        Returns:
            Interpolated value at x
        """
        result = 0
        n = len(points)
        
        for i in range(n):
            xi, yi = points[i]
            term = yi
            
            for j in range(n):
                if i != j:
                    xj, _ = points[j]
                    # Compute Lagrange basis polynomial
                    numerator = (x - xj) % self.prime
                    denominator = (xi - xj) % self.prime
                    # Modular inverse
                    inv_denominator = pow(denominator, self.prime - 2, self.prime)
                    term = (term * numerator * inv_denominator) % self.prime
            
            result = (result + term) % self.prime
        
        return result
    
    def create_shares(self, secret: int, threshold: int, num_shares: int) -> List[Tuple[int, int]]:
        """
        Split a secret into shares using Shamir's Secret Sharing.
        
        Args:
            secret: The secret value to split
            threshold: Minimum number of shares needed to reconstruct
            num_shares: Total number of shares to create
            
        Returns:
            List of (party_id, share_value) tuples
            
        Raises:
            ValueError: If threshold > num_shares or invalid parameters
        """
        if threshold > num_shares:
            raise ValueError("Threshold cannot be greater than number of shares")
        if threshold < 1 or num_shares < 1:
            raise ValueError("Threshold and num_shares must be positive")
        
        # Ensure secret is within field
        secret = secret % self.prime
        
        # Generate random coefficients for polynomial of degree (threshold - 1)
        coefficients = [secret]  # a0 = secret
        for _ in range(threshold - 1):
            coefficients.append(random.randint(1, self.prime - 1))
        
        # Generate shares by evaluating polynomial at different points
        shares = []
        for party_id in range(1, num_shares + 1):  # x values from 1 to num_shares
            share_value = self._evaluate_polynomial(coefficients, party_id)
            shares.append((party_id, share_value))
        
        return shares
    
    def reconstruct_secret(self, shares: List[Tuple[int, int]]) -> int:
        """
        Reconstruct secret from shares using Lagrange interpolation.
        
        Args:
            shares: List of (party_id, share_value) tuples
            
        Returns:
            Reconstructed secret value
            
        Raises:
            ValueError: If insufficient shares provided
        """
        if len(shares) < 2:
            raise ValueError("At least 2 shares required for reconstruction")
        
        return self._lagrange_interpolation(shares)
    
    def add_shares(self, shares1: List[Tuple[int, int]], shares2: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """
        Add two sets of shares homomorphically (enables secure addition).
        
        Args:
            shares1: First set of shares
            shares2: Second set of shares
            
        Returns:
            Sum of the two share sets
            
        Raises:
            ValueError: If share sets have different party IDs
        """
        if len(shares1) != len(shares2):
            raise ValueError("Share sets must have same length")
        
        result_shares = []
        for (id1, val1), (id2, val2) in zip(shares1, shares2):
            if id1 != id2:
                raise ValueError(f"Party ID mismatch: {id1} != {id2}")
            
            sum_value = (val1 + val2) % self.prime
            result_shares.append((id1, sum_value))
        
        return result_shares
    
    def get_prime(self) -> int:
        """Get the prime used for finite field operations."""
        return self.prime