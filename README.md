# Secure Multi-Party Computation (SMPC) for Collaborative Data Analysis

A Python implementation of Secure Multi-Party Computation using Shamir's Secret Sharing scheme. This system allows multiple parties to collaboratively compute the sum of their private inputs without revealing individual values to each other.

## 🧪 Testing
Run the quick test to verify everything works:
python quick_test.py

Or run the full demo:
python smpc_system.py

## 🎯 Project Overview

This project demonstrates a practical SMPC implementation where:
- A user submits two secret numbers
- The system splits these secrets into shares distributed among 3 parties
- Each party computes the sum of their shares locally
- The final sum is reconstructed without any party learning the original secrets

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   User Input    │    │   SMPC System    │    │   Crypto Module │
│                 │    │                  │    │                 │
│ • Secret 1      │───▶│ • Share Creation │◄──▶│ • Shamir's SS   │
│ • Secret 2      │    │ • Distribution   │    │ • Reconstruction│
│                 │    │ • Computation    │    │ • Field Ops     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                    ┌─────────────────────────────────┐
                    │           Parties               │
                    │                                 │
                    │  Party 1  │  Party 2  │  Party 3 │
                    │  Share A  │  Share B  │  Share C │
                    │  Share D  │  Share E  │  Share F │
                    └─────────────────────────────────┘
```

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd smpc-collaborative-analysis

# Install dependencies
pip install -r requirements.txt
```

### Basic Usage

```python
from smpc_system import SMPCSystem

# Initialize SMPC system with 3 parties, threshold of 2
smpc = SMPCSystem(num_parties=3, threshold=2)

# Run secure computation
secret1, secret2 = 100, 250
result = smpc.run_secure_computation(secret1, secret2)

print(f"Secure sum: {result}")  # Output: 350
```

### Running the Demo

```bash
python smpc_system.py
```

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Run all tests
python test_smpc.py

# Run with pytest (if installed)
pytest test_smpc.py -v

# Run with coverage
pytest test_smpc.py --cov=. --cov-report=html
```

## 📁 Project Structure

```
smpc-collaborative-analysis/
├── smpc_crypto.py      # Core cryptographic operations
├── smpc_system.py      # Main SMPC system implementation
├── test_smpc.py        # Comprehensive test suite
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## 🔧 Core Components

### SMPCCrypto (`smpc_crypto.py`)
- **Shamir's Secret Sharing**: Split secrets into shares with configurable threshold
- **Lagrange Interpolation**: Reconstruct secrets from sufficient shares
- **Homomorphic Addition**: Add shares without revealing underlying values
- **Finite Field Arithmetic**: Secure operations using large prime fields

### SMPCSystem (`smpc_system.py`)
- **Party Management**: Coordinate multiple parties in computation
- **Share Distribution**: Securely distribute secret shares
- **Secure Computation**: Execute privacy-preserving calculations
- **Result Reconstruction**: Aggregate results without exposing individual inputs

## 🔐 Security Features

- **Information-Theoretic Security**: Perfect secrecy for shares below threshold
- **Threshold Cryptography**: Configurable number of parties required for reconstruction
- **No Trusted Third Party**: Distributed computation without central authority
- **Privacy Preservation**: Individual inputs never revealed to any party

## 📊 Example Workflow

1. **Secret Submission**: User provides two private values (e.g., 100, 250)

2. **Share Creation**: System generates shares using Shamir's Secret Sharing
   ```
   Secret 1 (100) → Shares: (1,a₁), (2,a₂), (3,a₃)
   Secret 2 (250) → Shares: (1,b₁), (2,b₂), (3,b₃)
   ```

3. **Distribution**: Each party receives shares from both secrets
   ```
   Party 1: (1,a₁), (1,b₁)
   Party 2: (2,a₂), (2,b₂)  
   Party 3: (3,a₃), (3,b₃)
   ```

4. **Local Computation**: Each party computes sum of their shares
   ```
   Party 1: sum₁ = a₁ + b₁
   Party 2: sum₂ = a₂ + b₂
   Party 3: sum₃ = a₃ + b₃
   ```

5. **Reconstruction**: Final sum computed from party sums
   ```
   Final Result = Reconstruct(sum₁, sum₂, sum₃) = 350
   ```

## ⚙️ Configuration Options

### System Parameters
- **num_parties**: Number of participating parties (default: 3)
- **threshold**: Minimum shares needed for reconstruction (default: 2)
- **prime_size**: Size of prime field in bits (default: 256)

### Usage Examples

```python
# Different configurations
smpc_5_parties = SMPCSystem(num_parties=5, threshold=3)
smpc_high_security = SMPCSystem(num_parties=7, threshold=4)

# Multiple computations
smpc.run_secure_computation(100, 200, "computation_1")
smpc.run_secure_computation(50, 75, "computation_2")

# Check computation status
status = smpc.get_computation_status("computation_1")
print(f"Status: {status['status']}")
```

## 🎛️ API Reference

### SMPCSystem Methods

- `run_secure_computation(value1, value2, computation_id)`: Complete workflow
- `submit_secret_values(values, computation_id)`: Distribute shares
- `compute_party_sums(computation_id)`: Calculate local sums
- `reconstruct_final_sum(computation_id)`: Rebuild final result
- `get_computation_status(computation_id)`: Check computation state
- `reset_computation(computation_id)`: Clear computation data

### SMPCCrypto Methods

- `create_shares(secret, threshold, num_shares)`: Generate secret shares
- `reconstruct_secret(shares)`: Rebuild secret from shares
- `add_shares(shares1, shares2)`: Homomorphically add share sets

## 🔍 Testing Coverage

The test suite includes:
- **Unit Tests**: Individual component functionality
- **Integration Tests**: End-to-end system behavior
- **Edge Cases**: Boundary conditions and error scenarios
- **Security Tests**: Cryptographic correctness verification
- **Performance Tests**: Different system configurations

## 🚨 Security Considerations

### Threat Model
- **Semi-honest adversaries**: Parties follow protocol but may try to learn secrets
- **Threshold security**: Up to (threshold-1) parties may collude
- **No network security**: Assumes secure communication channels

### Limitations
- **Computational overhead**: Cryptographic operations add latency
- **Fixed operation**: Currently supports only addition
- **Scalability**: Performance decreases with more parties

## 🛠️ Development

### Code Quality
```bash
# Format code
black *.py

# Lint code
flake8 *.py

# Type checking
mypy *.py
```

### Adding New Operations
To support additional operations (multiplication, comparison), extend the `SMPCCrypto` class with appropriate homomorphic operations.

## 📈 Performance Characteristics

- **Share Generation**: O(threshold × num_parties)
- **Reconstruction**: O(threshold²)
- **Memory Usage**: O(num_parties × num_secrets)
- **Communication**: O(num_parties) rounds

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📚 References

- [Shamir's Secret Sharing](https://en.wikipedia.org/wiki/Shamir%27s_Secret_Sharing)
- [Secure Multi-Party Computation](https://en.wikipedia.org/wiki/Secure_multi-party_computation)
- [PyCryptodome Documentation](https://pycryptodome.readthedocs.io/)

## 📄 License

This project is for educational purposes. See individual components for specific licensing terms.

---

**Authors**: Shir Buchner and Roi Even Haim  
**Course**: Secure Multi-Party Computation Implementation  
**Date**: June 2025