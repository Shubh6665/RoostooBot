from app import db
from datetime import datetime

class TradeRecord(db.Model):
    """Model for storing trade records"""
    id = db.Column(db.Integer, primary_key=True)
    pair = db.Column(db.String(20), nullable=False)
    side = db.Column(db.String(10), nullable=False)  # BUY or SELL
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    order_id = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(20), nullable=False, default="EXECUTED")
    profit_loss = db.Column(db.Float, nullable=True)

class PerformanceMetric(db.Model):
    """Model for storing bot performance metrics"""
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    balance = db.Column(db.Float, nullable=False)
    portfolio_value = db.Column(db.Float, nullable=False)
    profit_loss = db.Column(db.Float, nullable=False)
    trades_executed = db.Column(db.Integer, nullable=False)
    win_rate = db.Column(db.Float, nullable=True)
    sharpe_ratio = db.Column(db.Float, nullable=True)

class BotConfig(db.Model):
    """Model for storing bot configuration"""
    id = db.Column(db.Integer, primary_key=True)
    pair = db.Column(db.String(20), nullable=False)
    risk_level = db.Column(db.Float, nullable=False, default=0.02)
    model_path = db.Column(db.String(200), nullable=True)
    is_active = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
