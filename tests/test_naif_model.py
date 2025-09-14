import unittest
from unittest.mock import patch, MagicMock
import json
import os
import sys
import tempfile

# Add parent directory to path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml_components.naif_alrasheed_model import NaifAlRasheedModel

class TestNaifAlRasheedModel(unittest.TestCase):
    """Test cases for the Naif Al-Rasheed Investment Model"""
    
    def setUp(self):
        """Set up test environment"""
        self.model = NaifAlRasheedModel()
        # Create a mock SaudiMarketAPI
        patcher = patch('ml_components.naif_alrasheed_model.SaudiMarketAPI')
        self.mock_api_class = patcher.start()
        self.mock_api = self.mock_api_class.return_value
        self.model.saudi_api = self.mock_api
        self.addCleanup(patcher.stop)
        
        # Create a mock StockAnalyzer
        patcher2 = patch('ml_components.naif_alrasheed_model.EnhancedStockAnalyzer')
        self.mock_analyzer_class = patcher2.start()
        self.mock_analyzer = self.mock_analyzer_class.return_value
        self.model.stock_analyzer = self.mock_analyzer
        self.addCleanup(patcher2.stop)
        
        # Create a mock PortfolioManager
        patcher3 = patch('ml_components.naif_alrasheed_model.PortfolioManager')
        self.mock_portfolio_class = patcher3.start()
        self.mock_portfolio = self.mock_portfolio_class.return_value
        self.model.portfolio_manager = self.mock_portfolio
        self.addCleanup(patcher3.stop)
        
    def test_rank_sectors(self):
        """Test sector ranking functionality"""
        # Mock API responses
        self.mock_api.get_symbols.return_value = [
            {'symbol': 'SECO', 'name': 'Saudi Electricity Co.', 'sector': 'Utilities'},
            {'symbol': 'SABIC', 'name': 'Saudi Basic Industries Corp.', 'sector': 'Materials'},
            {'symbol': 'STC', 'name': 'Saudi Telecom Co.', 'sector': 'Communication Services'}
        ]
        
        # Mock sector calculations
        self.model._calculate_sector_growth = MagicMock(return_value=70)
        self.model._calculate_sector_momentum = MagicMock(return_value=60)
        self.model._calculate_sector_profitability = MagicMock(return_value=80)
        self.model._calculate_sector_valuation = MagicMock(return_value=40)
        
        # Run the ranking
        sector_scores = self.model._rank_sectors()
        
        # Verify results
        self.assertIn('Utilities', sector_scores)
        self.assertIn('Materials', sector_scores)
        self.assertIn('Communication Services', sector_scores)
        
        # Calculate expected score manually
        expected_score = (
            70 * 0.35 +  # Growth score
            60 * 0.25 +  # Momentum score
            80 * 0.25 +  # Profitability score
            (100 - 40) * 0.15  # Inverted valuation score
        )
        
        # Check scores (should be the same for all sectors with our mocked values)
        self.assertAlmostEqual(sector_scores['Utilities'], expected_score)
        self.assertAlmostEqual(sector_scores['Materials'], expected_score)
        self.assertAlmostEqual(sector_scores['Communication Services'], expected_score)
    
    def test_select_top_sectors(self):
        """Test selecting top sectors"""
        # Create some sector scores
        sector_scores = {
            'Technology': 85,
            'Healthcare': 75,
            'Financials': 70,
            'Energy': 60,
            'Materials': 50,
            'Consumer Discretionary': 45,
            'Utilities': 40,
            'Real Estate': 35
        }
        
        # Run the selection
        top_sectors = self.model._select_top_sectors(sector_scores)
        
        # Verify results
        self.assertEqual(len(top_sectors), 4)  # Top 3 plus Financials
        self.assertIn('Technology', top_sectors)
        self.assertIn('Healthcare', top_sectors)
        self.assertIn('Financials', top_sectors)  # Always included if available
        
        # Test with Financials already in top 3
        sector_scores = {
            'Financials': 85,
            'Technology': 80,
            'Healthcare': 75,
            'Energy': 60
        }
        
        top_sectors = self.model._select_top_sectors(sector_scores)
        self.assertEqual(len(top_sectors), 3)  # Top 3 including Financials
        self.assertIn('Financials', top_sectors)
        self.assertIn('Technology', top_sectors)
        self.assertIn('Healthcare', top_sectors)
    
    def test_fundamental_screening(self):
        """Test fundamental screening of companies"""
        # Mock companies data
        companies = [
            {'symbol': 'COMPANY1', 'name': 'Company 1', 'sector': 'Technology'},
            {'symbol': 'COMPANY2', 'name': 'Company 2', 'sector': 'Healthcare'},
            {'symbol': 'COMPANY3', 'name': 'Company 3', 'sector': 'Financials'}
        ]
        
        # Mock API responses for symbol info
        def get_symbol_info(symbol):
            if symbol == 'COMPANY1':
                return {
                    'market_cap': 5_000_000_000,  # 5 billion (passes)
                    'roe': 15.0,                  # 15% (passes)
                    'debt_to_equity': 0.8,        # 0.8 (passes)
                    'revenue_growth': 8.0,        # 8% (passes)
                    'profit_margin': 12.0         # 12% (passes)
                }
            elif symbol == 'COMPANY2':
                return {
                    'market_cap': 500_000_000,    # 500 million (fails)
                    'roe': 5.0,                   # 5% (fails)
                    'debt_to_equity': 0.5,        # 0.5 (passes)
                    'revenue_growth': 10.0,       # 10% (passes)
                    'profit_margin': 15.0         # 15% (passes)
                }
            elif symbol == 'COMPANY3':
                return {
                    'market_cap': 2_000_000_000,  # 2 billion (passes)
                    'roe': 12.0,                  # 12% (passes)
                    'debt_to_equity': 1.5,        # 1.5 (fails)
                    'revenue_growth': 4.0,        # 4% (fails)
                    'profit_margin': 8.0          # 8% (fails)
                }
        
        self.mock_api.get_symbol_info.side_effect = get_symbol_info
        
        # Run fundamental screening
        screened_companies = self.model._run_fundamental_screening(companies)
        
        # Verify only COMPANY1 passes all criteria
        self.assertEqual(len(screened_companies), 1)
        self.assertEqual(screened_companies[0]['symbol'], 'COMPANY1')
        self.assertIn('fundamental_score', screened_companies[0])
    
    def test_run_full_screening(self):
        """Test the full screening pipeline"""
        # Mock sector rankings
        self.model._rank_sectors = MagicMock(return_value={
            'Technology': 80,
            'Healthcare': 70,
            'Financials': 65
        })
        
        # Mock top sectors selection
        self.model._select_top_sectors = MagicMock(return_value=[
            'Technology', 'Healthcare', 'Financials'
        ])
        
        # Mock companies in sectors
        self.model._get_companies_in_sectors = MagicMock(return_value=[
            {'symbol': 'TECH1', 'name': 'Tech Company 1', 'sector': 'Technology'},
            {'symbol': 'HEALTH1', 'name': 'Health Company 1', 'sector': 'Healthcare'},
            {'symbol': 'FIN1', 'name': 'Financial Company 1', 'sector': 'Financials'}
        ])
        
        # Mock fundamental screening
        self.model._run_fundamental_screening = MagicMock(return_value=[
            {'symbol': 'TECH1', 'name': 'Tech Company 1', 'sector': 'Technology', 'fundamental_score': 85}
        ])
        
        # Mock valuation analysis
        self.model._run_valuation_analysis = MagicMock(return_value=[
            {'symbol': 'TECH1', 'name': 'Tech Company 1', 'sector': 'Technology', 
             'fundamental_score': 85, 'valuation_score': 75}
        ])
        
        # Mock final ranking and selection
        ranked_company = {'symbol': 'TECH1', 'name': 'Tech Company 1', 'sector': 'Technology', 
                         'fundamental_score': 85, 'valuation_score': 75, 'combined_score': 80}
        self.model._rank_companies = MagicMock(return_value=[ranked_company])
        self.model._select_final_companies = MagicMock(return_value=[ranked_company])
        
        # Mock portfolio generation
        portfolio = {
            'holdings': [
                {'symbol': 'TECH1', 'name': 'Tech Company 1', 'sector': 'Technology', 'weight': 1.0,
                 'fundamental_score': 85, 'valuation_score': 75, 'combined_score': 80}
            ],
            'total_value': 1_000_000,
            'positions_count': 1
        }
        self.model._generate_portfolio = MagicMock(return_value=portfolio)
        
        # Run full screening
        result = self.model.run_full_screening()
        
        # Verify results
        self.assertTrue(result['success'])
        self.assertEqual(result['selected_sectors'], ['Technology', 'Healthcare', 'Financials'])
        self.assertEqual(result['screened_companies'], ['TECH1'])
        self.assertEqual(result['valuated_companies'], ['TECH1'])
        self.assertEqual(result['selected_companies'], ['TECH1'])
        self.assertEqual(result['portfolio'], portfolio)
        
        # Verify method calls
        self.model._rank_sectors.assert_called_once()
        self.model._select_top_sectors.assert_called_once()
        self.model._get_companies_in_sectors.assert_called_once()
        self.model._run_fundamental_screening.assert_called_once()
        self.model._run_valuation_analysis.assert_called_once()
        self.model._rank_companies.assert_called_once()
        self.model._select_final_companies.assert_called_once()
        self.model._generate_portfolio.assert_called_once()

if __name__ == '__main__':
    unittest.main()