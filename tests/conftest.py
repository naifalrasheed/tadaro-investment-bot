import pytest
import sys
import os

# Add the src directory to the path so we can import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Common fixtures for tests
@pytest.fixture
def sample_stock_data():
    """Provides sample stock data for testing"""
    import pandas as pd
    import numpy as np
    
    # Generate sample data
    dates = pd.date_range(start='2020-01-01', periods=100, freq='D')
    data = {
        'Open': np.random.normal(100, 5, 100),
        'High': np.random.normal(105, 5, 100),
        'Low': np.random.normal(95, 5, 100),
        'Close': np.random.normal(100, 5, 100),
        'Volume': np.random.randint(1000, 10000, 100)
    }
    
    return pd.DataFrame(data, index=dates)

@pytest.fixture
def mock_yfinance_ticker(monkeypatch):
    """Mocks the yfinance Ticker class for testing"""
    import pandas as pd
    import numpy as np
    from unittest.mock import MagicMock
    
    mock_ticker = MagicMock()
    
    # Mock ticker.info
    mock_ticker.info = {
        'marketCap': 1000000000,
        'totalDebt': 200000000,
        'beta': 1.2,
        'industry': 'Technology',
        'sharesOutstanding': 10000000
    }
    
    # Mock ticker.history
    dates = pd.date_range(start='2020-01-01', periods=100, freq='D')
    history_data = {
        'Open': np.random.normal(100, 5, 100),
        'High': np.random.normal(105, 5, 100),
        'Low': np.random.normal(95, 5, 100),
        'Close': np.random.normal(100, 5, 100),
        'Volume': np.random.randint(1000, 10000, 100)
    }
    mock_ticker.history.return_value = pd.DataFrame(history_data, index=dates)
    
    # Mock ticker.cashflow
    cashflow_data = {
        'Total Cash From Operating Activities': [100000, 110000, 120000],
        'Capital Expenditures': [-20000, -25000, -30000],
    }
    cashflow_index = ['2018-12-31', '2019-12-31', '2020-12-31']
    mock_ticker.cashflow = pd.DataFrame(cashflow_data, index=cashflow_index)
    
    # Mock ticker.balance_sheet
    balance_sheet_data = {
        'Total Debt': [200000],
        'Cash': [100000],
    }
    mock_ticker.balance_sheet = pd.DataFrame(balance_sheet_data, index=['2020-12-31'])
    
    # Mock ticker.recommendations
    recommendations_data = {
        'Firm': ['Firm A', 'Firm B', 'Firm C'],
        'To Grade': ['Buy', 'Hold', 'Buy'],
        'Price Target': [110, 105, 115]
    }
    rec_dates = pd.date_range(end=pd.Timestamp.now(), periods=3, freq='M')
    mock_ticker.recommendations = pd.DataFrame(recommendations_data, index=rec_dates)
    
    # Create a patcher to replace yfinance.Ticker
    def mock_ticker_init(*args, **kwargs):
        return mock_ticker
    
    # Apply the monkeypatch
    monkeypatch.setattr("yfinance.Ticker", mock_ticker_init)
    
    return mock_ticker