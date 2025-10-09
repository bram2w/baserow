"""
Test field-level permissions (column visibility)
"""

import requests
import json

BASE_URL = "http://localhost/api"
TOKEN = "test_user_token_123456"
TABLE_ID = 738

def test_field_permissions():
    """Test that field permissions hide columns correctly."""
    
    # Get fields list
    print(f"📊 Getting fields from table {TABLE_ID} as test@test.com...\n")
    
    headers = {
        "Authorization": f"Token {TOKEN}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(
        f"{BASE_URL}/database/fields/table/{TABLE_ID}/",
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"❌ Get fields failed: {response.status_code}")
        print(response.text)
        return
    
    print("✅ Response received!")
    fields = response.json()
    
    print(f"Total fields visible: {len(fields)}\n")
    print("Fields:")
    for field in fields:
        print(f"  - {field['name']} (ID: {field['id']}, Type: {field['type']})")
    
    # Check which fields should be hidden
    print("\n" + "="*80)
    print("📋 Expected behavior:")
    print("  - User test@test.com should have some fields hidden")
    print("  - Check UserFieldPermission table for configured permissions")
    print("="*80)

if __name__ == "__main__":
    test_field_permissions()
