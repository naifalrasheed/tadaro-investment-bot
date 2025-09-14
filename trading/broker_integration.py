"""
Broker Integration Module for Investment Bot

This module provides a unified abstract interface for connecting with various
broker APIs to enable trading capabilities. It implements a common interface
that handles authentication, order placement, position tracking, and status checks
regardless of the underlying broker.

Currently supported brokers:
- Alpaca (paper trading and live trading)
- Interactive Brokers (via Client Portal API)
- Paper Trading (simulated, no real broker)

IMPORTANT: This is a preliminary implementation for architecture purposes.
Implementation details for actual API integration will need to be added.
"""

import os
import time
import json
import logging
import requests
from typing import Dict, List, Any, Optional, Union, Tuple
from abc import ABC, abstractmethod
from enum import Enum
from datetime import datetime, timedelta

# Set up logging
logger = logging.getLogger(__name__)

class OrderType(Enum):
    """Enum representing supported order types across brokers"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"

class OrderSide(Enum):
    """Enum representing order sides (buy/sell)"""
    BUY = "buy"
    SELL = "sell"

class TimeInForce(Enum):
    """Enum representing time-in-force options"""
    DAY = "day"
    GTC = "gtc"  # Good Till Canceled
    IOC = "ioc"  # Immediate or Cancel
    FOK = "fok"  # Fill or Kill

class BrokerException(Exception):
    """Base exception for broker-related errors"""
    pass

class AuthenticationError(BrokerException):
    """Exception raised for authentication issues"""
    pass

class OrderError(BrokerException):
    """Exception raised for order placement errors"""
    pass

class PositionError(BrokerException):
    """Exception raised for position-related errors"""
    pass

class Order:
    """Class representing a standardized order across brokers"""
    
    def __init__(
        self,
        symbol: str,
        quantity: float,
        side: OrderSide,
        order_type: OrderType = OrderType.MARKET,
        price: Optional[float] = None,
        stop_price: Optional[float] = None,
        time_in_force: TimeInForce = TimeInForce.DAY,
        client_order_id: Optional[str] = None
    ):
        self.symbol = symbol.upper()
        self.quantity = quantity
        self.side = side
        self.order_type = order_type
        self.price = price
        self.stop_price = stop_price
        self.time_in_force = time_in_force
        self.client_order_id = client_order_id or f"inv_bot_{int(time.time())}"
        self.id = None  # Will be set after order is placed
        self.status = None
        self.filled_quantity = 0
        self.filled_price = None
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        
        # Validate order parameters
        self._validate()
    
    def _validate(self):
        """Validate order parameters"""
        if not self.symbol or len(self.symbol) < 1:
            raise ValueError("Symbol must be provided")
        
        if self.quantity <= 0:
            raise ValueError("Quantity must be greater than 0")
            
        if self.order_type in [OrderType.LIMIT, OrderType.STOP_LIMIT] and self.price is None:
            raise ValueError(f"Price must be provided for {self.order_type.value} orders")
            
        if self.order_type in [OrderType.STOP, OrderType.STOP_LIMIT] and self.stop_price is None:
            raise ValueError(f"Stop price must be provided for {self.order_type.value} orders")
    
    def to_dict(self) -> Dict:
        """Convert order to dictionary representation"""
        return {
            "symbol": self.symbol,
            "quantity": self.quantity,
            "side": self.side.value,
            "order_type": self.order_type.value,
            "price": self.price,
            "stop_price": self.stop_price,
            "time_in_force": self.time_in_force.value,
            "client_order_id": self.client_order_id,
            "id": self.id,
            "status": self.status,
            "filled_quantity": self.filled_quantity,
            "filled_price": self.filled_price,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Order':
        """Create order from dictionary representation"""
        order = cls(
            symbol=data["symbol"],
            quantity=data["quantity"],
            side=OrderSide(data["side"]),
            order_type=OrderType(data["order_type"]),
            price=data.get("price"),
            stop_price=data.get("stop_price"),
            time_in_force=TimeInForce(data["time_in_force"]),
            client_order_id=data.get("client_order_id")
        )
        
        order.id = data.get("id")
        order.status = data.get("status")
        order.filled_quantity = data.get("filled_quantity", 0)
        order.filled_price = data.get("filled_price")
        
        if "created_at" in data:
            order.created_at = datetime.fromisoformat(data["created_at"])
        if "updated_at" in data:
            order.updated_at = datetime.fromisoformat(data["updated_at"])
            
        return order

class Position:
    """Class representing a standardized position across brokers"""
    
    def __init__(
        self,
        symbol: str,
        quantity: float,
        entry_price: float,
        current_price: float,
        market_value: float,
        cost_basis: float,
        unrealized_pl: float,
        unrealized_pl_percent: float,
        broker: str
    ):
        self.symbol = symbol.upper()
        self.quantity = quantity
        self.entry_price = entry_price
        self.current_price = current_price
        self.market_value = market_value
        self.cost_basis = cost_basis
        self.unrealized_pl = unrealized_pl
        self.unrealized_pl_percent = unrealized_pl_percent
        self.broker = broker
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict:
        """Convert position to dictionary representation"""
        return {
            "symbol": self.symbol,
            "quantity": self.quantity,
            "entry_price": self.entry_price,
            "current_price": self.current_price,
            "market_value": self.market_value,
            "cost_basis": self.cost_basis,
            "unrealized_pl": self.unrealized_pl,
            "unrealized_pl_percent": self.unrealized_pl_percent,
            "broker": self.broker,
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Position':
        """Create position from dictionary representation"""
        position = cls(
            symbol=data["symbol"],
            quantity=data["quantity"],
            entry_price=data["entry_price"],
            current_price=data["current_price"],
            market_value=data["market_value"],
            cost_basis=data["cost_basis"],
            unrealized_pl=data["unrealized_pl"],
            unrealized_pl_percent=data["unrealized_pl_percent"],
            broker=data["broker"]
        )
        
        if "updated_at" in data:
            position.updated_at = datetime.fromisoformat(data["updated_at"])
            
        return position

class BaseBroker(ABC):
    """Abstract base class for broker implementations"""
    
    def __init__(self, credentials: Dict[str, str], is_sandbox: bool = True):
        self.credentials = credentials
        self.is_sandbox = is_sandbox
        self.authenticated = False
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
    @abstractmethod
    def authenticate(self) -> bool:
        """Authenticate with the broker API"""
        pass
    
    @abstractmethod
    def place_order(self, order: Order) -> Order:
        """Place an order with the broker"""
        pass
    
    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order"""
        pass
    
    @abstractmethod
    def get_order(self, order_id: str) -> Order:
        """Get order details"""
        pass
    
    @abstractmethod
    def get_orders(self, status: Optional[str] = None) -> List[Order]:
        """Get list of orders"""
        pass
    
    @abstractmethod
    def get_positions(self) -> List[Position]:
        """Get current positions"""
        pass
    
    @abstractmethod
    def get_position(self, symbol: str) -> Optional[Position]:
        """Get position for a specific symbol"""
        pass
    
    @abstractmethod
    def get_account_info(self) -> Dict:
        """Get account information"""
        pass
    
    @abstractmethod
    def get_quote(self, symbol: str) -> Dict:
        """Get current quote for a symbol"""
        pass
    
    def market_buy(self, symbol: str, quantity: float) -> Order:
        """Convenience method for market buy order"""
        order = Order(
            symbol=symbol,
            quantity=quantity,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            time_in_force=TimeInForce.DAY
        )
        return self.place_order(order)
    
    def market_sell(self, symbol: str, quantity: float) -> Order:
        """Convenience method for market sell order"""
        order = Order(
            symbol=symbol,
            quantity=quantity,
            side=OrderSide.SELL,
            order_type=OrderType.MARKET,
            time_in_force=TimeInForce.DAY
        )
        return self.place_order(order)
    
    def limit_buy(self, symbol: str, quantity: float, price: float) -> Order:
        """Convenience method for limit buy order"""
        order = Order(
            symbol=symbol,
            quantity=quantity,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=price,
            time_in_force=TimeInForce.DAY
        )
        return self.place_order(order)
    
    def limit_sell(self, symbol: str, quantity: float, price: float) -> Order:
        """Convenience method for limit sell order"""
        order = Order(
            symbol=symbol,
            quantity=quantity,
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            price=price,
            time_in_force=TimeInForce.DAY
        )
        return self.place_order(order)

