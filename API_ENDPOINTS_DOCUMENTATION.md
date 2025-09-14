# Investment Bot API Endpoints Documentation

## Overview
This document outlines the RESTful API endpoints that will power the Investment Bot mobile applications and third-party integrations. All endpoints follow REST principles and return JSON responses.

## Authentication

### Base URL
```
https://api.investmentbot.com/v1
```

### Authentication Method
All API requests require authentication using JWT (JSON Web Tokens).

#### Authentication Endpoints

##### Login
```
POST /auth/login
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": 123,
      "email": "user@example.com",
      "name": "John Doe",
      "has_completed_profiling": true
    }
  }
}
```

##### Register
```
POST /auth/register
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123",
  "name": "John Doe"
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": 123,
      "email": "user@example.com",
      "name": "John Doe",
      "has_completed_profiling": false
    }
  }
}
```

##### Refresh Token
```
POST /auth/refresh
```

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

##### Logout
```
POST /auth/logout
```

**Response:**
```json
{
  "status": "success"
}
```

## User Profile

### Get User Profile
```
GET /user/profile
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "user": {
      "id": 123,
      "email": "user@example.com",
      "name": "John Doe",
      "has_completed_profiling": true,
      "created_at": "2025-03-01T12:00:00Z",
      "preferences": {
        "preferred_sectors": ["Technology", "Healthcare"],
        "excluded_sectors": ["Oil & Gas"],
        "feature_weights": {
          "pe_ratio": 0.3,
          "dividend_yield": 0.2,
          "rotc": 0.4,
          "debt_to_equity": 0.1
        }
      }
    }
  }
}
```

### Update User Profile
```
PUT /user/profile
```

**Request Body:**
```json
{
  "name": "John Smith",
  "preferences": {
    "preferred_sectors": ["Technology", "Consumer Staples"],
    "excluded_sectors": ["Oil & Gas", "Tobacco"],
    "feature_weights": {
      "pe_ratio": 0.25,
      "dividend_yield": 0.25,
      "rotc": 0.4,
      "debt_to_equity": 0.1
    }
  }
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "user": {
      "id": 123,
      "email": "user@example.com",
      "name": "John Smith",
      "preferences": {
        "preferred_sectors": ["Technology", "Consumer Staples"],
        "excluded_sectors": ["Oil & Gas", "Tobacco"],
        "feature_weights": {
          "pe_ratio": 0.25,
          "dividend_yield": 0.25,
          "rotc": 0.4,
          "debt_to_equity": 0.1
        }
      }
    }
  }
}
```

### Submit Profiling Questionnaire
```
POST /user/profiling
```

**Request Body:**
```json
{
  "risk_tolerance": 60,
  "time_horizon": 10,
  "investment_goals": ["retirement", "growth"],
  "preferred_sectors": ["Technology", "Healthcare"],
  "excluded_sectors": ["Tobacco", "Gambling"],
  "income_level": "middle",
  "behavioral_responses": {
    "market_drop": "hold",
    "investment_approach": "research_based",
    "past_decisions": "regret_selling_early",
    "decision_making": "analytical"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "has_completed_profiling": true,
    "profile_id": 456
  }
}
```

### Get Profiling Results
```
GET /user/profiling/results
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "risk_profile": {
      "category": "Moderate Growth",
      "risk_tolerance": 60,
      "max_risk": 25,
      "min_return": 6,
      "time_horizon": 10,
      "description": "You seek a balance of growth and capital preservation..."
    },
    "behavioral_analysis": {
      "top_biases": [
        {
          "name": "Disposition Effect",
          "score": 7.2,
          "description": "Tendency to sell winners too early and hold losers too long",
          "strategy": "Set pre-determined exit points for both gains and losses",
          "alert_level": "warning"
        },
        {
          "name": "Recency Bias",
          "score": 5.1,
          "description": "Overweighting recent events and underweighting historical data",
          "strategy": "Maintain a long-term perspective and review historical trends",
          "alert_level": "info"
        }
      ]
    },
    "asset_allocation": {
      "equities": 60,
      "fixed_income": 25,
      "alternatives": 10,
      "cash": 5
    },
    "investment_policy": {
      "investment_objectives": {
        "return_target": "7-9% annualized return",
        "primary_objectives": "Growth with moderate income"
      },
      "risk_constraints": {
        "max_volatility": "15%",
        "max_drawdown": "20%",
        "var_limit": "12% (95% confidence)",
        "beta_target": "0.8-1.0"
      },
      "time_horizon": "Medium-term (8-12 years)",
      "liquidity_requirements": {
        "cash_allocation": "5-10%",
        "illiquid_assets_max": "15%",
        "emergency_fund": "6 months of expenses"
      },
      "rebalancing_policy": {
        "frequency": "Semi-annual review, rebalance when allocations drift by 5% or more",
        "thresholds": "5% absolute deviation from targets"
      }
    },
    "preferred_sectors": ["Technology", "Healthcare"],
    "excluded_sectors": ["Tobacco", "Gambling"]
  }
}
```

