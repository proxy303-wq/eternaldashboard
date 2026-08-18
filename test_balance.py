# test_balance.py
"""Quick test to check your REAL balance"""

import requests

CLIENT_ID = "2608172958"  # Your actual client ID
ACCESS_TOKEN = "your_token_here"  # Your actual token

headers = {
    "access-token": ACCESS_TOKEN,
    "client-id": CLIENT_ID,
    "Content-Type": "application/json"
}

print("="*60)
print("🔍 CHECKING REAL DHAN BALANCE")
print("="*60)

try:
    response = requests.get(
        "https://api.dhan.co/v2/fundlimit",
        headers=headers,
        timeout=10
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("\n📊 FUND DATA:")
        for key, value in data.items():
            print(f"  {key}: {value}")
        
        print("\n" + "="*60)
        balance = data.get('availabelBalance')
        if balance:
            print(f"💰 YOUR REAL BALANCE: ₹{float(balance):,.2f}")
        else:
            print("⚠️ No 'availabelBalance' field found")
    else:
        print(f"❌ Error: {response.text}")
        
except Exception as e:
    print(f"❌ Error: {e}")

print("="*60)