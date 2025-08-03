#!/usr/bin/env python3
"""
Interactive Demo Script for Real Decentralized SMPC

This script demonstrates a truly decentralized Secure Multi-Party Computation system where:
- All parties actively participate and communicate peer-to-peer
- No central authority processes secrets
- Individual secrets are NEVER reconstructed
- Only the final sum is revealed to all parties

Based on the improved design that simulates real SMPC protocols.
"""

import sys
import time
from typing import List, Tuple
from smpc_controller import DecentralizedSMPCController, SMPCController
import smpc_crypto as crypto


def print_banner():
    """Display the improved SMPC banner"""
    banner = """
    ╔══════════════════════════════════════════════════════════════════╗
    ║            REAL DECENTRALIZED SMPC DEMONSTRATION                ║
    ║                                                                  ║
    ║    True Peer-to-Peer Secure Multi-Party Computation             ║
    ║    • All parties actively participate                            ║
    ║    • No central authority                                        ║
    ║    • Individual secrets NEVER reconstructed                      ║
    ║    • Only final sum revealed                                     ║
    ╚══════════════════════════════════════════════════════════════════╝
    """
    print(banner)


def print_step(step_num: int, description: str, details: str = ""):
    """Print a numbered demo step with optional details"""
    print(f"\n🔹 Step {step_num}: {description}")
    if details:
        print(f"   {details}")
    time.sleep(0.5)


def demonstrate_real_smpc_workflow():
    """
    Demonstrate the real decentralized SMPC workflow where all parties participate.
    """
    print("\n" + "=" * 80)
    print("🌐 REAL DECENTRALIZED SMPC WORKFLOW DEMONSTRATION")
    print("=" * 80)
    print("Key Innovation: All parties communicate peer-to-peer, no central coordinator!")

    try:
        print("\nEnter secret values for companies to compute total market size:")
        print("(Each company will participate actively in the protocol)")

        # Get secrets from user
        secrets = []
        company_names = ["TechCorp", "DataFlow", "CloudSys", "AI-Innovate", "CyberGuard"]

        print(f"\nEnter revenues for {len(company_names[:3])} companies:")
        for i, company in enumerate(company_names[:3]):
            try:
                secret = int(input(f"{company} revenue ($): "))
                secrets.append(secret)
            except ValueError:
                print(f"Invalid input for {company}, using default value")
                secrets.append((i + 1) * 250000)  # Default values

        if len(secrets) < 3:
            print("Using default company revenues for demonstration")
            secrets = [250000, 180000, 320000]

    except (ValueError, KeyboardInterrupt):
        print("Using default values for demonstration")
        secrets = [250000, 180000, 320000]

    print(f"\n💼 Company Secrets: {len(secrets)} companies participating")
    print(f"🎯 Expected Total Market Size: ${sum(secrets):,}")
    print("🔒 Note: In real SMPC, individual revenues remain completely hidden!")

    print_step(1, "Initializing Decentralized SMPC System",
               "Each company becomes an active participant")

    threshold = 2  # Need at least 2 companies to reconstruct
    controller = DecentralizedSMPCController(secrets, threshold)

    print(f"   • Companies: {len(secrets)}")
    print(f"   • Security threshold: {threshold}")
    print(f"   • Prime field size: {controller.prime.bit_length()} bits")
    print(f"   • Communication: Peer-to-peer channels")

    print_step(2, "Phase 1: Decentralized Share Creation & Distribution",
               "ALL companies create and exchange shares simultaneously")

    print_step(3, "Phase 2: Local Sum Computation",
               "Each company computes on received shares WITHOUT reconstructing secrets")

    print_step(4, "Phase 3: Collaborative Sum Reconstruction",
               "Companies collaborate to reveal ONLY the total sum")

    print("\n🚀 Executing Real Decentralized SMPC Protocol...")
    print("=" * 60)

    # Execute the real decentralized protocol
    final_result, success = controller.run_secure_computation()

    print("\n" + "=" * 60)
    print("🎉 DECENTRALIZED SMPC COMPLETED!")
    print("=" * 60)

    if success:
        print(f"💰 Total Market Size: ${final_result:,}")
        print(f"🎯 Expected Result:   ${sum(secrets):,}")
        print(f"✅ Accuracy: {'PERFECT' if final_result == sum(secrets) % controller.prime else 'ERROR'}")
        print(f"🔒 Privacy: Individual company revenues were NEVER revealed!")
        print(f"🌐 Decentralized: No central authority processed any secrets!")
    else:
        print("❌ Protocol failed - this shouldn't happen in a properly implemented system")


def run_test_suite():
    """Run the comprehensive test suite"""
    print("\n" + "=" * 80)
    print("🧪 COMPREHENSIVE SMPC TEST SUITE")
    print("=" * 80)

    try:
        # Try importing the test module (handle both possible names)
        test_module = None
        try:
            import test_smpc as test_module
            print("Found test_smpc.py")
        except ImportError:
            try:
                import tests as test_module
                print("Found tests.py")
            except ImportError:
                print("❌ No test file found. Please ensure either test_smpc.py or tests.py is present.")
                return

        # Check if the test module has the expected function
        if hasattr(test_module, 'run_massive_test_suite'):
            print("🚀 Running comprehensive test suite...")
            success = test_module.run_massive_test_suite()

            if success:
                print("\n🎉 All tests completed successfully!")
            else:
                print("\n⚠️ Some tests revealed issues - check output above")
        else:
            print("❌ Test module doesn't have the expected run_massive_test_suite function")

    except Exception as e:
        print(f"❌ Error running tests: {e}")
        import traceback
        traceback.print_exc()


def interactive_menu():
    """Show simplified interactive demo menu"""
    while True:
        print("\n" + "=" * 80)
        print("🎮 REAL DECENTRALIZED SMPC INTERACTIVE MENU")
        print("=" * 80)
        print("1. 🌐 Real Decentralized SMPC Workflow")
        print("2 🧪 Run Test Suite")
        print("3. ❌ Exit")

        try:
            choice = input("\nSelect option (1, 2, or 3): ").strip()
            if choice == "1":
                demonstrate_real_smpc_workflow()
            elif choice == "2":
                run_test_suite()
            elif choice == "3":
                print("\n👋 Thank you for exploring Real Decentralized SMPC!")
                break
            else:
                print("❌ Invalid choice. Please select 1, 2, or 3.")
        except KeyboardInterrupt:
            print("\n\n👋 Demo interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"❌ An error occurred: {e}")

        input("\nPress Enter to continue...")


def main():
    """
    Entry point for the improved demo script.
    """
    print_banner()
    print("Welcome to the Real Decentralized SMPC demonstration!")
    print("\nThis demo showcases TRUE peer-to-peer secure multi-party computation where:")
    print("• All parties actively participate and communicate directly")
    print("• No central authority coordinates or processes secrets")
    print("• Individual secrets are NEVER reconstructed")
    print("• Only the final sum is revealed to all parties")
    print("• Perfect privacy with information-theoretic security")

    if len(sys.argv) > 1:
        if sys.argv[1] == "--auto":
            print("\n🤖 Running automated demonstration...")
            demonstrate_real_smpc_workflow()
            return
        elif sys.argv[1] == "--test":
            print("\n🧪 Running test suite...")
            run_test_suite()
            return

    try:
        interactive_menu()
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted. Goodbye!")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()