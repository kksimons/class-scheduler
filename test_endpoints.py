#!/usr/bin/env python3
"""
Simple test script to verify the new dataset endpoints are working
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:8502"
API_KEY = "wI150Tb-MMhFnMRRQyB0RV0HJGaK57KkzgNCM8ep6Pk"

# Test dataset
test_dataset = {
    "program": "Test Program",
    "term": "Winter 2024",
    "courses": [
        {
            "course": "TEST 101",
            "sections": [
                {
                    "professor": "Dr. Test",
                    "day1": {
                        "day": "M",
                        "start": "09:00",
                        "end": "10:30",
                        "format": "in-person"
                    },
                    "day2": {
                        "day": "W",
                        "start": "09:00", 
                        "end": "10:30",
                        "format": "in-person"
                    }
                }
            ]
        }
    ]
}

def test_endpoints():
    print("🧪 Testing class-scheduler dataset endpoints...")
    
    # Headers for portfolio authentication (you'll need to implement the auth token generation)
    headers = {
        "Content-Type": "application/json",
        # Note: You'll need to implement proper portfolio auth headers here
        # "X-Portfolio-Auth": "...",
        # "X-Portfolio-Hash": "...", 
        # "X-Portfolio-Timestamp": "..."
    }
    
    print("📝 Test configuration:")
    print(f"   Base URL: {BASE_URL}")
    print(f"   API Key: {API_KEY[:8]}...")
    print()
    
    # Test 1: List datasets (GET)
    print("1️⃣ Testing GET /api/datasets...")
    try:
        response = requests.get(f"{BASE_URL}/api/datasets", headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ GET datasets endpoint working")
        else:
            print(f"   ❌ GET failed: {response.text}")
    except Exception as e:
        print(f"   ❌ GET error: {e}")
    print()
    
    # Test 2: Create dataset (POST)
    print("2️⃣ Testing POST /api/datasets...")
    try:
        payload = {
            "action": "create",
            "dataset": test_dataset
        }
        response = requests.post(f"{BASE_URL}/api/datasets", 
                               json=payload, headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            dataset_id = result.get('datasetId')
            print(f"   ✅ POST datasets endpoint working")
            print(f"   📄 Created dataset ID: {dataset_id}")
            return dataset_id
        else:
            print(f"   ❌ POST failed: {response.text}")
    except Exception as e:
        print(f"   ❌ POST error: {e}")
    print()
    
    return None

if __name__ == "__main__":
    test_endpoints()