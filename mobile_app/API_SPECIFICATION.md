# Investment Bot API Specification

## API Overview

This document outlines the RESTful API endpoints used by the Investment Bot mobile applications to communicate with the server. The API follows standard REST conventions and uses JSON for data exchange.

## Base URL

```
https://api.investmentbot.com/v1
```

## Authentication

All authenticated endpoints require a valid JWT token in the Authorization header:

```
Authorization: Bearer <jwt_token>
```

### Authentication Endpoints

#### Register New User

```
POST /auth/register
```

Request:
```json
{
  "email": "user@example.com",
  "password": "securePassword123",
  "name": "John Doe"
}
```

Response:
```json
{
  "user_id": 12345,
  "email": "user@example.com",
  "name": "John Doe",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### Login

```
POST /auth/login
```

Request:
```json
{
  "email": "user@example.com",
  "password": "securePassword123"
}
```

Response:
```json
{
  "user_id": 12345,
  "email": "user@example.com",
  "name": "John Doe",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_expiry": "2025-03-21T15:29:31Z"
}
```

#### Refresh Token

```
POST /auth/refresh
```

Request:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

Response:
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_expiry": "2025-03-21T15:29:31Z"
}
```

#### Logout

```
POST /auth/logout
```

Request:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

Response:
```json
{
  "success": true,
  "message": "Successfully logged out"
}
```

## Stock Analysis Endpoints

#### Get Stock Overview

```
GET /stocks/{symbol}
```

Response:
```json
{
  "symbol": "AAPL",
  "company_name": "Apple Inc.",
  "current_price": 174.79,
  "price_change": 1.25,
  "price_change_percent": 0.72,
  "market_cap": 2729845000000,
  "pe_ratio": 28.91,
  "dividend_yield": 0.50,
  "sector": "Technology",
  "industry": "Consumer Electronics",
  "price_updated_at": "2025-03-20T16:00:00Z"
}
```

#### Get Stock Analysis

```
GET /stocks/{symbol}/analysis
```

Response:
```json
{
  "symbol": "AAPL",
  "company_name": "Apple Inc.",
  "current_price": 174.79,
  "price_metrics": {
    "daily_change": 0.72,
    "ytd_performance": 12.35,
    "week_52_high": 198.23,
    "week_52_low": 143.90,
    "volume": 57840000,
    "avg_volume": 64120000,
    "sentiment_score": 68.5
  },
  "integrated_analysis": {
    "technical_analysis": {
      "technical_score": 68.5,
      "ml_prediction": 2.3,
      "confidence": 77.2,
      "price_metrics": {
        "current_price": 174.79,
        "predicted_price": 186.23,
        "volatility": 22.15
      }
    },
    "fundamental_analysis": {
      "pe_ratio": 28.91,
      "forward_pe": 26.43,
      "peg_ratio": 2.1,
      "profit_margin": 25.31,
      "rotc_data": {
        "latest_rotc": 36.45,
        "avg_rotc": 35.89,
        "improving": true,
        "quarterly_rotc": [
          {"date": "2024-12-31", "rotc": 36.45, "nopat": 24500000000, "tangible_capital": 67217000000},
          {"date": "2024-09-30", "rotc": 35.92, "nopat": 23980000000, "tangible_capital": 66760000000},
          {"date": "2024-06-30", "rotc": 35.65, "nopat": 23210000000, "tangible_capital": 65104000000},
          {"date": "2024-03-31", "rotc": 35.54, "nopat": 22980000000, "tangible_capital": 64659000000}
        ]
      },
      "growth_data": {
        "revenue_growth": 6.8,
        "earnings_growth": 8.2,
        "latest_cash_flow": 98342000000,
        "cash_flow_positive": true,
        "cash_flow_trend": 3.2
      }
    }
  },
  "balance_sheet": {
    "fiscal_date_ending": "2024-12-31",
    "total_assets": 375319000000,
    "total_current_assets": 143600000000,
    "cash_and_equivalents": 62639000000,
    "total_liabilities": 290342000000,
    "total_current_liabilities": 123654000000,
    "long_term_debt": 98760000000,
    "total_shareholder_equity": 84977000000,
    "debt_to_equity": 3.42,
    "current_ratio": 1.16
  },
  "sentiment_data": {
    "sentiment_score": 68.5,
    "sentiment_label": "Bullish",
    "components": {
      "news_sentiment": 72.3,
      "social_media_sentiment": 65.8,
      "analyst_ratings": 70.2,
      "institutional_sentiment": 64.1
    }
  },
  "naif_model_criteria": {
    "meets_criteria": true,
    "failing_criteria": [],
    "passing_criteria": [
      "ROTC > 15%",
      "Debt-to-Equity < 5"
    ]
  },
  "recommendation": {
    "action": "Buy",
    "target_price": 186.23,
    "time_horizon": "6-12 months",
    "confidence": 77.2,
    "explanation": "Strong ROTC, positive cash flow trend, and bullish sentiment metrics"
  }
}
```

