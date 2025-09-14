# Examples

This directory contains example usage patterns for the Investment Bot codebase.

## Available Examples

### 1. Parallel Data Fetching

**File**: `parallel_data_fetching_example.py`

Demonstrates how to fetch data from multiple sources in parallel and reconcile the results using the DataComparisonService. This example shows:

- How to create factory functions for different data sources
- How to use the fetch_multi_source_data method
- How to handle the reconciled results

**Usage**:
```bash
python parallel_data_fetching_example.py
```

**Key Performance Benefits**:
- Reduces overall latency by fetching from all sources simultaneously
- Automatically selects the most accurate data
- Provides detailed reconciliation information

## Best Practices

When working with multiple data sources:

1. **Always provide fallbacks**: Define multiple data sources with appropriate factory functions
2. **Handle failures gracefully**: Each factory function should handle its own exceptions
3. **Use thread-safe data collection**: When aggregating results from multiple threads
4. **Measure performance**: Log timing information to track performance gains
5. **Validate results**: Check that returned data is complete and valid

## Implementation Guidelines

When implementing parallel data fetching:

1. Use ThreadPoolExecutor for I/O-bound operations (API calls)
2. Use ProcessPoolExecutor for CPU-bound operations (complex calculations)
3. Implement proper thread synchronization with locks
4. Set appropriate timeouts for external API calls
5. Use the factory pattern to initialize clients lazily