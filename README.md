# Secure Multi-Party Computation (SMPC) for Collaborative Data Analysis

A Python-based simulation of Secure Multi-Party Computation using Shamir's Secret Sharing. This project demonstrates how multiple independent parties can compute a joint function (e.g., a sum) without revealing their private inputs.

---

## 🚀 Running
Run the parties:
python party.py 1
python party.py 2
python party.py 3

Each number passed must be a unique party ID (e.g. 1, 2, 3) corresponding to port 8001, 8002, 8003.

Stop a party:  
ctrl + C

---

## 🧪 Testing
Run tests locally:  
python test_smpc.py

python test_party.py

---


## 🔧 Core Components

smpc_crypto.py: Core Shamir's Secret Sharing, reconstruction, and field arithmetic

---

## 🔐 Security Features

Threshold-based reconstruction

No single party learns another’s input

Secure sharing and addition over finite field

Lagrange interpolation guarantees correctness

---

## ⚙️ Configuration Options
num_parties: Total number of participating parties

threshold: Minimum number of shares needed to reconstruct the result

---

Authors: Shir Buchner and Roi Even Haim
Course: Secure Multi-Party Computation Implementation
Date: June 2025