## Stock Analysis

### Analyze Stock
```
GET /stocks/analyze/{symbol}
```

**Path Parameters:**
- symbol: Stock ticker symbol (e.g., AAPL, MSFT)

**Query Parameters:**
- market: Market identifier (optional, default "US") - "US" or "SA" (Saudi Arabia)
- use_ml: Whether to use machine learning model (optional, default true)

**Response:**
```json
{
  "status": "success",
  "data": {
    "symbol": "MSFT",
    "name": "Microsoft Corporation",
    "current_price": 336.25,
    "price_change": 4.32,
    "price_change_percent": 1.28,
    "market_cap": 2490000000000,
    "fundamental_analysis": {
      "pe_ratio": 34.21,
      "forward_pe": 28.53,
      "peg_ratio": 2.1,
      "rotc": 18.7,
      "debt_to_equity": 0.41,
      "free_cash_flow": 65200000000,
      "revenue_growth": 16.8,
      "eps_growth": 19.2,
      "dividend_yield": 0.8,
      "payout_ratio": 27.4
    },
    "technical_analysis": {
      "sma_50": 320.45,
      "sma_200": 295.83,
      "rsi_14": 63.2,
      "macd": 2.5,
      "bollinger_bands": {
        "upper": 345.2,
        "middle": 320.45,
        "lower": 295.7
      },
      "support_levels": [315.2, 300.4],
      "resistance_levels": [340.5, 350.0]
    },
    "sentiment_analysis": {
      "overall_score": 75,
      "news_sentiment": 68,
      "social_sentiment": 82,
      "analyst_sentiment": 76,
      "recent_news": [
        {
          "title": "Microsoft Announces New AI Features",
          "url": "https://example.com/news/12345",
          "sentiment": "positive",
          "date": "2025-03-18T14:30:00Z"
        }
      ]
    },
    "naif_model_analysis": {
      "meets_criteria": true,
      "rotc_check": "pass",
      "pe_check": "pass",
      "debt_check": "pass",
      "growth_check": "pass",
      "fcf_check": "pass"
    },
    "ml_analysis": {
      "score": 83,
      "recommendation": "buy",
      "confidence": "high",
      "key_factors": ["strong_fundamentals", "positive_momentum", "reasonable_valuation"]
    },
    "recommendation": {
      "action": "buy",
      "reasoning": "Strong fundamentals with consistent growth and profitability. ROTC of 18.7% exceeds the 15% threshold, with reasonable valuation and strong technical support.",
      "target_price": 372.50,
      "time_horizon": "medium_term",
      "risk_level": "moderate"
    }
  }
}
```

### Compare Stocks
```
GET /stocks/compare
```

**Query Parameters:**
- symbols: Comma-separated list of stock symbols (e.g., AAPL,MSFT,GOOGL)
- metrics: Comma-separated list of metrics to compare (optional, default includes essential metrics)
- market: Market identifier (optional, default "US")

