#!/usr/bin/env python3
"""
Quick auth test script to debug login issues
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """Test if backend is running"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"✅ Backend health: {response.status_code} - {response.json()}")
        return True
    except Exception as e:
        print(f"❌ Backend not running: {e}")
        return False

def test_google_auth(google_token):
    """Test Google auth endpoint"""
    try:
        response = requests.post(
            f"{BASE_URL}/auth/google",
            json={"token": google_token},
            headers={"Content-Type": "application/json"}
        )
        print(f"\n🔍 Google Auth Response:")
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Login successful!")
            print(f"Access token: {data.get('access_token', 'MISSING')[:50]}...")
            print(f"User: {data.get('user', {}).get('email', 'MISSING')}")
            return data.get('access_token')
        else:
            print(f"❌ Login failed: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Auth request failed: {e}")
        return None

def test_protected_endpoint(access_token):
    """Test a protected endpoint with the token"""
    try:
        response = requests.get(
            f"{BASE_URL}/auth/user",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        print(f"\n🔍 Protected Endpoint Test:")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            user = response.json()
            print(f"✅ Token valid! User: {user.get('email')}")
        else:
            print(f"❌ Token invalid: {response.text}")
    except Exception as e:
        print(f"❌ Protected request failed: {e}")

if __name__ == "__main__":
    print("🚀 Testing Auth Flow...\n")
    
    # Test 1: Backend health
    if not test_health():
        exit(1)
    
    # Test 2: Google auth (you'll need to replace with a real token)
    print("\n" + "="*50)
    print("📝 To test Google auth, you need a real Google access token.")
    print("Get one from: https://developers.google.com/oauthplayground")
    print("Or check your browser's network tab when logging in.")
    print("="*50)
    
    google_token = input("\nPaste your Google access token (or press Enter to skip): ").strip()
    
    if google_token:
        access_token = test_google_auth(google_token)
        if access_token:
            test_protected_endpoint(access_token)
    else:
        print("⏭️  Skipping Google auth test")
    
    print("\n✅ Auth debugging complete!") 