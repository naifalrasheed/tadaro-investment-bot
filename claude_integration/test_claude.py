import os
from claude_handler import ClaudeHandler
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    # Get API key from environment variable
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        logger.error("Please set your ANTHROPIC_API_KEY environment variable")
        return
    
    try:
        # Initialize Claude handler
        claude = ClaudeHandler(api_key)
        
        # Test connection
        logger.info("Testing Claude connection...")
        if claude.test_connection():
            logger.info("Successfully connected to Claude API!")
        else:
            logger.error("Failed to connect to Claude API")
            return
            
        # Test code analysis
        test_code = """
def analyze_stock(symbol):
    data = get_stock_data(symbol)
    return {'price': data['price']}
        """
        
        logger.info("Testing code analysis...")
        result = claude.analyze_code(test_code)
        if result['status'] == 'success':
            logger.info("Code analysis successful!")
            logger.info("Suggestions:")
            print(result['suggestions'])
        else:
            logger.error(f"Code analysis failed: {result.get('error')}")
            
    except Exception as e:
        logger.error(f"Error: {str(e)}")

if __name__ == "__main__":
    main()