**Response:**
```json
{
  "status": "success",
  "data": {
    "symbols": ["AAPL", "MSFT", "GOOGL"],
    "names": ["Apple Inc.", "Microsoft Corporation", "Alphabet Inc."],
    "comparison": {
      "current_price": [182.63, 336.25, 140.42],
      "market_cap": [2850000000000, 2490000000000, 1790000000000],
      "pe_ratio": [30.42, 34.21, 25.67],
      "forward_pe": [27.84, 28.53, 21.93],
      "rotc": [27.3, 18.7, 22.1],
      "revenue_growth": [14.2, 16.8, 13.5],
      "dividend_yield": [0.5, 0.8, 0],
      "debt_to_equity": [1.52, 0.41, 0.12],
      "free_cash_flow": [90200000000, 65200000000, 70800000000],
      "rsi_14": [68.3, 63.2, 57.4]
    },
    "naif_criteria_met": {
      "AAPL": true,
      "MSFT": true,
      "GOOGL": true
    },
    "ml_recommendations": {
      "AAPL": {
        "score": 78,
        "recommendation": "buy"
      },
      "MSFT": {
        "score": 83,
        "recommendation": "buy"
      },
      "GOOGL": {
        "score": 81,
        "recommendation": "buy"
      }
    }
  }
}
```

### Get Stock News
```
GET /stocks/{symbol}/news
```

**Path Parameters:**
- symbol: Stock ticker symbol

**Query Parameters:**
- limit: Number of news items to return (optional, default 10)
- days: Number of days to look back (optional, default 7)

**Response:**
```json
{
  "status": "success",
  "data": {
    "symbol": "AAPL",
    "name": "Apple Inc.",
    "sentiment_score": 72,
    "news": [
      {
        "title": "Apple's New AI Strategy Could Reshape The Industry",
        "url": "https://example.com/news/45678",
        "source": "TechCrunch",
        "date": "2025-03-19T09:45:00Z",
        "summary": "Apple is planning to reveal major AI initiatives at WWDC that could reshape its product strategy...",
        "sentiment": "positive",
        "sentiment_score": 0.86
      },
      {
        "title": "Supply Chain Issues May Impact Apple's Q2 Results",
        "url": "https://example.com/news/45679",
        "source": "Bloomberg",
        "date": "2025-03-18T14:20:00Z",
        "summary": "Analysts are concerned about potential supply chain constraints affecting Apple's production capacity...",
        "sentiment": "negative",
        "sentiment_score": 0.32
      }
    ]
  }
}
```

### Get Sector Performance
```
GET /market/sectors
```

**Query Parameters:**
- market: Market identifier (optional, default "US")
- period: Time period (optional, default "1m", options: "1d", "1w", "1m", "3m", "6m", "1y", "ytd")

**Response:**
```json
{
  "status": "success",
  "data": {
    "market": "US",
    "period": "1m",
    "sectors": [
      {
        "name": "Technology",
        "performance": 3.2,
        "performance_ytd": 8.7,
        "average_pe": 28.5,
        "average_dividend": 0.8
      },
      {
        "name": "Healthcare",
        "performance": 1.8,
        "performance_ytd": 5.3,
        "average_pe": 22.4,
        "average_dividend": 1.6
      },
      {
        "name": "Financials",
        "performance": 0.9,
        "performance_ytd": 4.1,
        "average_pe": 13.2,
        "average_dividend": 2.4
      }
    ]
  }
}
```

## Portfolio Management

### Get User Portfolios
```
GET /portfolios
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "portfolios": [
      {
        "id": 123,
        "name": "Growth Portfolio",
        "total_value": 125436.78,
        "cash_balance": 12500.00,
        "return_ytd": 8.4,
        "return_1y": 12.7,
        "created_at": "2025-01-15T10:30:00Z",
        "last_updated": "2025-03-20T14:45:00Z"
      },
      {
        "id": 124,
        "name": "Dividend Income",
        "total_value": 85240.32,
        "cash_balance": 5280.15,
        "return_ytd": 4.2,
        "return_1y": 9.3,
        "created_at": "2025-02-03T09:15:00Z",
        "last_updated": "2025-03-20T14:45:00Z"
      }
    ]
  }
}
```

### Get Portfolio Details
```
GET /portfolios/{id}
```

**Path Parameters:**
- id: Portfolio ID

