# claude_integration/chat_interface.py

import os
import logging
import json
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from anthropic import Anthropic

from analysis.enhanced_stock_analyzer import EnhancedStockAnalyzer
from portfolio.portfolio_management import PortfolioManager
from claude_integration.claude_handler import ClaudeHandler
from ml_components.naif_alrasheed_model import NaifAlRasheedModel
from ml_components.adaptive_learning_db import AdaptiveLearningDB
from behavioral.behavioral_bias_analyzer import BehavioralBiasAnalyzer, InvestmentDecisionFramework
from portfolio.advanced_portfolio_analytics import AdvancedPortfolioAnalytics
from user_profiling.cfa_profiler import CFAProfiler

class ChatInterface:
    """
    Chat interface for natural language interactions with the investment bot.
    
    Handles:
    - Command parsing and interpretation
    - Stock analysis requests
    - Portfolio management
    - Investment recommendations
    - Context management
    """
    
    def __init__(self, user_id: Optional[int] = None):
        self.logger = logging.getLogger(__name__)
        self.user_id = user_id
        self.claude_handler = ClaudeHandler()
        self.stock_analyzer = EnhancedStockAnalyzer()
        self.portfolio_manager = PortfolioManager()
        self.naif_model = NaifAlRasheedModel()
        
        # Initialize adaptive learning if user_id provided
        self.adaptive_learning = None
        self.bias_analyzer = None
        self.decision_framework = None
        self.portfolio_analytics = None
        self.cfa_profiler = None
        
        if user_id:
            self.adaptive_learning = AdaptiveLearningDB(user_id)
            self.bias_analyzer = BehavioralBiasAnalyzer(user_id)
            self.decision_framework = InvestmentDecisionFramework(user_id)
            self.portfolio_analytics = AdvancedPortfolioAnalytics()
            self.cfa_profiler = CFAProfiler(user_id)
        
        # Command patterns
        self.command_patterns = {
            'analyze_stock': re.compile(r'analyze\s+([A-Za-z0-9.]+)', re.IGNORECASE),
            'compare_stocks': re.compile(r'compare\s+([A-Za-z0-9.]+)\s+and\s+([A-Za-z0-9.]+)', re.IGNORECASE),
            'portfolio_summary': re.compile(r'portfolio\s+summary', re.IGNORECASE),
            'portfolio_optimize': re.compile(r'optimize\s+portfolio', re.IGNORECASE),
            'sector_analysis': re.compile(r'sector\s+analysis', re.IGNORECASE),
            'run_naif_model': re.compile(r'run\s+naif\s+model', re.IGNORECASE),
            'run_naif_model_market': re.compile(r'run\s+naif\s+model\s+for\s+([A-Za-z]+)\s+market', re.IGNORECASE),
            # CFA-related commands
            'show_investment_profile': re.compile(r'show\s+(my\s+)?(investment|risk)\s+profile', re.IGNORECASE),
            'behavioral_biases': re.compile(r'(my\s+)?(behavioral\s+biases|bias\s+analysis)', re.IGNORECASE),
            'factor_analysis': re.compile(r'(run\s+)?factor\s+analysis', re.IGNORECASE),
            'investment_policy': re.compile(r'(show\s+)?(my\s+)?investment\s+policy(\s+statement)?', re.IGNORECASE),
            'record_decision': re.compile(r'record\s+(investment\s+)?decision', re.IGNORECASE),
            'get_recommendations': re.compile(r'(?:get|show)\s+(?:stock)?\s*recommendations', re.IGNORECASE),
            'sentiment_analysis': re.compile(r'(?:analyze|check)\s+sentiment\s+(?:for|of)\s+([A-Za-z0-9.]+)', re.IGNORECASE),
            'customize_sentiment': re.compile(r'customize\s+sentiment\s+weights', re.IGNORECASE),
            'set_risk_profile': re.compile(r'set\s+(?:my)?\s+risk\s+(?:profile|tolerance)\s+(?:to)?\s+([a-z]+)', re.IGNORECASE),
            'analyze_portfolio_risk': re.compile(r'analyze\s+(?:my)?\s+portfolio\s+risk', re.IGNORECASE),
            'monte_carlo': re.compile(r'run\s+monte\s+carlo\s+(?:simulation|analysis)', re.IGNORECASE),
            'valuation_analysis': re.compile(r'run\s+valuation\s+analysis\s+(?:for|on)\s+([A-Za-z0-9.]+)', re.IGNORECASE),
            'technical_analysis': re.compile(r'run\s+technical\s+analysis\s+(?:for|on)\s+([A-Za-z0-9.]+)', re.IGNORECASE),
            'fundamental_analysis': re.compile(r'run\s+fundamental\s+analysis\s+(?:for|on)\s+([A-Za-z0-9.]+)', re.IGNORECASE),
            'balance_sheet': re.compile(r'(?:get|show)\s+balance\s+sheet\s+(?:for|of)\s+([A-Za-z0-9.]+)', re.IGNORECASE),
            'learn_preference': re.compile(r'remember\s+(?:that)?\s+i\s+(?:like|prefer|prioritize)\s+([a-z\s]+)', re.IGNORECASE),
            'add_to_portfolio': re.compile(r'add\s+(\d+)\s+shares?\s+of\s+([A-Za-z0-9.]+)(?:\s+to\s+portfolio)?', re.IGNORECASE),
            'portfolio_impact': re.compile(r'show\s+(?:portfolio\s+)?impact\s+(?:of\s+)?([A-Za-z0-9.]+)', re.IGNORECASE),
            'menu': re.compile(r'(?:show|display)?\s*(?:menu|options|what can you do|what are your capabilities|what functions|functionality)', re.IGNORECASE),
            'menu_selection': re.compile(r'^(\d{1,2})$', re.IGNORECASE), # Changed to match digits 1-99
            'upload_portfolio': re.compile(r'upload\s+(?:my)?\s*portfolio', re.IGNORECASE),
            'process_attachment': re.compile(r'(?:process|analyze)\s+(?:attachment|file|document|image)(?:\s+(\w+))?', re.IGNORECASE),
            'help': re.compile(r'help|commands', re.IGNORECASE),
            # ML Learning commands
            'train_ml': re.compile(r'train\s+(?:ml|machine learning)(?:\s+on\s+(.+))?', re.IGNORECASE),
            'feedback_ml': re.compile(r'(?:feedback|correct)\s+prediction(?:\s+for\s+([A-Za-z0-9.]+))?(?:\s+to\s+([A-Za-z0-9.]+))?', re.IGNORECASE),
            'analyze_with_ml': re.compile(r'analyze\s+with\s+ml\s+([A-Za-z0-9.]+)', re.IGNORECASE),
            'ml_status': re.compile(r'(?:show|get)\s+ml\s+(?:status|metrics|performance)', re.IGNORECASE),
            'reset_ml': re.compile(r'reset\s+ml\s+(?:model|engine|learning)', re.IGNORECASE)
        }
        
        # Chat context - stored in memory for this implementation
        # In a production system, this would be stored in a database
        self.chat_history = []
        self.context = {
            'current_stocks': [],
            'current_portfolio_id': None,
            'last_analysis': None,
            'current_menu_state': None,
            'attachments': []
        }
        
        # Define the main menu options (using numbers instead of letters)
        self.menu_options = {
            '1': {
                'title': 'Analyze a Stock',
                'description': 'Get comprehensive analysis of any stock ticker',
                'prompt': 'Please enter the stock symbol you want to analyze (e.g., AAPL, MSFT):',
                'command': 'analyze_stock',
                'parameters': ['symbol']
            },
            '2': {
                'title': 'Compare Stocks',
                'description': 'Compare two stocks side by side',
                'prompt': 'Please enter the two stock symbols you want to compare, separated by a space (e.g., AAPL MSFT):',
                'command': 'compare_stocks',
                'parameters': ['symbol1', 'symbol2']
            },
            '3': {
                'title': 'Portfolio Management',
                'description': 'View, analyze and optimize your investment portfolio',
                'prompt': 'Please select a portfolio option:\n1. View portfolio summary\n2. Optimize portfolio\n3. Analyze portfolio risk\n4. Run Monte Carlo simulation\n5. Import portfolio from file',
                'command': 'portfolio_options',
                'parameters': ['option']
            },
            '4': {
                'title': 'Run Naif Al-Rasheed Model',
                'description': 'Run the Naif Al-Rasheed investment model for stock screening',
                'prompt': 'Please select a market for the Naif Al-Rasheed model:\n1. US Market\n2. Saudi Market\n3. All Markets',
                'command': 'naif_model',
                'parameters': ['market']
            },
            '5': {
                'title': 'Get Stock Recommendations',
                'description': 'Receive personalized stock recommendations based on your profile',
                'prompt': 'I\'ll generate personalized stock recommendations for you. Do you want to:\n1. Use your existing preference profile\n2. Set up a new preference profile\n3. Get recommendations based on specific criteria',
                'command': 'recommendations',
                'parameters': ['option']
            },
            '6': {
                'title': 'Sentiment Analysis',
                'description': 'Check market sentiment for a specific stock or sector',
                'prompt': 'Please enter the stock symbol or sector name you want to analyze sentiment for:',
                'command': 'sentiment',
                'parameters': ['symbol']
            },
            '7': {
                'title': 'Risk Management',
                'description': 'Configure risk parameters and perform risk analysis',
                'prompt': 'Please select a risk management option:\n1. Set your personal risk profile\n2. Analyze portfolio risk\n3. Run Monte Carlo simulation\n4. Optimize risk-adjusted returns\n5. Analyze diversification',
                'command': 'risk_management',
                'parameters': ['option']
            },
            '8': {
                'title': 'Market Analysis',
                'description': 'Analyze market sectors, trends and economic conditions',
                'prompt': 'Please select a market analysis option:\n1. Sector performance overview\n2. Analysis of a specific sector\n3. Market trends\n4. Economic indicators\n5. Market correlation analysis',
                'command': 'market_analysis',
                'parameters': ['option']
            },
            '9': {
                'title': 'Technical Analysis',
                'description': 'Run detailed technical analysis for a stock',
                'prompt': 'Please enter the stock symbol you want to run technical analysis for:',
                'command': 'technical_analysis',
                'parameters': ['symbol']
            },
            '10': {
                'title': 'Fundamental Analysis',
                'description': 'Analyze company financials and valuation metrics',
                'prompt': 'Please enter the stock symbol you want to run fundamental analysis for:',
                'command': 'fundamental_analysis',
                'parameters': ['symbol']
            },
            '11': {
                'title': 'View Balance Sheet',
                'description': 'Examine detailed company balance sheet information',
                'prompt': 'Please enter the stock symbol to view its balance sheet:',
                'command': 'balance_sheet',
                'parameters': ['symbol']
            },
            '12': {
                'title': 'Upload Files',
                'description': 'Analyze uploaded financial documents or portfolio files',
                'prompt': 'Please select the type of file you want to upload:\n1. Portfolio (CSV/Excel)\n2. Financial statements\n3. Market data\n4. Other financial document\n\nThen click the + icon to upload.',
                'command': 'upload_files',
                'parameters': ['file_type']
            },
            '13': {
                'title': 'Educational Resources',
                'description': 'Learn about investing concepts and strategies',
                'prompt': 'What investment topic would you like to learn about?\n1. Investment basics\n2. Technical analysis indicators\n3. Fundamental analysis metrics\n4. Portfolio theory\n5. Risk management\n6. Other (please specify)',
                'command': 'education',
                'parameters': ['topic']
            },
            '14': {
                'title': 'Custom Analysis',
                'description': 'Request specialized analysis not covered in other options',
                'prompt': 'Please describe the custom analysis you\'d like me to perform:',
                'command': 'custom_analysis',
                'parameters': ['description']
            },
            '15': {
                'title': 'Set Investment Preferences',
                'description': 'Configure your investment preferences and priorities',
                'prompt': 'What investment preferences would you like to set?\n1. Preferred sectors\n2. Investment style (growth/value/income)\n3. ESG preferences\n4. Geographic preferences\n5. Other (please specify)',
                'command': 'set_preferences',
                'parameters': ['preference_type']
            },
            '16': {
                'title': 'Investment Profile',
                'description': 'View your CFA-based investment profile and behavioral analysis',
                'prompt': 'Please select a profile option:\n1. View investment profile\n2. Behavioral bias analysis\n3. Investment Policy Statement\n4. Factor analysis\n5. Record investment decision',
                'command': 'investment_profile',
                'parameters': ['option']
            }
        }
    
    def process_message(self, message: str, include_visualizations: bool = False, attachment: Optional[Dict] = None) -> Dict:
        """
        Process a user message and return a response
        
        Args:
            message: The user's message
            include_visualizations: Whether to include visualizations in the response
            attachment: Optional attachment data (file path, type, etc.)
            
        Returns:
            Dict with response text and any visualizations
        """
        # Special case for ML reset confirmation
        if message.lower().strip() == 'confirm reset ml' and self.context.get('pending_ml_reset'):
            confirmation_result = self._confirm_reset_ml()
            
            response = {'text': confirmation_result[0]}
            if include_visualizations and confirmation_result[1]:
                response['visualizations'] = confirmation_result[1]
                
            # Add bot response to chat history
            self.chat_history.append({'role': 'assistant', 'content': confirmation_result[0], 'timestamp': datetime.now().isoformat()})
            return response
        # Special case for empty or initial message - show menu immediately
        if not message or message.strip() == "":
            # Show welcome message with the menu
            menu_result = self._show_menu_command()
            welcome_text = "<div style='text-align:center; margin-bottom:20px;'><h2>👋 Welcome to your Investment Assistant!</h2><p>Please select one of the options below:</p></div>\n\n" + menu_result[0]
            
            # Add to chat history
            self.chat_history.append({'role': 'assistant', 'content': welcome_text, 'timestamp': datetime.now().isoformat()})
            
            # Set menu state
            self.context['current_menu_state'] = 'main'
            
            return {'text': welcome_text}
            
        # Add user message to chat history
        self.chat_history.append({'role': 'user', 'content': message, 'timestamp': datetime.now().isoformat()})
        
        # Handle attachments if provided
        if attachment:
            # Store attachment in context
            if 'attachments' not in self.context:
                self.context['attachments'] = []
            self.context['attachments'].append(attachment)
            
            # Acknowledge the attachment
            response = {'text': f"I've received your attachment: {attachment.get('file_name', 'file')}. To analyze this file, type 'process attachment'."}
            self.chat_history.append({'role': 'assistant', 'content': response['text'], 'timestamp': datetime.now().isoformat()})
            return response
        
        # Check for commands first
        command_result = self._check_for_commands(message)
        if command_result:
            response_text, visualizations = command_result
            response = {'text': response_text}
            
            if include_visualizations and visualizations:
                response['visualizations'] = visualizations
                
            # Add bot response to chat history
            self.chat_history.append({'role': 'assistant', 'content': response_text, 'timestamp': datetime.now().isoformat()})
            return response
        
        # Check for "what can you do" type questions
        capability_questions = [
            "what can you do",
            "how can i use you",
            "what can you do for me",
            "how do i use this",
            "help me get started",
            "what are your capabilities",
            "what do you do",
            "tell me what you can do",
            "what are your features"
        ]
        
        # Direct match for capability questions
        if any(message.lower().strip() == question or message.lower().strip() == question + "?" for question in capability_questions):
            # Skip Claude API completely for this specific question
            # Show the menu immediately with minimal text and a clear follow-up prompt
            menu_result = self._show_menu_command()
            response_text = "Here are the functions I can help you with:\n\n" + menu_result[0]
            
            self.chat_history.append({'role': 'assistant', 'content': response_text, 'timestamp': datetime.now().isoformat()})
            
            # Set menu state
            self.context['current_menu_state'] = 'main'
            
            return {'text': response_text}
                
        # For direct "yes" responses that might be looking for the menu
        if message.lower().strip() in ["yes", "menu", "show menu", "y"]:
            # Show the menu
            menu_result = self._show_menu_command()
            response = {'text': menu_result[0]}
            self.chat_history.append({'role': 'assistant', 'content': menu_result[0], 'timestamp': datetime.now().isoformat()})
            return response
        
        # Check for explicit menu commands
        menu_patterns = [
            r'(?:show|display)\s+menu',
            r'show\s+me\s+the\s+menu',
            r'available\s+functions',
            r'available\s+features',
            r'list\s+your\s+features',
            r'main\s+menu',
            r'menu\s+of\s+options'
        ]
        
        for pattern in menu_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                menu_result = self._show_menu_command()
                response = {'text': menu_result[0]}
                self.chat_history.append({'role': 'assistant', 'content': menu_result[0], 'timestamp': datetime.now().isoformat()})
                return response
        
        # If no command matched, process with Claude
        try:
            # Prepare stock and portfolio context from the chat context
            stock_context = None
            if self.context.get('last_analysis'):
                stock_context = self.context['last_analysis']
            
            # Extract potential stock symbols from current message and add to context
            self._extract_stock_symbols(message)
                
            # Add additional context about discussed stocks
            if self.context['current_stocks'] and not stock_context:
                stock_context = {
                    'symbols_in_discussion': self.context['current_stocks'],
                    'last_mentioned': self.context['current_stocks'][-1] if self.context['current_stocks'] else None
                }
                
            portfolio_context = None
            if self.context.get('current_portfolio_id'):
                portfolio_context = {'portfolio_id': self.context['current_portfolio_id']}
                
            # If user has set preferences, include them
            if 'preferences' in self.context and self.context['preferences']:
                if not stock_context:
                    stock_context = {}
                stock_context['user_preferences'] = self.context['preferences']
                
            # Include risk profile if set
            if 'risk_profile' in self.context:
                if not stock_context:
                    stock_context = {}
                stock_context['risk_profile'] = self.context['risk_profile']
            
            # Include menu information if in a menu state
            if self.context.get('current_menu_state'):
                if not stock_context:
                    stock_context = {}
                stock_context['menu_state'] = self.context['current_menu_state']
            
            # Send to Claude for processing using the chat_with_assistant method
            claude_response = self.claude_handler.chat_with_assistant(
                user_id=str(self.user_id),
                user_message=message,
                stock_context=stock_context,
                portfolio_context=portfolio_context
            )
            
            response_text = claude_response.get('response', "I'm sorry, I couldn't process your request.")
            
            # Add bot response to chat history
            self.chat_history.append({'role': 'assistant', 'content': response_text, 'timestamp': datetime.now().isoformat()})
            
            # Extract any potential stock symbols mentioned by Claude
            self._extract_stock_symbols(response_text)
            
            # No need to suggest menu here as we handle these patterns earlier
            
            return {'text': response_text}
            
        except Exception as e:
            self.logger.error(f"Error processing message with Claude: {str(e)}")
            error_response = "I'm sorry, I encountered an error processing your request. Please try again."
            self.chat_history.append({'role': 'assistant', 'content': error_response, 'timestamp': datetime.now().isoformat()})
            return {'text': error_response}
    
    def _check_for_commands(self, message: str) -> Optional[Tuple[str, Optional[Dict]]]:
        """
        Check if the message contains a command and execute it
        
        Args:
            message: The user's message
            
        Returns:
            Optional tuple of (response_text, visualizations)
        """
        # Check if we have a pending selection from the previous interaction
        if self.context.get('pending_selection'):
            selection = self.context.pop('pending_selection')  # Get and remove pending selection
            if selection.isdigit() and selection in self.menu_options:
                return self._process_menu_selection(selection)
        
        # Check if we're in a menu state expecting a selection
        if self.context.get('current_menu_state'):
            menu_selection = message.strip()
            
            # If menu selection is a valid option, process it
            if menu_selection in self.menu_options or menu_selection.isdigit():
                return self._process_menu_selection(menu_selection)
                
            # If it doesn't look like a menu selection, clear the menu state
            # and continue with normal command processing
            self.context['current_menu_state'] = None
        
        # Check each command pattern
        for command, pattern in self.command_patterns.items():
            match = pattern.search(message)
            if match:
                if command == 'analyze_stock':
                    symbol = match.group(1).upper()
                    return self._analyze_stock_command(symbol)
                elif command == 'compare_stocks':
                    symbol1 = match.group(1).upper()
                    symbol2 = match.group(2).upper()
                    return self._compare_stocks_command(symbol1, symbol2)
                elif command == 'portfolio_summary':
                    return self._portfolio_summary_command()
                elif command == 'portfolio_optimize':
                    return self._portfolio_optimize_command()
                elif command == 'sector_analysis':
                    return self._sector_analysis_command()
                elif command == 'run_naif_model':
                    return self._run_naif_model_command()
                elif command == 'run_naif_model_market':
                    market = match.group(1).lower()
                    return self._run_naif_model_market_command(market)
                elif command == 'get_recommendations':
                    return self._get_recommendations_command()
                elif command == 'sentiment_analysis':
                    symbol = match.group(1).upper()
                    return self._sentiment_analysis_command(symbol)
                elif command == 'customize_sentiment':
                    return self._customize_sentiment_command()
                elif command == 'set_risk_profile':
                    risk_level = match.group(1).lower()
                    return self._set_risk_profile_command(risk_level)
                elif command == 'analyze_portfolio_risk':
                    return self._analyze_portfolio_risk_command()
                elif command == 'monte_carlo':
                    return self._monte_carlo_command()
                elif command == 'valuation_analysis':
                    symbol = match.group(1).upper()
                    return self._valuation_analysis_command(symbol)
                elif command == 'technical_analysis':
                    symbol = match.group(1).upper()
                    return self._technical_analysis_command(symbol)
                elif command == 'fundamental_analysis':
                    symbol = match.group(1).upper()
                    return self._fundamental_analysis_command(symbol)
                elif command == 'balance_sheet':
                    symbol = match.group(1).upper()
                    return self._balance_sheet_command(symbol)
                elif command == 'learn_preference':
                    preference = match.group(1).lower()
                    return self._learn_preference_command(preference)
                elif command == 'add_to_portfolio':
                    quantity = int(match.group(1))
                    symbol = match.group(2).upper()
                    return self._add_to_portfolio_command(symbol, quantity)
                elif command == 'portfolio_impact':
                    symbol = match.group(1).upper()
                    return self._portfolio_impact_command(symbol)
                elif command == 'menu':
                    return self._show_menu_command()
                elif command == 'menu_selection':
                    selection = match.group(1).lower()
                    return self._process_menu_selection(selection)
                elif command == 'upload_portfolio':
                    return self._upload_portfolio_command()
                elif command == 'process_attachment':
                    file_type = match.group(1) if match.groups() else None
                    return self._process_attachment_command(file_type)
                elif command == 'help':
                    return self._help_command()
                # ML training commands
                elif command == 'train_ml':
                    data_source = match.group(1) if match.groups() else None
                    return self._train_ml_command(data_source)
                elif command == 'feedback_ml':
                    stock = match.group(1) if len(match.groups()) > 0 and match.group(1) else None
                    correction = match.group(2) if len(match.groups()) > 1 and match.group(2) else None
                    return self._feedback_ml_command(stock, correction)
                elif command == 'analyze_with_ml':
                    symbol = match.group(1).upper()
                    return self._analyze_with_ml_command(symbol)
                elif command == 'ml_status':
                    return self._ml_status_command()
                elif command == 'reset_ml':
                    return self._reset_ml_command()
                # CFA-related commands
                elif command == 'show_investment_profile':
                    return self._handle_show_investment_profile(message)
                elif command == 'behavioral_biases':
                    return self._handle_behavioral_biases(message)
                elif command == 'factor_analysis':
                    return self._handle_factor_analysis(message)
                elif command == 'investment_policy':
                    return self._handle_investment_policy(message)
                elif command == 'record_decision':
                    return self._handle_record_decision(message)
        
        # Also check for direct symbol-only inputs (e.g., "AAPL")
        symbol_match = re.match(r'^([A-Za-z0-9.]+)$', message.strip())
        if symbol_match:
            symbol = symbol_match.group(1).upper()
            return self._analyze_stock_command(symbol)
            
        # No command matched
        return None
        
    def _show_menu_command(self) -> Tuple[str, None]:
        """Display a visually structured menu with interactive elements"""
        # Start with a simple introduction
        response = "## Investment Bot Menu\n\n"
        
        # Group menu options into categories for better organization
        categories = {
            "Stock Analysis": ["1", "2", "9", "10", "11"],
            "Portfolio Management": ["3", "7"],
            "Investment Models": ["4", "5", "8"],
            "Analysis Tools": ["6", "12", "14"],
            "Learning & Preferences": ["13", "15"],
            "CFA Features": ["16"]
        }
        
        # Generate menu with HTML-styled elements
        for category, option_keys in categories.items():
            # Add category heading
            response += f'<div class="menu-category">{category}</div>\n\n'
            
            for key in option_keys:
                if key in self.menu_options:
                    option = self.menu_options[key]
                    # Create a clickable menu item with number, title and description
                    response += f'<div class="menu-item" onclick="document.getElementById(\'chatInput\').value=\'{key}\'; document.getElementById(\'sendButton\').click();">\n'
                    response += f'  <div class="menu-item-title">{key}. {option["title"]}</div>\n'
                    response += f'  <div class="menu-item-description">{option["description"]}</div>\n'
                    response += f'</div>\n\n'
                    
        # Add ML options as a special category
        response += f'<div class="menu-category">Machine Learning Features</div>\n\n'
        
        # ML options
        ml_options = [
            {"command": "analyze with ml AAPL", "title": "Analyze with ML", "description": "Analyze a stock using your personalized ML model"},
            {"command": "train ml", "title": "Train ML Model", "description": "Train your ML model based on your preferences"},
            {"command": "show ml status", "title": "ML Profile", "description": "View your ML profile and preferences"},
            {"command": "feedback for AAPL to like", "title": "Provide Feedback", "description": "Give feedback on stocks to improve ML accuracy"}
        ]
        
        for option in ml_options:
            response += f'<div class="menu-item" onclick="document.getElementById(\'chatInput\').value=\'{option["command"]}\'; document.getElementById(\'sendButton\').click();">\n'
            response += f'  <div class="menu-item-title">{option["title"]}</div>\n'
            response += f'  <div class="menu-item-description">{option["description"]}</div>\n'
            response += f'</div>\n\n'
        
        # Add follow-up prompt with clear instructions
        response += '<div class="menu-prompt">Please select an option above, type a number, or enter a command like "analyze AAPL"</div>'
        
        # Set menu state
        self.context['current_menu_state'] = 'main'
        
        return response, None
        
    def _process_menu_selection(self, selection: str) -> Tuple[str, Optional[Dict]]:
        """Process a menu selection"""
        selection = selection.strip()
        
        # Handle main menu selection
        if self.context.get('current_menu_state') == 'main':
            if selection in self.menu_options:
                option = self.menu_options[selection]
                
                # Set the selected option as the current menu state
                self.context['current_menu_state'] = f"option_{selection}"
                
                # Return the prompt for the selected option
                return option['prompt'], None
            else:
                return f"Invalid selection '{selection}'. Please select a valid option from the menu (1-16).", None
                
        # Handle sub-menu selections based on the current menu state
        elif self.context.get('current_menu_state', '').startswith('option_'):
            option_key = self.context['current_menu_state'].split('_')[1]
            option = self.menu_options.get(option_key)
            
            if not option:
                # Reset menu state
                self.context['current_menu_state'] = None
                return "Invalid menu state. Please try selecting from the main menu again.", None
                
            # Handle option 16 (Investment Profile) specifically
            if option_key == '16':
                sub_option = selection.strip()
                # Reset menu state
                self.context['current_menu_state'] = None
                
                if sub_option == '1':
                    return self._handle_show_investment_profile(sub_option)
                elif sub_option == '2':
                    return self._handle_behavioral_biases(sub_option)
                elif sub_option == '3':
                    return self._handle_investment_policy(sub_option)
                elif sub_option == '4':
                    return self._handle_factor_analysis(sub_option)
                elif sub_option == '5':
                    return self._handle_record_decision(sub_option)
                else:
                    return "Invalid selection. Please select a valid option from the menu.", None
                    
            # Other options handled by existing methods...
            
            # Reset menu state after processing
            self.context['current_menu_state'] = None
            
            # Schedule further implementation here...
            return f"You selected {option['title']}. This feature is currently being implemented.", None
        
        # If not in a recognized menu state, return error
        else:
            # Reset menu state
            self.context['current_menu_state'] = None
            return "Invalid menu state. Please try selecting from the main menu again.", None
    
    def _extract_stock_symbols(self, text: str) -> None:
        """Extract potential stock symbols from text and add to context"""
        # Simple pattern matching for stock symbols in text
        # This is a basic implementation - in a production system this would be more sophisticated
        symbol_pattern = r'\b[A-Z]{1,5}\b'  # Uppercase letters 1-5 characters
        potential_symbols = re.findall(symbol_pattern, text)
        
        # Filter out common words that might be mistaken for symbols
        common_words = ['I', 'A', 'FOR', 'TO', 'IN', 'ON', 'BY', 'AT', 'AND', 'OR', 'THE', 'IS', 'BE', 'AS', 'OF', 'IF']
        filtered_symbols = [s for s in potential_symbols if s not in common_words]
        
        # Add to context (without duplicates)
        for symbol in filtered_symbols:
            if symbol not in self.context['current_stocks']:
                self.context['current_stocks'].append(symbol)
    
    # Placeholder for analysis command
    def _analyze_stock_command(self, symbol: str) -> Tuple[str, Optional[Dict]]:
        """Analyze a stock with comprehensive metrics"""
        if not self.stock_analyzer:
            return "Stock analysis component is not available.", None
            
        try:
            # Get user's adaptive learning profile if available
            adaptive_preferences = None
            if self.adaptive_learning:
                # This will adjust the analysis based on user preferences
                adaptive_preferences = self.adaptive_learning.get_user_preferences()
                
                # Record this interaction
                self.adaptive_learning.record_view(symbol)
                
            # Analyze the stock
            analysis_result = self.stock_analyzer.analyze_stock(symbol, user_preferences=adaptive_preferences)
            
            if not analysis_result:
                return f"Could not find analysis data for {symbol}. Please check the symbol and try again.", None
                
            # Store analysis in context for follow-up questions
            self.context['last_analysis'] = {
                'symbol': symbol,
                'analysis': analysis_result
            }
            
            # In production, you would serialize this to be sent to Claude
            analysis_json = json.dumps(analysis_result, default=str)
            
            # Generate response using Claude
            prompt = f"You are a financial assistant. Generate a detailed but concise analysis of {symbol} based on this data.\n\n{analysis_json}"
            
            response = self.claude_handler.simple_completion(prompt, max_tokens=1000)
            
            return response, None
            
        except Exception as e:
            self.logger.error(f"Error analyzing stock {symbol}: {str(e)}")
            return f"Error analyzing {symbol}: {str(e)}", None
            
    # Placeholder for compare command
    def _compare_stocks_command(self, symbol1: str, symbol2: str) -> Tuple[str, Optional[Dict]]:
        """Compare two stocks side by side"""
        return f"Comparing {symbol1} and {symbol2}. (This is a placeholder for the compare command)", None
        
    # Placeholder for portfolio summary command  
    def _portfolio_summary_command(self) -> Tuple[str, Optional[Dict]]:
        """Display portfolio summary"""
        # Simulate delay for a realistic interaction
        chat_response = "This is a placeholder for the portfolio summary command."
            
        # Format the result
        return f"Portfolio summary:\n\n{chat_response}", None
        
    # Placeholder for portfolio optimize command
    def _portfolio_optimize_command(self) -> Tuple[str, Optional[Dict]]:
        """Optimize portfolio allocation"""
        return "This is a placeholder for the portfolio optimize command.", None
    
    # Placeholder for sector analysis command  
    def _sector_analysis_command(self) -> Tuple[str, Optional[Dict]]:
        """Analyze market sectors"""
        return "This is a placeholder for the sector analysis command.", None
        
    # Placeholder for naif model command
    def _run_naif_model_command(self) -> Tuple[str, Optional[Dict]]:
        """Run Naif Al-Rasheed investment model"""
        return "This is a placeholder for the Naif model command.", None
    
    # Placeholder for naif model market command  
    def _run_naif_model_market_command(self, market: str) -> Tuple[str, Optional[Dict]]:
        """Run Naif Al-Rasheed investment model for specific market"""
        return f"This is a placeholder for the Naif model {market} market command.", None
        
    # CFA-related command handlers  
    def _handle_show_investment_profile(self, message: str) -> Tuple[str, Optional[Dict]]:
        """Handle request to show the user's investment profile."""
        if not self.user_id or not self.cfa_profiler:
            return "Please log in to view your investment profile.", None
            
        try:
            # Get user profile
            profile_data = self.cfa_profiler.get_user_profile()
            
            if not profile_data:
                return "You haven't completed your investment profile yet. Please visit the profiling section to create your profile.", None
                
            # Format profile data for chat
            profile_category = profile_data['profile_category']
            risk_tolerance = profile_data['risk_scores']['risk_tolerance']
            time_horizon = profile_data['investment_constraints']['investment_horizon']
            asset_allocation = profile_data['asset_allocation']
            
            # Create allocation text
            allocation_text = "**Recommended Asset Allocation:**\n"
            for asset_class, percentage in asset_allocation.items():
                allocation_text += f"- {asset_class.capitalize()}: {percentage}%\n"
                
            # Format response
            response = f"""## Your Investment Profile

**Profile Category:** {profile_category}
**Risk Tolerance:** {risk_tolerance:.1f}%
**Investment Horizon:** {time_horizon} years

{allocation_text}

**Top Behavioral Tendencies:**
"""
            # Add bias information
            for bias in profile_data['top_biases']:
                response += f"- **{bias['name']}** ({bias['score']:.1f}/10): {bias['description']}\n"
                
            # Add IPS summary
            response += f"""
To see your complete Investment Policy Statement, type 'show investment policy statement'.
To analyze your behavioral biases in detail, type 'behavioral bias analysis'.
"""
            
            return response, None
        except Exception as e:
            self.logger.error(f"Error getting investment profile: {str(e)}")
            return "Sorry, there was an error retrieving your investment profile. Please try again later.", None
            
    def _handle_behavioral_biases(self, message: str) -> Tuple[str, Optional[Dict]]:
        """Handle request to show user's behavioral biases."""
        if not self.user_id or not self.bias_analyzer:
            return "Please log in to view your behavioral bias analysis.", None
            
        try:
            # Get bias profile
            bias_profile = self.bias_analyzer.get_user_bias_profile()
            
            if not bias_profile or not bias_profile.get('top_biases'):
                return "Your behavioral bias profile is not available yet. Please complete your investment profile.", None
                
            # Get debiasing strategies
            debiasing_strategies = self.bias_analyzer.generate_debiasing_strategies()
            
            # Format response
            response = f"""## Your Behavioral Bias Analysis

Based on the CFA's behavioral finance framework, here are your predominant behavioral tendencies:

"""
            # Add top biases
            for bias in bias_profile['top_biases']:
                response += f"""### {bias['name']} ({bias['score']:.1f}/10)
**Description:** {bias['description']}

**How it might affect your investing:**
This bias could lead to suboptimal investment decisions by {self._get_bias_impact(bias['type'])}.

**Debiasing Strategy:**
{bias['strategy']}

"""

            # Add general advice
            response += """## General Debiasing Strategies

To mitigate behavioral biases in your investment decisions:

1. Keep an investment journal to track your decision rationale
2. Establish a systematic investment process with clear rules
3. Implement automatic portfolio rebalancing
4. Use a pre-commitment strategy for major investment decisions
5. Seek out contradictory information before making decisions

These strategies from the CFA curriculum can help you make more rational investment choices.
"""
            
            return response, None
        except Exception as e:
            self.logger.error(f"Error getting behavioral biases: {str(e)}")
            return "Sorry, there was an error retrieving your behavioral bias analysis. Please try again later.", None
            
    def _handle_factor_analysis(self, message: str) -> Tuple[str, Optional[Dict]]:
        """Handle request to run factor analysis on the user's portfolio."""
        if not self.user_id or not self.portfolio_analytics:
            return "Please log in to run factor analysis on your portfolio.", None
            
        try:
            # Get user's portfolio
            portfolios = self.portfolio_manager.get_user_portfolios(self.user_id)
            
            if not portfolios:
                return "You don't have any portfolios yet. Please create a portfolio first.", None
                
            # Use the first portfolio for now - in a real implementation we would ask which one
            portfolio = portfolios[0]
            
            # Run factor analysis
            factor_exposures = self.portfolio_analytics.calculate_factor_exposures(portfolio)
            
            if not factor_exposures:
                return "Could not calculate factor exposures for your portfolio. Please ensure your portfolio contains valid holdings.", None
                
            # Format response
            response = f"""## Portfolio Factor Analysis

**Portfolio Name:** {portfolio.get('name', 'Your Portfolio')}

### Factor Exposures:
"""
            # Add factor exposures
            for factor, exposure in factor_exposures.items():
                response += f"- **{factor.capitalize()}:** {exposure:.2f}\n"
                
            # Add factor explanations
            response += """
### What These Factors Mean:

- **Size:** Exposure to small vs large market capitalization companies (positive = small-cap tilt)
- **Value:** Exposure to value vs growth companies (positive = value tilt)
- **Momentum:** Exposure to stocks with recent positive performance (positive = momentum tilt)
- **Quality:** Exposure to companies with strong balance sheets and earnings (positive = quality tilt)
- **Volatility:** Exposure to price volatility (positive = higher volatility exposure)
- **Yield:** Exposure to dividend-paying companies (positive = higher yield exposure)
- **Growth:** Exposure to earnings growth (positive = growth tilt)

This analysis is based on CFA's factor-based portfolio analytics framework. It helps you understand the underlying drivers of your portfolio's performance.
"""
            
            return response, None
        except Exception as e:
            self.logger.error(f"Error running factor analysis: {str(e)}")
            return "Sorry, there was an error running factor analysis on your portfolio. Please try again later.", None
            
    def _handle_investment_policy(self, message: str) -> Tuple[str, Optional[Dict]]:
        """Handle request to show the user's investment policy statement."""
        if not self.user_id or not self.cfa_profiler:
            return "Please log in to view your investment policy statement.", None
            
        try:
            # Get user profile
            profile_data = self.cfa_profiler.get_user_profile()
            
            if not profile_data or not profile_data.get('investment_policy'):
                return "Your investment policy statement is not available yet. Please complete your investment profile.", None
                
            # Get IPS data
            ips = profile_data['investment_policy']
            
            # Format response
            response = f"""## Your Investment Policy Statement

### Investment Objectives
{ips['objectives']['description'] if 'objectives' in ips and 'description' in ips['objectives'] else 'To achieve long-term growth while managing risk according to your risk tolerance.'}

**Return Target:** {ips['objectives']['return_target']['target'] if 'objectives' in ips and 'return_target' in ips['objectives'] else '7-10%'} - {ips['objectives']['return_target']['description'] if 'objectives' in ips and 'return_target' in ips['objectives'] and 'description' in ips['objectives']['return_target'] else 'Balance between capital growth and preservation.'}

### Risk Constraints
- **Maximum Volatility:** {ips['risk_constraints']['max_volatility'] if 'risk_constraints' in ips and 'max_volatility' in ips['risk_constraints'] else '12%'}
- **Maximum Drawdown:** {ips['risk_constraints']['max_drawdown'] if 'risk_constraints' in ips and 'max_drawdown' in ips['risk_constraints'] else '15%'}
- **VaR Limit:** {ips['risk_constraints']['var_limit'] if 'risk_constraints' in ips and 'var_limit' in ips['risk_constraints'] else '8% (95% confidence)'}
- **Beta Target:** {ips['risk_constraints']['beta_target'] if 'risk_constraints' in ips and 'beta_target' in ips['risk_constraints'] else '0.8-1.0'}

### Time Horizon
{ips['time_horizon']['description'] if 'time_horizon' in ips and 'description' in ips['time_horizon'] else 'Medium to long-term focus with appropriate asset allocation for your age and goals.'}

### Liquidity Requirements
- **Cash Allocation:** {ips['liquidity']['cash_allocation'] if 'liquidity' in ips and 'cash_allocation' in ips['liquidity'] else '5-10%'}
- **Illiquid Assets Maximum:** {ips['liquidity']['illiquid_assets_max'] if 'liquidity' in ips and 'illiquid_assets_max' in ips['liquidity'] else '20%'}
- **Emergency Fund:** {ips['liquidity']['emergency_fund'] if 'liquidity' in ips and 'emergency_fund' in ips['liquidity'] else '3-6 months of expenses'}

### Rebalancing Policy
{ips['rebalancing']['frequency'] if 'rebalancing' in ips and 'frequency' in ips['rebalancing'] else 'Semi-annual review with threshold-based rebalancing'}
{ips['rebalancing']['thresholds'] if 'rebalancing' in ips and 'thresholds' in ips['rebalancing'] else 'Standard thresholds (±5%) for asset classes, wider for individual positions'}

This Investment Policy Statement follows CFA guidelines for structured investment management and serves as a roadmap for your investment decisions.
"""
            
            return response, None
        except Exception as e:
            self.logger.error(f"Error getting investment policy statement: {str(e)}")
            return "Sorry, there was an error retrieving your investment policy statement. Please try again later.", None
            
    def _handle_record_decision(self, message: str) -> Tuple[str, Optional[Dict]]:
        """Handle request to record an investment decision."""
        if not self.user_id or not self.decision_framework:
            return "Please log in to record investment decisions.", None
            
        # This is a more complex interaction - need to ask for details
        return """To record your investment decision with CFA-based framework, I'll need some details:

Please provide the following information:
1. Stock symbol
2. Decision type (buy, sell, hold)
3. Your rationale for this decision
4. (Optional) Amount of shares
5. (Optional) Price per share

Example format: "Record decision: AAPL, buy, Strong fundamentals and new product cycle, 10 shares, $175.50"

Once recorded, I'll analyze your decision for potential behavioral biases and provide feedback.
""", None
    
    def _get_bias_impact(self, bias_type: str) -> str:
        """Get the potential impact description for a given bias type."""
        bias_impacts = {
            "loss_aversion": "causing you to hold losing positions too long and sell winners too early",
            "herding": "leading you to follow market trends rather than your own analysis",
            "recency": "placing too much weight on recent market events rather than long-term trends",
            "overconfidence": "overestimating your ability to beat the market or time market movements",
            "availability": "focusing too much on information that is easily recalled or vivid",
            "anchoring": "fixating on specific reference points like purchase prices when making decisions",
            "confirmation": "seeking only information that confirms your existing views",
            "status_quo": "maintaining your current investments even when changes would be beneficial"
        }
        
        return bias_impacts.get(bias_type, "affecting your ability to make objective investment decisions")