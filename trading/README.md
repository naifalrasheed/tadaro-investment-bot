# Trading Integration Module

This module provides a unified interface for connecting the Investment Bot with various broker APIs to enable trading capabilities.

## Overview

The trading module abstracts away the differences between broker APIs, providing a consistent interface for:

- Order placement (market, limit, stop, stop-limit)
- Order cancellation and modification
- Portfolio position tracking
- Account information retrieval
- Quote data access

## Supported Brokers

- **Alpaca** (paper trading and live trading)
- **Paper Trading** (simulated, no real broker)
- **Interactive Brokers** (planned)

## Components

### Core Classes

- `BaseBroker` - Abstract base class that defines the interface for all broker implementations
- `Order` - Standardized order representation
- `Position` - Standardized position representation
- `BrokerFactory` - Factory for creating broker instances

### Implementation Classes

- `AlpacaBroker` - Alpaca API implementation
- `PaperTradingBroker` - Simulated trading implementation
- `InteractiveBrokersBroker` - Interactive Brokers implementation (planned)

## Usage Example

```python
from trading.broker_integration import BrokerFactory, OrderSide, OrderType

# Create a broker instance (paper trading)
broker = BrokerFactory.create_broker(
    broker_type="paper",
    credentials={},
    is_sandbox=True
)

# Authenticate
broker.authenticate()

# Place a market order
order = broker.market_buy(symbol="AAPL", quantity=10)
print(f"Order placed: {order.id}, Status: {order.status}")

# Check positions
positions = broker.get_positions()
for position in positions:
    print(f"{position.symbol}: {position.quantity} shares @ ${position.entry_price}")

# Get account info
account = broker.get_account_info()
print(f"Cash: ${account['cash']}, Portfolio Value: ${account['portfolio_value']}")
```

## Chatbot Integration

This module enables the Claude chatbot to execute trades based on natural language commands. Example commands:

- "Buy 10 shares of AAPL at market"
- "Sell 5 shares of MSFT at limit $350"
- "Show my current positions"
- "Cancel order 12345"

The trading module parses these commands into the appropriate broker API calls and provides confirmations and status updates back to the user.

## Security Considerations

- All trading activity requires user authentication
- Confirmation dialogs are shown for all trading operations
- Trading limits can be set to prevent large/unexpected trades
- All trading activity is logged for audit purposes

## Development Status

This is a preliminary implementation for architecture purposes. Additional work will be needed to fully implement all broker APIs and ensure robust error handling.

## Testing

To run the paper trading broker tests:

```bash
python -m unittest tests.test_paper_trading
```