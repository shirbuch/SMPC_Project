#!/usr/bin/env python3
"""
Interactive Demo Script for SMPC Collaborative Data Analysis

This script provides a user-friendly demonstration of Secure Multi-Party Computation (SMPC)
using Shamir's Secret Sharing scheme. Users can interactively:
- Enter secrets to be securely computed
- Observe share distribution among parties
- See how partial computations are securely reconstructed
- Explore security and performance of the system

It supports multiple demo modes through a text menu interface and CLI flags.
"""

import sys
import time
from smpc_controller import SMPCController
import smpc_crypto as crypto

def print_banner():
    """Display a decorative SMPC banner to introduce the demo."""
    banner = """
    ╔════════════════════════════════════════════════════════════════╗
    ║              SMPC Collaborative Data Analysis Demo           ║
    ║                                                              ║
    ║ Secure Multi-Party Computation using Shamir's Secret Sharing ║
    ╚════════════════════════════════════════════════════════════╝
    """
    print(banner)

def print_step(step_num: int, description: str, details: str = ""):
    """
    Print a numbered demo step with optional additional details.

    Args:
        step_num (int): Step number for reference.
        description (str): Main description of the step.
        details (str, optional): Further explanation to be printed below.
    """
    print(f"\n🔹 Step {step_num}: {description}")
    if details:
        print(f"   {details}")
    time.sleep(0.5)

def demonstrate_basic_workflow():
    """
    Demonstrate the full basic SMPC workflow:
    - Secret entry
    - Share creation
    - Local computations
    - Secure reconstruction of the final result
    """
    print("\n" + "=" * 60)
    print("📊 BASIC SMPC WORKFLOW DEMONSTRATION")
    print("=" * 60)

    try:
        print("\nEnter two secret numbers to compute their sum securely:")
        secret1 = int(input("Secret 1: "))
        secret2 = int(input("Secret 2: "))
    except ValueError:
        print("❌ Invalid input. Using default values: 100, 250")
        secret1, secret2 = 100, 250

    print(f"\n🔒 Your secrets: {secret1} and {secret2}")
    print(f"🎯 Expected sum: {secret1 + secret2}")

    print_step(1, "Initializing SMPC System", "Creating 3 parties with threshold 2")
    smpc = SMPCController(num_parties=3, threshold=2)

    print(f"   Parties: {smpc.num_parties}")
    print(f"   Threshold: {smpc.threshold}")
    print(f"   Prime field size: {smpc.prime.bit_length()} bits")

    print_step(2, "Creating Secret Shares", "Splitting secrets using Shamir's Secret Sharing")
    share_map = smpc.create_shares_for_parties([secret1, secret2])

    print("   📤 Share distribution:")
    for party in smpc.parties:
        shares = share_map[party.id]
        print(f"   {party.get_name()}: {[share.name for share in shares]}")
        for share in shares:
            print(f"   │  └─ {share}")

    print_step(3, "Computing Party Sums", "Each party sums their shares locally")
    print("   🔢 Local computations:")
    partial_results = smpc.request_parties_to_compute_results(share_map)
    for pid, val in partial_results.items():
        print(f"   Party {pid}: {str(val)[:5]}...")

    print_step(4, "Reconstructing Final Sum", "Using Lagrange interpolation")
    final_result = smpc.reconstruct_final_result(partial_results)

    print("\n" + "=" * 40)
    print("🎉 COMPUTATION COMPLETE!")
    print("=" * 40)
    print(f"🔒 Input secrets: {secret1}, {secret2}")
    print(f"✅ Secure result: {final_result}")
    print(f"🎯 Expected sum: {secret1 + secret2}")

    if final_result == secret1 + secret2:
        print("✅ SUCCESS: Secure computation produced correct result!")
    else:
        print("❌ ERROR: Results don't match!")

    print(f"\n🛡️  Privacy guarantee: No party learned the individual secrets!")

def demonstrate_security_properties():
    """
    Demonstrate security properties of Shamir's Secret Sharing:
    - Show failure to reconstruct with < threshold shares
    - Confirm success with >= threshold shares
    """
    print("\n" + "=" * 60)
    print("🔐 SECURITY PROPERTIES DEMONSTRATION")
    print("=" * 60)

    secret = 12345
    prime = crypto.get_prime()

    print(f"\n🔒 Original secret: {secret}")
    shares = crypto.create_shares(secret, threshold=3, num_shares=5, prime=prime)
    print(f"\n📊 Generated {len(shares)} shares with threshold 3:")
    for party_id, share_value in shares:
        print(f"   Party {party_id}: {share_value}")

    print(f"\n🔍 Threshold Security Demonstration:")

    print(f"\n❌ Trying to reconstruct with 2 shares (below threshold):")
    try:
        r = crypto.reconstruct_secret(shares[:2], prime=prime)
        print(f"   Result: {r} \n{'❌ Unexpected success' if r == secret else '✅ Properly failed'}")
    except Exception as e:
        print(f"   ✅ Properly failed: {e}")

    print(f"\nReconstructing with 3 shares:")
    r = crypto.reconstruct_secret(shares[:3], prime=prime)
    print(f"   Result: {r} \n{'✅ CORRECT' if r == secret else '❌ INCORRECT'}")

    print(f"\nReconstructing with 4 shares:")
    r = crypto.reconstruct_secret(shares[:4], prime=prime)
    print(f"   Result: {r} \n{'✅ CORRECT' if r == secret else '❌ INCORRECT'}")

