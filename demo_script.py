#!/usr/bin/env python3
"""
Interactive Demo Script for SMPC Collaborative Data Analysis

This script provides an interactive demonstration of the Secure Multi-Party
Computation system, allowing users to experiment with different scenarios.
"""

import sys
import time
from typing import Optional
from smpc_system import SMPCSystem
from smpc_crypto import SMPCCrypto


def print_banner():
    """Print the demo banner."""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║              SMPC Collaborative Data Analysis Demo           ║
    ║                                                              ║
    ║  Secure Multi-Party Computation using Shamir's Secret Sharing ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def print_step(step_num: int, description: str, details: str = ""):
    """Print a formatted step description."""
    print(f"\n🔹 Step {step_num}: {description}")
    if details:
        print(f"   {details}")
    time.sleep(0.5)


def demonstrate_basic_workflow():
    """Demonstrate the basic SMPC workflow."""
    print("\n" + "="*60)
    print("📊 BASIC SMPC WORKFLOW DEMONSTRATION")
    print("="*60)
    
    # Get user input
    try:
        print("\nEnter two secret numbers to compute their sum securely:")
        secret1 = int(input("Secret 1: "))
        secret2 = int(input("Secret 2: "))
    except ValueError:
        print("❌ Invalid input. Using default values: 100, 250")
        secret1, secret2 = 100, 250
    
    print(f"\n🔒 Your secrets: {secret1} and {secret2}")
    print(f"🎯 Expected sum: {secret1 + secret2}")
    
    # Initialize SMPC system
    print_step(1, "Initializing SMPC System", "Creating 3 parties with threshold 2")
    smpc = SMPCSystem(num_parties=3, threshold=2)
    
    # Show system configuration
    print(f"   ├─ Number of parties: {smpc.num_parties}")
    print(f"   ├─ Threshold: {smpc.threshold}")
    print(f"   └─ Prime field size: {smpc.crypto.get_prime().bit_length()} bits")
    
    # Submit secrets and create shares
    print_step(2, "Creating Secret Shares", "Splitting secrets using Shamir's Secret Sharing")
    success = smpc.submit_secret_values([secret1, secret2], "demo")
    
    if not success:
        print("❌ Failed to create shares!")
        return
    
    # Show share distribution (simulated)
    print("   📤 Share distribution:")
    for i, party in enumerate(smpc.parties):
        shares = party.shares["demo"]
        share_names = [name for name, _ in shares]
        print(f"   ├─ {party.name}: Received shares {share_names}")
        # Don't show actual share values for security demonstration
        for share_name, _ in shares:
            print(f"   │  └─ {share_name}: [HIDDEN FOR PRIVACY]")
    
    # Each party computes local sum
    print_step(3, "Computing Party Sums", "Each party sums their shares locally")
    party_sums = smpc.compute_party_sums("demo")
    
    print("   🔢 Local computations:")
    for party_id, sum_value in party_sums.items():
        print(f"   ├─ Party {party_id}: Local sum = {sum_value}")
    
    # Reconstruct final result
    print_step(4, "Reconstructing Final Sum", "Using Lagrange interpolation")
    final_result = smpc.reconstruct_final_sum("demo")
    
    # Show results
    print("\n" + "="*40)
    print("🎉 COMPUTATION COMPLETE!")
    print("="*40)
    print(f"🔒 Input secrets: {secret1}, {secret2}")
    print(f"✅ Secure result: {final_result}")
    print(f"🎯 Expected sum: {secret1 + secret2}")
    
    if final_result == secret1 + secret2:
        print("✅ SUCCESS: Secure computation produced correct result!")
    else:
        print("❌ ERROR: Results don't match!")
    
    print(f"\n🛡️  Privacy guarantee: No party learned the individual secrets!")
    
    return final_result


def demonstrate_security_properties():
    """Demonstrate security properties of the SMPC system."""
    print("\n" + "="*60)
    print("🔐 SECURITY PROPERTIES DEMONSTRATION")
    print("="*60)
    
    crypto = SMPCCrypto()
    secret = 12345
    
    print(f"\n🔒 Original secret: {secret}")
    
    # Create shares
    shares = crypto.create_shares(secret, threshold=3, num_shares=5)
    
    print(f"\n📊 Generated {len(shares)} shares with threshold 3:")
    for party_id, share_value in shares:
        print(f"   Party {party_id}: {share_value}")
    
    # Demonstrate threshold property
    print(f"\n🔍 Threshold Security Demonstration:")
    
    # Show that 2 shares are insufficient
    print(f"\n❌ Trying to reconstruct with 2 shares (below threshold):")
    insufficient_shares = shares[:2]
    try:
        wrong_result = crypto.reconstruct_secret(insufficient_shares)
        print(f"   Result: {wrong_result} (INCORRECT - not enough shares)")
    except ValueError as e:
        print(f"   ✅ Properly failed: {e}")
    
    # Show that 3 shares work
    print(f"\n✅ Reconstructing with 3 shares (meets threshold):")
    sufficient_shares = shares[:3]
    correct_result = crypto.reconstruct_secret(sufficient_shares)
    print(f"   Result: {correct_result} ({'CORRECT' if correct_result == secret else 'INCORRECT'})")
    
    # Show that more shares also work
    print(f"\n✅ Reconstructing with 4 shares (above threshold):")
    more_shares = shares[:4]
    correct_result2 = crypto.reconstruct_secret(more_shares)
    print(f"   Result: {correct_result2} ({'CORRECT' if correct_result2 == secret else 'INCORRECT'})")


