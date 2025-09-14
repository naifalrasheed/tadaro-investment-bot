#!/usr/bin/env python3
"""
Migration 001: Normalize Critical JSON Columns
Creates normalized tables for the most critical JSON column anti-patterns
"""

import sys
import os
import json
from datetime import datetime

# Add the src directory to the path so we can import models
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/../')

from flask import Flask
from models import db

def create_app():
    """Create Flask app for migration"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'migration-key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///investment_bot.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app

# New normalized table definitions
from sqlalchemy import Column, Integer, String, DateTime, Decimal, Text, ForeignKey, Date, BigInteger

class PortfolioHolding(db.Model):
    """Normalized portfolio holdings table"""
    __tablename__ = 'portfolio_holdings'
    
    id = Column(Integer, primary_key=True)
    portfolio_id = Column(Integer, ForeignKey('portfolio.id'), nullable=False)
    symbol = Column(String(10), nullable=False)
    shares = Column(Decimal(10,4))
    purchase_price = Column(Decimal(10,2))
    purchase_date = Column(Date)
    current_value = Column(Decimal(10,2))
    weight_percentage = Column(Decimal(5,2))
    sector = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)

class StockAnalysisMetric(db.Model):
    """Normalized stock analysis metrics table"""
    __tablename__ = 'stock_analysis_metrics'
    
    id = Column(Integer, primary_key=True)
    analysis_id = Column(Integer, ForeignKey('stock_analysis.id'), nullable=False)
    metric_name = Column(String(50), nullable=False)
    metric_value = Column(Decimal(15,6))
    metric_type = Column(String(20))  # 'technical', 'fundamental', 'sentiment'
    calculation_date = Column(Date)
    data_source = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)

class StockMetricsSnapshot(db.Model):
    """Normalized stock metrics snapshot table"""
    __tablename__ = 'stock_metrics_snapshot'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(10), nullable=False)
    snapshot_date = Column(DateTime, nullable=False)
    price = Column(Decimal(10,2))
    pe_ratio = Column(Decimal(8,2))
    rotc = Column(Decimal(8,4))
    dividend_yield = Column(Decimal(6,4))
    market_cap = Column(BigInteger)
    volume = Column(BigInteger)
    sentiment_score = Column(Decimal(5,4))
    momentum_score = Column(Decimal(5,4))
    created_at = Column(DateTime, default=datetime.utcnow)

def migrate_portfolio_stocks():
    """Migrate Portfolio.stocks JSON to portfolio_holdings table"""
    from models import Portfolio
    
    print("Migrating portfolio stocks...")
    portfolios = Portfolio.query.all()
    migrated_count = 0
    
    for portfolio in portfolios:
        if portfolio.stocks:
            try:
                stocks_data = portfolio.stocks if isinstance(portfolio.stocks, list) else json.loads(portfolio.stocks)
                
                for stock_data in stocks_data:
                    holding = PortfolioHolding(
                        portfolio_id=portfolio.id,
                        symbol=stock_data.get('symbol', ''),
                        shares=stock_data.get('shares'),
                        purchase_price=stock_data.get('purchase_price'),
                        purchase_date=stock_data.get('purchase_date'),
                        current_value=stock_data.get('current_value'),
                        weight_percentage=stock_data.get('weight', stock_data.get('weight_percentage')),
                        sector=stock_data.get('sector', '')
                    )
                    db.session.add(holding)
                    migrated_count += 1
                
                print(f"✓ Migrated {len(stocks_data)} holdings for portfolio {portfolio.id}")
                
            except Exception as e:
                print(f"✗ Error migrating portfolio {portfolio.id}: {e}")
                continue
    
    db.session.commit()
    print(f"✓ Total migrated holdings: {migrated_count}")

def migrate_analysis_data():
    """Migrate StockAnalysis.analysis_data JSON to stock_analysis_metrics table"""
    from models import StockAnalysis
    
    print("Migrating stock analysis data...")
    analyses = StockAnalysis.query.all()
    migrated_count = 0
    
    for analysis in analyses:
        if analysis.analysis_data:
            try:
                data = analysis.analysis_data if isinstance(analysis.analysis_data, dict) else json.loads(analysis.analysis_data)
                
                # Extract common metrics from analysis data
                metrics_to_extract = [
                    ('price', 'fundamental'),
                    ('pe_ratio', 'fundamental'), 
                    ('rotc', 'fundamental'),
                    ('dividend_yield', 'fundamental'),
                    ('market_cap', 'fundamental'),
                    ('volume', 'technical'),
                    ('sentiment_score', 'sentiment'),
                    ('momentum_score', 'technical'),
                    ('rsi', 'technical'),
                    ('moving_average_50', 'technical'),
                    ('moving_average_200', 'technical')
                ]
                
                for metric_name, metric_type in metrics_to_extract:
                    value = data.get(metric_name)
                    if value is not None:
                        metric = StockAnalysisMetric(
                            analysis_id=analysis.id,
                            metric_name=metric_name,
                            metric_value=value,
                            metric_type=metric_type,
                            calculation_date=analysis.date.date() if analysis.date else datetime.utcnow().date(),
                            data_source='migrated_from_json'
                        )
                        db.session.add(metric)
                        migrated_count += 1
                
                print(f"✓ Migrated analysis {analysis.id} for {analysis.symbol}")
                
            except Exception as e:
                print(f"✗ Error migrating analysis {analysis.id}: {e}")
                continue
    
    db.session.commit()
    print(f"✓ Total migrated metrics: {migrated_count}")

def migrate_metrics_snapshots():
    """Migrate StockPreference.metrics_at_feedback to stock_metrics_snapshot"""
    from models import StockPreference
    
    print("Migrating stock metrics snapshots...")
    preferences = StockPreference.query.filter(StockPreference.metrics_at_feedback.isnot(None)).all()
    migrated_count = 0
    
    for pref in preferences:
        if pref.metrics_at_feedback:
            try:
                metrics = pref.metrics_at_feedback if isinstance(pref.metrics_at_feedback, dict) else json.loads(pref.metrics_at_feedback)
                
                snapshot = StockMetricsSnapshot(
                    symbol=pref.symbol,
                    snapshot_date=pref.feedback_date or pref.created_date,
                    price=metrics.get('price'),
                    pe_ratio=metrics.get('pe_ratio'),
                    rotc=metrics.get('rotc'),
                    dividend_yield=metrics.get('dividend_yield'),
                    market_cap=metrics.get('market_cap'),
                    volume=metrics.get('volume'),
                    sentiment_score=metrics.get('sentiment_score'),
                    momentum_score=metrics.get('momentum_score')
                )
                db.session.add(snapshot)
                migrated_count += 1
                
                print(f"✓ Migrated snapshot for {pref.symbol}")
                
            except Exception as e:
                print(f"✗ Error migrating metrics snapshot for {pref.symbol}: {e}")
                continue
    
    db.session.commit()
    print(f"✓ Total migrated snapshots: {migrated_count}")

def run_migration():
    """Run the complete migration"""
    app = create_app()
    
    with app.app_context():
        print("🗄️ Starting Database Normalization Migration 001")
        print("=" * 60)
        
        # Create new tables
        print("Creating normalized tables...")
        db.create_all()
        print("✓ Tables created successfully")
        
        # Run migrations
        migrate_portfolio_stocks()
        migrate_analysis_data() 
        migrate_metrics_snapshots()
        
        print("=" * 60)
        print("✅ Migration 001 completed successfully!")
        print("\nNext steps:")
        print("1. Test the application with new normalized data")
        print("2. Update service layer to use new tables") 
        print("3. Run migration 002 for remaining JSON columns")

if __name__ == "__main__":
    run_migration()