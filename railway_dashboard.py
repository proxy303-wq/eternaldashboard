# terminal_dashboard.py
"""Athena-X Terminal Dashboard - No Flask needed"""

import os
import time
from datetime import datetime

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def format_money(amount):
    return f"₹{amount:+,.2f}"

def print_dashboard():
    """Display performance dashboard"""
    clear_screen()
    
    # Sample data - replace with your actual data
    capital = 500000
    today_pnl = 2350
    month_pnl = 45200
    year_pnl = 285000
    wins = 28
    losses = 11
    total = wins + losses
    win_rate = (wins / total * 100) if total > 0 else 0
    
    print("="*60)
    print("🚀 ATHENA-X PERFORMANCE DASHBOARD")
    print("="*60)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    print("\n💰 CAPITAL:")
    print(f"  Balance: ₹{capital:,.2f}")
    
    print("\n📈 P&L:")
    pnl_color = "\033[92m" if today_pnl >= 0 else "\033[91m"
    print(f"  Today: {pnl_color}₹{today_pnl:+,.2f}\033[0m")
    month_color = "\033[93m" if month_pnl >= 0 else "\033[91m"
    print(f"  Month: {month_color}₹{month_pnl:+,.2f}\033[0m")
    print(f"  Year: ₹{year_pnl:+,.2f}")
    
    print("\n📊 PERFORMANCE:")
    win_color = "\033[92m" if win_rate >= 60 else "\033[91m"
    print(f"  Win Rate: {win_color}{win_rate:.1f}%\033[0m")
    print(f"  Wins: {wins}W / {losses}L")
    print(f"  Total Trades: {total}")
    
    print("\n🎯 TARGETS:")
    print(f"  Monthly Target: ₹62,500")
    progress = (month_pnl / 62500) * 100
    print(f"  Progress: {progress:.1f}%")
    
    # Progress bar
    bar_length = 30
    filled = int(bar_length * min(progress/100, 1))
    bar = "█" * filled + "░" * (bar_length - filled)
    print(f"  [{bar}]")
    
    print("\n" + "="*60)
    print("🔄 Refreshing in 5 seconds... (Press Ctrl+C to exit)")
    print("="*60)

def main():
    try:
        while True:
            print_dashboard()
            time.sleep(5)
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")

if __name__ == "__main__":
    main()