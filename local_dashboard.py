"""
ATHENA-X LOCAL DASHBOARD
Fetches REAL data from Dhan API
"""

import os
import sys
import time
import json
import requests
from datetime import datetime
import traceback

# ============================================================
# CONFIGURATION - UPDATE THESE
# ============================================================

# Your Dhan credentials (get from Dhan Web → My Profile → DhanHQ APIs)
CLIENT_ID = "2608172958"  # Replace with your actual client ID
ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ..."  # Replace with your actual token

# ============================================================
# API ENDPOINTS
# ============================================================

BASE_URL = "https://api.dhan.co/v2"

def get_headers():
    return {
        "access-token": ACCESS_TOKEN,
        "client-id": CLIENT_ID,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

# ============================================================
# DATA FETCHING FUNCTIONS
# ============================================================

def get_real_balance():
    """Fetch real balance from Dhan API"""
    
    print("📡 Fetching real balance from Dhan...")
    
    try:
        response = requests.get(
            f"{BASE_URL}/fundlimit",
            headers=get_headers(),
            timeout=15
        )
        
        print(f"📡 API Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📡 Raw Response: {json.dumps(data, indent=2)}")
            
            # Try different possible keys
            balance = data.get('availabelBalance')
            if balance is None:
                balance = data.get('availableBalance')
            if balance is None:
                balance = data.get('available_balance')
            
            if balance is not None:
                balance = float(balance)
                print(f"✅ REAL BALANCE FOUND: ₹{balance:,.2f}")
                return balance
            
            # If balance is 0, try other fields
            sod_limit = data.get('sodLimit', 0)
            if sod_limit > 0:
                print(f"✅ Using SOD Limit: ₹{sod_limit:,.2f}")
                return float(sod_limit)
            
            withdrawable = data.get('withdrawableBalance', 0)
            if withdrawable > 0:
                print(f"✅ Using Withdrawable Balance: ₹{withdrawable:,.2f}")
                return float(withdrawable)
            
            print("⚠️ No balance field found in response")
            return None
            
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return None
            
    except Exception as e:
        print(f"❌ Error fetching balance: {e}")
        traceback.print_exc()
        return None

def get_real_positions():
    """Fetch real positions from Dhan API"""
    
    try:
        response = requests.get(
            f"{BASE_URL}/positions",
            headers=get_headers(),
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                positions = []
                for pos in data:
                    net_qty = pos.get('netQty', 0)
                    if net_qty != 0:
                        positions.append({
                            'symbol': pos.get('tradingSymbol', 'NIFTY'),
                            'option_type': pos.get('drvOptionType', ''),
                            'strike': pos.get('drvStrikePrice', 0),
                            'quantity': net_qty,
                            'buy_avg': float(pos.get('buyAvg', 0) or 0),
                            'ltp': float(pos.get('ltp', 0) or 0),
                            'unrealized_pnl': float(pos.get('unrealizedProfit', 0) or 0)
                        })
                return positions
        return []
    except Exception as e:
        print(f"⚠️ Error fetching positions: {e}")
        return []

def get_real_orders():
    """Fetch recent orders from Dhan API"""
    
    try:
        response = requests.get(
            f"{BASE_URL}/orders",
            headers=get_headers(),
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                trades = []
                for order in data[:5]:  # Last 5 orders
                    trades.append({
                        'time': order.get('createTime', ''),
                        'symbol': order.get('tradingSymbol', ''),
                        'option': f"{order.get('drvStrikePrice', '')}{order.get('drvOptionType', '')}",
                        'status': order.get('orderStatus', ''),
                        'quantity': order.get('filledQty', 0)
                    })
                return trades
        return []
    except Exception as e:
        print(f"⚠️ Error fetching orders: {e}")
        return []

# ============================================================
# DASHBOARD DISPLAY
# ============================================================

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def format_money(amount):
    return f"₹{amount:+,.2f}"

def print_dashboard(balance, positions, trades, last_update):
    """Display dashboard in terminal"""
    
    clear_screen()
    
    print("="*60)
    print("🚀 ATHENA-X REAL DASHBOARD")
    print("="*60)
    print(f"📅 {last_update.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📡 Data Source: LIVE DHAN API")
    print("="*60)
    
    # Balance Section
    if balance is not None and balance > 0:
        print("\n💰 ACCOUNT BALANCE:")
        print(f"  Available: {format_money(balance)}")
        print(f"  Status: ✅ LIVE")
    else:
        print("\n💰 ACCOUNT BALANCE:")
        print(f"  ⚠️ Balance not available (fallback: ₹500,000)")
        print(f"  Status: ⚠️ Using FALLBACK")
    
    print("\n📊 ACTIVE POSITIONS:")
    if positions:
        for pos in positions:
            pnl_color = "\033[92m" if pos['unrealized_pnl'] >= 0 else "\033[91m"
            print(f"  {pos['symbol']} {pos['option_type']}{pos['strike']} | "
                  f"Qty: {pos['quantity']} | "
                  f"P&L: {pnl_color}{format_money(pos['unrealized_pnl'])}\033[0m")
    else:
        print("  No active positions")
    
    print("\n📋 RECENT ORDERS:")
    if trades:
        for trade in trades:
            print(f"  {trade['time']} | {trade['symbol']} | {trade['option']} | "
                  f"Status: {trade['status']}")
    else:
        print("  No recent orders")
    
    print("\n" + "="*60)
    print("🔄 Refreshing in 10 seconds... (Press Ctrl+C to exit)")
    print("="*60)

# ============================================================
# MAIN FUNCTION
# ============================================================

def main():
    print("="*60)
    print("🚀 ATHENA-X REAL DASHBOARD")
    print("="*60)
    print("📡 Fetching REAL data from Dhan API...")
    print("="*60)
    print(f"Client ID: {CLIENT_ID}")
    print(f"Token: {ACCESS_TOKEN[:20]}...")
    print("="*60)
    print()
    
    # Test the token first
    print("🔍 Testing API connection...")
    test_balance = get_real_balance()
    
    if test_balance is None:
        print("\n⚠️ WARNING: Could not fetch real balance!")
        print("💡 Possible issues:")
        print("   1. Access Token is expired - generate a new one")
        print("   2. Client ID is incorrect")
        print("   3. Internet connection issue")
        print("\n⏳ Using fallback balance: ₹500,000")
        print("="*60)
    else:
        print(f"✅ Connection successful! Real balance: ₹{test_balance:,.2f}")
        print("="*60)
    
    input("\nPress Enter to start dashboard...")
    
    try:
        iteration = 0
        while True:
            iteration += 1
            
            # Fetch real data
            balance = get_real_balance()
            positions = get_real_positions()
            trades = get_real_orders()
            
            # Display dashboard
            print_dashboard(balance, positions, trades, datetime.now())
            
            # Wait before next refresh
            time.sleep(10)
            
    except KeyboardInterrupt:
        print("\n\n👋 Dashboard stopped")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        traceback.print_exc()
        sys.exit(1)

# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()