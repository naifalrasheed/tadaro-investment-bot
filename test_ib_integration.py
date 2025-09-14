#!/usr/bin/env python
"""
Test script for Interactive Brokers integration with the investment bot.
This script helps with setting up and testing the Interactive Brokers Client Portal Web API.
"""

import os
import sys
import logging
import json
import time
import argparse
from datetime import datetime
from pathlib import Path
from pprint import pprint
import subprocess

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add current directory to path
sys.path.append('.')

# Import our module
from data.ib_data_client import IBDataClient

def check_jre_installation():
    """Check if Java Runtime Environment is installed"""
    try:
        result = subprocess.run(['java', '-version'], capture_output=True, text=True)
        # Java version info goes to stderr, not stdout
        if 'version' in result.stderr:
            version_info = result.stderr.split('\n')[0]
            logger.info(f"JRE is installed: {version_info}")
            return True
        else:
            logger.warning("JRE is not installed or not in PATH")
            return False
    except Exception as e:
        logger.error(f"Error checking Java installation: {str(e)}")
        return False

def check_gateway_installation():
    """Check if the Client Portal Gateway is installed"""
    # Define possible paths where the gateway might be installed
    possible_paths = [
        './clientportal.gw',
        '../clientportal.gw',
        '../../clientportal.gw',
        './ibportal',
        '../ibportal',
        '../../ibportal',
        './clientportal.beta.gw',
        '../clientportal.beta.gw',
        '../../clientportal.beta.gw'
    ]
    
    # Check each path
    for path in possible_paths:
        if os.path.exists(path) and os.path.isdir(path):
            if os.path.exists(os.path.join(path, 'bin')) and os.path.exists(os.path.join(path, 'root')):
                logger.info(f"Client Portal Gateway found at: {os.path.abspath(path)}")
                return os.path.abspath(path)
    
    logger.warning("Client Portal Gateway not found in the expected locations")
    return None

def start_gateway(gateway_path):
    """Start the Client Portal Gateway"""
    if not gateway_path:
        logger.error("Gateway path not provided")
        return False
    
    # Determine the correct script to run based on the platform
    if sys.platform.startswith('win'):
        run_script = os.path.join(gateway_path, 'bin', 'run.bat')
        config_file = os.path.join(gateway_path, 'root', 'conf.yaml')
        cmd = [run_script, config_file]
    else:  # Unix-like (Linux, MacOS)
        run_script = os.path.join(gateway_path, 'bin', 'run.sh')
        config_file = os.path.join(gateway_path, 'root', 'conf.yaml')
        cmd = [run_script, config_file]
    
    # Check if the gateway is already running
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect(('localhost', 5000))
        s.close()
        logger.info("Client Portal Gateway is already running on port 5000")
        return True
    except:
        logger.info("Port 5000 is available, starting the gateway...")
    
    # Start the gateway in a new process
    try:
        # Use CREATE_NEW_CONSOLE on Windows to open in a new window
        if sys.platform.startswith('win'):
            import subprocess
            process = subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_CONSOLE)
        else:
            # On Unix-like systems, start in background
            import subprocess
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        logger.info(f"Started Client Portal Gateway with PID: {process.pid}")
        
        # Wait for the gateway to start up
        time.sleep(5)
        logger.info("Client Portal Gateway should now be running")
        logger.info("Please login through the browser at https://localhost:5000")
        return True
    except Exception as e:
        logger.error(f"Error starting the gateway: {str(e)}")
        return False

