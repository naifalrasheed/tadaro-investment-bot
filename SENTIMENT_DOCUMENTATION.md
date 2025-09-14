# Investment Bot Sentiment Score Documentation

## Overview

The Investment Bot uses a comprehensive sentiment score to evaluate stocks. This score combines multiple factors to provide a holistic view of a stock's current market sentiment, technical indicators, and fundamental metrics.

## Sentiment Score Composition

The sentiment score is calculated on a scale of -100 to +100, with the following weightings:

| Component | Weight | Description |
|-----------|--------|-------------|
| Price Momentum | 40% | Measures recent price movement trends |
| 52-Week Range Position | 20% | Where the current price sits in the 52-week trading range |
| YTD Performance | 20% | Year-to-date percentage return |
| News Sentiment | 10% | Analysis of recent news articles sentiment |
| Return on Total Capital (ROTC) | 10% | Fundamental performance metric |

## Interpretation Guide

| Score Range | Interpretation | Color |
|-------------|----------------|-------|
| +75 to +100 | Very Bullish | Dark Green |
| +50 to +74 | Bullish | Green |
| +25 to +49 | Mildly Bullish | Light Green |
| -24 to +24 | Neutral | Gray |
| -25 to -49 | Mildly Bearish | Light Red |
| -50 to -74 | Bearish | Red |
| -75 to -100 | Very Bearish | Dark Red |

## Component Details

### Price Momentum (40%)
- Calculated based on recent price movements (5-day, 10-day, 20-day)
- Positive score: Upward price trend
- Negative score: Downward price trend
- Higher weights given to more recent movements

### 52-Week Range Position (20%)
- Score of +100: Price at 52-week high
- Score of -100: Price at 52-week low
- Linear scale between these points

### YTD Performance (20%)
- Direct percentage scaled appropriately:
  - +30% or more YTD: +100 score
  - -30% or more YTD: -100 score
  - Linear scale between these points

### News Sentiment (10%)
- Derived from natural language processing of recent news articles
- Measures positive vs. negative language and context
- Sources include financial news sites and social media

### Return on Total Capital (10%)
- Fundamental metric measuring company's efficiency
- Compared to sector average:
  - Above average: Positive score
  - Below average: Negative score
  - Scaled based on deviation from average

## Usage Notes

- The sentiment score is designed as a quick reference point, not a comprehensive analysis
- Always review individual components for context
- Scores should be considered alongside other investment research
- Certain market conditions may affect the reliability of specific components
- Scores are recalculated daily with fresh data

## Example Calculation

For stock ABC with:
- Strong recent uptrend (+75 momentum score)
- Price near 52-week high (+90 range position)
- YTD return of +15% (+50 YTD score)
- Mixed news coverage (0 news sentiment)
- Above average ROTC (+40 ROTC score)

The weighted calculation would be:
(75 × 0.4) + (90 × 0.2) + (50 × 0.2) + (0 × 0.1) + (40 × 0.1) = 30 + 18 + 10 + 0 + 4 = +62

This would result in a "Bullish" sentiment rating.