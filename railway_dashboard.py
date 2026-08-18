"""
ATHENA-X COMPLETE DASHBOARD
Connects to Dhan API + Strategy Logs
"""

from flask import Flask, render_template_string, jsonify, request
from flask_cors import CORS
import requests
import json
import os
from datetime import datetime, timedelta
import time

app = Flask(__name__)
CORS(app)

# ============================================================
# CONFIGURATION
# ============================================================

CLIENT_ID = os.environ.get('DHAN_CLIENT_ID', '2608172958')
ACCESS_TOKEN = os.environ.get('DHAN_ACCESS_TOKEN', '')
DHAN_API = "https://api.dhan.co/v2"

# ============================================================
# REAL DATA FETCHER
# ============================================================

def get_real_data():
    """Fetch real data from Dhan API"""
    
    headers = {
        "access-token": ACCESS_TOKEN,
        "client-id": CLIENT_ID,
        "Content-Type": "application/json"
    }
    
    data = {
        "balance": 0,
        "today_pnl": 0,
        "month_pnl": 0,
        "year_pnl": 0,
        "win_rate": 0,
        "wins": 0,
        "losses": 0,
        "total_trades": 0,
        "status": "WAITING",
        "positions": [],
        "trades": [],
        "capital": 0,
        "nifty_ltp": 0,
        "pcr": 0,
        "max_pain": 0
    }
    
    try:
        # 1. Get Balance
        funds = requests.get(f"{DHAN_API}/fundlimit", headers=headers, timeout=10)
        if funds.status_code == 200:
            fund_data = funds.json()
            if 'data' in fund_data:
                balance = float(fund_data['data'].get('availabelBalance', 0))
                data['balance'] = balance
                data['capital'] = balance
                data['status'] = "RUNNING"
        
        # 2. Get Positions
        positions = requests.get(f"{DHAN_API}/positions", headers=headers, timeout=10)
        if positions.status_code == 200:
            pos_data = positions.json()
            if isinstance(pos_data, list):
                for pos in pos_data:
                    if pos.get('netQty', 0) != 0:
                        data['positions'].append({
                            'symbol': pos.get('tradingSymbol', 'NIFTY'),
                            'option': f"{pos.get('drvStrikePrice', '')}{pos.get('drvOptionType', '')}",
                            'entry': float(pos.get('buyAvg', 0) or 0),
                            'current': float(pos.get('ltp', 0) or 0),
                            'pnl': float(pos.get('unrealizedProfit', 0) or 0),
                            'qty': int(pos.get('netQty', 0))
                        })
        
        # 3. Get Orders (for trade history)
        orders = requests.get(f"{DHAN_API}/orders", headers=headers, timeout=10)
        if orders.status_code == 200:
            order_data = orders.json()
            if isinstance(order_data, list):
                for order in order_data[:20]:
                    if order.get('orderStatus') == 'TRADED':
                        entry_price = float(order.get('price', 0))
                        exit_price = float(order.get('averageTradedPrice', 0))
                        qty = int(order.get('filledQty', 0))
                        pnl = (exit_price - entry_price) * qty
                        data['trades'].append({
                            'time': order.get('createTime', '')[:5],
                            'symbol': order.get('tradingSymbol', 'NIFTY'),
                            'option': f"{order.get('drvStrikePrice', '')}{order.get('drvOptionType', '')}",
                            'pnl': pnl,
                            'status': 'WIN' if pnl > 0 else 'LOSS'
                        })
        
        # 4. Get NIFTY LTP
        nifty = requests.get(
            f"{DHAN_API}/market/quote/26000",
            headers=headers,
            timeout=10
        )
        if nifty.status_code == 200:
            nifty_data = nifty.json()
            data['nifty_ltp'] = float(nifty_data.get('ltp', 0))
        
        # 5. Calculate metrics
        total_trades = len(data['trades'])
        if total_trades > 0:
            data['wins'] = sum(1 for t in data['trades'] if t['status'] == 'WIN')
            data['losses'] = total_trades - data['wins']
            data['win_rate'] = (data['wins'] / total_trades) * 100
            data['total_trades'] = total_trades
            data['today_pnl'] = sum(t['pnl'] for t in data['trades'])
            data['month_pnl'] = data['today_pnl']
            data['year_pnl'] = data['today_pnl']
        
    except Exception as e:
        print(f"⚠️ Error: {e}")
    
    return data

