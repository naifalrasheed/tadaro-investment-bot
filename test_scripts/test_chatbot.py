#!/usr/bin/env python
"""
Test script for Claude chatbot functionality in investment bot

This script tests different user scenarios with the Claude chatbot integration
to verify functionality and ensure responses are appropriate.
"""

import sys
import os
import logging
import json
from typing import Dict, List, Any
import uuid

# Set up path to import from parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the Claude handler
from claude_integration.claude_handler import ClaudeHandler

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Test user contexts
TEST_STOCK_CONTEXT = {
    "symbol": "MSFT",
    "name": "Microsoft Corporation",
    "price": 402.3,
    "change": 2.1,
    "market_cap": 2989000000000,
    "sector": "Technology",
    "pe_ratio": 35.2,
    "dividend_yield": 0.75,
    "52w_high": 425.32,
    "52w_low": 309.65
}

TEST_PORTFOLIO_CONTEXT = {
    "total_value": 156420.32,
    "cash": 15642.03,
    "holdings": [
        {"symbol": "MSFT", "shares": 50, "value": 20115.00, "weight": 0.13},
        {"symbol": "AAPL", "shares": 75, "value": 13875.00, "weight": 0.09},
        {"symbol": "AMZN", "shares": 25, "value": 4125.00, "weight": 0.03},
        {"symbol": "GOOGL", "shares": 30, "value": 5175.00, "weight": 0.03},
        {"symbol": "JNJ", "shares": 55, "value": 8525.00, "weight": 0.05}
    ],
    "sectors": {
        "Technology": 0.36,
        "Healthcare": 0.18,
        "Consumer Discretionary": 0.12,
        "Financials": 0.09,
        "Communication Services": 0.08,
        "Other": 0.17
    },
    "performance": {
        "1m": 2.3,
        "3m": 5.1,
        "6m": 8.7,
        "1y": 16.2
    }
}