**Response:**
```json
{
  "status": "success",
  "data": {
    "portfolio": {
      "id": 123,
      "name": "Growth Portfolio",
      "description": "Long-term growth focused on technology and healthcare",
      "total_value": 125436.78,
      "cash_balance": 12500.00,
      "return_data": {
        "return_ytd": 8.4,
        "return_1y": 12.7,
        "return_3y": 34.2,
        "return_5y": 56.8
      },
      "metrics": {
        "alpha": 2.3,
        "beta": 1.2,
        "sharpe_ratio": 1.42,
        "volatility": 14.8,
        "max_drawdown": 18.5
      },
      "allocations": {
        "by_sector": {
          "Technology": 42.5,
          "Healthcare": 25.3,
          "Consumer Discretionary": 15.2,
          "Financials": 9.8,
          "Cash": 7.2
        },
        "by_asset_class": {
          "Equities": 92.8,
          "Cash": 7.2
        }
      },
      "holdings": [
        {
          "symbol": "AAPL",
          "name": "Apple Inc.",
          "shares": 150,
          "purchase_price": 145.75,
          "current_price": 182.63,
          "value": 27394.50,
          "weight": 21.8,
          "gain_loss": 5532.00,
          "gain_loss_percent": 25.3,
          "purchase_date": "2025-01-20T00:00:00Z"
        },
        {
          "symbol": "MSFT",
          "name": "Microsoft Corporation",
          "shares": 75,
          "purchase_price": 310.25,
          "current_price": 336.25,
          "value": 25218.75,
          "weight": 20.1,
          "gain_loss": 1950.00,
          "gain_loss_percent": 8.4,
          "purchase_date": "2025-01-20T00:00:00Z"
        }
      ]
    }
  }
}
```

### Create Portfolio
```
POST /portfolios
```

**Request Body:**
```json
{
  "name": "Balanced Growth",
  "description": "Mix of growth and value stocks with moderate risk",
  "cash_balance": 25000.00
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "portfolio": {
      "id": 125,
      "name": "Balanced Growth",
      "description": "Mix of growth and value stocks with moderate risk",
      "total_value": 25000.00,
      "cash_balance": 25000.00,
      "created_at": "2025-03-20T15:30:00Z"
    }
  }
}
```

### Update Portfolio
```
PUT /portfolios/{id}
```

**Path Parameters:**
- id: Portfolio ID

**Request Body:**
```json
{
  "name": "Balanced Growth & Income",
  "description": "Mix of growth, value, and dividend stocks with moderate risk"
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "portfolio": {
      "id": 125,
      "name": "Balanced Growth & Income",
      "description": "Mix of growth, value, and dividend stocks with moderate risk"
    }
  }
}
```

### Delete Portfolio
```
DELETE /portfolios/{id}
```

**Path Parameters:**
- id: Portfolio ID

**Response:**
```json
{
  "status": "success"
}
```

### Add Stock to Portfolio
```
POST /portfolios/{id}/holdings
```

**Path Parameters:**
- id: Portfolio ID

**Request Body:**
```json
{
  "symbol": "GOOGL",
  "shares": 10,
  "purchase_price": 138.42,
  "purchase_date": "2025-03-20T00:00:00Z"
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "holding": {
      "symbol": "GOOGL",
      "name": "Alphabet Inc.",
      "shares": 10,
      "purchase_price": 138.42,
      "current_price": 140.42,
      "value": 1404.20,
      "weight": 5.32,
      "gain_loss": 20.00,
      "gain_loss_percent": 1.44,
      "purchase_date": "2025-03-20T00:00:00Z"
    },
    "portfolio": {
      "cash_balance": 23615.80,
      "total_value": 26404.20
    }
  }
}
```

### Update Portfolio Holding
```
PUT /portfolios/{portfolio_id}/holdings/{symbol}
```

**Path Parameters:**
- portfolio_id: Portfolio ID
- symbol: Stock symbol

**Request Body:**
```json
{
  "shares": 15
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "holding": {
      "symbol": "GOOGL",
      "name": "Alphabet Inc.",
      "shares": 15,
      "purchase_price": 138.42,
      "current_price": 140.42,
      "value": 2106.30,
      "weight": 7.82,
      "gain_loss": 30.00,
      "gain_loss_percent": 1.44,
      "purchase_date": "2025-03-20T00:00:00Z"
    }
  }
}
```

### Remove Stock from Portfolio
```
DELETE /portfolios/{portfolio_id}/holdings/{symbol}
```

**Path Parameters:**
- portfolio_id: Portfolio ID
- symbol: Stock symbol

