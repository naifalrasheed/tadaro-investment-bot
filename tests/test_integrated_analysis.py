import unittest
import logging
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from ml_components.integrated_analysis import IntegratedAnalysis

class TestIntegratedAnalysis(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures before all tests"""
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(levelname)s: %(message)s'
        )
        cls.logger = logging.getLogger(__name__)
        
    def test_basic_initialization(self):
        """Test if the analyzer can be initialized"""
        analyzer = IntegratedAnalysis()
        self.assertIsInstance(analyzer, IntegratedAnalysis)
        self.logger.info("Basic initialization test passed")

    @patch('ml_components.integrated_analysis.ImprovedMLEngine')
    @patch('yfinance.Ticker')
    def test_single_stock_analysis(self, mock_ticker, mock_ml_engine):
        """Test analysis with a single stock using mocks to avoid API calls"""
        symbol = 'AAPL'
        self.logger.info(f"Testing analysis for {symbol}")
        
        # Create mock price data
        dates = pd.date_range(start='2020-01-01', periods=100, freq='D')
        price_data = pd.DataFrame({
            'Open': np.random.normal(100, 2, 100),
            'High': np.random.normal(102, 2, 100),
            'Low': np.random.normal(98, 2, 100),
            'Close': np.random.normal(101, 2, 100),
            'Volume': np.random.randint(1000, 10000, 100)
        }, index=dates)
        
        # Set up mock ticker
        mock_ticker_instance = MagicMock()
        mock_ticker.return_value = mock_ticker_instance
        
        # Mock ticker.info
        mock_ticker_instance.info = {
            'marketCap': 1000000000,
            'beta': 1.2,
            'sector': 'Technology',
            'industry': 'Consumer Electronics',
            'returnOnEquity': 0.25,
            'forwardPE': 20.5,
            'debtToEquity': 1.1,
            'revenueGrowth': 0.15,
            'profitMargins': 0.2
        }
        
        # Mock history method
        mock_ticker_instance.history.return_value = price_data
        
        # Create cash flow data for DCF valuation
        cashflow_data = {
            'Total Cash From Operating Activities': [100000, 110000, 120000],
            'Capital Expenditures': [-20000, -25000, -30000],
        }
        cashflow_index = pd.DatetimeIndex(['2020-12-31', '2021-12-31', '2022-12-31'])
        mock_ticker_instance.cashflow = pd.DataFrame(cashflow_data, index=cashflow_index)
        
        # Create balance sheet data
        balance_sheet_data = {
            'Total Debt': [200000],
            'Cash': [100000],
        }
        mock_ticker_instance.balance_sheet = pd.DataFrame(balance_sheet_data, index=pd.DatetimeIndex(['2022-12-31']))
        
        # Create recommendation data
        recommendations_data = {
            'Firm': ['Firm A', 'Firm B', 'Firm C', 'Firm D', 'Firm E'],
            'To Grade': ['Buy', 'Buy', 'Hold', 'Buy', 'Sell'],
            'Price Target': [110, 105, 95, 115, 90]
        }
        rec_dates = pd.date_range(end=datetime.now(), periods=5, freq='ME')
        mock_ticker_instance.recommendations = pd.DataFrame(recommendations_data, index=rec_dates)
        
        # Setup mock for ML engine
        mock_engine_instance = MagicMock()
        mock_ml_engine.return_value = mock_engine_instance
        
        # Mock the prepare_features method to return a dataframe and a series
        features_df = pd.DataFrame({'feature1': np.random.random(95)}, index=price_data.index[:-5])
        targets_series = pd.Series(np.random.random(95), index=price_data.index[:-5])
        mock_engine_instance.prepare_features.return_value = (features_df, targets_series)
        
        # Mock the predict method
        mock_engine_instance.predict.return_value = (0.05, 75.0)  # 5% return prediction, 75% confidence
        
        # Initialize analyzer and run the test
        analyzer = IntegratedAnalysis()
        result = analyzer.analyze_stock(symbol)
        
        # Check the result
        self.assertIsInstance(result, dict)
        self.assertEqual(result['symbol'], symbol)
        self.assertIn('analysis_date', result)
        self.assertIn('integrated_score', result)
        self.assertIn('recommendation', result)
        
        # Log results
        self.logger.info(f"Analysis completed for {symbol}")
        self.logger.info(f"Result keys: {list(result.keys())}")
        self.logger.info(f"Integrated score: {result['integrated_score']}")


if __name__ == '__main__':
    unittest.main()