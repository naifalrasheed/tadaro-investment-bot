import unittest
from unittest.mock import patch, MagicMock
import json
import os
import sys

# Add parent directory to path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from claude_integration.chat_interface import ChatInterface

class TestChatInterface(unittest.TestCase):
    """Test cases for the Chat Interface"""
    
    def setUp(self):
        """Set up test environment"""
        # Patch dependencies
        patcher1 = patch('claude_integration.chat_interface.ClaudeHandler')
        self.mock_claude_class = patcher1.start()
        self.mock_claude = self.mock_claude_class.return_value
        self.addCleanup(patcher1.stop)
        
        patcher2 = patch('claude_integration.chat_interface.EnhancedStockAnalyzer')
        self.mock_analyzer_class = patcher2.start()
        self.mock_analyzer = self.mock_analyzer_class.return_value
        self.addCleanup(patcher2.stop)
        
        patcher3 = patch('claude_integration.chat_interface.PortfolioManager')
        self.mock_portfolio_class = patcher3.start()
        self.mock_portfolio = self.mock_portfolio_class.return_value
        self.addCleanup(patcher3.stop)
        
        patcher4 = patch('claude_integration.chat_interface.NaifAlRasheedModel')
        self.mock_naif_class = patcher4.start()
        self.mock_naif = self.mock_naif_class.return_value
        self.addCleanup(patcher4.stop)
        
        patcher5 = patch('claude_integration.chat_interface.AdaptiveLearningDB')
        self.mock_adaptive_class = patcher5.start()
        self.mock_adaptive = self.mock_adaptive_class.return_value
        self.addCleanup(patcher5.stop)
        
        # Create chat interface with mocked dependencies
        self.chat = ChatInterface(user_id=1)
        self.chat.claude_handler = self.mock_claude
        self.chat.stock_analyzer = self.mock_analyzer
        self.chat.portfolio_manager = self.mock_portfolio
        self.chat.naif_model = self.mock_naif
        self.chat.adaptive_learning = self.mock_adaptive
    
    def test_analyze_stock_command(self):
        """Test analyze_stock command handler"""
        # Mock the stock analyzer
        sample_results = {
            'current_price': 150.0,
            'change_percent': 2.5,
            'sector': 'Technology',
            'sentiment_score': 75.0,
            'price_momentum': 3.2,
            'pe_ratio': 22.5,
            'dividend_yield': 1.8
        }
        self.mock_analyzer.analyze_stock.return_value = sample_results
        
        # Call the command handler
        response, visualizations = self.chat._analyze_stock_command('AAPL')
        
        # Verify the analyzer was called with correct symbol
        self.mock_analyzer.analyze_stock.assert_called_once_with('AAPL')
        
        # Verify response contains expected data
        self.assertIn('AAPL', response)
        self.assertIn('$150.0', response)
        self.assertIn('2.5%', response)
        self.assertIn('Technology', response)
        self.assertIn('75.0/100', response)
        
        # Verify context was updated
        self.assertEqual(self.chat.context['last_analysis']['symbol'], 'AAPL')
        self.assertEqual(self.chat.context['last_analysis']['data'], sample_results)
        self.assertIn('AAPL', self.chat.context['current_stocks'])
        
        # Verify adaptive learning was updated
        self.mock_adaptive.record_stock_view.assert_called_once_with('AAPL', sector='Technology')
        
        # Verify visualizations were created
        self.assertIn('price_chart', visualizations)
        self.assertIn('sentiment_gauge', visualizations)
    
    def test_help_command(self):
        """Test help command handler"""
        response, visualizations = self.chat._help_command()
        
        # Verify response contains expected sections
        self.assertIn('Commands', response)
        self.assertIn('Stock Analysis', response)
        self.assertIn('Portfolio Management', response)
        self.assertIn('Investment Models', response)
        
        # No visualizations expected for help command
        self.assertIsNone(visualizations)
    
    def test_command_pattern_matching(self):
        """Test command pattern matching"""
        # Test analyze stock pattern
        result = self.chat._check_for_commands('analyze AAPL')
        self.assertIsNotNone(result)
        
        # Test compare stocks pattern
        result = self.chat._check_for_commands('compare MSFT and AAPL')
        self.assertIsNotNone(result)
        
        # Test portfolio summary pattern
        result = self.chat._check_for_commands('portfolio summary')
        self.assertIsNotNone(result)
        
        # Test sector analysis pattern
        result = self.chat._check_for_commands('sector analysis')
        self.assertIsNotNone(result)
        
        # Test help pattern
        result = self.chat._check_for_commands('help')
        self.assertIsNotNone(result)
        result = self.chat._check_for_commands('commands')
        self.assertIsNotNone(result)
        
        # Test non-matching pattern
        result = self.chat._check_for_commands('hello there')
        self.assertIsNone(result)
    
    def test_process_message_command(self):
        """Test processing a message with a command"""
        # Mock command handler
        self.chat._analyze_stock_command = MagicMock(return_value=('Stock analysis response', {'chart': 'data'}))
        
        # Process a message with a command
        response = self.chat.process_message('analyze AAPL', include_visualizations=True)
        
        # Verify command handler was called
        self.chat._analyze_stock_command.assert_called_once()
        
        # Verify response format
        self.assertEqual(response['text'], 'Stock analysis response')
        self.assertEqual(response['visualizations'], {'chart': 'data'})
        
        # Verify message was added to chat history
        self.assertEqual(len(self.chat.chat_history), 2)
        self.assertEqual(self.chat.chat_history[0]['role'], 'user')
        self.assertEqual(self.chat.chat_history[0]['content'], 'analyze AAPL')
        self.assertEqual(self.chat.chat_history[1]['role'], 'assistant')
        self.assertEqual(self.chat.chat_history[1]['content'], 'Stock analysis response')
    
    def test_process_message_with_claude(self):
        """Test processing a message that goes to Claude"""
        # Mock Claude response
        class Content:
            def __init__(self, text):
                self.text = text
                
        class ClaudeResponse:
            def __init__(self, content):
                self.content = content
                
        self.mock_claude.chat_completion.return_value = ClaudeResponse([Content("Claude's response")])
        
        # Process a message that doesn't match any command
        response = self.chat.process_message('What do you think about tech stocks?')
        
        # Verify Claude was called
        self.mock_claude.chat_completion.assert_called_once()
        
        # Verify response
        self.assertEqual(response['text'], "Claude's response")
        
        # Verify message was added to chat history
        self.assertEqual(len(self.chat.chat_history), 2)
        self.assertEqual(self.chat.chat_history[0]['role'], 'user')
        self.assertEqual(self.chat.chat_history[0]['content'], 'What do you think about tech stocks?')
        self.assertEqual(self.chat.chat_history[1]['role'], 'assistant')
        self.assertEqual(self.chat.chat_history[1]['content'], "Claude's response")
    
    def test_extract_stock_symbols(self):
        """Test extracting stock symbols from text"""
        text = "AAPL is showing strong momentum while MSFT has better fundamentals than INTC."
        
        # Clear current stocks
        self.chat.context['current_stocks'] = []
        
        # Extract symbols
        self.chat._extract_stock_symbols(text)
        
        # Verify symbols were extracted
        extracted_symbols = self.chat.context['current_stocks']
        self.assertIn('AAPL', extracted_symbols)
        self.assertIn('MSFT', extracted_symbols)
        self.assertIn('INTC', extracted_symbols)
        
        # Test filtering common words
        text = "THE MARKET showed A significant drop IN recent days."
        self.chat.context['current_stocks'] = []
        self.chat._extract_stock_symbols(text)
        
        # Common words should be filtered out
        self.assertEqual(len(self.chat.context['current_stocks']), 0)

if __name__ == '__main__':
    unittest.main()