def test_chatbot_scenarios():
    """Test various chatbot usage scenarios"""
    logger.info("=== Starting Chatbot Functionality Test ===")
    
    # Initialize Claude handler
    claude_handler = ClaudeHandler()
    
    # Generate a unique test user ID
    test_user_id = f"test_user_{uuid.uuid4().hex[:8]}"
    logger.info(f"Created test user ID: {test_user_id}")
    
    # Define test scenarios with expected content checks
    test_scenarios = [
        {
            "name": "Basic greeting",
            "message": "Hello, I'm new to investing. Can you help me?",
            "context": None,
            "portfolio_context": None,
            "expected_content": ["welcome", "invest", "help"]
        },
        {
            "name": "Stock question",
            "message": "What do you think about Microsoft?",
            "context": TEST_STOCK_CONTEXT,
            "portfolio_context": None,
            "expected_content": ["Microsoft", "technology", "stock"]
        },
        {
            "name": "Portfolio question",
            "message": "How is my portfolio performing?",
            "context": None,
            "portfolio_context": TEST_PORTFOLIO_CONTEXT,
            "expected_content": ["portfolio", "value", "performance"]
        },
        {
            "name": "Investment concept",
            "message": "What is dollar cost averaging?",
            "context": None,
            "portfolio_context": None,
            "expected_content": ["dollar cost averaging", "regular", "intervals"]
        },
        {
            "name": "Risk question",
            "message": "What's a good asset allocation for a conservative investor?",
            "context": None,
            "portfolio_context": None,
            "expected_content": ["conservative", "bonds", "allocation"]
        }
    ]
    
    # Run each test scenario
    test_results = []
    for i, scenario in enumerate(test_scenarios, 1):
        logger.info(f"\nScenario {i}: {scenario['name']}")
        logger.info(f"User message: \"{scenario['message']}\"")
        
        # Call the chat function with the scenario
        try:
            response = claude_handler.chat_with_assistant(
                user_id=test_user_id,
                user_message=scenario['message'],
                stock_context=scenario['context'],
                portfolio_context=scenario['portfolio_context']
            )
            
            # Check if the response contains expected content
            if response['status'] == 'success':
                logger.info("Response received successfully")
                response_text = response['response']
                
                # Truncate response for logging
                log_response = response_text[:150] + "..." if len(response_text) > 150 else response_text
                logger.info(f"Response preview: {log_response}")
                
                # Check for expected content
                content_found = []
                for content in scenario['expected_content']:
                    if content.lower() in response_text.lower():
                        content_found.append(content)
                
                # Calculate match percentage
                match_percentage = len(content_found) / len(scenario['expected_content']) * 100
                logger.info(f"Expected content match: {match_percentage:.1f}% ({len(content_found)}/{len(scenario['expected_content'])})")
                
                # Log what content was missing
                if match_percentage < 100:
                    missing = [c for c in scenario['expected_content'] if c not in content_found]
                    logger.warning(f"Missing expected content: {', '.join(missing)}")
                
                # Add to test results
                test_results.append({
                    "scenario": scenario['name'],
                    "success": True,
                    "match_percentage": match_percentage,
                    "missing_content": [c for c in scenario['expected_content'] if c not in content_found]
                })
            else:
                logger.error(f"Response error: {response.get('error', 'Unknown error')}")
                test_results.append({
                    "scenario": scenario['name'],
                    "success": False,
                    "error": response.get('error', 'Unknown error')
                })
                
        except Exception as e:
            logger.error(f"Test exception: {str(e)}")
            test_results.append({
                "scenario": scenario['name'],
                "success": False,
                "error": str(e)
            })
    
    # Test conversation history
    logger.info("\nChecking conversation history functionality")
    history = claude_handler.get_conversation_history(test_user_id)
    history_length = len(history)
    expected_length = len(test_scenarios) * 2  # Each scenario adds user message and assistant response
    
    logger.info(f"History length: {history_length} messages (expected {expected_length})")
    if history_length == expected_length:
        logger.info("Conversation history tracking is working correctly")
    else:
        logger.warning(f"Conversation history length mismatch: got {history_length}, expected {expected_length}")
    
    # Test conversation continuation (context awareness)
    logger.info("\nTesting conversation continuation (context awareness)")
    follow_up_message = "Can you explain more about that?"
    
    response = claude_handler.chat_with_assistant(
        user_id=test_user_id,
        user_message=follow_up_message
    )
    
    if response['status'] == 'success' and len(response['response']) > 50:
        logger.info("Follow-up response received successfully")
        logger.info(f"Response length: {len(response['response'])} characters")
        logger.info("Context awareness test PASSED")
        
        test_results.append({
            "scenario": "Conversation continuation",
            "success": True
        })
    else:
        logger.error("Context awareness test FAILED")
        logger.error(f"Error: {response.get('error', 'Response too short or generic')}")
        
        test_results.append({
            "scenario": "Conversation continuation",
            "success": False,
            "error": response.get('error', 'Response too short or generic')
        })
    
    # Test history clearing
    logger.info("\nTesting conversation history clearing")
    claude_handler.clear_conversation_history(test_user_id)
    history_after_clear = claude_handler.get_conversation_history(test_user_id)
    
    if len(history_after_clear) == 0:
        logger.info("Conversation history cleared successfully")
    else:
        logger.error(f"Failed to clear conversation history: {len(history_after_clear)} messages remain")
    
    # Summarize test results
    logger.info("\n=== Chatbot Test Summary ===")
    success_count = sum(1 for result in test_results if result.get('success', False))
    logger.info(f"Scenarios: {len(test_results)}")
    logger.info(f"Successful: {success_count}")
    logger.info(f"Failed: {len(test_results) - success_count}")
    logger.info(f"Success rate: {success_count / len(test_results) * 100:.1f}%")
    
    return test_results

if __name__ == "__main__":
    # Run the test suite
    results = test_chatbot_scenarios()
    
    # Save results to file
    with open("chatbot_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Test results saved to chatbot_test_results.json")