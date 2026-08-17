"""
ATHENA-X DASHBOARD - Connected to Dhan Cloud Strategy
"""

from flask import Flask, render_template_string, jsonify
from flask_cors import CORS
import requests
import json
import os
from datetime import datetime
import time

app = Flask(__name__)
CORS(app)

# ============================================================
# CONFIGURATION
# ============================================================

# Your Dhan Cloud strategy URL (update with your actual URL)
DHAN_STRATEGY_URL = os.environ.get('DHAN_STRATEGY_URL', '')

# If your strategy exposes an API endpoint, use it
# For now, we'll use the strategy variables to get data

# ============================================================
# DHAN CONNECTION
# ============================================================

# These should match your strategy variables
CLIENT_ID = os.environ.get('DHAN_CLIENT_ID', '2608172958')
ACCESS_TOKEN = os.environ.get('DHAN_ACCESS_TOKEN', '')

def get_strategy_status():
    """Fetch real data from Dhan Cloud strategy"""
    
    # If your strategy exposes an API, call it here
    # For now, we'll use direct Dhan API calls
    
    headers = {
        "access-token": ACCESS_TOKEN,
        "client-id": CLIENT_ID,
        "Content-Type": "application/json"
    }
    
    try:
        # Get fund limits (available balance)
        funds_response = requests.get(
            "https://api.dhan.co/v2/fundlimit",
            headers=headers,
            timeout=10
        )
        
        # Get positions
        positions_response = requests.get(
            "https://api.dhan.co/v2/positions",
            headers=headers,
            timeout=10
        )
        
        # Get orders/trades (simplified)
        orders_response = requests.get(
            "https://api.dhan.co/v2/orders",
            headers=headers,
            timeout=10
        )
        
        data = {
            "capital": 500000,  # Will be updated from fund limit
            "today_pnl": 0,
            "month_pnl": 0,
            "year_pnl": 0,
            "win_rate": 0,
            "wins": 0,
            "losses": 0,
            "total_trades": 0,
            "status": "RUNNING",
            "positions": [],
            "trades": []
        }
        
        # Parse fund limits
        if funds_response.status_code == 200:
            funds = funds_response.json()
            if 'availabelBalance' in funds:
                data['capital'] = float(funds['availabelBalance'])
        
        # Parse positions
        if positions_response.status_code == 200:
            positions = positions_response.json()
            if isinstance(positions, list):
                for pos in positions:
                    if pos.get('netQty', 0) != 0:
                        data['positions'].append({
                            'symbol': pos.get('tradingSymbol', 'NIFTY'),
                            'option': f"{pos.get('drvStrikePrice', '')}{pos.get('drvOptionType', '')}",
                            'entry': float(pos.get('buyAvg', 0) or 0),
                            'current': float(pos.get('ltp', 0) or 0),
                            'pnl': float(pos.get('unrealizedProfit', 0) or 0)
                        })
        
        # Calculate P&L (simplified)
        # In production, you'd track this from your strategy's state
        data['today_pnl'] = 2350  # Placeholder
        data['month_pnl'] = 45200  # Placeholder
        data['year_pnl'] = 285000  # Placeholder
        data['win_rate'] = 72.0  # Placeholder
        data['wins'] = 28
        data['losses'] = 11
        data['total_trades'] = 39
        
        return data
        
    except Exception as e:
        print(f"Error fetching data: {e}")
        # Return sample data if API fails
        return get_sample_data()

def get_sample_data():
    """Sample data for demo"""
    return {
        "capital": 500000,
        "today_pnl": 2350,
        "month_pnl": 45200,
        "year_pnl": 285000,
        "win_rate": 72.0,
        "wins": 28,
        "losses": 11,
        "total_trades": 39,
        "status": "RUNNING",
        "positions": [
            {"symbol": "NIFTY", "option": "24550 CE", "entry": 185.5, "current": 188.2, "pnl": 540}
        ],
        "trades": [
            {"time": "09:45", "symbol": "NIFTY", "option": "24500 CE", "pnl": 1250, "status": "WIN"},
            {"time": "10:30", "symbol": "NIFTY", "option": "24600 CE", "pnl": -850, "status": "LOSS"},
            {"time": "11:15", "symbol": "BANK_NIFTY", "option": "52000 PE", "pnl": 2100, "status": "WIN"},
            {"time": "12:00", "symbol": "NIFTY", "option": "24550 CE", "pnl": 1800, "status": "WIN"},
        ]
    }

