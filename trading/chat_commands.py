"""
Chat command processor for trading-related functionality.

This module provides the interface between natural language commands in the chatbot
and the broker integration module. It parses commands, validates them, and converts
them into the appropriate broker API calls.
"""

import re
import logging
from typing import Dict, List, Any, Optional, Union, Tuple, Callable
from datetime import datetime

from .broker_integration import (
    BrokerFactory, BaseBroker, Order, OrderSide, OrderType, TimeInForce,
    BrokerException, AuthenticationError, OrderError, PositionError
)

logger = logging.getLogger(__name__)

class TradingCommandProcessor:
    """
    Process trading-related commands from chat and execute them through the broker API.
    
    This class handles the parsing, validation, and execution of trading commands
    received from the chatbot, while enforcing security and safety checks.
    """
    
    # Command patterns for trading actions
    COMMAND_PATTERNS = {
        # Buy commands
        'buy_market': re.compile(r'buy\s+(\d+)\s+(?:shares?\s+)?(?:of\s+)?([A-Za-z]+)(?:\s+at\s+market)?', re.IGNORECASE),
        'buy_limit': re.compile(r'buy\s+(\d+)\s+(?:shares?\s+)?(?:of\s+)?([A-Za-z]+)\s+(?:at|for|limit|price)\s+\$?(\d+\.?\d*)', re.IGNORECASE),
        'buy_stop': re.compile(r'buy\s+(\d+)\s+(?:shares?\s+)?(?:of\s+)?([A-Za-z]+)\s+(?:with\s+)?stop\s+\$?(\d+\.?\d*)', re.IGNORECASE),
        'buy_stop_limit': re.compile(r'buy\s+(\d+)\s+(?:shares?\s+)?(?:of\s+)?([A-Za-z]+)\s+(?:with\s+)?stop\s+\$?(\d+\.?\d*)\s+limit\s+\$?(\d+\.?\d*)', re.IGNORECASE),
        
        # Sell commands
        'sell_market': re.compile(r'sell\s+(\d+)\s+(?:shares?\s+)?(?:of\s+)?([A-Za-z]+)(?:\s+at\s+market)?', re.IGNORECASE),
        'sell_limit': re.compile(r'sell\s+(\d+)\s+(?:shares?\s+)?(?:of\s+)?([A-Za-z]+)\s+(?:at|for|limit|price)\s+\$?(\d+\.?\d*)', re.IGNORECASE),
        'sell_stop': re.compile(r'sell\s+(\d+)\s+(?:shares?\s+)?(?:of\s+)?([A-Za-z]+)\s+(?:with\s+)?stop\s+\$?(\d+\.?\d*)', re.IGNORECASE),
        'sell_stop_limit': re.compile(r'sell\s+(\d+)\s+(?:shares?\s+)?(?:of\s+)?([A-Za-z]+)\s+(?:with\s+)?stop\s+\$?(\d+\.?\d*)\s+limit\s+\$?(\d+\.?\d*)', re.IGNORECASE),
        
        # Position and order commands
        'show_positions': re.compile(r'(?:show|list|get|display|view)\s+(?:my\s+)?(?:current\s+)?(?:all\s+)?positions', re.IGNORECASE),
        'show_position': re.compile(r'(?:show|get|display|view)\s+(?:my\s+)?(?:position|holding)\s+(?:for|in|of)\s+([A-Za-z]+)', re.IGNORECASE),
        'show_orders': re.compile(r'(?:show|list|get|display|view)\s+(?:my\s+)?(?:current\s+)?(?:all\s+)?orders', re.IGNORECASE),
        'show_order': re.compile(r'(?:show|get|display|view)\s+(?:my\s+)?order\s+([A-Za-z0-9]+)', re.IGNORECASE),
        'cancel_order': re.compile(r'cancel\s+(?:my\s+)?order\s+([A-Za-z0-9]+)', re.IGNORECASE),
        
        # Account commands
        'show_account': re.compile(r'(?:show|get|display|view)\s+(?:my\s+)?account', re.IGNORECASE),
        'show_balance': re.compile(r'(?:show|get|display|view)\s+(?:my\s+)?(?:cash\s+)?balance', re.IGNORECASE),
        'show_buying_power': re.compile(r'(?:show|get|display|view)\s+(?:my\s+)?buying\s+power', re.IGNORECASE),
        
        # Quote commands
        'get_quote': re.compile(r'(?:get|show|display|view)\s+(?:the\s+)?(?:current\s+)?(?:quote|price)\s+(?:for|of)\s+([A-Za-z]+)', re.IGNORECASE),
    }
    
    def __init__(self, broker: BaseBroker, max_order_value: float = 50000.0):
        """
        Initialize the trading command processor
        
        Args:
            broker: The broker instance to use for executing commands
            max_order_value: Maximum value for any single order (safety limit)
        """
        self.broker = broker
        self.max_order_value = max_order_value
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Map command patterns to handler methods
        self.command_handlers = {
            'buy_market': self._handle_buy_market,
            'buy_limit': self._handle_buy_limit,
            'buy_stop': self._handle_buy_stop,
            'buy_stop_limit': self._handle_buy_stop_limit,
            'sell_market': self._handle_sell_market,
            'sell_limit': self._handle_sell_limit,
            'sell_stop': self._handle_sell_stop,
            'sell_stop_limit': self._handle_sell_stop_limit,
            'show_positions': self._handle_show_positions,
            'show_position': self._handle_show_position,
            'show_orders': self._handle_show_orders,
            'show_order': self._handle_show_order,
            'cancel_order': self._handle_cancel_order,
            'show_account': self._handle_show_account,
            'show_balance': self._handle_show_balance,
            'show_buying_power': self._handle_show_buying_power,
            'get_quote': self._handle_get_quote,
        }
    
    def process_command(self, command: str, user_id: str) -> Dict:
        """
        Process a trading command from the chat interface
        
        Args:
            command: The command text from the user
            user_id: User ID for authentication and tracking
            
        Returns:
            Dict with response information and status
        """
        self.logger.info(f"Processing trading command from user {user_id}: {command}")
        
        try:
            # First, authenticate with the broker if needed
            if not self.broker.authenticated:
                self.broker.authenticate()
            
            # Try to match command against known patterns
            for cmd_type, pattern in self.COMMAND_PATTERNS.items():
                match = pattern.match(command)
                if match:
                    handler = self.command_handlers.get(cmd_type)
                    if handler:
                        return handler(match, user_id)
            
            # No matching command found
            return {
                'status': 'error',
                'message': "I couldn't understand that trading command. Try something like 'buy 10 AAPL at market' or 'show my positions'.",
                'type': 'unknown_command'
            }
            
        except AuthenticationError as e:
            return {
                'status': 'error',
                'message': f"Authentication failed: {str(e)}",
                'type': 'auth_error'
            }
        except OrderError as e:
            return {
                'status': 'error',
                'message': f"Order error: {str(e)}",
                'type': 'order_error'
            }
        except PositionError as e:
            return {
                'status': 'error',
                'message': f"Position error: {str(e)}",
                'type': 'position_error'
            }
        except BrokerException as e:
            return {
                'status': 'error',
                'message': f"Broker error: {str(e)}",
                'type': 'broker_error'
            }
        except Exception as e:
            self.logger.error(f"Unexpected error processing command: {str(e)}")
            return {
                'status': 'error',
                'message': f"An unexpected error occurred: {str(e)}",
                'type': 'unexpected_error'
            }
    
    def _validate_order_size(self, symbol: str, quantity: float, est_price: float) -> bool:
        """
        Validate that order size is within allowed limits
        
        Args:
            symbol: Stock symbol
            quantity: Number of shares
            est_price: Estimated price per share
            
        Returns:
            True if valid, False otherwise
        """
        est_order_value = quantity * est_price
        
        # Check against maximum order value
        if est_order_value > self.max_order_value:
            return False
            
        return True
    
    def _get_estimated_price(self, symbol: str) -> float:
        """
        Get an estimated current price for a symbol
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Estimated price per share
        """
        try:
            quote = self.broker.get_quote(symbol)
            return quote.get('ask_price', 0)
        except Exception:
            # If we can't get a quote, use a conservative estimate
            position = self.broker.get_position(symbol)
            if position:
                return position.current_price
            else:
                # If all else fails, use a default high value for safety
                return 1000.0  # Conservative high price estimate
    
    def _handle_buy_market(self, match: re.Match, user_id: str) -> Dict:
        """Handle market buy order command"""
        quantity = int(match.group(1))
        symbol = match.group(2).upper()
        
        # Get estimated price for validation
        est_price = self._get_estimated_price(symbol)
        
        # Validate order size
        if not self._validate_order_size(symbol, quantity, est_price):
            return {
                'status': 'error',
                'message': f"Order value exceeds maximum limit of ${self.max_order_value:,.2f}",
                'type': 'validation_error'
            }
        
        # Execute the order
        order = self.broker.market_buy(symbol, quantity)
        
        # Create response
        if order.status == "filled":
            return {
                'status': 'success',
                'message': f"Successfully bought {quantity} shares of {symbol} at ${order.filled_price:.2f} per share (total: ${order.filled_price * quantity:.2f})",
                'type': 'market_buy',
                'data': {
                    'order': order.to_dict(),
                    'symbol': symbol,
                    'quantity': quantity,
                    'total_value': order.filled_price * quantity
                }
            }
        else:
            return {
                'status': 'success',
                'message': f"Market buy order for {quantity} shares of {symbol} placed successfully. Order ID: {order.id}",
                'type': 'market_buy',
                'data': {
                    'order': order.to_dict(),
                    'symbol': symbol,
                    'quantity': quantity
                }
            }
    
    def _handle_sell_market(self, match: re.Match, user_id: str) -> Dict:
        """Handle market sell order command"""
        quantity = int(match.group(1))
        symbol = match.group(2).upper()
        
        # Check if user has the position
        position = self.broker.get_position(symbol)
        if not position:
            return {
                'status': 'error',
                'message': f"You don't have a position in {symbol} to sell.",
                'type': 'validation_error'
            }
        
        # Check if user has enough shares
        if position.quantity < quantity:
            return {
                'status': 'error',
                'message': f"You only have {position.quantity} shares of {symbol}, but tried to sell {quantity}.",
                'type': 'validation_error'
            }
        
        # Execute the order
        order = self.broker.market_sell(symbol, quantity)
        
        # Create response
        if order.status == "filled":
            return {
                'status': 'success',
                'message': f"Successfully sold {quantity} shares of {symbol} at ${order.filled_price:.2f} per share (total: ${order.filled_price * quantity:.2f})",
                'type': 'market_sell',
                'data': {
                    'order': order.to_dict(),
                    'symbol': symbol,
                    'quantity': quantity,
                    'total_value': order.filled_price * quantity
                }
            }
        else:
            return {
                'status': 'success',
                'message': f"Market sell order for {quantity} shares of {symbol} placed successfully. Order ID: {order.id}",
                'type': 'market_sell',
                'data': {
                    'order': order.to_dict(),
                    'symbol': symbol,
                    'quantity': quantity
                }
            }
    
    def _handle_buy_limit(self, match: re.Match, user_id: str) -> Dict:
        """Handle limit buy order command"""
        quantity = int(match.group(1))
        symbol = match.group(2).upper()
        price = float(match.group(3))
        
        # Validate order size
        if not self._validate_order_size(symbol, quantity, price):
            return {
                'status': 'error',
                'message': f"Order value exceeds maximum limit of ${self.max_order_value:,.2f}",
                'type': 'validation_error'
            }
        
        # Execute the order
        order = self.broker.limit_buy(symbol, quantity, price)
        
        # Create response
        return {
            'status': 'success',
            'message': f"Limit buy order for {quantity} shares of {symbol} at ${price:.2f} placed successfully. Order ID: {order.id}",
            'type': 'limit_buy',
            'data': {
                'order': order.to_dict(),
                'symbol': symbol,
                'quantity': quantity,
                'price': price,
                'estimated_value': price * quantity
            }
        }
    
    def _handle_sell_limit(self, match: re.Match, user_id: str) -> Dict:
        """Handle limit sell order command"""
        quantity = int(match.group(1))
        symbol = match.group(2).upper()
        price = float(match.group(3))
        
        # Check if user has the position
        position = self.broker.get_position(symbol)
        if not position:
            return {
                'status': 'error',
                'message': f"You don't have a position in {symbol} to sell.",
                'type': 'validation_error'
            }
        
        # Check if user has enough shares
        if position.quantity < quantity:
            return {
                'status': 'error',
                'message': f"You only have {position.quantity} shares of {symbol}, but tried to sell {quantity}.",
                'type': 'validation_error'
            }
        
        # Execute the order
        order = self.broker.limit_sell(symbol, quantity, price)
        
        # Create response
        return {
            'status': 'success',
            'message': f"Limit sell order for {quantity} shares of {symbol} at ${price:.2f} placed successfully. Order ID: {order.id}",
            'type': 'limit_sell',
            'data': {
                'order': order.to_dict(),
                'symbol': symbol,
                'quantity': quantity,
                'price': price,
                'estimated_value': price * quantity
            }
        }
    
    def _handle_buy_stop(self, match: re.Match, user_id: str) -> Dict:
        """Handle stop buy order command"""
        quantity = int(match.group(1))
        symbol = match.group(2).upper()
        stop_price = float(match.group(3))
        
        # Validate order size
        if not self._validate_order_size(symbol, quantity, stop_price):
            return {
                'status': 'error',
                'message': f"Order value exceeds maximum limit of ${self.max_order_value:,.2f}",
                'type': 'validation_error'
            }
        
        # Create order
        order = Order(
            symbol=symbol,
            quantity=quantity,
            side=OrderSide.BUY,
            order_type=OrderType.STOP,
            stop_price=stop_price,
            time_in_force=TimeInForce.DAY
        )
        
        # Execute the order
        executed_order = self.broker.place_order(order)
        
        # Create response
        return {
            'status': 'success',
            'message': f"Stop buy order for {quantity} shares of {symbol} at ${stop_price:.2f} stop price placed successfully. Order ID: {executed_order.id}",
            'type': 'stop_buy',
            'data': {
                'order': executed_order.to_dict(),
                'symbol': symbol,
                'quantity': quantity,
                'stop_price': stop_price,
                'estimated_value': stop_price * quantity
            }
        }
    
    def _handle_sell_stop(self, match: re.Match, user_id: str) -> Dict:
        """Handle stop sell order command"""
        quantity = int(match.group(1))
        symbol = match.group(2).upper()
        stop_price = float(match.group(3))
        
        # Check if user has the position
        position = self.broker.get_position(symbol)
        if not position:
            return {
                'status': 'error',
                'message': f"You don't have a position in {symbol} to sell.",
                'type': 'validation_error'
            }
        
        # Check if user has enough shares
        if position.quantity < quantity:
            return {
                'status': 'error',
                'message': f"You only have {position.quantity} shares of {symbol}, but tried to sell {quantity}.",
                'type': 'validation_error'
            }
        
        # Create order
        order = Order(
            symbol=symbol,
            quantity=quantity,
            side=OrderSide.SELL,
            order_type=OrderType.STOP,
            stop_price=stop_price,
            time_in_force=TimeInForce.DAY
        )
        
        # Execute the order
        executed_order = self.broker.place_order(order)
        
        # Create response
        return {
            'status': 'success',
            'message': f"Stop sell order for {quantity} shares of {symbol} at ${stop_price:.2f} stop price placed successfully. Order ID: {executed_order.id}",
            'type': 'stop_sell',
            'data': {
                'order': executed_order.to_dict(),
                'symbol': symbol,
                'quantity': quantity,
                'stop_price': stop_price,
                'estimated_value': stop_price * quantity
            }
        }
    
    def _handle_buy_stop_limit(self, match: re.Match, user_id: str) -> Dict:
        """Handle stop-limit buy order command"""
        quantity = int(match.group(1))
        symbol = match.group(2).upper()
        stop_price = float(match.group(3))
        limit_price = float(match.group(4))
        
        # Validate order size
        if not self._validate_order_size(symbol, quantity, limit_price):
            return {
                'status': 'error',
                'message': f"Order value exceeds maximum limit of ${self.max_order_value:,.2f}",
                'type': 'validation_error'
            }
        
        # Create order
        order = Order(
            symbol=symbol,
            quantity=quantity,
            side=OrderSide.BUY,
            order_type=OrderType.STOP_LIMIT,
            stop_price=stop_price,
            price=limit_price,
            time_in_force=TimeInForce.DAY
        )
        
        # Execute the order
        executed_order = self.broker.place_order(order)
        
        # Create response
        return {
            'status': 'success',
            'message': f"Stop-limit buy order for {quantity} shares of {symbol} at ${limit_price:.2f} with stop price ${stop_price:.2f} placed successfully. Order ID: {executed_order.id}",
            'type': 'stop_limit_buy',
            'data': {
                'order': executed_order.to_dict(),
                'symbol': symbol,
                'quantity': quantity,
                'stop_price': stop_price,
                'limit_price': limit_price,
                'estimated_value': limit_price * quantity
            }
        }
    
    def _handle_sell_stop_limit(self, match: re.Match, user_id: str) -> Dict:
        """Handle stop-limit sell order command"""
        quantity = int(match.group(1))
        symbol = match.group(2).upper()
        stop_price = float(match.group(3))
        limit_price = float(match.group(4))
        
        # Check if user has the position
        position = self.broker.get_position(symbol)
        if not position:
            return {
                'status': 'error',
                'message': f"You don't have a position in {symbol} to sell.",
                'type': 'validation_error'
            }
        
        # Check if user has enough shares
        if position.quantity < quantity:
            return {
                'status': 'error',
                'message': f"You only have {position.quantity} shares of {symbol}, but tried to sell {quantity}.",
                'type': 'validation_error'
            }
        
        # Create order
        order = Order(
            symbol=symbol,
            quantity=quantity,
            side=OrderSide.SELL,
            order_type=OrderType.STOP_LIMIT,
            stop_price=stop_price,
            price=limit_price,
            time_in_force=TimeInForce.DAY
        )
        
        # Execute the order
        executed_order = self.broker.place_order(order)
        
        # Create response
        return {
            'status': 'success',
            'message': f"Stop-limit sell order for {quantity} shares of {symbol} at ${limit_price:.2f} with stop price ${stop_price:.2f} placed successfully. Order ID: {executed_order.id}",
            'type': 'stop_limit_sell',
            'data': {
                'order': executed_order.to_dict(),
                'symbol': symbol,
                'quantity': quantity,
                'stop_price': stop_price,
                'limit_price': limit_price,
                'estimated_value': limit_price * quantity
            }
        }
    
    def _handle_show_positions(self, match: re.Match, user_id: str) -> Dict:
        """Handle show positions command"""
        positions = self.broker.get_positions()
        
        if not positions:
            return {
                'status': 'success',
                'message': "You don't have any open positions.",
                'type': 'show_positions',
                'data': {
                    'positions': []
                }
            }
        
        # Calculate total portfolio value
        total_value = sum(pos.market_value for pos in positions)
        
        # Calculate total profit/loss
        total_pl = sum(pos.unrealized_pl for pos in positions)
        total_pl_percent = (total_pl / (total_value - total_pl)) * 100 if (total_value - total_pl) > 0 else 0
        
        # Format positions for display
        formatted_positions = []
        for pos in positions:
            formatted_positions.append({
                'symbol': pos.symbol,
                'quantity': pos.quantity,
                'entry_price': pos.entry_price,
                'current_price': pos.current_price,
                'market_value': pos.market_value,
                'unrealized_pl': pos.unrealized_pl,
                'unrealized_pl_percent': pos.unrealized_pl_percent,
                'weight': pos.market_value / total_value if total_value > 0 else 0
            })
        
        # Sort by market value (descending)
        formatted_positions.sort(key=lambda p: p['market_value'], reverse=True)
        
        # Build message
        message = f"You have {len(positions)} positions with a total value of ${total_value:,.2f}:\n\n"
        
        for pos in formatted_positions:
            pl_sign = "+" if pos['unrealized_pl'] >= 0 else ""
            message += (f"{pos['symbol']}: {pos['quantity']} shares @ ${pos['entry_price']:.2f}, "
                       f"now ${pos['current_price']:.2f} (${pos['market_value']:,.2f}) - "
                       f"P/L: {pl_sign}${pos['unrealized_pl']:,.2f} ({pl_sign}{pos['unrealized_pl_percent']:.2f}%)\n")
        
        # Add total P/L
        pl_sign = "+" if total_pl >= 0 else ""
        message += f"\nTotal Profit/Loss: {pl_sign}${total_pl:,.2f} ({pl_sign}{total_pl_percent:.2f}%)"
        
        return {
            'status': 'success',
            'message': message,
            'type': 'show_positions',
            'data': {
                'positions': [p.to_dict() for p in positions],
                'total_value': total_value,
                'total_pl': total_pl,
                'total_pl_percent': total_pl_percent
            }
        }
    
    def _handle_show_position(self, match: re.Match, user_id: str) -> Dict:
        """Handle show specific position command"""
        symbol = match.group(1).upper()
        position = self.broker.get_position(symbol)
        
        if not position:
            return {
                'status': 'success',
                'message': f"You don't have a position in {symbol}.",
                'type': 'show_position',
                'data': {
                    'symbol': symbol,
                    'position': None
                }
            }
        
        # Get latest quote for more detailed data
        quote = self.broker.get_quote(symbol)
        
        # Calculate profit/loss
        pl_sign = "+" if position.unrealized_pl >= 0 else ""
        
        # Format message
        message = (f"Position in {position.symbol}:\n"
                  f"Quantity: {position.quantity} shares\n"
                  f"Entry Price: ${position.entry_price:.2f}\n"
                  f"Current Price: ${position.current_price:.2f}\n"
                  f"Market Value: ${position.market_value:,.2f}\n"
                  f"Profit/Loss: {pl_sign}${position.unrealized_pl:,.2f} ({pl_sign}{position.unrealized_pl_percent:.2f}%)\n"
                  f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return {
            'status': 'success',
            'message': message,
            'type': 'show_position',
            'data': {
                'symbol': symbol,
                'position': position.to_dict(),
                'quote': quote
            }
        }
    
    def _handle_show_orders(self, match: re.Match, user_id: str) -> Dict:
        """Handle show orders command"""
        # Get active orders (open or partially filled)
        active_orders = self.broker.get_orders(status="open")
        
        if not active_orders:
            return {
                'status': 'success',
                'message': "You don't have any open orders.",
                'type': 'show_orders',
                'data': {
                    'orders': []
                }
            }
        
        # Build message
        message = f"You have {len(active_orders)} open orders:\n\n"
        
        for order in active_orders:
            # Format order details
            side = "Buy" if order.side == OrderSide.BUY else "Sell"
            order_type = order.order_type.value.capitalize()
            
            message += f"Order ID: {order.id}\n"
            message += f"{side} {order.quantity} {order.symbol} ({order_type})\n"
            
            if order.order_type in [OrderType.LIMIT, OrderType.STOP_LIMIT]:
                message += f"Limit Price: ${order.price:.2f}\n"
                
            if order.order_type in [OrderType.STOP, OrderType.STOP_LIMIT]:
                message += f"Stop Price: ${order.stop_price:.2f}\n"
                
            message += f"Status: {order.status.capitalize()}\n"
            
            if order.filled_quantity > 0:
                message += f"Filled: {order.filled_quantity} / {order.quantity} @ ${order.filled_price:.2f}\n"
                
            message += f"Created: {order.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        return {
            'status': 'success',
            'message': message,
            'type': 'show_orders',
            'data': {
                'orders': [o.to_dict() for o in active_orders]
            }
        }
    
    def _handle_show_order(self, match: re.Match, user_id: str) -> Dict:
        """Handle show specific order command"""
        order_id = match.group(1)
        
        try:
            order = self.broker.get_order(order_id)
            
            # Format order details
            side = "Buy" if order.side == OrderSide.BUY else "Sell"
            order_type = order.order_type.value.capitalize()
            
            message = f"Order ID: {order.id}\n"
            message += f"{side} {order.quantity} {order.symbol} ({order_type})\n"
            
            if order.order_type in [OrderType.LIMIT, OrderType.STOP_LIMIT]:
                message += f"Limit Price: ${order.price:.2f}\n"
                
            if order.order_type in [OrderType.STOP, OrderType.STOP_LIMIT]:
                message += f"Stop Price: ${order.stop_price:.2f}\n"
                
            message += f"Status: {order.status.capitalize()}\n"
            
            if order.filled_quantity > 0:
                message += f"Filled: {order.filled_quantity} / {order.quantity} @ ${order.filled_price:.2f}\n"
                
            message += f"Created: {order.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
            message += f"Updated: {order.updated_at.strftime('%Y-%m-%d %H:%M:%S')}"
            
            return {
                'status': 'success',
                'message': message,
                'type': 'show_order',
                'data': {
                    'order': order.to_dict()
                }
            }
            
        except OrderError:
            return {
                'status': 'error',
                'message': f"Order {order_id} not found.",
                'type': 'order_not_found',
                'data': {
                    'order_id': order_id
                }
            }
    
    def _handle_cancel_order(self, match: re.Match, user_id: str) -> Dict:
        """Handle cancel order command"""
        order_id = match.group(1)
        
        # Check if order exists
        try:
            order = self.broker.get_order(order_id)
            
            # Only open orders can be cancelled
            if order.status != "open":
                return {
                    'status': 'error',
                    'message': f"Order {order_id} cannot be cancelled because it is in {order.status} status.",
                    'type': 'invalid_order_status',
                    'data': {
                        'order_id': order_id,
                        'status': order.status
                    }
                }
            
            # Cancel the order
            success = self.broker.cancel_order(order_id)
            
            if success:
                return {
                    'status': 'success',
                    'message': f"Order {order_id} has been cancelled successfully.",
                    'type': 'cancel_order',
                    'data': {
                        'order_id': order_id
                    }
                }
            else:
                return {
                    'status': 'error',
                    'message': f"Failed to cancel order {order_id}. Please try again later.",
                    'type': 'cancel_failed',
                    'data': {
                        'order_id': order_id
                    }
                }
        
        except OrderError:
            return {
                'status': 'error',
                'message': f"Order {order_id} not found.",
                'type': 'order_not_found',
                'data': {
                    'order_id': order_id
                }
            }
    
    def _handle_show_account(self, match: re.Match, user_id: str) -> Dict:
        """Handle show account command"""
        account = self.broker.get_account_info()
        
        # Format message
        message = f"Account Summary:\n"
        message += f"Cash Balance: ${account.get('cash', 0):,.2f}\n"
        message += f"Portfolio Value: ${account.get('portfolio_value', 0):,.2f}\n"
        message += f"Buying Power: ${account.get('buying_power', 0):,.2f}\n"
        
        if 'equity' in account:
            message += f"Equity: ${account.get('equity', 0):,.2f}\n"
            
        if 'initial_margin' in account:
            message += f"Initial Margin: ${account.get('initial_margin', 0):,.2f}\n"
            message += f"Maintenance Margin: ${account.get('maintenance_margin', 0):,.2f}\n"
            
        if 'status' in account:
            message += f"Account Status: {account.get('status', '')}\n"
            
        if 'is_pattern_day_trader' in account:
            message += f"Pattern Day Trader: {'Yes' if account.get('is_pattern_day_trader') else 'No'}"
        
        return {
            'status': 'success',
            'message': message,
            'type': 'show_account',
            'data': {
                'account': account
            }
        }
    
    def _handle_show_balance(self, match: re.Match, user_id: str) -> Dict:
        """Handle show balance command"""
        account = self.broker.get_account_info()
        
        # Format message
        message = f"Cash Balance: ${account.get('cash', 0):,.2f}"
        
        return {
            'status': 'success',
            'message': message,
            'type': 'show_balance',
            'data': {
                'cash': account.get('cash', 0)
            }
        }
    
    def _handle_show_buying_power(self, match: re.Match, user_id: str) -> Dict:
        """Handle show buying power command"""
        account = self.broker.get_account_info()
        
        # Format message
        message = f"Buying Power: ${account.get('buying_power', 0):,.2f}"
        
        return {
            'status': 'success',
            'message': message,
            'type': 'show_buying_power',
            'data': {
                'buying_power': account.get('buying_power', 0)
            }
        }
    
    def _handle_get_quote(self, match: re.Match, user_id: str) -> Dict:
        """Handle get quote command"""
        symbol = match.group(1).upper()
        
        try:
            quote = self.broker.get_quote(symbol)
            
            # Format message
            message = f"Current Quote for {symbol}:\n"
            message += f"Ask: ${quote.get('ask_price', 0):,.2f} x {quote.get('ask_size', 0)}\n"
            message += f"Bid: ${quote.get('bid_price', 0):,.2f} x {quote.get('bid_size', 0)}\n"
            message += f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            return {
                'status': 'success',
                'message': message,
                'type': 'get_quote',
                'data': {
                    'symbol': symbol,
                    'quote': quote
                }
            }
        
        except BrokerException:
            return {
                'status': 'error',
                'message': f"Unable to get quote for {symbol}. Please check the symbol and try again.",
                'type': 'quote_error',
                'data': {
                    'symbol': symbol
                }
            }