#### Get Technical Analysis

```
GET /stocks/{symbol}/technical
```

Response:
```json
{
  "symbol": "AAPL",
  "technical_score": 68.5,
  "price_momentum": 72.3,
  "volume_trend": 64.8,
  "ma_score": 65.9,
  "historical_data": {
    "data": [
      {
        "date": "2025-03-20",
        "open": 173.54,
        "high": 175.23,
        "low": 172.91,
        "close": 174.79,
        "volume": 57840000
      },
      // Additional historical data points...
    ]
  },
  "indicators": {
    "rsi": 58.3,
    "macd": {
      "macd_line": 1.23,
      "signal_line": 0.85,
      "histogram": 0.38
    },
    "bollinger_bands": {
      "upper": 182.45,
      "middle": 174.23,
      "lower": 166.01
    },
    "moving_averages": {
      "sma_50": 172.43,
      "sma_200": 168.92,
      "ema_20": 173.65
    }
  },
  "signal_summary": "AAPL shows moderate bullish momentum with support at 50-day moving average. The RSI at 58.3 indicates neither overbought nor oversold conditions. MACD is showing positive momentum with the MACD line above the signal line."
}
```

#### Get Fundamental Analysis

```
GET /stocks/{symbol}/fundamental
```

Response:
```json
{
  "symbol": "AAPL",
  "company_name": "Apple Inc.",
  "sector": "Technology",
  "industry": "Consumer Electronics",
  "financials": {
    "revenue": {
      "value": 383933000000,
      "growth": 6.8,
      "trend": "increasing"
    },
    "eps": {
      "value": 6.05,
      "growth": 8.2,
      "trend": "increasing"
    },
    "profit_margin": 25.31,
    "operating_margin": 30.18,
    "return_on_equity": 160.09,
    "return_on_assets": 27.93,
    "rotc": 36.45
  },
  "valuation": {
    "pe_ratio": 28.91,
    "forward_pe": 26.43,
    "peg_ratio": 2.1,
    "price_to_book": 45.23,
    "price_to_sales": 7.32,
    "enterprise_value_to_ebitda": 21.5
  },
  "growth_metrics": {
    "revenue_growth_5yr": 11.2,
    "eps_growth_5yr": 13.5,
    "dividend_growth_5yr": 8.7
  },
  "naif_model_evaluation": {
    "rotc_threshold": 15.0,
    "rotc_actual": 36.45,
    "pe_threshold": 25.0,
    "pe_actual": 28.91,
    "meets_criteria": true
  }
}
```

#### Get Sentiment Analysis

```
GET /stocks/{symbol}/sentiment
```

Response:
```json
{
  "symbol": "AAPL",
  "overall_sentiment": {
    "score": 68.5,
    "label": "Bullish",
    "change_7d": 3.2
  },
  "components": {
    "news_sentiment": {
      "score": 72.3,
      "sources": 42,
      "recent_headlines": [
        "Apple's AI Strategy Shows Promise, Analysts Say",
        "iPhone 16 Expected to Drive Strong Upgrade Cycle",
        "Apple Services Growth Accelerates in Q1"
      ]
    },
    "social_media_sentiment": {
      "score": 65.8,
      "mentions": 18243,
      "positive_ratio": 0.71
    },
    "analyst_ratings": {
      "score": 70.2,
      "buy": 28,
      "hold": 12,
      "sell": 3,
      "average_target_price": 188.45
    },
    "institutional_sentiment": {
      "score": 64.1,
      "institutional_holdings_change": 2.3,
      "top_buyers": [
        "Vanguard Group Inc",
        "BlackRock Inc",
        "State Street Corporation"
      ]
    }
  },
  "historical_sentiment": [
    {"date": "2025-03-13", "score": 65.3},
    {"date": "2025-03-06", "score": 63.8},
    {"date": "2025-02-27", "score": 62.5},
    {"date": "2025-02-20", "score": 64.2}
  ]
}
```

