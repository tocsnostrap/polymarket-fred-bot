#!/usr/bin/env python3
"""
Polymarket Bond Scanner Bot with Dashboard
Single-file Flask application combining scanner logic and mobile-responsive dashboard.
"""

import os
import json
import time
import random
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from flask import Flask, render_template_string, jsonify, request

# ============================================================================
# HTML TEMPLATE (Dashboard)
# ============================================================================
HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Polymarket Bond Scanner - Professional</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; background: #0d1117; color: #c9d1d9; }
        .header { background: #161b22; padding: 20px; border-bottom: 1px solid #30363d; }
        .header h1 { margin: 0; color: #58a6ff; font-size: 24px; }
        .header .subtitle { color: #8b949e; margin-top: 5px; }
        .tabs { display: flex; background: #161b22; border-bottom: 1px solid #30363d; flex-wrap: wrap; }
        .tab { padding: 15px 25px; cursor: pointer; border-right: 1px solid #30363d; color: #8b949e; flex: 1; min-width: 120px; text-align: center; }
        .tab.active { background: #0d1117; color: #58a6ff; border-bottom: 2px solid #58a6ff; }
        .content { padding: 20px; }
        .card { background: #161b22; border: 1px solid #30363d; border-radius: 6px; padding: 20px; margin-bottom: 20px; }
        .card h3 { margin-top: 0; color: #58a6ff; border-bottom: 1px solid #30363d; padding-bottom: 10px; }
        .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; }
        .metric { text-align: center; padding: 15px; background: #0d1117; border-radius: 6px; }
        .metric .value { font-size: 24px; font-weight: bold; color: #58a6ff; }
        .metric .label { color: #8b949e; font-size: 14px; margin-top: 5px; }
        table { width: 100%; border-collapse: collapse; }
        th { background: #161b22; color: #58a6ff; padding: 12px; text-align: left; border-bottom: 2px solid #30363d; }
        td { padding: 12px; border-bottom: 1px solid #30363d; }
        tr:hover { background: #161b22; }
        .btn { background: #238636; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-weight: bold; }
        .btn:hover { background: #2ea043; }
        .btn-secondary { background: #30363d; }
        .btn-secondary:hover { background: #484f58; }
        @media (max-width: 768px) {
            .tab { min-width: 100px; padding: 12px 15px; font-size: 14px; }
            .content { padding: 15px; }
            .metric .value { font-size: 20px; }
        }
        @media (max-width: 480px) {
            .tabs { flex-direction: column; }
            .tab { border-right: none; border-bottom: 1px solid #30363d; }
            .metrics { grid-template-columns: 1fr 1fr; }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Polymarket Bond Scanner</h1>
        <div class="subtitle">Professional Trading Interface | Bot Status: <span id="bot-status">Running</span></div>
    </div>
    
    <div class="tabs">
        <div class="tab active" onclick="showTab('dashboard')">Dashboard</div>
        <div class="tab" onclick="showTab('opportunities')">Opportunities</div>
        <div class="tab" onclick="showTab('positions')">Positions</div>
        <div class="tab" onclick="showTab('settings')">Settings</div>
    </div>
    
    <div class="content">
        <div id="dashboard-tab" class="tab-content">
            <div class="metrics">
                <div class="metric">
                    <div class="value" id="markets-scanned">{{ state.markets_scanned }}</div>
                    <div class="label">Markets Scanned</div>
                </div>
                <div class="metric">
                    <div class="value" id="opportunities-found">{{ state.opportunities_found }}</div>
                    <div class="label">Opportunities Found</div>
                </div>
                <div class="metric">
                    <div class="value" id="open-positions">{{ state.open_positions }}</div>
                    <div class="label">Open Positions</div>
                </div>
                <div class="metric">
                    <div class="value" id="total-invested">${{ state.total_invested }}</div>
                    <div class="label">Total Invested</div>
                </div>
            </div>
            
            <div class="card">
                <h3>Recent Activity</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Time</th>
                            <th>Action</th>
                            <th>Market</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody id="activity-table">
                        {% for activity in state.recent_activity %}
                        <tr>
                            <td>{{ activity.time }}</td>
                            <td>{{ activity.action }}</td>
                            <td>{{ activity.market }}</td>
                            <td>{{ activity.status }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
        
        <div id="opportunities-tab" class="tab-content" style="display:none;">
            <div class="card">
                <h3>Trading Opportunities</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Market</th>
                            <th>Probability</th>
                            <th>Days Left</th>
                            <th>Volume</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody id="opportunities-table">
                        {% for opp in state.opportunities %}
                        <tr>
                            <td>{{ opp.market }}</td>
                            <td>{{ opp.probability }}%</td>
                            <td>{{ opp.days_left }}</td>
                            <td>${{ opp.volume }}</td>
                            <td><button class="btn" onclick="executeTrade('{{ opp.id }}')">Trade</button></td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
        
        <div id="positions-tab" class="tab-content" style="display:none;">
            <div class="card">
                <h3>Active Positions</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Market</th>
                            <th>Entry</th>
                            <th>Current</th>
                            <th>P&L</th>
                            <th>Days Left</th>
                        </tr>
                    </thead>
                    <tbody id="positions-table">
                        {% for pos in state.positions %}
                        <tr>
                            <td>{{ pos.market }}</td>
                            <td>{{ pos.entry_price }}</td>
                            <td>{{ pos.current_price }}</td>
                            <td class="{{ 'profit' if pos.pnl > 0 else 'loss' }}">{{ pos.pnl }}%</td>
                            <td>{{ pos.days_left }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
        
        <div id="settings-tab" class="tab-content" style="display:none;">
            <div class="card">
                <h3>Bot Configuration</h3>
                <div style="display:grid;gap:15px;">
                    <div>
                        <label style="display:block;margin-bottom:5px;color:#8b949e;">Scan Interval (minutes)</label>
                        <input type="number" id="scan-interval" value="{{ state.config.scan_interval }}" style="width:100%;padding:10px;background:#0d1117;border:1px solid #30363d;border-radius:6px;color:#c9d1d9;">
                    </div>
                    <div>
                        <label style="display:block;margin-bottom:5px;color:#8b949e;">Minimum Probability (%)</label>
                        <input type="number" id="min-probability" value="{{ state.config.min_probability }}" step="0.1" style="width:100%;padding:10px;background:#0d1117;border:1px solid #30363d;border-radius:6px;color:#c9d1d9;">
                    </div>
                    <div>
                        <label style="display:block;margin-bottom:5px;color:#8b949e;">Max Days to Resolution</label>
                        <input type="number" id="max-days" value="{{ state.config.max_days }}" style="width:100%;padding:10px;background:#0d1117;border:1px solid #30363d;border-radius:6px;color:#c9d1d9;">
                    </div>
                    <button class="btn" onclick="saveSettings()">Save Settings</button>
                    <button class="btn btn-secondary" onclick="startStopBot()" id="bot-toggle">Stop Bot</button>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        function showTab(tabName) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.style.display = 'none');
            event.target.classList.add('active');
            document.getElementById(tabName + '-tab').style.display = 'block';
        }
        
        function updateData() {
            fetch('/api/state')
                .then(r => r.json())
                .then(data => {
                    document.getElementById('markets-scanned').textContent = data.markets_scanned;
                    document.getElementById('opportunities-found').textContent = data.opportunities_found;
                    document.getElementById('open-positions').textContent = data.open_positions;
                    document.getElementById('total-invested').textContent = '$' + data.total_invested;
                    document.getElementById('bot-status').textContent = data.bot_running ? 'Running' : 'Stopped';
                    document.getElementById('bot-toggle').textContent = data.bot_running ? 'Stop Bot' : 'Start Bot';
                });
        }
        
        function executeTrade(opportunityId) {
            fetch('/api/trade', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({opportunity_id: opportunityId})
            })
            .then(r => r.json())
            .then(data => {
                alert(data.message);
                updateData();
            });
        }
        
        function saveSettings() {
            const settings = {
                scan_interval: parseInt(document.getElementById('scan-interval').value),
                min_probability: parseFloat(document.getElementById('min-probability').value),
                max_days: parseInt(document.getElementById('max-days').value)
            };
            
            fetch('/api/settings', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(settings)
            })
            .then(r => r.json())
            .then(data => {
                alert('Settings saved!');
            });
        }
        
        function startStopBot() {
            fetch('/api/toggle', {method: 'POST'})
                .then(r => r.json())
                .then(data => {
                    updateData();
                });
        }
        
        // Update data every 10 seconds
        setInterval(updateData, 10000);
        updateData();
    </script>
</body>
</html>'''

# ============================================================================
# BOT SCANNER LOGIC (Simplified)
# ============================================================================

class PolymarketScanner:
    """Simplified Polymarket bond scanner."""
    
    def __init__(self):
        self.markets_scanned = 0
        self.opportunities_found = 0
        self.open_positions = 0
        self.total_invested = 0
        self.bot_running = True
        self.scan_interval = 360  # minutes
        self.min_probability = 93.0
        self.max_days = 60
        self.min_volume = 500
        
        # Mock data for demo
        self.recent_activity = [
            {"time": "14:05", "action": "Scan", "market": "All Markets", "status": "Complete"},
            {"time": "14:00", "action": "Opportunity Found", "market": "BTC > 100k by EOY", "status": "Analyzing"},
            {"time": "13:55", "action": "Market Update", "market": "Election 2024", "status": "Updated"},
        ]
        
        self.opportunities = [
            {"id": "1", "market": "BTC > 100k by EOY", "probability": 94.5, "days_left": 45, "volume": 1250},
            {"id": "2", "market": "ETH > 5k by Q3", "probability": 93.2, "days_left": 32, "volume": 850},
            {"id": "3", "market": "SPY > 600 by Dec", "probability": 95.1, "days_left": 28, "volume": 2100},
        ]
        
        self.positions = []
        
        # Start scanner thread
        self.scanner_thread = threading.Thread(target=self._scanner_loop, daemon=True)
        self.scanner_thread.start()
    
    def _scanner_loop(self):
        """Main scanner loop running in background thread."""
        while True:
            if self.bot_running:
                self._scan_markets()
            time.sleep(self.scan_interval * 60)  # Convert minutes to seconds
    
    def _scan_markets(self):
        """Mock market scanning logic."""
        self.markets_scanned += 1000
        
        # Simulate finding opportunities
        new_opportunities = random.randint(0, 3)
        self.opportunities_found += new_opportunities
        
        # Add to recent activity
        if new_opportunities > 0:
            self.recent_activity.insert(0, {
                "time": datetime.now().strftime("%H:%M"),
                "action": f"Found {new_opportunities} opportunities",
                "market": "Auto-scan",
                "status": "Success"
            })
        
        # Keep only last 5 activities
        if len(self.recent_activity) > 5:
            self.recent_activity = self.recent_activity[:5]
    
    def get_state(self) -> Dict[str, Any]:
        """Get current bot state for dashboard."""
        return {
            "markets_scanned": self.markets_scanned,
            "opportunities_found": self.opportunities_found,
            "open_positions": self.open_positions,
            "total_invested": self.total_invested,
            "bot_running": self.bot_running,
            "recent_activity": self.recent_activity,
            "opportunities": self.opportunities,
            "positions": self.positions,
            "config": {
                "scan_interval": self.scan_interval,
                "min_probability": self.min_probability,
                "max_days": self.max_days,
            }
        }
    
    def update_settings(self, scan_interval: int, min_probability: float, max_days: int):
        """Update bot settings."""
        self.scan_interval = scan_interval
        self.min_probability = min_probability
        self.max_days = max_days
    
    def toggle_bot(self):
        """Start/stop the bot."""
        self.bot_running = not self.bot_running
        return self.bot_running
    
    def execute_trade(self, opportunity_id: str) -> Dict[str, Any]:
        """Mock trade execution."""
        # Find the opportunity
        opp = next((o for o in self.opportunities if o["id"] == opportunity_id), None)
        if not opp:
            return {"success": False, "message": "Opportunity not found"}
        
        # Simulate trade
        self.open_positions += 1
        self.total_invested += 200  # $200 per position
        
        # Add position
        self.positions.append({
            "market": opp["market"],
            "entry_price": opp["probability"],
            "current_price": opp["probability"] + random.uniform(-0.5, 0.5),
            "pnl": random.uniform(-2, 5),
            "days_left": opp["days_left"]
        })
        
        # Remove opportunity
        self.opportunities = [o for o in self.opportunities if o["id"] != opportunity_id]
        
        # Add to activity
        self.recent_activity.insert(0, {
            "time": datetime.now().strftime("%H:%M"),
            "action": "Trade Executed",
            "market": opp["market"],
            "status": "Success"
        })
        
        return {"success": True, "message": f"Trade executed for {opp['market']}"}

# ============================================================================
# FLASK APPLICATION
# ============================================================================

app = Flask(__name__)
scanner = PolymarketScanner()

@app.route('/')
def index():
    """Render the dashboard."""
    state = scanner.get_state()
    return render_template_string(HTML_TEMPLATE, state=state)

@app.route('/api/state')
def api_state():
    """Get current bot state as JSON."""
    return jsonify(scanner.get_state())

@app.route('/api/settings', methods=['POST'])
def api_settings():
    """Update bot settings."""
    data = request.json
    scanner.update_settings(
        scan_interval=data.get('scan_interval', 360),
        min_probability=data.get('min_probability', 93.0),
        max_days=data.get('max_days', 60)
    )
    return jsonify({"success": True, "message": "Settings updated"})

@app.route('/api/trade', methods=['POST'])
def api_trade():
    """Execute a trade."""
    data = request.json
    opportunity_id = data.get('opportunity_id')
    if not opportunity_id:
        return jsonify({"success": False, "message": "No opportunity ID provided"})
    
    result = scanner.execute_trade(opportunity_id)
    return jsonify(result)

@app.route('/api/toggle', methods=['POST'])
def api_toggle():
    """Toggle bot on/off."""
    is_running = scanner.toggle_bot()
    status = "running" if is_running else "stopped"
    return jsonify({"success": True, "message": f"Bot is now {status}", "bot_running": is_running})

@app.route('/api/scan', methods=['POST'])
def api_scan():
    """Trigger immediate scan."""
    scanner._scan_markets()
    return jsonify({"success": True, "message": "Scan completed"})

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    print("Starting Polymarket Bond Scanner Bot...")
    print("Dashboard available at: http://localhost:5000")
    print("Press Ctrl+C to stop")
    
    # Run Flask app
    app.run(host='0.0.0.0', port=5000, debug=False)