**Response:**
```json
{
  "status": "success",
  "data": {
    "portfolio": {
      "cash_balance": 25722.10,
      "total_value": 26404.20
    }
  }
}
```

### Get Portfolio Performance
```
GET /portfolios/{id}/performance
```

**Path Parameters:**
- id: Portfolio ID

**Query Parameters:**
- period: Time period (optional, default "1y", options: "1w", "1m", "3m", "6m", "1y", "3y", "5y", "ytd", "all")
- interval: Data interval (optional, default "1d", options: "1d", "1w", "1m")

**Response:**
```json
{
  "status": "success",
  "data": {
    "portfolio_id": 123,
    "portfolio_name": "Growth Portfolio",
    "period": "1y",
    "interval": "1d",
    "base_currency": "USD",
    "start_date": "2024-03-20T00:00:00Z",
    "end_date": "2025-03-20T00:00:00Z",
    "start_value": 111305.87,
    "end_value": 125436.78,
    "absolute_return": 14130.91,
    "percent_return": 12.7,
    "benchmark_return": 9.2,
    "alpha": 3.5,
    "time_series": [
      {
        "date": "2024-03-20T00:00:00Z",
        "value": 111305.87,
        "cash": 10000.00
      },
      {
        "date": "2024-03-21T00:00:00Z",
        "value": 111623.45,
        "cash": 10000.00
      },
      // Additional time series data...
      {
        "date": "2025-03-20T00:00:00Z",
        "value": 125436.78,
        "cash": 12500.00
      }
    ],
    "holdings_performance": [
      {
        "symbol": "AAPL",
        "name": "Apple Inc.",
        "return_percent": 25.3,
        "contribution": 4.4
      },
      {
        "symbol": "MSFT",
        "name": "Microsoft Corporation",
        "return_percent": 8.4,
        "contribution": 1.7
      }
    ]
  }
}
```

### Optimize Portfolio
```
POST /portfolios/{id}/optimize
```

**Path Parameters:**
- id: Portfolio ID

**Request Body:**
```json
{
  "optimization_target": "sharpe",
  "risk_tolerance": 60,
  "constraints": {
    "max_position_size": 0.25,
    "min_position_size": 0.02,
    "sector_constraints": {
      "Technology": {"min": 0.10, "max": 0.40},
      "Financials": {"min": 0.05, "max": 0.25}
    }
  }
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "current_portfolio": {
      "expected_return": 8.7,
      "volatility": 15.2,
      "sharpe_ratio": 0.57
    },
    "optimized_portfolio": {
      "expected_return": 9.3,
      "volatility": 14.1,
      "sharpe_ratio": 0.66
    },
    "current_weights": {
      "AAPL": 0.218,
      "MSFT": 0.201,
      "GOOGL": 0.156,
      "JNJ": 0.123,
      "PG": 0.082,
      "JPM": 0.065,
      "CASH": 0.155
    },
    "recommended_weights": {
      "AAPL": 0.200,
      "MSFT": 0.200,
      "GOOGL": 0.150,
      "JNJ": 0.150,
      "PG": 0.100,
      "JPM": 0.100,
      "CASH": 0.100
    },
    "recommended_trades": [
      {
        "symbol": "AAPL",
        "action": "sell",
        "current_shares": 150,
        "target_shares": 137,
        "difference": -13
      },
      {
        "symbol": "JNJ",
        "action": "buy",
        "current_shares": 85,
        "target_shares": 103,
        "difference": 18
      }
    ],
    "sector_allocations": {
      "current": {
        "Technology": 0.575,
        "Healthcare": 0.123,
        "Consumer Staples": 0.082,
        "Financials": 0.065,
        "Cash": 0.155
      },
      "recommended": {
        "Technology": 0.550,
        "Healthcare": 0.150,
        "Consumer Staples": 0.100,
        "Financials": 0.100,
        "Cash": 0.100
      }
    }
  }
}
```

## Recommendations

### Get Stock Recommendations
```
GET /recommendations/stocks
```

**Query Parameters:**
- count: Number of recommendations to return (optional, default 10)
- market: Market identifier (optional, default "US")
- sectors: Comma-separated list of sectors to include (optional)
- exclude_sectors: Comma-separated list of sectors to exclude (optional)

