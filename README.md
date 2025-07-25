# Secure Multi-Party Computation (SMPC) for Collaborative Data Analysis

A Python-based simulation of Secure Multi-Party Computation using Shamir's Secret Sharing. This project demonstrates how multiple independent parties can compute a joint function (e.g., a sum) without revealing their private inputs.

---

## 🚀 Running
Run the parties:
python party_server.py 1  
python party_server.py 2  
python party_server.py 3  
Each number passed must be a unique party ID (e.g. 1, 2, 3) corresponding to port 8001, 8002, 8003.

Stop a party:  
ctrl + C

Run the controller (after running the parties):  
python smpc_controller_server.py 100 200 -n 3 -t 2  
n: number of parties  
t: threshold

Run the system locally:  
python smpc_controller.py

Run the local full demo:  
python demo_script.py

---

## 🧪 Testing
Run tests locally:  
python test_smpc.py

Run network integration tests:  
python test_smpc_servers.py

---

## 🎯 Project Overview

This project simulates a privacy-preserving computation system where:
- Users submit secret inputs
- Inputs are split into cryptographic shares
- Shares are distributed across simulated parties
- Each party computes local results without learning others’ inputs
- The final result is reconstructed securely

---

## 📁 Project Structure

smpc-collaborative-analysis/
├── smpc_crypto.py # Cryptographic primitives
├── party.py # Party and Share classes
├── party_server.py # TCP party server
├── smpc_controller.py # Local controller logic
├── smpc_controller_server.py # TCP-based controller
├── comm_layer.py # Communication base class
├── test_smpc.py # Unit tests (local logic)
├── test_smpc_servers.py # Integration tests (network)
├── demo_script.py # Interactive CLI demo
└── README.md # Project documentation

---

## 🔧 Core Components

smpc_crypto.py: Core Shamir's Secret Sharing, reconstruction, and field arithmetic

smpc_controller.py: Local simulation logic for share distribution and final aggregation

smpc_controller_server.py: TCP-based coordinator for distributed computation

party_server.py: Networked party node for computing modular sums

comm_layer.py: Abstract base class for TCP communication servers

---

## 🔐 Security Features

Threshold-based reconstruction

No single party learns another’s input

Secure sharing and addition over finite field

Lagrange interpolation guarantees correctness

---

## 📊 Example Workflow

User inputs: 100, 250

Shares are created using Shamir’s (t, n) scheme

Each party receives a distinct share

Parties compute partial results

The final sum is reconstructed from any t of n results

---

## ⚙️ Configuration Options
num_parties: Total number of participating parties

threshold: Minimum number of shares needed to reconstruct the result

---

Authors: Shir Buchner and Roi Even Haim
Course: Secure Multi-Party Computation Implementation
Date: June 2025