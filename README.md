# Real Decentralized SMPC (Secure Multi-Party Computation)

[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-comprehensive-green.svg)](#testing)

A truly decentralized Secure Multi-Party Computation system that enables multiple parties to compute the sum of their private inputs without revealing individual secrets to anyone, including a central coordinator.

## 🌟 Key Features

- **True Decentralization**: All parties actively participate with peer-to-peer communication
- **No Central Authority**: No coordinator ever sees or processes individual secrets
- **Information-Theoretic Security**: Based on Shamir's Secret Sharing with threshold security
- **Individual Privacy**: Secrets are NEVER reconstructed - only the final sum is revealed
- **Distributed Deployment**: Supports parties running on different servers globally
- **Robust Error Handling**: Comprehensive failure detection and graceful degradation
- **Extensive Testing**: Massive test suite covering edge cases and security boundaries

## 🚀 Quick Start

### Local Demo

```bash
# Run the interactive demo
python demo_script.py

# Or run automated demo
python demo_script.py --auto

# Run comprehensive tests
python demo_script.py --test
```

### Distributed Deployment

1. **Generate Configuration Files**:
Use provided config files.

2. **Start Party Servers** (on different machines):
```bash
# On server 1
python distributed_party_server.py --config party_1_config.json

# On server 2
python distributed_party_server.py --config party_2_config.json

# On server 3
python distributed_party_server.py --config party_3_config.json
```

3. **Run Distributed Protocol**:
```bash
python distributed_coordinator.py --config global_config.json --mode interactive
```

## 📋 Requirements

### Python Dependencies
```bash
pip install pycryptodome flask requests
```

### System Requirements
- Python 3.7 or higher
- Network connectivity between distributed parties
- Sufficient memory for cryptographic operations

## 🏗️ Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                    SMPC System Architecture                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │   Party A   │    │   Party B   │    │   Party C   │     │
│  │ Secret: 100 │◄──►│ Secret: 200 │◄──►│ Secret: 300 │     │
│  │             │    │             │    │             │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
│         │                   │                   │          │
│         └───────────────────┼───────────────────┘          │
│                             ▼                              │
│                    ┌─────────────────┐                     │
│                    │   Final Sum:    │                     │
│                    │      600        │                     │
│                    │ (No individual  │                     │
│                    │ secrets leaked) │                     │
│                    └─────────────────┘                     │
└─────────────────────────────────────────────────────────────┘
```

### Protocol Flow

1. **Share Distribution**: Each party creates shares of their secret using Shamir's scheme
2. **Secure Communication**: Shares are distributed through secure channels
3. **Homomorphic Addition**: Parties compute sum shares without reconstructing secrets
4. **Final Reconstruction**: Only the sum is reconstructed using threshold shares

## 📁 Project Structure

```
smpc-project/
├── README.md                          # This file
├── demo_script.py                     # Interactive demonstration
├── smpc_controller.py                 # Main SMPC orchestration
├── party.py                          # Decentralized party implementation
├── smpc_crypto.py                    # Cryptographic primitives
├── distributed_coordinator.py        # Global coordinator for distributed deployment
├── distributed_party_server.py       # HTTP server for distributed parties
├── test_smpc.py                      # Comprehensive test suite
├── global_config.json               # Global configuration
├── party_1_config.json              # Party 1 configuration
├── party_2_config.json              # Party 2 configuration
└── party_3_config.json              # Party 3 configuration
```

## 🔧 Configuration

### Global Configuration (`global_config.json`)
```json
{
  "parties": [
    {
      "party_id": 1,
      "host": "localhost",
      "port": 5001
    },
    {
      "party_id": 2,
      "host": "localhost",
      "port": 5002
    },
    {
      "party_id": 3,
      "host": "localhost",
      "port": 5003
    }
  ],
  "threshold": 2,
  "prime": 13407807929942597099574024998205846127479365820592393377723561443721764030073546976801874298166903427690031858186486050853753882811946569946433649006084171
}
```

### Party Configuration (`party_X_config.json`)
```json
{
  "party_id": 2,
  "host": "0.0.0.0",
  "port": 5002,
  "secret_value": 250000,
  "threshold": 2,
  "total_parties": 3,
  "prime": 13407807929942597099574024998205846127479365820592393377723561443721764030073546976801874298166903427690031858186486050853753882811946569946433649006084171,
  "other_parties": [
    {
      "party_id": 1,
      "host": "localhost",
      "port": 5001
    },
    {
      "party_id": 3,
      "host": "localhost",
      "port": 5003
    }
  ]
}
```

## 🧪 Testing

### Run Complete Test Suite
```bash
python test_smpc.py
```

### Test Categories
- **Normal Operation Cases**: Standard configurations that should work
- **Edge Cases**: Boundary conditions and tricky scenarios
- **Failure Cases**: Invalid inputs that should fail gracefully
- **Security Tests**: Collusion resistance and privacy boundaries
- **Performance Tests**: Stress testing with large inputs
- **Integration Tests**: End-to-end system validation

## 🔐 Security Properties

### Privacy Guarantees
- **Individual Secret Privacy**: Secrets never reconstructed during computation
- **Threshold Security**: Requires `t` parties to collude to break privacy
- **Information-Theoretic**: Security proven mathematically, not just computationally