## Portfolio Endpoints

#### Get All Portfolios

```
GET /portfolio
```

Response:
```json
{
  "portfolios": [
    {
      "id": 123,
      "name": "Growth Portfolio",
      "description": "High-growth tech focus",
      "created_at": "2024-06-15T10:30:00Z",
      "last_updated": "2025-03-19T14:45:00Z",
      "summary": {
        "total_value": 125345.67,
        "cash_balance": 5340.21,
        "daily_change": 1.23,
        "total_gain": 23.45,
        "holdings_count": 12
      }
    },
    {
      "id": 124,
      "name": "Dividend Portfolio",
      "description": "Income focus with stable dividends",
      "created_at": "2024-08-22T11:20:00Z",
      "last_updated": "2025-03-20T09:15:00Z",
      "summary": {
        "total_value": 98765.43,
        "cash_balance": 2150.32,
        "daily_change": 0.56,
        "total_gain": 15.78,
        "holdings_count": 8
      }
    }
  ]
}
```

#### Get Portfolio Details

```
GET /portfolio/{id}
```

Response:
```json
{
  "id": 123,
  "name": "Growth Portfolio",
  "description": "High-growth tech focus",
  "created_at": "2024-06-15T10:30:00Z",
  "last_updated": "2025-03-19T14:45:00Z",
  "cash_balance": 5340.21,
  "total_value": 125345.67,
  "performance": {
    "daily_change": 1.23,
    "daily_change_value": 1523.45,
    "week_change": 2.34,
    "month_change": 5.67,
    "ytd_change": 12.34,
    "total_gain": 23.45,
    "total_gain_value": 23789.45
  },
  "holdings": [
    {
      "symbol": "AAPL",
      "company_name": "Apple Inc.",
      "shares": 50,
      "average_price": 150.23,
      "current_price": 174.79,
      "current_value": 8739.50,
      "weight": 7.27,
      "gain": 16.35,
      "gain_value": 1228.00
    },
    {
      "symbol": "MSFT",
      "company_name": "Microsoft Corporation",
      "shares": 30,
      "average_price": 280.45,
      "current_price": 420.72,
      "current_value": 12621.60,
      "weight": 10.50,
      "gain": 50.02,
      "gain_value": 4208.10
    },
    // Additional holdings...
  ],
  "sector_allocation": [
    {"sector": "Technology", "allocation": 45.3},
    {"sector": "Healthcare", "allocation": 20.1},
    {"sector": "Consumer Discretionary", "allocation": 15.6},
    {"sector": "Financials", "allocation": 10.2},
    {"sector": "Industrials", "allocation": 8.8}
  ],
  "risk_metrics": {
    "volatility": 15.4,
    "beta": 1.2,
    "sharpe_ratio": 1.45,
    "alpha": 3.2,
    "max_drawdown": 12.5
  }
}
```

#### Create Portfolio

```
POST /portfolio
```

Request:
```json
{
  "name": "Retirement Portfolio",
  "description": "Long-term retirement goals",
  "cash_balance": 10000
}
```

Response:
```json
{
  "id": 125,
  "name": "Retirement Portfolio",
  "description": "Long-term retirement goals",
  "created_at": "2025-03-20T17:30:00Z",
  "last_updated": "2025-03-20T17:30:00Z",
  "cash_balance": 10000,
  "total_value": 10000,
  "holdings": []
}
```

#### Update Portfolio

```
PUT /portfolio/{id}
```

Request:
```json
{
  "name": "Updated Retirement Portfolio",
  "description": "Updated long-term retirement goals",
  "cash_balance": 12000
}
```

