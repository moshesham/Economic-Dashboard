#!/usr/bin/env python3
"""
Verification script for API Key Management feature
Run this to verify the implementation is working correctly
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


def verify_implementation():
    """Verify all components of the API key management feature"""
    
    print("=" * 70)
    print("🔍 API KEY MANAGEMENT FEATURE VERIFICATION")
    print("=" * 70)
    
    results = []
    
    # Test 1: Module imports
    print("\n[1/8] Testing module imports...")
    try:
        from modules.auth.credentials_manager import CredentialsManager, get_credentials_manager
        from modules.auth import CredentialsManager as CM
        print("✅ All modules import successfully")
        results.append(True)
    except Exception as e:
        print(f"❌ Import failed: {e}")
        results.append(False)
    
    # Test 2: Credentials manager initialization
    print("\n[2/8] Testing credentials manager initialization...")
    try:
        creds = get_credentials_manager()
        assert creds is not None
        assert creds.credentials_dir.exists()
        assert creds.key_file.exists()
        print("✅ Credentials manager initialized")
        print(f"   Directory: {creds.credentials_dir}")
        print(f"   Key file: {creds.key_file}")
        results.append(True)
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        results.append(False)
        return results
    
    # Test 3: API key storage
    print("\n[3/8] Testing API key storage...")
    try:
        test_key = "test_verification_key_12345"
        creds.set_api_key('test_service', test_key)
        retrieved = creds.get_api_key('test_service')
        assert retrieved == test_key
        print("✅ API key storage working")
        print(f"   Stored and retrieved key successfully")
        results.append(True)
    except Exception as e:
        print(f"❌ Storage failed: {e}")
        results.append(False)
    
    # Test 4: FRED API key
    print("\n[4/8] Checking FRED API key...")
    try:
        expected_fred_key = "b077ecbf05fa5f0a6407b38e22552c4e"
        
        # Try to retrieve existing key
        fred_key = creds.get_api_key('fred')
        
        if fred_key == expected_fred_key:
            print("✅ FRED API key is configured correctly")
            print(f"   Key preview: {fred_key[:10]}...{fred_key[-10:]}")
            results.append(True)
        elif fred_key is None:
            print("⚠️  FRED API key not configured yet")
            print("   Run: python quickstart_api_keys.py")
            results.append(False)
        else:
            print("⚠️  FRED API key found but doesn't match expected value")
            print(f"   Current: {fred_key[:10]}...{fred_key[-10:]}")
            print(f"   Expected: {expected_fred_key[:10]}...{expected_fred_key[-10:]}")
            results.append(False)
    except Exception as e:
        print(f"❌ FRED key check failed: {e}")
        results.append(False)
    
    # Test 5: Data loader integration
    print("\n[5/8] Testing data loader integration...")
    try:
        from modules.data_loader import load_fred_data, get_latest_value
        print("✅ Data loader imports successfully")
        print("   Functions: load_fred_data, get_latest_value")
        results.append(True)
    except Exception as e:
        print(f"❌ Data loader integration failed: {e}")
        results.append(False)
    
    # Test 6: File structure
    print("\n[6/8] Verifying file structure...")
    try:
        required_files = [
            'modules/auth/__init__.py',
            'modules/auth/credentials_manager.py',
            'pages/3_API_Key_Management.py',
            'tests/test_credentials_manager.py',
            'setup_credentials.py',
            'quickstart_api_keys.py',
            'FEATURE_API_KEY_MANAGEMENT.md',
            'IMPLEMENTATION_SUMMARY.md'
        ]
        
        all_exist = True
        for file in required_files:
            if os.path.exists(file):
                print(f"   ✓ {file}")
            else:
                print(f"   ✗ {file} (missing)")
                all_exist = False
        
        if all_exist:
            print("✅ All required files present")
            results.append(True)
        else:
            print("❌ Some files are missing")
            results.append(False)
    except Exception as e:
        print(f"❌ File structure check failed: {e}")
        results.append(False)
    
    # Test 7: Encryption verification
    print("\n[7/8] Testing encryption...")
    try:
        # Store a test key
        original_key = "encryption_test_secret_123"
        creds.set_api_key('encryption_test', original_key)
        
        # Read the encrypted file
        if creds.creds_file.exists():
            with open(creds.creds_file, 'rb') as f:
                encrypted_data = f.read()
            
            # Verify it's actually encrypted (should not contain plaintext)
            if original_key.encode() not in encrypted_data:
                print("✅ Encryption verified")
                print("   Keys are encrypted in storage")
                results.append(True)
            else:
                print("❌ Keys appear to be stored in plaintext!")
                results.append(False)
        else:
            print("⚠️  No credentials file found")
            results.append(False)
        
        # Clean up
        creds.delete_api_key('encryption_test')
        creds.delete_api_key('test_service')
    except Exception as e:
        print(f"❌ Encryption verification failed: {e}")
        results.append(False)
    
    # Test 8: Configuration
    print("\n[8/8] Checking configuration...")
    try:
        # Check requirements.txt
        with open('requirements.txt', 'r') as f:
            reqs = f.read()
            if 'cryptography' in reqs:
                print("✅ cryptography dependency in requirements.txt")
            else:
                print("❌ cryptography missing from requirements.txt")
                results.append(False)
                return results
        
        # Check .gitignore
        with open('.gitignore', 'r') as f:
            gitignore = f.read()
            if 'data/credentials/' in gitignore:
                print("✅ credentials directory in .gitignore")
            else:
                print("❌ credentials directory not in .gitignore")
                results.append(False)
                return results
        
        results.append(True)
    except Exception as e:
        print(f"❌ Configuration check failed: {e}")
        results.append(False)
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 70)
    
    total_tests = len(results)
    passed_tests = sum(results)
    failed_tests = total_tests - passed_tests
    
    print(f"\nTotal Tests: {total_tests}")
    print(f"Passed: {passed_tests} ✅")
    print(f"Failed: {failed_tests} ❌")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if all(results):
        print("\n🎉 ALL TESTS PASSED!")
        print("\n✅ The API Key Management feature is fully functional")
        print("\n📋 Next steps:")
        print("   1. Run: python quickstart_api_keys.py (if FRED key not configured)")
        print("   2. Run: streamlit run app.py")
        print("   3. Check the 'API Key Management' page")
        print("   4. Verify FRED API status in sidebar")
        return 0
    else:
        print("\n⚠️  SOME TESTS FAILED")
        print("\n🔧 Troubleshooting:")
        print("   1. Ensure all dependencies installed: pip install -r requirements.txt")
        print("   2. Run setup: python quickstart_api_keys.py")
        print("   3. Check file permissions on data/credentials/")
        print("   4. Review error messages above")
        return 1


if __name__ == "__main__":
    try:
        exit_code = verify_implementation()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nVerification cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