**Response:**
```json
{
  "status": "success",
  "data": {
    "recommendations": [
      {
        "symbol": "AAPL",
        "name": "Apple Inc.",
        "sector": "Technology",
        "current_price": 182.63,
        "price_change_percent": 1.2,
        "reasons": ["strong_fundamentals", "consistent_growth", "naif_criteria_met"],
        "match_score": 92,
        "fundamental_highlights": {
          "pe_ratio": 30.42,
          "rotc": 27.3,
          "revenue_growth": 14.2
        }
      },
      {
        "symbol": "MSFT",
        "name": "Microsoft Corporation",
        "sector": "Technology",
        "current_price": 336.25,
        "price_change_percent": 0.8,
        "reasons": ["strong_financials", "dividend_growth", "technical_strength"],
        "match_score": 88,
        "fundamental_highlights": {
          "pe_ratio": 34.21,
          "rotc": 18.7,
          "revenue_growth": 16.8
        }
      }
    ],
    "personalization_factors": {
      "risk_profile": "moderate_growth",
      "preferred_sectors": ["Technology", "Healthcare"],
      "feature_weights": {
        "pe_ratio": 0.3,
        "rotc": 0.4,
        "revenue_growth": 0.3
      }
    }
  }
}
```

### Get Portfolio Recommendations
```
GET /recommendations/portfolio/{id}
```

**Path Parameters:**
- id: Portfolio ID

**Response:**
```json
{
  "status": "success",
  "data": {
    "portfolio_id": 123,
    "portfolio_name": "Growth Portfolio",
    "current_allocations": {
      "Technology": 57.5,
      "Healthcare": 12.3,
      "Consumer Staples": 8.2,
      "Financials": 6.5,
      "Cash": 15.5
    },
    "recommendations": {
      "rebalancing": {
        "required": true,
        "reason": "Technology sector exceeds target allocation by more than 10%",
        "actions": [
          {
            "description": "Reduce Technology exposure",
            "current": 57.5,
            "target": 45.0,
            "trades": [
              {
                "symbol": "AAPL",
                "action": "reduce",
                "amount": 5000
              }
            ]
          },
          {
            "description": "Increase Healthcare exposure",
            "current": 12.3,
            "target": 20.0,
            "trades": [
              {
                "symbol": "JNJ",
                "action": "add",
                "amount": 5000
              }
            ]
          }
        ]
      },
      "diversification": {
        "current_score": 72,
        "recommendations": [
          {
            "type": "add_sector",
            "sector": "Utilities",
            "reasoning": "Adds defensive exposure with low correlation to tech",
            "suggestion": "Consider XLU ETF or NEE"
          },
          {
            "type": "reduce_concentration",
            "description": "Top 2 holdings represent 41.9% of portfolio",
            "target": "Reduce to maximum of 30%"
          }
        ]
      },
      "new_positions": [
        {
          "symbol": "NEE",
          "name": "NextEra Energy",
          "sector": "Utilities",
          "reasoning": "Adds sector diversification, strong dividend growth",
          "suggested_allocation": 5.0
        },
        {
          "symbol": "V",
          "name": "Visa Inc.",
          "sector": "Financials",
          "reasoning": "Strong growth, high ROTC, meets Naif criteria",
          "suggested_allocation": 5.0
        }
      ]
    }
  }
}
```

### Get ML Recommendations
```
GET /recommendations/ml
```

**Query Parameters:**
- count: Number of recommendations to return (optional, default 10)
- market: Market identifier (optional, default "US")

**Response:**
```json
{
  "status": "success",
  "data": {
    "ml_profile": {
      "risk_profile": "growth_oriented",
      "preferred_metrics": ["rotc", "revenue_growth", "pe_ratio"],
      "sector_preferences": {
        "Technology": "strong_preference",
        "Healthcare": "moderate_preference",
        "Energy": "avoid"
      },
      "strategy_alignment": "growth_investing"
    },
    "recommendations": [
      {
        "symbol": "NVDA",
        "name": "NVIDIA Corporation",
        "sector": "Technology",
        "match_score": 95,
        "ml_confidence": "very_high",
        "key_factors": [
          {
            "factor": "revenue_growth",
            "value": 41.2,
            "contribution": "very_positive"
          },
          {
            "factor": "rotc",
            "value": 26.8,
            "contribution": "very_positive"
          }
        ],
        "user_alignment": 0.91
      },
      {
        "symbol": "ADBE",
        "name": "Adobe Inc.",
        "sector": "Technology",
        "match_score": 89,
        "ml_confidence": "high",
        "key_factors": [
          {
            "factor": "rotc",
            "value": 22.3,
            "contribution": "positive"
          },
          {
            "factor": "operating_margin",
            "value": 34.5,
            "contribution": "very_positive"
          }
        ],
        "user_alignment": 0.87
      }
    ]
  }
}
```

