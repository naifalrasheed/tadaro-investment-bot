# Investment Bot

An AI-powered investment analysis and portfolio optimization tool.

## Setup Instructions

1. Create a virtual environment:
```
conda create -n investment_env python=3.9
conda activate investment_env
```

2. Install dependencies:
```
pip install -r requirements.txt
```

3. Run tests:
```
python run_tests.py
```

4. Start the application:
```
python main.py
```

## Environment Variables

The following environment variables can be set to configure the application:

- `ALPHA_VANTAGE_API_KEY`: API key for Alpha Vantage
- `MONGODB_URI`: MongoDB connection string
- `DATABASE_NAME`: MongoDB database name

## Usage

The main entry point provides a command line interface with the following options:

1. Analyze Individual Stock
2. Create/Update Investment Profile
3. Optimize Portfolio
4. View Current Portfolio
5. View Investment Profile

## Naif Al-Rasheed Investment Model

The application now features the Naif Al-Rasheed Investment Model with multi-market support.

### Key Features

- **Multi-Market Support**: Analyzes both US and Saudi markets with market-specific parameters
- **Comprehensive Analysis Pipeline**:
  - Macro-economic analysis for growth indicators
  - Sector-level ranking with growth projections
  - Fundamental screening based on ROTC, revenue growth, and FCF criteria
  - Management team quality assessment
  - Portfolio construction with 12-18 companies from 5+ sectors

- **Advanced Risk Analysis**:
  - Monte Carlo simulation for future projection (5000 iterations during testing phase, 10000 for production)
  - Portfolio optimization based on user risk profile

### Investment Criteria

The model applies market-specific criteria:

#### US Market
- ROTC > 15%
- Revenue Growth > 5%
- Market Cap > $1B
- P/E < 25

#### Saudi Market  
- ROTC > 12%
- Revenue Growth > 5%
- Market Cap > 500M SAR
- P/E < 20
- Dividend Yield > 2%

### Performance Optimizations (Testing Phase Only)

For testing purposes, the following limits are in place:
- Sector analysis limited to maximum 40 companies per sector
- Monte Carlo simulations limited to 5000 iterations
- These limits MUST be removed for the production version

### Web Interface Integration

Use the web interface to:
- Select which market to analyze (US or Saudi)
- Customize screening parameters
- View detailed sector and technical analysis
- Create portfolios with stocks from both markets
- View Monte Carlo simulations of portfolio performance