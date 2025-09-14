# Investment Bot Test Scripts

This directory contains test scripts for verifying the functionality and performance of the Investment Bot application.

## Available Tests

### 1. Naif Al-Rasheed Model Performance Test

Tests the performance limits and accuracy of the Naif Al-Rasheed investment model.

```bash
python test_naif_model.py [market]
```

- `market`: Optional argument to specify which market to test (default: 'us', options: 'us', 'saudi')

This test compares the performance between test limits (40 companies per sector, 5000 Monte Carlo simulations) and production settings (unlimited companies, 10000 simulations). It measures execution time and result differences.

### 2. Chatbot Functionality Test

Tests the Claude chatbot integration with various user scenarios.

```bash
python test_chatbot.py
```

This test verifies:
- Basic responses to common investment questions
- Context-awareness with stock and portfolio information
- Conversation history tracking
- Response quality and expected content

### 3. Responsive Design Test

Tests the responsive design of the web interface across different device sizes.

```bash
python test_responsive_design.py [--url URL] [--devices DEVICES] [--pages PAGES] [--no-screenshots]
```

Arguments:
- `--url`: Base URL of the application (default: http://localhost:5000)
- `--devices`: Devices to test (options: desktop, laptop, tablet_landscape, tablet_portrait, mobile_large, mobile_medium, mobile_small)
- `--pages`: Pages to test (default: all main pages)
- `--no-screenshots`: Disable taking screenshots

Requirements:
- Selenium (`pip install selenium`)
- Chrome WebDriver (must be installed and in your PATH)

This test verifies that UI elements properly adapt to different screen sizes and captures screenshots for visual inspection.

## Running All Tests

To run all tests sequentially, use:

```bash
# Start the application server in a separate terminal
# cd to src directory and run:
python app.py

# Then run the tests
python -m test_scripts.test_naif_model
python -m test_scripts.test_chatbot
python -m test_scripts.test_responsive_design
```

## Test Results

All tests generate detailed logs and result files:
- Naif model test: `naif_model_performance_test_*.log`
- Chatbot test: `chatbot_test_results.json`
- Responsive design test: `responsive_test_results_*.json` and screenshots in the `screenshots/` directory

## Future Tests

Planned additional tests include:
- API endpoint tests
- Performance benchmarks
- Security and authentication tests