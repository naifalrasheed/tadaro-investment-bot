from claude_handler import ClaudeHandler
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    claude = ClaudeHandler()
    
    # Test 1: Connection
    logger.info("Testing connection...")
    if not claude.test_connection():
        logger.error("Connection failed!")
        return

    # Test 2: Code Review
    test_code = """
def analyze_stock(symbol):
    # Get stock data
    data = get_stock_data(symbol)
    return {'price': data['price']}
    """
    
    logger.info("\nTesting code review...")
    result = claude.review_code(test_code)
    if result['status'] == 'success':
        logger.info("Code review suggestions:")
        print(result['suggestions'])
    
    # Test 3: Stock Analysis
    test_data = {
        'symbol': 'AAPL',
        'metrics': {
            'price': 150.0,
            'pe_ratio': 25.5,
            'market_cap': '2.5T'
        }
    }
    
    logger.info("\nTesting stock analysis...")
    result = claude.analyze_stock(test_data)
    if result['status'] == 'success':
        logger.info("Stock analysis:")
        print(result['analysis'])

if __name__ == "__main__":
    main()