Response:
```json
{
  "id": 125,
  "name": "Updated Retirement Portfolio",
  "description": "Updated long-term retirement goals",
  "cash_balance": 12000,
  "last_updated": "2025-03-20T18:15:00Z"
}
```

#### Add Stock to Portfolio

```
POST /portfolio/{id}/stocks
```

Request:
```json
{
  "symbol": "NVDA",
  "shares": 10,
  "purchase_price": 850.23,
  "purchase_date": "2025-03-20T18:30:00Z"
}
```

Response:
```json
{
  "portfolio_id": 125,
  "symbol": "NVDA",
  "company_name": "NVIDIA Corporation",
  "shares": 10,
  "purchase_price": 850.23,
  "current_price": 858.65,
  "current_value": 8586.50,
  "weight": 41.36,
  "gain": 0.99,
  "gain_value": 84.20
}
```

#### Get Portfolio Analysis

```
GET /portfolio/{id}/analysis
```

Response:
```json
{
  "portfolio_id": 125,
  "portfolio_name": "Retirement Portfolio",
  "total_value": 20586.50,
  "performance_metrics": {
    "returns": {
      "daily": 1.23,
      "weekly": 2.45,
      "monthly": 4.56,
      "ytd": 8.76,
      "annual": 12.34
    },
    "risk_metrics": {
      "volatility": 15.4,
      "beta": 1.2,
      "sharpe_ratio": 1.45,
      "alpha": 3.2,
      "max_drawdown": 12.5
    }
  },
  "sector_analysis": {
    "allocations": [
      {"sector": "Technology", "allocation": 75.6, "benchmark": 28.5, "difference": 47.1},
      {"sector": "Consumer Discretionary", "allocation": 24.4, "benchmark": 10.8, "difference": 13.6}
    ],
    "over_allocated": ["Technology"],
    "under_allocated": ["Financials", "Healthcare", "Energy", "Utilities", "Materials"]
  },
  "optimization_suggestions": {
    "current_efficient_frontier": {
      "risk": 15.4,
      "return": 12.34
    },
    "optimized_efficient_frontier": {
      "risk": 13.8,
      "return": 13.56
    },
    "rebalance_suggestions": [
      {"symbol": "NVDA", "current_weight": 41.36, "suggested_weight": 30.0, "difference": -11.36},
      {"symbol": "PFE", "current_weight": 0, "suggested_weight": 10.0, "difference": 10.0},
      {"symbol": "JPM", "current_weight": 0, "suggested_weight": 10.0, "difference": 10.0}
    ]
  },
  "diversification_score": 42,
  "risk_level": "High"
}
```

## Chat Endpoints

#### Send Message

```
POST /chat
```

Request:
```json
{
  "message": "Analyze AAPL and show me its current valuation",
  "include_visualizations": true
}
```

Response:
```json
{
  "id": "msg_12345",
  "text": "Here's the analysis for Apple Inc. (AAPL):\n\nCurrent Price: $174.79\n\nTechnical Analysis:\n- Technical Score: 68.5/100 (Moderately Bullish)\n- Short-term prediction: +2.3% (Confidence: 77.2%)\n\nFundamental Analysis:\n- P/E Ratio: 28.91 (Sector avg: 25.3)\n- ROTC: 36.45% (Excellent)\n- Revenue Growth: 6.8% YoY\n\nValuation:\n- Current: Slightly overvalued based on P/E\n- Target Price: $186.23 (6-12 month horizon)\n\nNaif Model Criteria: Passes (Strong ROTC, moderate P/E)\n\nRecommendation: Buy - Strong fundamentals with solid growth metrics",
  "visualizations": {
    "price_chart": {
      "type": "line",
      "title": "AAPL Price History (6 Months)",
      "data": {
        "labels": ["2024-10-20", "2024-11-20", "2024-12-20", "2025-01-20", "2025-02-20", "2025-03-20"],
        "datasets": [
          {
            "label": "Price",
            "data": [150.23, 158.45, 165.67, 170.34, 172.56, 174.79],
            "borderColor": "rgba(75, 192, 192, 1)"
          }
        ]
      }
    },
    "valuation_gauge": {
      "type": "gauge",
      "title": "AAPL Valuation",
      "data": {
        "value": 65,
        "min": 0,
        "max": 100,
        "thresholds": [33, 66]
      }
    }
  }
}
```

