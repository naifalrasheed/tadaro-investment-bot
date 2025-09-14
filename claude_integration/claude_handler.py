from anthropic import Anthropic
from typing import Dict, Any, List, Optional
import logging
import json
import datetime

class ClaudeHandler:
    def __init__(self):
        self.api_key = "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"
        self.anthropic = Anthropic(api_key=self.api_key)
        self.model = "claude-3-opus-20240229"  # Using the highest capability model for best investment advice
        self.logger = logging.getLogger(__name__)
        self.conversation_history = {}  # Store chat history by user_id

    def enhance_analysis(self, stock_data: Dict, technical_analysis: Dict, fundamental_analysis: Dict) -> Dict:
        """Enhance stock analysis with Claude's insights"""
        try:
            prompt = f"""
            Analyze this stock data and provide comprehensive insights:

            Stock Data:
            {json.dumps(stock_data, indent=2)}

            Technical Analysis:
            {json.dumps(technical_analysis, indent=2)}

            Fundamental Analysis:
            {json.dumps(fundamental_analysis, indent=2)}

            Please provide:
            1. Key insights from technical indicators
            2. Fundamental analysis interpretation
            3. Risk assessment
            4. Investment recommendation
            5. Potential catalysts to watch
            """

            response = self.anthropic.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            # Extract text from response
            response_text = ""
            if hasattr(response, 'content') and isinstance(response.content, list):
                for content_block in response.content:
                    if hasattr(content_block, 'text'):
                        response_text += content_block.text
                    elif isinstance(content_block, dict) and 'text' in content_block:
                        response_text += content_block['text']
            elif hasattr(response, 'content') and isinstance(response.content, str):
                response_text = response.content
            elif hasattr(response, 'text'):
                response_text = response.text
            else:
                self.logger.error(f"Unexpected response format: {type(response)}")
                response_text = str(response)

            return {
                'ai_insights': response_text,
                'status': 'success'
            }
        except Exception as e:
            self.logger.error(f"AI analysis failed: {str(e)}")
            return {'status': 'error', 'error': str(e)}

    def validate_analysis(self, analysis_result: Dict) -> Dict:
        """Validate analysis results and check for potential issues"""
        try:
            prompt = f"""
            Review this investment analysis and identify potential issues or improvements:
            {json.dumps(analysis_result, indent=2)}

            Please check for:
            1. Data consistency
            2. Calculation accuracy
            3. Risk assessment completeness
            4. Recommendation logic
            5. Missing important factors
            """

            response = self.anthropic.messages.create(
                model=self.model,
                max_tokens=2048,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            # Extract text from response
            response_text = ""
            if hasattr(response, 'content') and isinstance(response.content, list):
                for content_block in response.content:
                    if hasattr(content_block, 'text'):
                        response_text += content_block.text
                    elif isinstance(content_block, dict) and 'text' in content_block:
                        response_text += content_block['text']
            elif hasattr(response, 'content') and isinstance(response.content, str):
                response_text = response.content
            elif hasattr(response, 'text'):
                response_text = response.text
            else:
                self.logger.error(f"Unexpected response format: {type(response)}")
                response_text = str(response)

            return {
                'validation_result': response_text,
                'status': 'success'
            }
        except Exception as e:
            self.logger.error(f"Validation failed: {str(e)}")
            return {'status': 'error', 'error': str(e)}
            
    def chat_with_assistant(self, user_id: str, user_message: str, 
                           stock_context: Optional[Dict] = None,
                           portfolio_context: Optional[Dict] = None) -> Dict:
        """Chat with Claude assistant with context about user's portfolio and preferences"""
        try:
            # Initialize conversation history for new users
            if user_id not in self.conversation_history:
                self.conversation_history[user_id] = []
            
            # Prepare context for the conversation
            system_prompt = """You are an AI investment assistant for the Investment Bot platform. 
            You help users understand investment concepts, analyze stocks, and make informed decisions.
            Your responses should be:
            1. Clear and educational
            2. Balanced and objective
            3. Factual and data-driven
            4. Risk-aware and responsible

            CAPABILITIES:
            - Stock analysis (technical, fundamental, sentiment, valuation)
            - Portfolio management and optimization
            - Risk assessment and Monte Carlo simulations
            - Market sector analysis
            - Investment strategy recommendations
            - Balance sheet analysis
            - Naif Al-Rasheed model implementation for US and Saudi markets
            - Personalized stock recommendations based on user preferences and risk profile
            
            INSTRUCTIONS:
            - If a user asks for analysis, suggest specific commands they can use (e.g., "analyze AAPL", "run technical analysis for TSLA")
            - When users ask about concepts like P/E ratio, ROTC, or investment strategies, provide educational explanations
            - For complex questions, break down your answers into clear steps or points
            - When appropriate, suggest commands for deeper insights (e.g., "You can run 'analyze portfolio risk' for detailed metrics")
            - Always include appropriate risk disclaimers when providing investment advice
            - Focus on explaining concepts clearly rather than making specific buy or sell recommendations
            - Remember user preferences to provide personalized advice
            """
            
            # Add relevant context about user's stocks or portfolio if available
            context = ""
            if stock_context:
                context += f"\nCurrent stock being analyzed: {json.dumps(stock_context, indent=2)}\n"
            
            if portfolio_context:
                context += f"\nUser portfolio summary: {json.dumps(portfolio_context, indent=2)}\n"
            
            # Combine context with user message
            full_message = user_message
            if context:
                full_message = f"{context}\n\nUser message: {user_message}"
            
            # Build message history for the API call
            # For Claude API, "system" is not a message role, but a top-level parameter
            
            # Prepare conversation history (limit to last 10 exchanges to control token usage)
            history_messages = []
            for msg in self.conversation_history[user_id][-10:]:
                history_messages.append(msg)
            
            # Add current user message
            history_messages.append({"role": "user", "content": full_message})
            
            # Call Claude API - system prompt is a separate parameter
            response = self.anthropic.messages.create(
                model=self.model,
                max_tokens=4096,
                system=system_prompt,
                messages=history_messages
            )
            
            # Extract text from response
            # The new Claude API returns content objects that need text extraction
            response_text = ""
            if hasattr(response, 'content') and isinstance(response.content, list):
                for content_block in response.content:
                    if hasattr(content_block, 'text'):
                        response_text += content_block.text
                    elif isinstance(content_block, dict) and 'text' in content_block:
                        response_text += content_block['text']
            elif hasattr(response, 'content') and isinstance(response.content, str):
                response_text = response.content
            elif hasattr(response, 'text'):
                response_text = response.text
            else:
                self.logger.error(f"Unexpected response format: {type(response)}")
                response_text = str(response)
            
            # Store the exchange in conversation history
            self.conversation_history[user_id].append({"role": "user", "content": user_message})
            self.conversation_history[user_id].append({"role": "assistant", "content": response_text})
            
            # Limit history size to prevent excessive memory usage
            if len(self.conversation_history[user_id]) > 50:
                self.conversation_history[user_id] = self.conversation_history[user_id][-50:]
            
            return {
                'response': response_text,
                'timestamp': datetime.datetime.now().isoformat(),
                'status': 'success'
            }
            
        except Exception as e:
            self.logger.error(f"Chat with assistant failed: {str(e)}")
            return {'status': 'error', 'error': str(e)}
    
    def get_conversation_history(self, user_id: str) -> List:
        """Get conversation history for a specific user"""
        if user_id in self.conversation_history:
            return self.conversation_history[user_id]
        return []
    
    def clear_conversation_history(self, user_id: str) -> None:
        """Clear conversation history for a specific user"""
        if user_id in self.conversation_history:
            self.conversation_history[user_id] = []