# ============================================================
# HTML TEMPLATE - FULL FEATURED
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
        .header h1 span { color: #ffd700; font-size: 14px; }
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
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
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
        .card:hover { border-color: #00ff88; transform: translateY(-2px); }
        .card .label { font-size: 11px; color: #888; text-transform: uppercase; letter-spacing: 1px; }
        .card .value { font-size: 24px; font-weight: bold; margin-top: 8px; }
        .card .value.green { color: #00ff88; }
        .card .value.red { color: #ff4444; }
        .card .value.gold { color: #ffd700; }
        .card .value.blue { color: #00ccff; }
        .card .sub { font-size: 11px; color: #666; margin-top: 4px; }
        
        .charts {
            display: grid;
            grid-template-columns: 1fr 1fr;
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
            font-size: 11px;
            font-weight: bold;
            color: #0a0a1a;
        }
        .progress-bar .fill.gold { background: linear-gradient(90deg, #ffd700, #ff8c00); }
        .progress-bar .fill.green { background: linear-gradient(90deg, #00ff88, #00ccff); }
        
        .market-data {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 15px;
            margin-bottom: 25px;
        }
        .market-card {
            background: #1a1a2e;
            border-radius: 12px;
            padding: 15px 20px;
            border: 1px solid #2a2a4a;
            text-align: center;
        }
        .market-card .label { font-size: 11px; color: #888; }
        .market-card .value { font-size: 20px; font-weight: bold; margin-top: 5px; }
        .market-card .value.green { color: #00ff88; }
        .market-card .value.red { color: #ff4444; }
        
        .trades-section {
            background: #1a1a2e;
            border-radius: 12px;
            padding: 20px;
            border: 1px solid #2a2a4a;
        }
        .trades-section h3 { color: #888; font-size: 14px; margin-bottom: 15px; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 8px 12px; text-align: left; border-bottom: 1px solid #2a2a4a; }
        th { color: #666; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; }
        td { font-size: 13px; }
        .win { color: #00ff88; }
        .loss { color: #ff4444; }
        .badge {
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: bold;
        }
        .badge.win { background: rgba(0,255,136,0.2); color: #00ff88; }
        .badge.loss { background: rgba(255,68,68,0.2); color: #ff4444; }
        
        .positions {
            display: grid;
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
            .market-data { grid-template-columns: 1fr; }
            .cards { grid-template-columns: repeat(2, 1fr); }
            .header { flex-direction: column; gap: 10px; text-align: center; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div>
                <h1>🚀 Athena-X <span>Wealth Manager</span></h1>
            </div>
            <div style="text-align:right;">
                <div class="time" id="timestamp">Loading...</div>
                <div style="margin-top:8px;">
                    <span class="status running" id="status">● RUNNING</span>
                </div>
            </div>
        </div>
        
        <!-- Market Data -->
        <div class="market-data">
            <div class="market-card">
                <div class="label">🇮🇳 NIFTY</div>
                <div class="value" id="nifty-price">---</div>
            </div>
            <div class="market-card">
                <div class="label">📊 PCR</div>
                <div class="value" id="pcr">---</div>
            </div>
            <div class="market-card">
                <div class="label">💰 Balance</div>
                <div class="value blue" id="balance">₹---</div>
            </div>
        </div>
        
        <!-- Cards -->
        <div class="cards" id="cards">
            <div class="card">
                <div class="label">📈 Today P&L</div>
                <div class="value green" id="today-pnl">₹0</div>
            </div>
            <div class="card">
                <div class="label">📊 Month P&L</div>
                <div class="value gold" id="month-pnl">₹0</div>
            </div>
            <div class="card">
                <div class="label">✅ Win Rate</div>
                <div class="value green" id="win-rate">0%</div>
                <div class="sub" id="trade-count">0W / 0L</div>
            </div>
            <div class="card">
                <div class="label">📊 Total Trades</div>
                <div class="value gold" id="total-trades">0</div>
            </div>
        </div>
        
        <!-- Charts -->
        <div class="charts">
            <div class="chart-box">
                <h3>🎯 Monthly Progress</h3>
                <div class="progress-bar">
                    <div class="fill gold" id="month-progress" style="width: 0%;">0%</div>
                </div>
                <div style="display:flex; justify-content:space-between; font-size:12px; color:#666;">
                    <span>₹0</span>
                    <span id="current-month-pnl">₹0</span>
                    <span>₹62,500</span>
                </div>
            </div>
            <div class="chart-box">
                <h3>📊 Daily Progress</h3>
                <div class="progress-bar">
                    <div class="fill green" id="daily-progress" style="width: 0%;">0%</div>
                </div>
                <div style="display:flex; justify-content:space-between; font-size:12px; color:#666;">
                    <span>₹0</span>
                    <span id="current-daily-pnl">₹0</span>
                    <span>₹5,000</span>
                </div>
            </div>
        </div>
        
        <!-- Positions -->
        <div class="trades-section" style="margin-bottom:20px;">
            <h3>📌 Active Positions</h3>
            <div id="positions">
                <div style="color:#666; font-size:14px; text-align:center; padding:20px;">No active positions</div>
            </div>
        </div>
        
        <!-- Trades -->
        <div class="trades-section">
            <h3>📋 Recent Trades</h3>
            <table>
                <thead>
                    <tr><th>Time</th><th>Symbol</th><th>Option</th><th>P&L</th><th>Status</th></tr>
                </thead>
                <tbody id="trades-body">
                    <tr><td colspan="5" style="text-align:center; color:#666; padding:20px;">No trades yet</td></tr>
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
            document.getElementById('timestamp').textContent = '🔄 ' + data.last_update;
            
            // Market Data
            document.getElementById('nifty-price').textContent = data.nifty_ltp ? '₹' + data.nifty_ltp.toFixed(2) : '---';
            document.getElementById('pcr').textContent = data.pcr ? data.pcr.toFixed(2) : '---';
            document.getElementById('balance').textContent = '₹' + formatNumber(data.balance);
            
            // P&L
            const todayPnl = document.getElementById('today-pnl');
            todayPnl.textContent = '₹' + formatNumber(data.today_pnl);
            todayPnl.className = 'value ' + (data.today_pnl >= 0 ? 'green' : 'red');
            
            const monthPnl = document.getElementById('month-pnl');
            monthPnl.textContent = '₹' + formatNumber(data.month_pnl);
            monthPnl.className = 'value ' + (data.month_pnl >= 0 ? 'gold' : 'red');
            
            // Performance
            document.getElementById('win-rate').textContent = data.win_rate.toFixed(1) + '%';
            document.getElementById('win-rate').className = 'value ' + (data.win_rate >= 60 ? 'green' : 'red');
            document.getElementById('total-trades').textContent = data.total_trades;
            document.getElementById('trade-count').textContent = data.wins + 'W / ' + data.losses + 'L';
            
            // Status
            const status = document.getElementById('status');
            if (data.status === 'RUNNING') {
                status.textContent = '● RUNNING';
                status.className = 'status running';
            } else {
                status.textContent = '● WAITING';
                status.className = 'status waiting';
            }
            
            // Progress
            const monthProgress = Math.min((data.month_pnl / 62500) * 100, 100);
            document.getElementById('month-progress').style.width = monthProgress + '%';
            document.getElementById('month-progress').textContent = monthProgress.toFixed(0) + '%';
            document.getElementById('current-month-pnl').textContent = '₹' + formatNumber(data.month_pnl);
            
            const dailyProgress = Math.min((data.today_pnl / 5000) * 100, 100);
            document.getElementById('daily-progress').style.width = dailyProgress + '%';
            document.getElementById('daily-progress').textContent = dailyProgress.toFixed(0) + '%';
            document.getElementById('current-daily-pnl').textContent = '₹' + formatNumber(data.today_pnl);
            
            // Positions
            const positionsDiv = document.getElementById('positions');
            if (data.positions && data.positions.length > 0) {
                let html = '<div class="positions">';
                data.positions.forEach(pos => {
                    const pnlClass = pos.pnl >= 0 ? 'green' : 'red';
                    html += `
                        <div class="position-item">
                            <div class="symbol">${pos.symbol} <span style="color:#ffd700;">${pos.option}</span></div>
                            <div class="details">
                                Qty: ${pos.qty} | Entry: ₹${pos.entry.toFixed(2)} | Current: ₹${pos.current.toFixed(2)}
                                | P&L: <span class="${pnlClass}">₹${pos.pnl.toFixed(2)}</span>
                            </div>
                        </div>
                    `;
                });
                html += '</div>';
                positionsDiv.innerHTML = html;
            } else {
                positionsDiv.innerHTML = '<div style="color:#666; font-size:14px; text-align:center; padding:20px;">No active positions</div>';
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
                tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; color:#666; padding:20px;">No trades yet</td></tr>';
            }
        }
        
        function formatNumber(num) {
            return num.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
        }
        
        fetchData();
        setInterval(fetchData, 3000);
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
    data = get_real_data()
    data['last_update'] = datetime.now().strftime("%H:%M:%S")
    return jsonify(data)

@app.route('/api/refresh')
def refresh():
    return jsonify({"status": "refreshed", "timestamp": datetime.now().isoformat()})

@app.route('/api/health')
def health():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "client_id": CLIENT_ID
    })

# ============================================================
# MAIN
# ============================================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("="*60)
    print("🚀 Athena-X Dashboard")
    print("="*60)
    print(f"📊 Dashboard: http://0.0.0.0:{port}")
    print(f"🔑 Client ID: {CLIENT_ID}")
    print("="*60)
    app.run(host='0.0.0.0', port=port, debug=False)