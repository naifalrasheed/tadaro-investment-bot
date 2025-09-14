# API Integration Plan for Investment Bot

## Overview
This document outlines the plan to integrate real-time and historical market data from two sources:
1. Alpha Vantage API
2. Interactive Brokers Web API

The goal is to create a dual-source data fetching system that can compare data from both sources and select the most accurate and up-to-date information.

## Current System Analysis
The investment bot currently attempts to fetch data from:
- YFinance (primary source)
- Mock data (fallback)
- Manual data configuration (recently added)

Issues:
- YFinance data is often inaccurate or unavailable
- Mock data doesn't reflect real market conditions
- Manual configuration requires constant updates

## Integration Goals
1. Implement Alpha Vantage API integration with proper rate limiting
2. Implement Interactive Brokers Web API integration
3. Create a comparison mechanism to select the most accurate data
4. Provide a fallback strategy when one source is unavailable
5. Cache data efficiently to avoid redundant API calls

## Detailed Implementation Plan

### Phase 1: Alpha Vantage API Integration

1. Create `AlphaVantageClient` class:
   - API key configuration (using the provided key: 4D88F5GR4MGIG3MQ)
   - Rate limiting (5 calls per minute on free tier)
   - Error handling and retry logic
   - Caching mechanism

2. Implement core Alpha Vantage endpoints:
   - Real-time quotes (`GLOBAL_QUOTE`)
   - Intraday data (`TIME_SERIES_INTRADAY`)
   - Historical data (`TIME_SERIES_DAILY`, `TIME_SERIES_WEEKLY`)
   - Company fundamentals (`OVERVIEW`)
   - News sentiment (`NEWS_SENTIMENT`)

3. Data mapping functions:
   - Convert Alpha Vantage response format to investment bot's internal format

### Phase 2: Interactive Brokers Web API Integration

1. Create `IBDataClient` class:
   - Authentication management
   - Session handling
   - Error recovery

2. Implement core IB API endpoints:
   - Market data snapshots
   - Historical data retrieval
   - Contract details and fundamentals

3. Data mapping functions:
   - Convert IB response format to investment bot's internal format

### Phase 3: Comparison and Selection Mechanism

1. Create `DataComparisonService` class:
   - Compare timestamps of data from both sources
   - Check price differentials between sources
   - Apply validation rules to select most reliable data
   - Weight factors: recency, comprehensiveness, source reliability

2. Implementation options:
   - Sequential fetching (try primary, fall back to secondary)
   - Parallel fetching (fetch both simultaneously, compare and select)
   - Hybrid approach (parallel for critical data, sequential for others)

3. Selection criteria:
   - For real-time quotes: prefer source with most recent timestamp
   - For historical data: select source with most complete dataset
   - For fundamentals: prioritize based on freshness of data

### Phase 4: Caching and Persistence

1. Enhanced caching system:
   - Multi-level cache (memory and disk)
   - TTL-based expiration for different data types
   - Source tracking in cache

2. Cache invalidation rules:
   - Different expiration times for different data types:
     - Real-time quotes: 1 minute
     - Daily data: 6 hours
     - Historical data: 24 hours
     - Fundamentals: 1 week

3. Persistence layer:
   - Store successful API responses locally
   - Create reconciliation process for data conflicts

### Phase 5: Integration with Existing System

1. Updates to `EnhancedStockAnalyzer`:
   - Add new data sources to the fetch pipeline
   - Use DataComparisonService to select data
   - Prioritize real-time sources over cached/mock data

2. Modify analysis pipelines:
   - Update functions to handle the new data formats
   - Ensure backward compatibility

3. UI/UX enhancements:
   - Add data source indicator in UI
   - Show data freshness information
   - Display when comparison detected discrepancies

## Implementation Timeline

1. **Week 1: Base Implementation**
   - Set up Alpha Vantage client (1-2 days)
   - Implement core AV endpoints (2-3 days)
   - Unit tests (1 day)

2. **Week 2: IB Integration**
   - Set up IB client authentication (1-2 days)
   - Implement core IB endpoints (2-3 days)
   - Unit tests (1 day)

3. **Week 3: Comparison and Integration**
   - Build comparison service (2 days)
   - Integrate with existing system (2 days)
   - Caching enhancements (1 day)

4. **Week 4: Testing and Refinement**
   - End-to-end testing (2 days)
   - Performance optimization (1 day)
   - Documentation (1 day)
   - Final adjustments (1 day)

## Required Changes

### New Files to Create:
1. `data/alpha_vantage_client.py`
2. `data/ib_data_client.py`
3. `data/data_comparison_service.py`
4. `data/enhanced_caching.py`
5. `tests/test_alpha_vantage.py`
6. `tests/test_ib_data.py`
7. `tests/test_data_comparison.py`

### Files to Modify:
1. `analysis/enhanced_stock_analyzer.py`
2. `config.py` (for API configuration)
3. `app.py` (to update data fetching logic)
4. `templates/analysis.html` (to show data source)

## Risk Assessment and Mitigation

### Risks:
1. Alpha Vantage rate limits (5 calls/min on free tier)
2. IB API availability and potential authentication issues
3. Data inconsistencies between sources
4. Performance impact of using multiple sources

### Mitigation Strategies:
1. Implement aggressive caching for Alpha Vantage
2. Create fallback mechanisms for all API calls
3. Develop clear conflict resolution rules
4. Optimize request scheduling and batching
5. Consider premium Alpha Vantage tier if volume requires
6. Use background processing for non-critical data updates

## Next Steps After Approval

1. Implement Alpha Vantage client first (highest priority)
2. Set up tests to validate data quality
3. Add IB integration once Alpha Vantage is stable
4. Build comparison logic iteratively
5. Continuously monitor data quality and API reliability

## Success Criteria
1. Real-time data accuracy within 1% of actual market prices
2. 99% API call success rate (accounting for rate limits)
3. Response time under 500ms for cached data, under 2s for fresh data
4. Smooth fallback when primary source is unavailable
5. Clear source attribution in UI for transparency