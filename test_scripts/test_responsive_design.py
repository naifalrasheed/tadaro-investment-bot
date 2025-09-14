#!/usr/bin/env python
"""
Test script for responsive design in the investment bot

This script uses Selenium with different device viewports to test
the responsive design of the investment bot's web interface.
"""

import sys
import os
import logging
import json
import time
from typing import Dict, List, Any
import argparse

# Set up path to import from parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Check if selenium is installed
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, WebDriverException
except ImportError:
    print("Selenium is not installed. Install it with: pip install selenium")
    print("You will also need the Chrome WebDriver installed and in your PATH")
    sys.exit(1)

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define device viewports for testing
DEVICE_VIEWPORTS = {
    "desktop": {"width": 1920, "height": 1080},
    "laptop": {"width": 1366, "height": 768},
    "tablet_landscape": {"width": 1024, "height": 768},
    "tablet_portrait": {"width": 768, "height": 1024},
    "mobile_large": {"width": 414, "height": 896},  # iPhone 11 Pro Max
    "mobile_medium": {"width": 375, "height": 812},  # iPhone X
    "mobile_small": {"width": 320, "height": 568}    # iPhone 5/SE
}

# Define pages to test
PAGES_TO_TEST = [
    "/",                # Home page
    "/login",           # Login page
    "/register",        # Register page
    "/portfolio",       # Portfolio page
    "/analysis",        # Analysis page
    "/analyze",         # Analyze form page
    "/profile",         # User profile page
]

# Define UI elements to check on each page
UI_ELEMENTS = {
    "navigation": {
        "selector": "nav",
        "expected_on": PAGES_TO_TEST,
        "responsive_checks": {
            "desktop": {"visible": True, "element_class_contains": "navbar"},
            "mobile_medium": {"visible": True, "element_class_contains": "navbar-collapse"}
        }
    },
    "footer": {
        "selector": "footer",
        "expected_on": PAGES_TO_TEST,
        "responsive_checks": {
            "desktop": {"visible": True},
            "mobile_medium": {"visible": True}
        }
    },
    "chatbot": {
        "selector": "#chatbot-container",
        "expected_on": ["/portfolio", "/analysis", "/"],
        "responsive_checks": {
            "desktop": {"visible": True, "position": "right"},
            "mobile_medium": {"visible": True, "position": "bottom"}
        }
    }
}

def setup_webdriver(device: str, headless: bool = True) -> webdriver.Chrome:
    """Set up Chrome WebDriver with device emulation"""
    
    # Get viewport dimensions for the device
    viewport = DEVICE_VIEWPORTS.get(device, DEVICE_VIEWPORTS["desktop"])
    
    # Set up Chrome options
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size={},{}".format(viewport["width"], viewport["height"]))
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-gpu")
    
    # Set up mobile device emulation if testing mobile
    if "mobile" in device:
        mobile_emulation = {
            "deviceMetrics": {
                "width": viewport["width"],
                "height": viewport["height"],
                "pixelRatio": 3.0
            },
            "userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1"
        }
        chrome_options.add_experimental_option("mobileEmulation", mobile_emulation)
    
    # Create the WebDriver instance
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_window_size(viewport["width"], viewport["height"])
    
    return driver

def take_screenshot(driver: webdriver.Chrome, device: str, page: str) -> str:
    """Take a screenshot and save it to a file"""
    # Clean the page name for the filename
    clean_page = page.replace("/", "_").replace(".", "_")
    if clean_page == "_":
        clean_page = "home"
    
    # Create screenshots directory if it doesn't exist
    os.makedirs("screenshots", exist_ok=True)
    
    # Generate filename
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    filename = f"screenshots/{device}_{clean_page}_{timestamp}.png"
    
    # Take screenshot
    driver.save_screenshot(filename)
    logger.info(f"Screenshot saved to {filename}")
    
    return filename

def check_element_visibility(driver: webdriver.Chrome, selector: str, wait_time: int = 5) -> Dict:
    """Check if an element is visible on the page"""
    try:
        element = WebDriverWait(driver, wait_time).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, selector))
        )
        
        # Get element position
        location = element.location
        size = element.size
        
        # Get page dimensions
        window_width = driver.execute_script("return window.innerWidth")
        window_height = driver.execute_script("return window.innerHeight")
        
        # Determine position (top, bottom, left, right, center)
        position = "center"  # Default
        
        # Check horizontal position
        element_center_x = location['x'] + size['width'] / 2
        if element_center_x < window_width * 0.33:
            position = "left"
        elif element_center_x > window_width * 0.66:
            position = "right"
            
        # Check vertical position
        element_center_y = location['y'] + size['height'] / 2
        if element_center_y < window_height * 0.33:
            position = f"top-{position}"
        elif element_center_y > window_height * 0.66:
            position = f"bottom-{position}"
        
        # Get element classes
        element_class = element.get_attribute("class")
        
        return {
            "visible": True,
            "position": position,
            "size": {"width": size['width'], "height": size['height']},
            "classes": element_class.split() if element_class else []
        }
    except TimeoutException:
        return {"visible": False, "error": "Element not found or not visible"}
    except Exception as e:
        return {"visible": False, "error": str(e)}