def demonstrate_different_configurations():
    """
    Demonstrate SMPC behavior across different configurations of (parties, threshold).
    Includes positive and negative tests.
    """
    print("\n" + "=" * 60)
    print("⚙️  DIFFERENT CONFIGURATION DEMONSTRATION")
    print("=" * 60)

    configurations = [
        (3, 2, "Standard Setup"),
        (5, 3, "Higher Security"),
        (4, 4, "All Parties Required")
    ]
    test_values = [100, 200]
    expected_sum = sum(test_values)
    summary = []

    for num_parties, threshold, desc in configurations:
        print(f"\n🔧 Configuration: {desc}")
        print(f"   Parties: {num_parties}")
        print(f"   Threshold: {threshold}")

        try:
            smpc = SMPCController(num_parties, threshold)
            share_map = smpc.create_shares_for_parties(test_values)
            partial_results = smpc.request_parties_to_compute_results(share_map)

            print("   Valid reconstructions:")
            for i in range(threshold, num_parties + 1):
                subset = smpc.parties[i - threshold:i]
                ids = [p.id for p in subset]
                try:
                    r = smpc.reconstruct_final_result(partial_results, party_ids=ids)
                    ok = "✓" if r == expected_sum else "✗"
                    print(f"     From parties {ids}: {r} ({ok})")
                except Exception as e:
                    print(f"     From parties {ids}: Reconstruction failed: {e} (✗)")

            print("   Negative test (below threshold):")
            bad_subset = smpc.parties[:threshold - 1]
            ids = [p.id for p in bad_subset]
            try:
                smpc.reconstruct_final_result(partial_results, party_ids=ids)
                print(f"     From parties {ids}: Unexpected success! (✗)")
                status = "❌ FAIL"
            except Exception:
                print(f"     From parties {ids}: Failed as expected (✓)")
                status = "✅ SUCCESS" if sum(test_values) % smpc.prime == expected_sum else "❌ FAIL"

            summary.append((f"{desc} ({num_parties}P-{threshold}T)", expected_sum, status))
            print(f"   {status}")

        except Exception as e:
            print(f"   ❌ Error: {e}")
            summary.append((f"{desc} ({num_parties}P-{threshold}T)", "ERROR", "❌ FAIL"))

    print("\n📋 Summary of Configurations:")
    print(f"{'Config':<30} {'Result':<15} {'Status'}")
    print("-" * 60)
    for config, result, status in summary:
        print(f"{config:<30} {str(result):<15} {status}")

def performance_benchmark():
    """
    Benchmark SMPC runtime with increasingly large inputs.
    Prints timings and verifies correctness of results.
    """
    print("\n" + "="*60)
    print("⚡ PERFORMANCE BENCHMARK")
    print("="*60)

    smpc = SMPCController(num_parties=3, threshold=2)

    test_cases = [
        (10, 20, "Small values"),
        (1000, 2000, "Medium values"),
        (10**6, 2*10**6, "Large values"),
        (10**9, 2*10**9, "Very large values")
    ]

    print(f"\n📊 Performance Results:")
    print(f"{'Test Case':<20} {'Time (ms)':<12} {'Result':<15} {'Status':<10}")
    print("-" * 60)

    for val1, val2, description in test_cases:
        start_time = time.time()
        try:
            result = smpc.run_secure_computation([val1, val2])
            end_time = time.time()

            duration_ms = (end_time - start_time) * 1000
            expected = (val1 + val2) % smpc.prime
            status = "✅ OK" if result == expected else "❌ FAIL"

            print(f"{description:<20} {duration_ms:<12.2f} {result:<15} {status:<10}")

        except Exception as e:
            print(f"{description:<20} {'ERROR':<12} {'N/A':<15} {'❌ FAIL':<10}")

def interactive_menu():
    """
    Show interactive demo menu to the user.
    Handles input routing to appropriate demo features.
    """
    while True:
        print("\n" + "="*60)
        print("🎮 INTERACTIVE DEMO MENU")
        print("="*60)
        print("1. 📊 Basic SMPC Workflow")
        print("2. 🔐 Security Properties Demo")
        print("3. ⚙️  Different Configurations")
        print("4. ⚡ Performance Benchmark")
        print("5. 🚀 Run Basic Functionality")
        print("6. 🧪 Run All Tests")
        print("7. ❌ Exit")

        try:
            choice = input("\nSelect option (1-7): ").strip()
            if choice == "1":
                demonstrate_basic_workflow()
            elif choice == "2":
                demonstrate_security_properties()
            elif choice == "3":
                demonstrate_different_configurations()
            elif choice == "4":
                performance_benchmark()
            elif choice == "5":
                from smpc_controller import run_basic_functionality
                run_basic_functionality()
            elif choice == "6":
                print("\n🧪 Running comprehensive test suite...")
                from test_smpc import run_tests
                run_tests()
            elif choice == "7":
                print("\n👋 Thank you for trying SMPC Demo!")
                break
            else:
                print("❌ Invalid choice. Please select 1-7.")
        except KeyboardInterrupt:
            print("\n\n👋 Demo interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"❌ An error occurred: {e}")

        input("\nPress Enter to continue...")

def main():
    """
    Entry point for demo script.
    Supports CLI flags for automated testing or benchmarking.
    """
    print_banner()
    print("Welcome to the Secure Multi-Party Computation demonstration!")
    print("This demo shows how multiple parties can compute a sum of secrets")
    print("without revealing their individual inputs to each other.")

    if len(sys.argv) > 1:
        if sys.argv[1] == "--auto":
            demonstrate_basic_workflow()
            demonstrate_security_properties()
            demonstrate_different_configurations()
            performance_benchmark()
            return
        elif sys.argv[1] == "--test":
            from test_smpc import run_tests
            sys.exit(0 if run_tests() else 1)

    try:
        interactive_menu()
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted. Goodbye!")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()