def test_ib_client():
    """Test the Interactive Brokers client"""
    logger.info("Testing Interactive Brokers client")
    client = IBDataClient()
    
    # Check if the gateway is running
    if not client.check_gateway_status():
        logger.error("Client Portal Gateway is not running.")
        print("\nTo start the gateway manually:")
        print("1. Open a command prompt/terminal")
        print("2. Navigate to the gateway directory")
        print("3. Run: bin/run.bat root/conf.yaml (Windows)")
        print("   or:  bin/run.sh root/conf.yaml (Mac/Linux)")
        print("\nThen try running this script again.")
        return False
    
    logger.info("Gateway is running!")
    
    # Check authentication
    if not client.check_authentication():
        logger.warning("Not authenticated to IB Gateway")
        print("\nTo authenticate:")
        print("1. Open a web browser and go to https://localhost:5000")
        print("2. Login with your IB credentials")
        print("3. Complete any two-factor authentication if prompted")
        print("4. You should see a message saying 'Client login succeeds'")
        print("\nThen try running this script again.")
        return False
    
    logger.info("Authenticated to IB Gateway!")
    
    # Get account information
    accounts = client.get_account_summary()
    if accounts:
        logger.info(f"Found {len(accounts)} account(s)")
        for account in accounts:
            account_id = account.get('accountId', 'Unknown')
            account_type = account.get('accountType', 'Unknown')
            logger.info(f"Account ID: {account_id}, Type: {account_type}")
    else:
        logger.warning("No accounts found or error getting account information")
    
    # Test stocks
    symbols = ['AAPL', 'MSFT', 'NVDA', 'GOOGL']
    
    for symbol in symbols:
        logger.info(f"\nTesting {symbol}...")
        
        # Get stock information
        stock_data = client.get_stock_by_symbol(symbol)
        if stock_data:
            logger.info(f"Found {symbol} ({stock_data['contract'].get('name', 'N/A')})")
            
            # Check if we got market data
            if 'market_data' in stock_data and stock_data['market_data']:
                for item in stock_data['market_data']:
                    if str(item.get('conid')) == str(stock_data['contract']['conid']):
                        last_price = item.get('31', 'N/A')
                        logger.info(f"Last Price: {last_price}")
                        break
            
            # Get full analysis
            analysis = client.analyze_stock(symbol)
            logger.info(f"Analysis completed for {symbol}")
            logger.info(f"Current Price: ${analysis['current_price']}")
            logger.info(f"52-Week High: ${analysis['price_metrics']['week_52_high']}")
            logger.info(f"52-Week Low: ${analysis['price_metrics']['week_52_low']}")
            
            # Save analysis to file for inspection
            os.makedirs('test_output', exist_ok=True)
            with open(f"test_output/{symbol}_ib_analysis.json", 'w') as f:
                json.dump(analysis, f, indent=2)
            
            logger.info(f"Saved {symbol} analysis to test_output/{symbol}_ib_analysis.json")
        else:
            logger.warning(f"Could not find stock information for {symbol}")
    
    logger.info("\nIB client test completed")
    return True

def download_gateway():
    """Helper to download the Client Portal Gateway"""
    logger.info("Downloading Interactive Brokers Client Portal Gateway")
    print("\nDownload URLs:")
    print("- Standard release: https://download2.interactivebrokers.com/portal/clientportal.gw.zip")
    print("- Beta release: https://download2.interactivebrokers.com/portal/clientportal.beta.gw.zip")
    
    # Determine if we're on Windows or Unix-like system
    if sys.platform.startswith('win'):
        print("\nInstructions for Windows:")
        print("1. Download the ZIP file from one of the links above")
        print("2. Extract the ZIP file to a location of your choice")
        print("3. Open a command prompt and navigate to the extracted directory")
        print("4. Run: bin\\run.bat root\\conf.yaml")
    else:
        print("\nInstructions for Mac/Linux:")
        print("1. Download the ZIP file from one of the links above")
        print("2. Extract the ZIP file to a location of your choice")
        print("3. Open a terminal and navigate to the extracted directory")
        print("4. Run: bin/run.sh root/conf.yaml")
    
    print("\nAfter the gateway is running, open a web browser and go to https://localhost:5000")
    print("Login with your IB credentials")

def main():
    """Main function for the script"""
    parser = argparse.ArgumentParser(description='Interactive Brokers integration test script')
    parser.add_argument('--download', action='store_true', help='Show download information for the gateway')
    parser.add_argument('--start-gateway', action='store_true', help='Attempt to start the Client Portal Gateway')
    parser.add_argument('--test-client', action='store_true', help='Test the IB client functionality')
    
    args = parser.parse_args()
    
    # If no arguments, run the full script
    if not args.download and not args.start_gateway and not args.test_client:
        args.download = True
        args.start_gateway = True
        args.test_client = True
    
    # Create test output directory
    os.makedirs('test_output', exist_ok=True)
    
    if args.download:
        download_gateway()
    
    if args.start_gateway:
        # Check Java installation
        if not check_jre_installation():
            logger.error("Java Runtime Environment (JRE) is required but not found")
            print("\nPlease install Java 8 or later from:")
            print("https://www.oracle.com/java/technologies/javase-downloads.html")
            return
        
        # Check gateway installation
        gateway_path = check_gateway_installation()
        if not gateway_path:
            logger.error("Client Portal Gateway not found")
            download_gateway()
            return
        
        # Start the gateway
        if not start_gateway(gateway_path):
            logger.error("Failed to start the gateway")
            return
    
    if args.test_client:
        test_ib_client()

if __name__ == "__main__":
    main()