def test_responsive_design(base_url: str, devices: List[str], pages: List[str], take_screenshots: bool = True) -> Dict:
    """Test responsive design on multiple devices and pages"""
    logger.info(f"=== Starting Responsive Design Test ===")
    logger.info(f"Base URL: {base_url}")
    logger.info(f"Testing devices: {', '.join(devices)}")
    logger.info(f"Testing pages: {', '.join(pages)}")
    
    results = {}
    
    for device in devices:
        logger.info(f"\nTesting device: {device}")
        results[device] = {}
        
        # Set up WebDriver for this device
        try:
            driver = setup_webdriver(device, headless=True)
            
            for page in pages:
                logger.info(f"Testing page: {page}")
                results[device][page] = {"elements": {}, "screenshot": None}
                
                # Navigate to the page
                try:
                    page_url = f"{base_url}{page}"
                    driver.get(page_url)
                    
                    # Wait for page to load
                    time.sleep(2)
                    
                    # Take screenshot if enabled
                    if take_screenshots:
                        screenshot_path = take_screenshot(driver, device, page)
                        results[device][page]["screenshot"] = screenshot_path
                    
                    # Check UI elements
                    for element_name, element_config in UI_ELEMENTS.items():
                        if page in element_config["expected_on"]:
                            logger.info(f"Checking element: {element_name}")
                            element_result = check_element_visibility(driver, element_config["selector"])
                            
                            # Add element result to results
                            results[device][page]["elements"][element_name] = element_result
                            
                            # Check responsive requirements if specified for this device
                            if device in element_config.get("responsive_checks", {}):
                                checks = element_config["responsive_checks"][device]
                                
                                # Check visibility
                                if "visible" in checks and element_result["visible"] != checks["visible"]:
                                    logger.warning(f"Element {element_name} visibility ({element_result['visible']}) does not match expected ({checks['visible']})")
                                
                                # Check position if element is visible
                                if element_result["visible"] and "position" in checks and element_result["position"] != checks["position"]:
                                    logger.warning(f"Element {element_name} position ({element_result['position']}) does not match expected ({checks['position']})")
                                
                                # Check class contains
                                if element_result["visible"] and "element_class_contains" in checks:
                                    expected_class = checks["element_class_contains"]
                                    if not any(expected_class in cls for cls in element_result["classes"]):
                                        logger.warning(f"Element {element_name} classes ({element_result['classes']}) do not contain expected ({expected_class})")
                            
                except Exception as e:
                    logger.error(f"Error testing page {page}: {str(e)}")
                    results[device][page]["error"] = str(e)
            
            # Close the WebDriver
            driver.quit()
            
        except WebDriverException as e:
            logger.error(f"Error setting up WebDriver for {device}: {str(e)}")
            results[device]["error"] = f"WebDriver error: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error testing device {device}: {str(e)}")
            results[device]["error"] = f"Unexpected error: {str(e)}"
    
    # Calculate summary statistics
    summary = {
        "total_tests": len(devices) * len(pages),
        "passed_tests": 0,
        "failed_tests": 0,
        "passed_elements": 0,
        "failed_elements": 0
    }
    
    for device in results:
        for page in results[device]:
            if isinstance(results[device][page], dict) and "error" not in results[device][page]:
                summary["passed_tests"] += 1
                
                # Count passed/failed elements
                for element, element_result in results[device][page].get("elements", {}).items():
                    if element_result.get("visible") == True:
                        summary["passed_elements"] += 1
                    else:
                        summary["failed_elements"] += 1
            else:
                summary["failed_tests"] += 1
    
    results["summary"] = summary
    
    # Log summary
    logger.info("\n=== Responsive Design Test Summary ===")
    logger.info(f"Total tests: {summary['total_tests']}")
    logger.info(f"Passed tests: {summary['passed_tests']} ({summary['passed_tests']/summary['total_tests']*100:.1f}%)")
    logger.info(f"Failed tests: {summary['failed_tests']} ({summary['failed_tests']/summary['total_tests']*100:.1f}%)")
    logger.info(f"Visible elements: {summary['passed_elements']}")
    logger.info(f"Missing elements: {summary['failed_elements']}")
    
    return results

if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Test responsive design of the investment bot")
    parser.add_argument("--url", type=str, default="http://localhost:5000", help="Base URL of the application")
    parser.add_argument("--devices", type=str, nargs="+", default=["desktop", "tablet_portrait", "mobile_medium"], 
                      help="Devices to test (options: desktop, laptop, tablet_landscape, tablet_portrait, mobile_large, mobile_medium, mobile_small)")
    parser.add_argument("--pages", type=str, nargs="+", default=PAGES_TO_TEST,
                      help="Pages to test (default: all pages)")
    parser.add_argument("--no-screenshots", action="store_true", help="Disable taking screenshots")
    
    args = parser.parse_args()
    
    # Validate devices
    for device in args.devices:
        if device not in DEVICE_VIEWPORTS:
            logger.error(f"Unknown device: {device}")
            sys.exit(1)
    
    # Run the tests
    results = test_responsive_design(
        base_url=args.url,
        devices=args.devices,
        pages=args.pages,
        take_screenshots=not args.no_screenshots
    )
    
    # Save results to file
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    with open(f"responsive_test_results_{timestamp}.json", "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Test results saved to responsive_test_results_{timestamp}.json")
    
    # Exit with error code if any tests failed
    if results["summary"]["failed_tests"] > 0:
        sys.exit(1)