## Chat Interface

### Send Message
```
POST /chat/message
```

**Request Body:**
```json
{
  "message": "Analyze AAPL and tell me if it meets the Naif criteria",
  "context_id": "conv_12345678"
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "context_id": "conv_12345678",
    "response": {
      "text": "I've analyzed Apple Inc. (AAPL) and here's what I found:\n\nYes, AAPL meets all the Naif model criteria:\n\n• ROTC: 27.3% (exceeds 15% threshold)\n• P/E Ratio: 30.4 (slightly above 25 threshold but acceptable)\n• Debt-to-Equity: 1.52 (acceptable given Apple's stable cash flows)\n• Free Cash Flow: $90.2B (very strong)\n• Revenue Growth: 14.2% (solid growth rate)\n\nThe company shows excellent return on total capital and strong fundamentals overall. Would you like me to provide a more detailed analysis of any specific aspect?",
      "has_visualization": false,
      "detected_intent": "stock_analysis",
      "stock_data": {
        "symbol": "AAPL",
        "name": "Apple Inc.",
        "meets_naif_criteria": true,
        "current_price": 182.63
      }
    }
  }
}
```

### Generate Visualization
```
POST /chat/visualization
```

**Request Body:**
```json
{
  "visualization_type": "price_chart",
  "symbols": ["AAPL", "MSFT"],
  "time_period": "6m",
  "context_id": "conv_12345678"
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "context_id": "conv_12345678",
    "visualization_id": "viz_87654321",
    "image_url": "https://api.investmentbot.com/visualizations/viz_87654321.png",
    "visualization_data": {
      "type": "price_chart",
      "title": "Price Comparison: AAPL vs MSFT (6 Months)",
      "symbols": ["AAPL", "MSFT"],
      "time_period": "6m",
      "normalized": true
    }
  }
}
```

## Error Responses

### Authentication Error
```json
{
  "status": "error",
  "error": {
    "code": "authentication_error",
    "message": "Invalid or expired authentication token."
  }
}
```

### Validation Error
```json
{
  "status": "error",
  "error": {
    "code": "validation_error",
    "message": "Invalid request data.",
    "details": {
      "field": "email",
      "issue": "Invalid email format."
    }
  }
}
```

### Not Found Error
```json
{
  "status": "error",
  "error": {
    "code": "not_found",
    "message": "The requested resource was not found.",
    "resource_type": "portfolio",
    "resource_id": "123"
  }
}
```

### Rate Limit Error
```json
{
  "status": "error",
  "error": {
    "code": "rate_limit_exceeded",
    "message": "You have exceeded the rate limit for this API.",
    "limit": 100,
    "remaining": 0,
    "reset_at": "2025-03-20T15:45:00Z"
  }
}
```

## Implementation Notes

1. All endpoints require authentication via JWT token in the Authorization header:
   ```
   Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```

2. Refresh tokens have a 30-day expiration, while access tokens expire after 1 hour

3. API versioning is handled through the URL path (/v1)

4. Rate limiting is applied:
   - 100 requests per minute for standard users
   - 300 requests per minute for premium users

5. All timestamps use ISO 8601 format in UTC timezone

6. Monetary values are provided in the user's configured currency (default USD)

7. Pagination is supported via limit and offset query parameters for collection endpoints

8. Proper HTTP status codes are used:
   - 200: Successful GET, PUT requests
   - 201: Successful POST requests
   - 204: Successful DELETE requests
   - 400: Bad request (validation errors)
   - 401: Unauthorized
   - 403: Forbidden (authenticated but insufficient permissions)
   - 404: Resource not found
   - 429: Rate limit exceeded
   - 500: Server error