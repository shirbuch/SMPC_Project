#!/usr/bin/env python3
"""
Quick test script to verify SMPC implementation works correctly.
"""

import logging
logging.getLogger("smpc_system").setLevel(logging.CRITICAL)

def test_basic_functionality():
    """Test basic SMPC functionality with proper share naming."""
    print("🧪 Testing SMPC Basic Functionality")
    print("=" * 50)

    try:
        from smpc_system import SMPCSystem

        # Initialize system
        print("1. Initializing SMPC system...")
        smpc = SMPCSystem(num_parties=3, threshold=2)
        print("   ✅ System initialized successfully")

        # Test values
        secret1, secret2 = 100, 250
        expected_sum = secret1 + secret2

        print(f"\n2. Testing with secrets: {secret1}, {secret2}")
        print(f"   Expected sum: {expected_sum}")

        # Submit secrets
        print("\n3. Submitting secrets and creating shares...")
        success = smpc.submit_secret_values([secret1, secret2], "test")
        if not success:
            raise RuntimeError("Failed to submit secrets")
        print("   ✅ Secrets submitted successfully")

        # Show share distribution
        print("\n4. Share distribution:")
        for party in smpc.parties:
            shares = party.shares["test"]
            share_names = [share.name for share in shares]
            print(f"   {party.name}: {share_names}")

        # Compute party sums
        print("\n5. Computing party sums...")
        smpc.compute_party_sums("test")  # prints short share strings already
        print("   ✅ Party sums computed successfully")

        # Reconstruct final sum
        print("\n6. Reconstructing final sum...")
        final_result = smpc.reconstruct_final_sum("test")
        print(f"   Final result: {final_result}")

        # Verify result
        if final_result == expected_sum:
            print("   ✅ SUCCESS: Computation result is correct!")
            return True
        else:
            print(f"   ❌ FAILED: Expected {expected_sum}, got {final_result}")
            return False

    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_crypto_primitives():
    """Test the crypto primitives directly."""
    print("\n🔐 Testing Crypto Primitives")
    print("=" * 50)

    try:
        from smpc_crypto import SMPCCrypto

        crypto = SMPCCrypto()
        secret = 12345

        print(f"1. Testing secret sharing for secret: {secret}")

        # Create shares
        shares = crypto.create_shares(secret, threshold=2, num_shares=3)
        print(f"   Created shares: {shares}")

        # Test reconstruction
        reconstructed = crypto.reconstruct_secret(shares[:2])  # Use threshold
        print(f"   Reconstructed secret: {reconstructed}")

        if reconstructed == secret:
            print("   ✅ SUCCESS: Secret sharing works correctly!")
            return True
        else:
            print(f"   ❌ FAILED: Expected {secret}, got {reconstructed}")
            return False

    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_share_naming():
    """Test that share naming follows the required format."""
    print("\n🏷️  Testing Share Naming")
    print("=" * 50)

    try:
        from smpc_system import SMPCSystem

        smpc = SMPCSystem(num_parties=3, threshold=2)
        smpc.submit_secret_values([100, 200], "naming_test")

        expected_names = [
            ["1_A", "2_A"],  # Party 1
            ["1_B", "2_B"],  # Party 2
            ["1_C", "2_C"]   # Party 3
        ]

        print("Checking share names:")
        for i, party in enumerate(smpc.parties):
            shares = party.shares["naming_test"]
            actual_names = [share.name for share in shares]
            expected = expected_names[i]

            print(f"   {party.name}: {actual_names}")

            if actual_names == expected:
                print(f"   ✅ Correct naming for {party.name}")
            else:
                print(f"   ❌ Wrong naming for {party.name}: expected {expected}")
                return False

        print("   ✅ SUCCESS: All share names are correct!")
        return True

    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all quick tests."""
    print("🚀 SMPC Quick Test Suite")
    print("=" * 60)

    tests = [
        ("Crypto Primitives", test_crypto_primitives),
        ("Share Naming", test_share_naming),
        ("Basic Functionality", test_basic_functionality),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name} Test...")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} Test PASSED")
            else:
                print(f"❌ {test_name} Test FAILED")
        except Exception as e:
            print(f"❌ {test_name} Test ERROR: {e}")

    print(f"\n{'='*60}")
    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! SMPC implementation is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