def demonstrate_different_configurations():
    """Demonstrate SMPC with different configurations."""
    print("\n" + "="*60)
    print("⚙️  DIFFERENT CONFIGURATION DEMONSTRATION")
    print("="*60)
    
    configurations = [
        (3, 2, "Standard Setup"),
        (5, 3, "Higher Security"),
        (4, 4, "All Parties Required")
    ]
    
    test_values = [100, 200]
    expected_sum = sum(test_values)
    
    for num_parties, threshold, description in configurations:
        print(f"\n🔧 Configuration: {description}")
        print(f"   ├─ Parties: {num_parties}")
        print(f"   └─ Threshold: {threshold}")
        
        try:
            smpc = SMPCSystem(num_parties=num_parties, threshold=threshold)
            result = smpc.run_secure_computation(test_values[0], test_values[1], 
                                               f"config_{num_parties}_{threshold}")
            
            status = "✅ SUCCESS" if result == expected_sum else "❌ FAILED"
            print(f"   Result: {result} ({status})")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")


def performance_benchmark():
    """Simple performance benchmark."""
    print("\n" + "="*60)
    print("⚡ PERFORMANCE BENCHMARK")
    print("="*60)
    
    import time
    
    smpc = SMPCSystem(num_parties=3, threshold=2)
    
    # Benchmark different value sizes
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
            result = smpc.run_secure_computation(val1, val2, f"perf_{val1}")
            end_time = time.time()
            
            duration_ms = (end_time - start_time) * 1000
            expected = (val1 + val2) % smpc.crypto.get_prime()
            status = "✅ OK" if result == expected else "❌ FAIL"
            
            print(f"{description:<20} {duration_ms:<12.2f} {result:<15} {status:<10}")
            
        except Exception as e:
            print(f"{description:<20} {'ERROR':<12} {'N/A':<15} {'❌ FAIL':<10}")


def interactive_menu():
    """Interactive menu for demo options."""
    while True:
        print("\n" + "="*60)
        print("🎮 INTERACTIVE DEMO MENU")
        print("="*60)
        print("1. 📊 Basic SMPC Workflow")
        print("2. 🔐 Security Properties Demo")
        print("3. ⚙️  Different Configurations")
        print("4. ⚡ Performance Benchmark")
        print("5. 🧪 Run All Tests")
        print("6. ❌ Exit")
        
        try:
            choice = input("\nSelect option (1-6): ").strip()
            
            if choice == "1":
                demonstrate_basic_workflow()
            elif choice == "2":
                demonstrate_security_properties()
            elif choice == "3":
                demonstrate_different_configurations()
            elif choice == "4":
                performance_benchmark()
            elif choice == "5":
                print("\n🧪 Running comprehensive test suite...")
                from test_smpc import run_tests
                success = run_tests()
                if success:
                    print("✅ All tests passed!")
                else:
                    print("❌ Some tests failed!")
            elif choice == "6":
                print("\n👋 Thank you for trying SMPC Demo!")
                break
            else:
                print("❌ Invalid choice. Please select 1-6.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Demo interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"❌ An error occurred: {e}")
        
        input("\nPress Enter to continue...")


def main():
    """Main demo function."""
    print_banner()
    
    print("Welcome to the Secure Multi-Party Computation demonstration!")
    print("This demo shows how multiple parties can compute a sum of secrets")
    print("without revealing their individual inputs to each other.")
    
    # Check if arguments provided for automated run
    if len(sys.argv) > 1:
        if sys.argv[1] == "--auto":
            print("\n🤖 Running automated demonstration...")
            demonstrate_basic_workflow()
            demonstrate_security_properties()
            demonstrate_different_configurations()
            performance_benchmark()
            return
        elif sys.argv[1] == "--test":
            print("\n🧪 Running test suite...")
            from test_smpc import run_tests
            success = run_tests()
            sys.exit(0 if success else 1)
    
    # Interactive mode
    try:
        interactive_menu()
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted. Goodbye!")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("Please check your installation and try again.")


if __name__ == "__main__":
    main()