#### Get Chat History

```
GET /chat/history
```

Response:
```json
{
  "history": [
    {
      "id": "msg_12343",
      "role": "user",
      "content": "What are the best tech stocks right now?",
      "timestamp": "2025-03-20T14:30:00Z"
    },
    {
      "id": "msg_12344",
      "role": "assistant",
      "content": "Based on current analysis, some of the strongest tech stocks include:\n\n1. NVIDIA (NVDA) - Strong AI growth, excellent ROTC (42.3%)\n2. Microsoft (MSFT) - Cloud growth, AI integration, stable fundamentals\n3. AMD (AMD) - Data center expansion, competitive CPU/GPU roadmap\n4. Salesforce (CRM) - AI integration, margin improvements\n5. Apple (AAPL) - Services growth, strong ecosystem, loyal customer base\n\nWould you like me to analyze any of these in more detail?",
      "timestamp": "2025-03-20T14:30:15Z"
    },
    {
      "id": "msg_12345",
      "role": "user",
      "content": "Analyze AAPL and show me its current valuation",
      "timestamp": "2025-03-20T14:31:00Z"
    },
    {
      "id": "msg_12346",
      "role": "assistant",
      "content": "Here's the analysis for Apple Inc. (AAPL):\n\nCurrent Price: $174.79\n\nTechnical Analysis:\n- Technical Score: 68.5/100 (Moderately Bullish)\n- Short-term prediction: +2.3% (Confidence: 77.2%)\n\nFundamental Analysis:\n- P/E Ratio: 28.91 (Sector avg: 25.3)\n- ROTC: 36.45% (Excellent)\n- Revenue Growth: 6.8% YoY\n\nValuation:\n- Current: Slightly overvalued based on P/E\n- Target Price: $186.23 (6-12 month horizon)\n\nNaif Model Criteria: Passes (Strong ROTC, moderate P/E)\n\nRecommendation: Buy - Strong fundamentals with solid growth metrics",
      "timestamp": "2025-03-20T14:31:15Z",
      "visualizations": {
        "price_chart": {
          "type": "line",
          "title": "AAPL Price History (6 Months)"
        },
        "valuation_gauge": {
          "type": "gauge",
          "title": "AAPL Valuation"
        }
      }
    }
  ]
}
```

#### Clear Chat History

```
POST /chat/clear
```

Response:
```json
{
  "success": true,
  "message": "Chat history cleared"
}
```

## ML Endpoints

#### Get ML Status

```
GET /ml/status
```

Response:
```json
{
  "model_status": {
    "trained": true,
    "last_trained": "2025-03-19T14:30:00Z",
    "prediction_accuracy": 0.823,
    "feedback_count": 42,
    "version": "3.2.1"
  },
  "user_preferences": {
    "feature_weights": {
      "price_momentum_weight": 1.23,
      "weekly_range_weight": 0.95,
      "ytd_performance_weight": 1.12,
      "news_sentiment_weight": 1.35,
      "rotc_weight": 1.42,
      "pe_ratio_weight": 1.08,
      "dividend_yield_weight": 0.78,
      "volume_weight": 0.85,
      "market_cap_weight": 0.92,
      "volatility_weight": 0.73
    },
    "preferred_sectors": [
      {"sector": "Technology", "score": 8},
      {"sector": "Healthcare", "score": 6},
      {"sector": "Consumer Discretionary", "score": 4}
    ],
    "avoided_sectors": [
      {"sector": "Energy", "score": -3},
      {"sector": "Utilities", "score": -2}
    ]
  },
  "activity_summary": {
    "liked_stocks": 28,
    "disliked_stocks": 12,
    "purchased_stocks": 14,
    "most_viewed": [
      {"symbol": "NVDA", "views": 42},
      {"symbol": "AAPL", "views": 35},
      {"symbol": "MSFT", "views": 29}
    ]
  }
}
```

#### Train ML Model

```
POST /ml/train
```

