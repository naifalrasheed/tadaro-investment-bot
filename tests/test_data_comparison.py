"""
Test suite for the Data Comparison Service
"""

import os
import sys
import unittest
from datetime import datetime, timedelta
import logging

# Add the src directory to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from data.data_comparison_service import DataComparisonService

class TestDataComparisonService(unittest.TestCase):
    """Test cases for the Data Comparison Service"""
    
    def setUp(self):
        """Set up test environment before each test"""
        self.service = DataComparisonService()
        
        # Sample data from different sources
        current_time = datetime.now().timestamp()
        
        # Alpha Vantage data (1 hour old)
        self.av_data = {
            'symbol': 'AAPL',
            'company_name': 'Apple Inc.',
            'current_price': 192.53,
            'price_metrics': {
                'week_52_high': 220.20,
                'week_52_low': 164.04,
                'ytd_performance': -0.74,
                'daily_change': 0.38
            },
            'market_cap': 3150000000000,
            'data_source': 'alpha_vantage',
            'timestamp': current_time - 3600  # 1 hour old
        }
        
        # Interactive Brokers data (2 minutes old)
        self.ib_data = {
            'symbol': 'AAPL',
            'company_name': 'APPLE INC',
            'current_price': 193.02,
            'price_metrics': {
                'week_52_high': 221.15,
                'week_52_low': 163.88,
                'ytd_performance': -0.65,
                'daily_change': 0.42
            },
            'market_cap': 3160000000000,
            'data_source': 'interactive_brokers',
            'timestamp': current_time - 120  # 2 minutes old
        }
        
        # YFinance data (30 minutes old)
        self.yf_data = {
            'symbol': 'AAPL',
            'company_name': 'Apple Inc.',
            'current_price': 192.75,
            'price_metrics': {
                'week_52_high': 220.25,
                'week_52_low': 164.12,
                'ytd_performance': -0.70,
                'daily_change': 0.40
            },
            'market_cap': 3155000000000,
            'data_source': 'yfinance',
            'timestamp': current_time - 1800  # 30 minutes old
        }
        
        # Manual data (freshest)
        self.manual_data = {
            'symbol': 'AAPL',
            'company_name': 'Apple Inc.',
            'current_price': 192.85,
            'price_metrics': {
                'week_52_high': 220.20,
                'week_52_low': 164.10,
                'ytd_performance': -0.72,
                'daily_change': 0.39
            },
            'market_cap': 3152000000000,
            'data_source': 'manual_data',
            'timestamp': current_time - 60  # 1 minute old
        }
        
        # Invalid data (missing required fields)
        self.invalid_data = {
            'symbol': 'AAPL',
            'company_name': 'Apple Inc.',
            # Missing current_price
            'price_metrics': {
                'week_52_high': 220.20,
                'week_52_low': 164.04
            },
            'data_source': 'unknown'
        }
        
        # Significantly different data (potential error)
        self.outlier_data = {
            'symbol': 'AAPL',
            'company_name': 'Apple Inc.',
            'current_price': 250.00,  # Much higher than other sources
            'price_metrics': {
                'week_52_high': 250.00,
                'week_52_low': 150.00,
                'ytd_performance': 20.0,  # Very different
                'daily_change': 5.0  # Very different
            },
            'market_cap': 4000000000000,  # Much higher
            'data_source': 'mock_data',
            'timestamp': current_time - 7200  # 2 hours old
        }
    
    def test_filter_valid_sources(self):
        """Test filtering valid sources"""
        sources = [self.av_data, self.invalid_data, self.ib_data]
        valid_sources = self.service._filter_valid_sources(sources)
        
        # Should filter out the invalid data
        self.assertEqual(len(valid_sources), 2)
        self.assertIn(self.av_data, valid_sources)
        self.assertIn(self.ib_data, valid_sources)
    
    def test_select_primary_source(self):
        """Test selecting the primary source based on timestamp and reliability"""
        sources = [self.av_data, self.ib_data, self.yf_data]
        primary = self.service._select_primary_source(sources)
        
        # Interactive Brokers should be selected (highest combined score of recency and reliability)
        self.assertEqual(primary, self.ib_data)
        
        # Add manual data which has highest priority
        sources.append(self.manual_data)
        primary = self.service._select_primary_source(sources)
        
        # Manual data should now be selected (highest priority)
        self.assertEqual(primary, self.manual_data)
    
    def test_detect_conflicts(self):
        """Test detecting conflicts between sources"""
        # Similar sources with no significant conflicts
        sources = [self.av_data, self.ib_data, self.yf_data]
        conflicts = self.service._detect_conflicts(sources)
        
        # There might be small conflicts, but they should be below threshold
        self.assertEqual(len(conflicts), 0)
        
        # Add outlier data to create significant conflicts
        sources.append(self.outlier_data)
        conflicts = self.service._detect_conflicts(sources)
        
        # Now there should be conflicts
        self.assertGreater(len(conflicts), 0)
        
        # Check for specific conflicts
        self.assertIn('current_price', conflicts)
        self.assertIn('price_metrics.ytd_performance', conflicts)
    
    def test_resolve_conflicts(self):
        """Test resolving conflicts between sources"""
        sources = [self.av_data, self.ib_data, self.yf_data, self.outlier_data]
        primary = self.service._select_primary_source(sources)
        conflicts = self.service._detect_conflicts(sources)
        
        # Resolve conflicts
        resolved = self.service._resolve_conflicts(primary, conflicts, sources)
        
        # Check that the resolved data has reconciliation metadata
        self.assertIn('data_reconciliation', resolved)
        self.assertEqual(len(resolved['data_reconciliation']['sources']), 4)
        self.assertEqual(resolved['data_reconciliation']['primary_source'], primary['data_source'])
        
        # Check that conflicts were resolved with weighted averages
        # The outlier should have less weight, so result should be closer to the other sources
        self.assertLess(resolved['current_price'], self.outlier_data['current_price'])
        self.assertGreater(resolved['current_price'], self.av_data['current_price'])
    
    def test_select_most_accurate(self):
        """Test the high-level function to select the most accurate data"""
        # Test with all sources
        result = self.service.select_most_accurate(
            self.av_data, self.ib_data, self.yf_data, self.manual_data
        )
        
        # Manual data should be selected as base due to highest priority
        self.assertEqual(result['data_source'], 'manual_data')
        
        # Test with missing sources
        result = self.service.select_most_accurate(
            av_data=self.av_data, ib_data=self.ib_data
        )
        
        # IB data should be selected due to recency
        self.assertEqual(result['data_source'], 'interactive_brokers')
        
        # Test with only one source
        result = self.service.select_most_accurate(av_data=self.av_data)
        
        # The only source should be selected
        self.assertEqual(result['data_source'], 'alpha_vantage')
        
        # Test with conflicting sources
        result = self.service.select_most_accurate(
            av_data=self.av_data, ib_data=self.ib_data, yf_data=self.outlier_data
        )
        
        # Should select IB as primary but reconcile conflicts
        self.assertEqual(result['data_source'], 'interactive_brokers')
        self.assertIn('data_reconciliation', result)
    
    def test_compare_and_select(self):
        """Test the main method to compare and select data"""
        # Test with normal data
        sources = [self.av_data, self.ib_data, self.yf_data]
        result = self.service.compare_and_select(sources)
        
        # IB should be selected without conflicts
        self.assertEqual(result['data_source'], 'interactive_brokers')
        self.assertNotIn('data_reconciliation', result)
        
        # Test with conflicting data
        sources.append(self.outlier_data)
        result = self.service.compare_and_select(sources)
        
        # IB should be selected as primary but conflicts reconciled
        self.assertEqual(result['data_source'], 'interactive_brokers')
        self.assertIn('data_reconciliation', result)
        
        # Test with manual data (highest priority)
        sources = [self.av_data, self.ib_data, self.manual_data, self.outlier_data]
        result = self.service.compare_and_select(sources)
        
        # Manual data should be selected as primary
        self.assertEqual(result['data_source'], 'manual_data')
        self.assertIn('data_reconciliation', result)

if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    unittest.main()