class AlpacaBroker(BaseBroker):
    """Alpaca broker implementation"""
    
    def __init__(self, credentials: Dict[str, str], is_sandbox: bool = True):
        super().__init__(credentials, is_sandbox)
        
        # Set API URL based on sandbox mode
        if is_sandbox:
            self.base_url = "https://paper-api.alpaca.markets"
        else:
            self.base_url = "https://api.alpaca.markets"
        
        self.api_key = credentials.get("api_key")
        self.api_secret = credentials.get("api_secret")
        
        # Check credentials
        if not self.api_key or not self.api_secret:
            raise AuthenticationError("Alpaca API key and secret are required")
        
        # Headers for API requests
        self.headers = {
            "APCA-API-KEY-ID": self.api_key,
            "APCA-API-SECRET-KEY": self.api_secret,
            "Content-Type": "application/json"
        }
        
    def authenticate(self) -> bool:
        """Authenticate with Alpaca API"""
        try:
            response = requests.get(
                f"{self.base_url}/v2/account",
                headers=self.headers
            )
            
            if response.status_code == 200:
                self.authenticated = True
                self.logger.info("Successfully authenticated with Alpaca")
                return True
            else:
                self.logger.error(f"Failed to authenticate with Alpaca: {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error authenticating with Alpaca: {str(e)}")
            return False
    
    def place_order(self, order: Order) -> Order:
        """Place an order with Alpaca"""
        if not self.authenticated and not self.authenticate():
            raise AuthenticationError("Not authenticated with Alpaca")
        
        try:
            # Build order payload
            payload = {
                "symbol": order.symbol,
                "qty": str(order.quantity),
                "side": order.side.value,
                "type": order.order_type.value,
                "time_in_force": order.time_in_force.value,
                "client_order_id": order.client_order_id
            }
            
            # Add limit price if needed
            if order.order_type in [OrderType.LIMIT, OrderType.STOP_LIMIT] and order.price is not None:
                payload["limit_price"] = str(order.price)
                
            # Add stop price if needed
            if order.order_type in [OrderType.STOP, OrderType.STOP_LIMIT] and order.stop_price is not None:
                payload["stop_price"] = str(order.stop_price)
            
            # Send order to Alpaca
            response = requests.post(
                f"{self.base_url}/v2/orders",
                headers=self.headers,
                json=payload
            )
            
            if response.status_code == 200:
                # Parse response
                order_data = response.json()
                
                # Update order with broker data
                order.id = order_data.get("id")
                order.status = order_data.get("status")
                order.filled_quantity = float(order_data.get("filled_qty", 0))
                order.filled_price = float(order_data.get("filled_avg_price", 0)) if order_data.get("filled_avg_price") else None
                order.updated_at = datetime.now()
                
                self.logger.info(f"Successfully placed order for {order.quantity} shares of {order.symbol}")
                return order
            else:
                error_msg = f"Failed to place order: {response.text}"
                self.logger.error(error_msg)
                raise OrderError(error_msg)
                
        except Exception as e:
            error_msg = f"Error placing order with Alpaca: {str(e)}"
            self.logger.error(error_msg)
            raise OrderError(error_msg)
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order with Alpaca"""
        if not self.authenticated and not self.authenticate():
            raise AuthenticationError("Not authenticated with Alpaca")
        
        try:
            response = requests.delete(
                f"{self.base_url}/v2/orders/{order_id}",
                headers=self.headers
            )
            
            if response.status_code == 204:
                self.logger.info(f"Successfully cancelled order {order_id}")
                return True
            else:
                error_msg = f"Failed to cancel order {order_id}: {response.text}"
                self.logger.error(error_msg)
                return False
                
        except Exception as e:
            self.logger.error(f"Error cancelling order with Alpaca: {str(e)}")
            return False
    
    def get_order(self, order_id: str) -> Order:
        """Get order details from Alpaca"""
        if not self.authenticated and not self.authenticate():
            raise AuthenticationError("Not authenticated with Alpaca")
        
        try:
            response = requests.get(
                f"{self.base_url}/v2/orders/{order_id}",
                headers=self.headers
            )
            
            if response.status_code == 200:
                # Parse response
                order_data = response.json()
                
                # Map Alpaca data to our Order model
                order = Order(
                    symbol=order_data.get("symbol"),
                    quantity=float(order_data.get("qty")),
                    side=OrderSide(order_data.get("side")),
                    order_type=OrderType(order_data.get("type")),
                    price=float(order_data.get("limit_price")) if order_data.get("limit_price") else None,
                    stop_price=float(order_data.get("stop_price")) if order_data.get("stop_price") else None,
                    time_in_force=TimeInForce(order_data.get("time_in_force")),
                    client_order_id=order_data.get("client_order_id")
                )
                
                # Update with broker-specific data
                order.id = order_data.get("id")
                order.status = order_data.get("status")
                order.filled_quantity = float(order_data.get("filled_qty", 0))
                order.filled_price = float(order_data.get("filled_avg_price", 0)) if order_data.get("filled_avg_price") else None
                
                return order
            else:
                error_msg = f"Failed to get order {order_id}: {response.text}"
                self.logger.error(error_msg)
                raise OrderError(error_msg)
                
        except Exception as e:
            error_msg = f"Error getting order from Alpaca: {str(e)}"
            self.logger.error(error_msg)
            raise OrderError(error_msg)
    
    def get_orders(self, status: Optional[str] = None) -> List[Order]:
        """Get list of orders from Alpaca"""
        if not self.authenticated and not self.authenticate():
            raise AuthenticationError("Not authenticated with Alpaca")
        
        try:
            # Build query parameters
            params = {}
            if status:
                params["status"] = status
            
            response = requests.get(
                f"{self.base_url}/v2/orders",
                headers=self.headers,
                params=params
            )
            
            if response.status_code == 200:
                orders_data = response.json()
                orders = []
                
                for order_data in orders_data:
                    # Map Alpaca data to our Order model
                    order = Order(
                        symbol=order_data.get("symbol"),
                        quantity=float(order_data.get("qty")),
                        side=OrderSide(order_data.get("side")),
                        order_type=OrderType(order_data.get("type")),
                        price=float(order_data.get("limit_price")) if order_data.get("limit_price") else None,
                        stop_price=float(order_data.get("stop_price")) if order_data.get("stop_price") else None,
                        time_in_force=TimeInForce(order_data.get("time_in_force")),
                        client_order_id=order_data.get("client_order_id")
                    )
                    
                    # Update with broker-specific data
                    order.id = order_data.get("id")
                    order.status = order_data.get("status")
                    order.filled_quantity = float(order_data.get("filled_qty", 0))
                    order.filled_price = float(order_data.get("filled_avg_price", 0)) if order_data.get("filled_avg_price") else None
                    
                    orders.append(order)
                
                return orders
            else:
                error_msg = f"Failed to get orders: {response.text}"
                self.logger.error(error_msg)
                raise OrderError(error_msg)
                
        except Exception as e:
            error_msg = f"Error getting orders from Alpaca: {str(e)}"
            self.logger.error(error_msg)
            raise OrderError(error_msg)
    
    def get_positions(self) -> List[Position]:
        """Get current positions from Alpaca"""
        if not self.authenticated and not self.authenticate():
            raise AuthenticationError("Not authenticated with Alpaca")
        
        try:
            response = requests.get(
                f"{self.base_url}/v2/positions",
                headers=self.headers
            )
            
            if response.status_code == 200:
                positions_data = response.json()
                positions = []
                
                for position_data in positions_data:
                    # Map Alpaca data to our Position model
                    position = Position(
                        symbol=position_data.get("symbol"),
                        quantity=float(position_data.get("qty")),
                        entry_price=float(position_data.get("avg_entry_price")),
                        current_price=float(position_data.get("current_price")),
                        market_value=float(position_data.get("market_value")),
                        cost_basis=float(position_data.get("cost_basis")),
                        unrealized_pl=float(position_data.get("unrealized_pl")),
                        unrealized_pl_percent=float(position_data.get("unrealized_plpc")) * 100,
                        broker="alpaca"
                    )
                    
                    positions.append(position)
                
                return positions
            else:
                error_msg = f"Failed to get positions: {response.text}"
                self.logger.error(error_msg)
                raise PositionError(error_msg)
                
        except Exception as e:
            error_msg = f"Error getting positions from Alpaca: {str(e)}"
            self.logger.error(error_msg)
            raise PositionError(error_msg)
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """Get position for a specific symbol from Alpaca"""
        if not self.authenticated and not self.authenticate():
            raise AuthenticationError("Not authenticated with Alpaca")
        
        try:
            response = requests.get(
                f"{self.base_url}/v2/positions/{symbol}",
                headers=self.headers
            )
            
            if response.status_code == 200:
                position_data = response.json()
                
                # Map Alpaca data to our Position model
                position = Position(
                    symbol=position_data.get("symbol"),
                    quantity=float(position_data.get("qty")),
                    entry_price=float(position_data.get("avg_entry_price")),
                    current_price=float(position_data.get("current_price")),
                    market_value=float(position_data.get("market_value")),
                    cost_basis=float(position_data.get("cost_basis")),
                    unrealized_pl=float(position_data.get("unrealized_pl")),
                    unrealized_pl_percent=float(position_data.get("unrealized_plpc")) * 100,
                    broker="alpaca"
                )
                
                return position
            elif response.status_code == 404:
                # No position for this symbol
                return None
            else:
                error_msg = f"Failed to get position for {symbol}: {response.text}"
                self.logger.error(error_msg)
                raise PositionError(error_msg)
                
        except Exception as e:
            error_msg = f"Error getting position from Alpaca: {str(e)}"
            self.logger.error(error_msg)
            raise PositionError(error_msg)
    
    def get_account_info(self) -> Dict:
        """Get account information from Alpaca"""
        if not self.authenticated and not self.authenticate():
            raise AuthenticationError("Not authenticated with Alpaca")
        
        try:
            response = requests.get(
                f"{self.base_url}/v2/account",
                headers=self.headers
            )
            
            if response.status_code == 200:
                account_data = response.json()
                
                # Map Alpaca account data to standardized format
                return {
                    "account_id": account_data.get("id"),
                    "account_number": account_data.get("account_number"),
                    "cash": float(account_data.get("cash")),
                    "portfolio_value": float(account_data.get("portfolio_value")),
                    "equity": float(account_data.get("equity")),
                    "buying_power": float(account_data.get("buying_power")),
                    "initial_margin": float(account_data.get("initial_margin")),
                    "maintenance_margin": float(account_data.get("maintenance_margin")),
                    "status": account_data.get("status"),
                    "created_at": account_data.get("created_at"),
                    "is_pattern_day_trader": account_data.get("pattern_day_trader"),
                    "broker": "alpaca"
                }
            else:
                error_msg = f"Failed to get account info: {response.text}"
                self.logger.error(error_msg)
                raise AuthenticationError(error_msg)
                
        except Exception as e:
            error_msg = f"Error getting account info from Alpaca: {str(e)}"
            self.logger.error(error_msg)
            raise AuthenticationError(error_msg)
    
    def get_quote(self, symbol: str) -> Dict:
        """Get current quote for a symbol from Alpaca"""
        if not self.authenticated and not self.authenticate():
            raise AuthenticationError("Not authenticated with Alpaca")
        
        try:
            response = requests.get(
                f"{self.base_url}/v2/stocks/{symbol}/quotes/latest",
                headers=self.headers
            )
            
            if response.status_code == 200:
                quote_data = response.json()
                
                # Map Alpaca quote data to standardized format
                return {
                    "symbol": symbol,
                    "ask_price": float(quote_data.get("quote", {}).get("ap", 0)),
                    "ask_size": int(quote_data.get("quote", {}).get("as", 0)),
                    "bid_price": float(quote_data.get("quote", {}).get("bp", 0)),
                    "bid_size": int(quote_data.get("quote", {}).get("bs", 0)),
                    "timestamp": quote_data.get("quote", {}).get("t"),
                    "broker": "alpaca"
                }
            else:
                error_msg = f"Failed to get quote for {symbol}: {response.text}"
                self.logger.error(error_msg)
                raise BrokerException(error_msg)
                
        except Exception as e:
            error_msg = f"Error getting quote from Alpaca: {str(e)}"
            self.logger.error(error_msg)
            raise BrokerException(error_msg)

class PaperTradingBroker(BaseBroker):
    """Paper trading broker implementation (simulation)"""
    
    def __init__(self, credentials: Dict[str, str] = None, is_sandbox: bool = True,
                initial_balance: float = 100000.0, data_path: str = "./paper_trading_data"):
        super().__init__(credentials or {}, is_sandbox=True)
        
        self.initial_balance = initial_balance
        self.data_path = data_path
        
        # Create data directory if it doesn't exist
        os.makedirs(data_path, exist_ok=True)
        
        # Load or initialize data
        self._load_data()
    
    def _load_data(self):
        """Load paper trading data from disk"""
        
        # Path for account data
        account_path = os.path.join(self.data_path, "account.json")
        
        # Path for orders data
        orders_path = os.path.join(self.data_path, "orders.json")
        
        # Path for positions data
        positions_path = os.path.join(self.data_path, "positions.json")
        
        # Load or initialize account data
        if os.path.exists(account_path):
            with open(account_path, "r") as f:
                self.account = json.load(f)
        else:
            # Initialize new account
            self.account = {
                "account_id": f"paper_{int(time.time())}",
                "cash": self.initial_balance,
                "portfolio_value": self.initial_balance,
                "equity": self.initial_balance,
                "buying_power": self.initial_balance * 2,  # 2x leverage for margin account
                "created_at": datetime.now().isoformat(),
                "broker": "paper"
            }
            self._save_account()
        
        # Load or initialize orders data
        if os.path.exists(orders_path):
            with open(orders_path, "r") as f:
                orders_data = json.load(f)
                self.orders = [Order.from_dict(order) for order in orders_data]
        else:
            self.orders = []
            self._save_orders()
        
        # Load or initialize positions data
        if os.path.exists(positions_path):
            with open(positions_path, "r") as f:
                positions_data = json.load(f)
                self.positions = [Position.from_dict(position) for position in positions_data]
        else:
            self.positions = []
            self._save_positions()
    
    def _save_account(self):
        """Save account data to disk"""
        with open(os.path.join(self.data_path, "account.json"), "w") as f:
            json.dump(self.account, f, indent=2)
    
    def _save_orders(self):
        """Save orders data to disk"""
        with open(os.path.join(self.data_path, "orders.json"), "w") as f:
            json.dump([order.to_dict() for order in self.orders], f, indent=2)
    
    def _save_positions(self):
        """Save positions data to disk"""
        with open(os.path.join(self.data_path, "positions.json"), "w") as f:
            json.dump([position.to_dict() for position in self.positions], f, indent=2)
    
    def authenticate(self) -> bool:
        """Authenticate with paper trading (always succeeds)"""
        self.authenticated = True
        return True
    
    def place_order(self, order: Order) -> Order:
        """Place an order with paper trading"""
        
        # Generate order ID
        order.id = f"paper_order_{int(time.time())}_{len(self.orders)}"
        
        # Set initial status
        order.status = "filled" if order.order_type == OrderType.MARKET else "open"
        
        # For market orders, simulate immediate execution
        if order.order_type == OrderType.MARKET:
            # Get current price
            quote = self.get_quote(order.symbol)
            
            # Use ask price for buy orders, bid price for sell orders
            execution_price = quote["ask_price"] if order.side == OrderSide.BUY else quote["bid_price"]
            
            # Update order with execution details
            order.filled_quantity = order.quantity
            order.filled_price = execution_price
            
            # Update account and positions
            self._process_filled_order(order)
        
        # Add to orders list
        self.orders.append(order)
        
        # Save to disk
        self._save_orders()
        
        return order
    
    def _process_filled_order(self, order: Order):
        """Process a filled order, updating account and positions"""
        
        # Calculate trade value
        trade_value = order.filled_quantity * order.filled_price
        
        # Update account cash
        if order.side == OrderSide.BUY:
            self.account["cash"] -= trade_value
        else:
            self.account["cash"] += trade_value
        
        # Update position
        existing_position = self.get_position(order.symbol)
        
        if order.side == OrderSide.BUY:
            if existing_position:
                # Update existing position
                new_quantity = existing_position.quantity + order.filled_quantity
                new_cost_basis = (
                    (existing_position.quantity * existing_position.entry_price) + 
                    (order.filled_quantity * order.filled_price)
                ) / new_quantity
                
                # Update position
                existing_position.quantity = new_quantity
                existing_position.entry_price = new_cost_basis
                existing_position.current_price = order.filled_price
                existing_position.market_value = new_quantity * order.filled_price
                existing_position.cost_basis = new_quantity * new_cost_basis
                existing_position.unrealized_pl = existing_position.market_value - existing_position.cost_basis
                existing_position.unrealized_pl_percent = (
                    (existing_position.unrealized_pl / existing_position.cost_basis) * 100
                    if existing_position.cost_basis > 0 else 0
                )
                existing_position.updated_at = datetime.now()
            else:
                # Create new position
                new_position = Position(
                    symbol=order.symbol,
                    quantity=order.filled_quantity,
                    entry_price=order.filled_price,
                    current_price=order.filled_price,
                    market_value=trade_value,
                    cost_basis=trade_value,
                    unrealized_pl=0,
                    unrealized_pl_percent=0,
                    broker="paper"
                )
                self.positions.append(new_position)
        
        else:  # SELL
            if existing_position:
                # Update existing position
                new_quantity = existing_position.quantity - order.filled_quantity
                
                if new_quantity > 0:
                    # Still have shares left
                    existing_position.quantity = new_quantity
                    existing_position.current_price = order.filled_price
                    existing_position.market_value = new_quantity * order.filled_price
                    existing_position.unrealized_pl = existing_position.market_value - (
                        existing_position.entry_price * new_quantity
                    )
                    existing_position.unrealized_pl_percent = (
                        (existing_position.unrealized_pl / existing_position.cost_basis) * 100
                        if existing_position.cost_basis > 0 else 0
                    )
                    existing_position.updated_at = datetime.now()
                else:
                    # Sold all shares, remove position
                    self.positions = [p for p in self.positions if p.symbol != order.symbol]
        
        # Update account values
        self._update_account_values()
        
        # Save changes
        self._save_account()
        self._save_positions()
    
    def _update_account_values(self):
        """Update account values based on current positions"""
        
        # Calculate portfolio value (cash + positions)
        positions_value = sum(position.market_value for position in self.positions)
        self.account["portfolio_value"] = self.account["cash"] + positions_value
        
        # Update equity
        self.account["equity"] = self.account["portfolio_value"]
        
        # Update buying power (2x leverage)
        self.account["buying_power"] = self.account["cash"] * 2
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order"""
        
        # Find order
        for order in self.orders:
            if order.id == order_id and order.status == "open":
                order.status = "cancelled"
                self._save_orders()
                return True
        
        return False
    
    def get_order(self, order_id: str) -> Order:
        """Get order details"""
        
        # Find order
        for order in self.orders:
            if order.id == order_id:
                return order
        
        raise OrderError(f"Order {order_id} not found")
    
    def get_orders(self, status: Optional[str] = None) -> List[Order]:
        """Get list of orders"""
        
        if status:
            return [order for order in self.orders if order.status == status]
        else:
            return self.orders.copy()
    
    def get_positions(self) -> List[Position]:
        """Get current positions"""
        return self.positions.copy()
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """Get position for a specific symbol"""
        for position in self.positions:
            if position.symbol.upper() == symbol.upper():
                return position
        
        return None
    
    def get_account_info(self) -> Dict:
        """Get account information"""
        return self.account.copy()
    
    def get_quote(self, symbol: str) -> Dict:
        """Get current quote for a symbol"""
        # For paper trading, use a simple mock quote with minor randomization
        
        # First check if we have a position for this symbol
        position = self.get_position(symbol)
        
        if position:
            # Base price on the position's current price with some randomness
            base_price = position.current_price
        else:
            # Make up a reasonable stock price based on the symbol's string hash
            symbol_hash = sum(ord(c) for c in symbol)
            base_price = 10 + (symbol_hash % 990)  # Price between $10 and $1000
        
        # Add some randomness (±0.5%)
        random_factor = 1 + ((random.random() - 0.5) * 0.01)
        current_price = base_price * random_factor
        
        # Create bid/ask spread (±0.1%)
        bid_price = current_price * 0.999
        ask_price = current_price * 1.001
        
        return {
            "symbol": symbol,
            "ask_price": round(ask_price, 2),
            "ask_size": random.randint(100, 1000),
            "bid_price": round(bid_price, 2),
            "bid_size": random.randint(100, 1000),
            "timestamp": datetime.now().isoformat(),
            "broker": "paper"
        }

class BrokerFactory:
    """Factory class for creating broker instances"""
    
    @staticmethod
    def create_broker(broker_type: str, credentials: Dict[str, str], is_sandbox: bool = True) -> BaseBroker:
        """Create a broker instance based on type"""
        
        if broker_type.lower() == "alpaca":
            return AlpacaBroker(credentials, is_sandbox)
        elif broker_type.lower() == "paper":
            return PaperTradingBroker(credentials, is_sandbox)
        else:
            raise ValueError(f"Unsupported broker type: {broker_type}")