Response:
```json
{
  "success": true,
  "training_summary": {
    "training_time": 2.34,
    "samples_used": 42,
    "old_weights": {
      "price_momentum_weight": 1.15,
      "weekly_range_weight": 0.95,
      "ytd_performance_weight": 1.08,
      "news_sentiment_weight": 1.22,
      "rotc_weight": 1.35,
      "pe_ratio_weight": 1.08,
      "dividend_yield_weight": 0.78,
      "volume_weight": 0.85,
      "market_cap_weight": 0.92,
      "volatility_weight": 0.73
    },
    "new_weights": {
      "price_momentum_weight": 1.23,
      "weekly_range_weight": 0.95,
      "ytd_performance_weight": 1.12,
      "news_sentiment_weight": 1.35,
      "rotc_weight": 1.42,
      "pe_ratio_weight": 1.08,
      "dividend_yield_weight": 0.78,
      "volume_weight": 0.85,
      "market_cap_weight": 0.92,
      "volatility_weight": 0.73
    }
  },
  "top_priorities": [
    {"name": "ROTC", "weight": 1.42},
    {"name": "News Sentiment", "weight": 1.35},
    {"name": "Price Momentum", "weight": 1.23}
  ]
}
```

#### Provide Feedback

```
POST /ml/feedback
```

Request:
```json
{
  "symbol": "NVDA",
  "feedback_type": "like"
}
```

Response:
```json
{
  "success": true,
  "feedback_recorded": {
    "symbol": "NVDA",
    "feedback_type": "like",
    "feedback_date": "2025-03-20T19:15:00Z"
  },
  "updated_weights": {
    "price_momentum_weight": 1.29,
    "weekly_range_weight": 0.95,
    "ytd_performance_weight": 1.15,
    "news_sentiment_weight": 1.35,
    "rotc_weight": 1.49,
    "pe_ratio_weight": 1.08,
    "dividend_yield_weight": 0.78,
    "volume_weight": 0.85,
    "market_cap_weight": 0.92,
    "volatility_weight": 0.73
  },
  "learning_insights": [
    "Increased weights for ROTC based on NVDA's strong 42.3% return on total capital",
    "Reinforced preference for strong price momentum stocks",
    "Technology sector preference score increased to 9/10"
  ]
}
```

#### Reset ML Model

```
POST /ml/reset
```

Response:
```json
{
  "success": true,
  "message": "ML model reset to default values",
  "default_weights": {
    "price_momentum_weight": 1.0,
    "weekly_range_weight": 1.0,
    "ytd_performance_weight": 1.0,
    "news_sentiment_weight": 1.0,
    "rotc_weight": 1.0,
    "pe_ratio_weight": 1.0,
    "dividend_yield_weight": 1.0,
    "volume_weight": 1.0,
    "market_cap_weight": 1.0,
    "volatility_weight": 1.0
  }
}
```

## Error Handling

All API endpoints use standard HTTP status codes and return consistent error objects:

```json
{
  "error": {
    "code": "authentication_error",
    "message": "Invalid or expired token",
    "status": 401,
    "details": {
      "token_expired_at": "2025-03-20T15:30:00Z"
    }
  }
}
```

### Common Error Codes

| Status Code | Error Code | Description |
|------------|------------|-------------|
| 400 | invalid_request | Invalid request format or parameters |
| 401 | authentication_error | Authentication failure or expired token |
| 403 | permission_denied | User lacks permission for the action |
| 404 | not_found | Requested resource not found |
| 429 | rate_limit_exceeded | API rate limit exceeded |
| 500 | server_error | Internal server error |
| 503 | service_unavailable | Service temporarily unavailable |

## Rate Limiting

API requests are subject to rate limiting based on the following tiers:

| Plan | Requests / Minute | Requests / Day |
|------|-------------------|---------------|
| Free | 30 | 1,000 |
| Premium | 120 | 10,000 |
| Enterprise | 300 | 50,000 |

Rate limit information is included in API response headers:

```
X-RateLimit-Limit: 120
X-RateLimit-Remaining: 116
X-RateLimit-Reset: 1616179200
```

## Versioning

API versioning is handled via the URL path (e.g., `/v1/stocks`). When a new major version is released, the previous version will be maintained for at least 12 months to allow for client migration.

## Support

For API support, please contact:
- Email: api-support@investmentbot.com
- Documentation: https://developers.investmentbot.com