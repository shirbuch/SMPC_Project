# Secure Multi-Party Computation (SMPC) for Collaborative Data Analysis

A Python implementation of Secure Multi-Party Computation using Shamir's Secret Sharing scheme. This system allows multiple parties to collaboratively compute the sum of their private inputs without revealing individual values to each other.

## Running
Run the parties:
python party_server.py 1
python party_server.py 2
python party_server.py 3

Stop a party:
ctrl + C

Run the controller:
python -c "from smpc_system_tcp import SMPCSystemTCP; smpc=SMPCSystemTCP(); smpc.run([100,250], 'demo')"

## 🧪 Testing
Run the quick test to verify everything works:
python quick_test.py

Run the full demo:
python demo_script.py

Run the quick test to simply see that the system works:
python quick_test.py

Run the full tests to verify everything works:
python test_smpc.py
---

## 🎯 Project Overview

* User submits two secret numbers
* System splits them into shares using Shamir's Secret Sharing
* Shares are distributed to multiple parties
* Each party computes local sums
* Final result is reconstructed securely without revealing secrets

---

## 🏗️ Architecture
```
┌──────────────────┐     ┌───────────────────────────┐      ┌────────────────────┐
│   User Input     │     │     SMPC System           │      │   SMPCCrypto Core  │
│                  │     │                           │      │                    │
│ • Secret 1       │──▶ │ • Distribute Shares        │───▶ │ • Shamir's SS      │
│ • Secret 2       │     │ • Recieve Local Sums      │      │ • Field Ops        │
│                  │     │ • Reconstruct Computation │      │                    │
└──────────────────┘     └───────────────────────────┘      └────────────────────┘
                                      │ 
                ┌────────────────────────────────────────────┐
                │               Parties                      │
                │                                            │
                │  Party_1     │  Party_2     │  Party_3     │
                │                                            │
                │  Share 1_A   │  Share 1_B   │  Share 1_C   │
                │  Share 2_A   │  Share 2_B   │  Share 2_C   │
                │  Local Sum A │  Local Sum B │  Local Sum C │
                └────────────────────────────────────────────┘ 
```

---

## 📁 Project Structure

```
smpc-collaborative-analysis/
├── demo_script.py       # Interactive demo
├── quick_test.py        # Quick test suite
├── test_smpc.py         # Full test suite
├── smpc_crypto.py       # Cryptographic logic
├── smpc_system.py       # Core SMPC operations
├── requirements.txt     # Dependencies
└── README.md            # Documentation
```

---

## 📦 Minimal Requirements
Install the cryptographic dependency:
pip install pycryptodome

---

## 🔧 Core Components

* `smpc_crypto.py`: Shamir's Secret Sharing, reconstruction, homomorphic addition
* `smpc_system.py`: Party logic, share handling, computation, result reconstruction

---

## 🔐 Security Features

* Threshold-based confidentiality
* No single party can reconstruct the secret
* Supports additive homomorphism

---

## 📊 Example Workflow

1. User inputs: 100 and 250
2. Shares created for each secret
3. Parties receive their shares
4. Parties compute local sums
5. Final sum reconstructed securely

User Input
   │
   ▼
Submit Secret Values
   │
   ▼
SMPC System
 ├─ Create Shares (Shamir's SS)
 ├─ Distribute Shares to Parties
 ├─ Each Party Computes Local Sum
 └─ Reconstruct Final Sum (Lagrange Interpolation)

---

## ⚙️ Configuration Options

* `num_parties`: Total parties involved
* `threshold`: Minimum number of parties required to reconstruct

---

## 🧪 Usage Examples

```python
from smpc_system import SMPCSystem
smpc = SMPCSystem(num_parties=3, threshold=2)
result = smpc.run_secure_computation(100, 250)
print(result)  # Output: 350
```

---

**Authors**: Shir Buchner and Roi Even Haim
**Course**: Secure Multi-Party Computation Implementation
**Date**: June 2025
