"""
Data Source Priority Service - FIXED VERSION
Priority-based data source selection without averaging/mixing data

CRITICAL FIX: Removes all weighted averaging and data mixing
Uses single-source priority system for accurate financial data
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

class DataComparisonService:
    """
    Priority-based data source selection service

    Uses strict priority hierarchy:
    1. TwelveData (primary) - if valid data available
    2. Alpha Vantage (secondary) - if TwelveData fails
    3. YFinance (tertiary) - if both above fail

    NO DATA MIXING OR AVERAGING - Single source only
    """

    # Source priority order (higher number = higher priority)
    SOURCE_PRIORITY = {
        'twelvedata': 100,      # Primary source
        'alpha_vantage': 80,    # Secondary source
        'interactive_brokers': 75,  # Tertiary
        'yfinance': 60,         # Fourth choice
        'manual_data': 50,      # Manual overrides
        'mock_data': 10,        # Testing only
        'fallback': 1           # Last resort
    }

    def __init__(self):
        """Initialize the Data Source Priority Service"""
        self.logger = logging.getLogger(__name__)
        self.logger.info("Data Source Priority Service initialized - NO data mixing")

    def select_best_source(self, sources: List[Dict]) -> Dict:
        """
        Select the single best data source based on priority and data validity

        Args:
            sources: List of data dictionaries from different sources

        Returns:
            Single best data source (no mixing/averaging)
        """
        if not sources:
            self.logger.error("No data sources provided")
            return {'error': 'No data sources available', 'success': False}

        # Filter valid sources
        valid_sources = self._filter_valid_sources(sources)

        if not valid_sources:
            self.logger.error("No valid data sources found")
            return {'error': 'No valid data sources', 'success': False}

        # Select highest priority valid source
        best_source = self._select_highest_priority_source(valid_sources)

        # Add metadata about selection (but don't modify data)
        best_source = best_source.copy()  # Don't modify original
        best_source['data_selection'] = {
            'selected_source': best_source.get('data_source', 'unknown'),
            'available_sources': [s.get('data_source') for s in valid_sources],
            'selection_reason': 'highest_priority_valid_source',
            'selected_at': datetime.now().isoformat(),
            'no_data_mixing': True
        }

        self.logger.info(f"Selected data source: {best_source.get('data_source')} "
                        f"from {len(valid_sources)} available sources")

        return best_source

    def _filter_valid_sources(self, sources: List[Dict]) -> List[Dict]:
        """
        Filter sources to only include those with valid, usable data

        Args:
            sources: Raw data sources

        Returns:
            List of sources with valid data
        """
        valid_sources = []

        for source in sources:
            # Must have basic required fields
            if not source.get('symbol'):
                self.logger.debug(f"Skipping source without symbol: {source.get('data_source')}")
                continue

            # Must have valid price data
            current_price = source.get('current_price')
            if not current_price or current_price <= 0:
                self.logger.debug(f"Skipping source with invalid price: {source.get('data_source')}")
                continue

            # Must indicate success
            if source.get('success') is False:
                self.logger.debug(f"Skipping failed source: {source.get('data_source')}")
                continue

            # Check for errors
            if source.get('error'):
                self.logger.debug(f"Skipping source with error: {source.get('data_source')} - {source.get('error')}")
                continue

            # Add data source if missing
            if not source.get('data_source'):
                source['data_source'] = 'unknown'

            # Add timestamp if missing
            if not source.get('data_timestamp') and not source.get('timestamp'):
                source['data_timestamp'] = datetime.now().isoformat()

            valid_sources.append(source)
            self.logger.debug(f"Valid source found: {source.get('data_source')} for {source.get('symbol')}")

        self.logger.info(f"Found {len(valid_sources)} valid sources from {len(sources)} total")
        return valid_sources

    def _select_highest_priority_source(self, valid_sources: List[Dict]) -> Dict:
        """
        Select the source with the highest priority

        Args:
            valid_sources: Pre-filtered valid sources

        Returns:
            Highest priority source
        """
        if not valid_sources:
            raise ValueError("No valid sources to select from")

        # Sort by priority (highest first)
        prioritized_sources = []

        for source in valid_sources:
            data_source = source.get('data_source', 'unknown')
            priority = self.SOURCE_PRIORITY.get(data_source, 0)

            prioritized_sources.append((source, priority))
            self.logger.debug(f"Source {data_source} priority: {priority}")

        # Sort by priority (highest first)
        prioritized_sources.sort(key=lambda x: x[1], reverse=True)

        selected_source = prioritized_sources[0][0]
        selected_priority = prioritized_sources[0][1]

        self.logger.info(f"Selected highest priority source: {selected_source.get('data_source')} "
                        f"(priority: {selected_priority})")

        return selected_source

    def get_source_info(self, source: Dict) -> Dict:
        """
        Get information about a data source for display

        Args:
            source: Data source dictionary

        Returns:
            Source information for UI display
        """
        data_source = source.get('data_source', 'unknown')

        return {
            'source_name': data_source,
            'priority': self.SOURCE_PRIORITY.get(data_source, 0),
            'is_real_time': data_source in ['twelvedata', 'interactive_brokers'],
            'is_delayed': data_source in ['alpha_vantage', 'yfinance'],
            'data_timestamp': source.get('data_timestamp', source.get('timestamp')),
            'symbol': source.get('symbol'),
            'current_price': source.get('current_price'),
            'currency': source.get('currency', 'USD'),
            'exchange': source.get('exchange', ''),
            'last_updated': datetime.now().isoformat()
        }

    # Legacy method for compatibility - redirects to new method
    def compare_and_select(self, sources: List[Dict]) -> Dict:
        """
        Legacy method - redirects to select_best_source
        Maintains compatibility with existing code
        """
        self.logger.warning("Using legacy compare_and_select method - redirecting to priority-based selection")
        return self.select_best_source(sources)