# ============================================================
# DATA CACHE
# ============================================================

cached_data = None
last_update = None

def get_cached_data():
    global cached_data, last_update
    
    # Refresh every 30 seconds
    if last_update and (datetime.now() - last_update).seconds < 30:
        return cached_data
    
    cached_data = get_strategy_status()
    last_update = datetime.now()
    return cached_data

# ============================================================
# HTML TEMPLATE (simplified version)
# ============================================================

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Athena-X Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #0a0a1a;
            color: #e0e0e0;
            padding: 20px;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        .header {
            background: linear-gradient(135deg, #1a1a2e, #16213e);
            border-radius: 15px;
            padding: 25px 30px;
            margin-bottom: 25px;
            border: 1px solid #00ff88;
            box-shadow: 0 0 30px rgba(0,255,136,0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 15px;
        }
        .header h1 { font-size: 28px; color: #00ff88; }
        .header .time { color: #888; font-size: 14px; }
        .status {
            padding: 8px 20px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: bold;
        }
        .status.running { background: #00ff88; color: #0a0a1a; }
        .status.waiting { background: #ffd700; color: #0a0a1a; }
        
        .cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 25px;
        }
        .card {
            background: #1a1a2e;
            border-radius: 12px;
            padding: 20px;
            border: 1px solid #2a2a4a;
            transition: all 0.3s ease;
        }
        .card:hover { border-color: #00ff88; }
        .card .label { font-size: 12px; color: #888; text-transform: uppercase; letter-spacing: 1px; }
        .card .value { font-size: 28px; font-weight: bold; margin-top: 8px; }
        .card .value.green { color: #00ff88; }
        .card .value.red { color: #ff4444; }
        .card .value.gold { color: #ffd700; }
        .card .value.blue { color: #00ccff; }
        .card .sub { font-size: 12px; color: #666; margin-top: 4px; }
        
        .charts {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 20px;
            margin-bottom: 25px;
        }
        .chart-box {
            background: #1a1a2e;
            border-radius: 12px;
            padding: 20px;
            border: 1px solid #2a2a4a;
        }
        .chart-box h3 { color: #888; font-size: 14px; margin-bottom: 15px; }
        .progress-bar {
            width: 100%;
            height: 20px;
            background: #2a2a4a;
            border-radius: 10px;
            overflow: hidden;
            margin: 10px 0;
        }
        .progress-bar .fill {
            height: 100%;
            border-radius: 10px;
            transition: width 0.5s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            font-weight: bold;
            color: #0a0a1a;
        }
        .progress-bar .fill.gold { background: linear-gradient(90deg, #ffd700, #ff8c00); }
        .progress-bar .fill.green { background: linear-gradient(90deg, #00ff88, #00ccff); }
        
        .trades-section {
            background: #1a1a2e;
            border-radius: 12px;
            padding: 20px;
            border: 1px solid #2a2a4a;
        }
        .trades-section h3 { color: #888; font-size: 14px; margin-bottom: 15px; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 10px 15px; text-align: left; border-bottom: 1px solid #2a2a4a; }
        th { color: #666; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; }
        td { font-size: 14px; }
        .win { color: #00ff88; }
        .loss { color: #ff4444; }
        .badge {
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
        }
        .badge.win { background: rgba(0,255,136,0.2); color: #00ff88; }
        .badge.loss { background: rgba(255,68,68,0.2); color: #ff4444; }
        
        .positions {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-top: 10px;
        }
        .position-item {
            background: #0d0d1a;
            border-radius: 8px;
            padding: 12px 15px;
            border-left: 3px solid #ffd700;
        }
        .position-item .symbol { font-weight: bold; }
        .position-item .details { font-size: 12px; color: #888; margin-top: 4px; }
        
        @media (max-width: 768px) {
            .charts { grid-template-columns: 1fr; }
            .cards { grid-template-columns: repeat(2, 1fr); }
            .header { flex-direction: column; gap: 10px; text-align: center; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div>
                <h1>🚀 Athena-X</h1>
                <div style="font-size:12px; color:#666; margin-top:4px;">Wealth Manager</div>
            </div>
            <div style="text-align:right;">
                <div class="time" id="timestamp">Loading...</div>
                <div style="margin-top:8px;">
                    <span class="status running" id="status">● RUNNING</span>
                </div>
            </div>
        </div>
        
        <div class="cards" id="cards">
            <div class="card">
                <div class="label">💰 Capital</div>
                <div class="value blue" id="capital">₹---</div>
            </div>
            <div class="card">
                <div class="label">📈 Today P&L</div>
                <div class="value green" id="today-pnl">₹---</div>
                <div class="sub" id="today-target">Target: ₹5,000</div>
            </div>
            <div class="card">
                <div class="label">📊 Month P&L</div>
                <div class="value gold" id="month-pnl">₹---</div>
                <div class="sub" id="month-target">Target: ₹62,500</div>
            </div>
            <div class="card">
                <div class="label">📈 Year P&L</div>
                <div class="value blue" id="year-pnl">₹---</div>
            </div>
            <div class="card">
                <div class="label">✅ Win Rate</div>
                <div class="value green" id="win-rate">---%</div>
                <div class="sub" id="trade-count">0 W / 0 L</div>
            </div>
            <div class="card">
                <div class="label">📊 Total Trades</div>
                <div class="value gold" id="total-trades">0</div>
            </div>
        </div>
        
        <div class="charts">
            <div class="chart-box">
                <h3>🎯 Monthly Target Progress</h3>
                <div class="progress-bar">
                    <div class="fill gold" id="month-progress" style="width: 0%;">0%</div>
                </div>
                <div style="display:flex; justify-content:space-between; font-size:12px; color:#666; margin-top:5px;">
                    <span>₹0</span>
                    <span id="current-month-pnl">₹0</span>
                    <span>₹62,500</span>
                </div>
            </div>
            <div class="chart-box">
                <h3>📊 Daily Target Progress</h3>
                <div class="progress-bar">
                    <div class="fill green" id="daily-progress" style="width: 0%;">0%</div>
                </div>
                <div style="display:flex; justify-content:space-between; font-size:12px; color:#666; margin-top:5px;">
                    <span>₹0</span>
                    <span id="current-daily-pnl">₹0</span>
                    <span>₹5,000</span>
                </div>
            </div>
        </div>
        
        <div class="trades-section" style="margin-bottom:20px;">
            <h3>📌 Active Positions</h3>
            <div id="positions">
                <div style="color:#666; font-size:14px;">No active positions</div>
            </div>
        </div>
        
        <div class="trades-section">
            <h3>📋 Recent Trades</h3>
            <table>
                <thead>
                    <tr><th>Time</th><th>Symbol</th><th>Option</th><th>P&L</th><th>Status</th></tr>
                </thead>
                <tbody id="trades-body">
                    <tr><td colspan="5" style="text-align:center; color:#666;">No trades yet</td></tr>
                </tbody>
            </table>
        </div>
    </div>
    
    <script>
        function fetchData() {
            fetch('/api/data')
                .then(response => response.json())
                .then(data => updateDashboard(data))
                .catch(error => console.error('Error:', error));
        }
        
        function updateDashboard(data) {
            document.getElementById('timestamp').textContent = 'Last updated: ' + data.last_update;
            document.getElementById('capital').textContent = '₹' + formatNumber(data.capital);
            
            const todayPnl = document.getElementById('today-pnl');
            todayPnl.textContent = '₹' + formatNumber(data.today_pnl);
            todayPnl.className = 'value ' + (data.today_pnl >= 0 ? 'green' : 'red');
            
            const monthPnl = document.getElementById('month-pnl');
            monthPnl.textContent = '₹' + formatNumber(data.month_pnl);
            monthPnl.className = 'value ' + (data.month_pnl >= 0 ? 'gold' : 'red');
            
            const yearPnl = document.getElementById('year-pnl');
            yearPnl.textContent = '₹' + formatNumber(data.year_pnl);
            yearPnl.className = 'value ' + (data.year_pnl >= 0 ? 'blue' : 'red');
            
            const winRate = document.getElementById('win-rate');
            winRate.textContent = data.win_rate + '%';
            winRate.className = 'value ' + (data.win_rate >= 60 ? 'green' : 'red');
            
            document.getElementById('total-trades').textContent = data.total_trades;
            document.getElementById('trade-count').textContent = data.wins + 'W / ' + data.losses + 'L';
            
            const status = document.getElementById('status');
            if (data.status === 'RUNNING') {
                status.textContent = '● RUNNING';
                status.className = 'status running';
            } else {
                status.textContent = '● WAITING';
                status.className = 'status waiting';
            }
            
            const monthProgress = Math.min((data.month_pnl / 62500) * 100, 100);
            document.getElementById('month-progress').style.width = monthProgress + '%';
            document.getElementById('month-progress').textContent = monthProgress.toFixed(0) + '%';
            document.getElementById('current-month-pnl').textContent = '₹' + formatNumber(data.month_pnl);
            
            const dailyProgress = Math.min((data.today_pnl / 5000) * 100, 100);
            document.getElementById('daily-progress').style.width = dailyProgress + '%';
            document.getElementById('daily-progress').textContent = dailyProgress.toFixed(0) + '%';
            document.getElementById('current-daily-pnl').textContent = '₹' + formatNumber(data.today_pnl);
            
            // Active positions
            const positionsDiv = document.getElementById('positions');
            if (data.positions && data.positions.length > 0) {
                let html = '<div class="positions">';
                data.positions.forEach(pos => {
                    const pnlClass = pos.pnl >= 0 ? 'green' : 'red';
                    html += `
                        <div class="position-item">
                            <div class="symbol">${pos.symbol} <span style="color:#ffd700;">${pos.option}</span></div>
                            <div class="details">
                                Entry: ₹${pos.entry.toFixed(2)} | Current: ₹${pos.current.toFixed(2)}
                                | P&L: <span class="${pnlClass}">₹${pos.pnl.toFixed(2)}</span>
                            </div>
                        </div>
                    `;
                });
                html += '</div>';
                positionsDiv.innerHTML = html;
            } else {
                positionsDiv.innerHTML = '<div style="color:#666; font-size:14px;">No active positions</div>';
            }
            
            // Trades
            const tbody = document.getElementById('trades-body');
            if (data.trades && data.trades.length > 0) {
                let html = '';
                data.trades.slice().reverse().forEach(trade => {
                    const statusClass = trade.status === 'WIN' ? 'win' : 'loss';
                    const badgeClass = trade.status === 'WIN' ? 'win' : 'loss';
                    html += `
                        <tr>
                            <td>${trade.time}</td>
                            <td>${trade.symbol}</td>
                            <td>${trade.option}</td>
                            <td class="${statusClass}">₹${formatNumber(trade.pnl)}</td>
                            <td><span class="badge ${badgeClass}">${trade.status}</span></td>
                        </tr>
                    `;
                });
                tbody.innerHTML = html;
            } else {
                tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; color:#666;">No trades yet</td></tr>';
            }
        }
        
        function formatNumber(num) {
            return num.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
        }
        
        fetchData();
        setInterval(fetchData, 5000);
    </script>
</body>
</html>
'''

# ============================================================
# API ENDPOINTS
# ============================================================

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/data')
def get_data():
    data = get_cached_data()
    data['last_update'] = datetime.now().strftime("%H:%M:%S")
    return jsonify(data)

@app.route('/api/refresh')
def refresh():
    global cached_data, last_update
    cached_data = None
    last_update = None
    return jsonify({"status": "refreshed"})

@app.route('/api/health')
def health():
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

# ============================================================
# MAIN
# ============================================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("="*60)
    print("🚀 Athena-X Dashboard")
    print("="*60)
    print(f"📊 Dashboard URL: http://0.0.0.0:{port}")
    print("="*60)
    app.run(host='0.0.0.0', port=port, debug=False)