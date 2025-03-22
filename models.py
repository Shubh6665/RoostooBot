import os
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class Trade(db.Model):
    """Model to store trade history"""
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    pair = db.Column(db.String(20), nullable=False)
    side = db.Column(db.String(10), nullable=False)  # BUY or SELL
    type = db.Column(db.String(10), nullable=False)  # MARKET or LIMIT
    quantity = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=True)  # Null for market orders
    status = db.Column(db.String(20), nullable=False)  # PENDING, FILLED, CANCELLED
    order_id = db.Column(db.Integer, nullable=True)
    profit_loss = db.Column(db.Float, nullable=True)  # Calculated P&L for completed trades
    
    def __repr__(self):
        return f'<Trade {self.id} {self.side} {self.quantity} {self.pair} at {self.timestamp}>'

class BotConfig(db.Model):
    """Model to store bot configuration"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    pair = db.Column(db.String(20), nullable=False, default='BTC/USD')
    model_path = db.Column(db.String(255), nullable=True)
    max_position_size = db.Column(db.Float, nullable=False, default=0.01)  # Maximum position size in BTC
    risk_percentage = db.Column(db.Float, nullable=False, default=2.0)  # Risk as % of portfolio
    is_active = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<BotConfig {self.name} for {self.pair}>'

class PerformanceMetric(db.Model):
    """Model to store bot performance metrics"""
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    portfolio_value = db.Column(db.Float, nullable=False)
    btc_balance = db.Column(db.Float, nullable=False)
    usd_balance = db.Column(db.Float, nullable=False)
    total_trades = db.Column(db.Integer, nullable=False)
    profitable_trades = db.Column(db.Integer, nullable=False)
    sharpe_ratio = db.Column(db.Float, nullable=True)
    
    def __repr__(self):
        return f'<PerformanceMetric at {self.timestamp} - Portfolio: ${self.portfolio_value:.2f}>'
