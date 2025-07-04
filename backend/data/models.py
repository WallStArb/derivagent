"""
Standardized Data Models for Derivagent
Unified data structures for broker APIs and market data providers
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, date
from decimal import Decimal
from enum import Enum


class MarketDataType(str, Enum):
    """Types of market data"""
    QUOTE = "quote"
    OPTIONS_CHAIN = "options_chain"
    HISTORICAL = "historical"
    GREEKS = "greeks"
    VOLATILITY = "volatility"
    ECONOMIC = "economic"


class OrderStatus(str, Enum):
    """Order status types"""
    PENDING = "pending"
    WORKING = "working"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class OrderType(str, Enum):
    """Order types"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"
    BRACKET = "bracket"


class OrderSide(str, Enum):
    """Order sides"""
    BUY = "buy"
    SELL = "sell"
    BUY_TO_OPEN = "buy_to_open"
    SELL_TO_OPEN = "sell_to_open"
    BUY_TO_CLOSE = "buy_to_close"
    SELL_TO_CLOSE = "sell_to_close"


class OptionType(str, Enum):
    """Option types"""
    CALL = "call"
    PUT = "put"


class PositionType(str, Enum):
    """Position types"""
    LONG = "long"
    SHORT = "short"


# Base Data Models

class Quote(BaseModel):
    """Real-time quote data"""
    symbol: str
    bid: Optional[Decimal] = None
    ask: Optional[Decimal] = None
    last: Optional[Decimal] = None
    mark: Optional[Decimal] = None
    bid_size: Optional[int] = None
    ask_size: Optional[int] = None
    volume: Optional[int] = None
    open_price: Optional[Decimal] = None
    high: Optional[Decimal] = None
    low: Optional[Decimal] = None
    close_price: Optional[Decimal] = None
    change: Optional[Decimal] = None
    change_percent: Optional[Decimal] = None
    timestamp: datetime
    market_hours: bool = True
    source: str = Field(..., description="Data source identifier")
    
    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }


class Greeks(BaseModel):
    """Options Greeks"""
    delta: Optional[Decimal] = None
    gamma: Optional[Decimal] = None
    theta: Optional[Decimal] = None
    vega: Optional[Decimal] = None
    rho: Optional[Decimal] = None
    implied_volatility: Optional[Decimal] = None
    intrinsic_value: Optional[Decimal] = None
    extrinsic_value: Optional[Decimal] = None
    
    class Config:
        json_encoders = {Decimal: str}


class OptionContract(BaseModel):
    """Individual option contract"""
    symbol: str
    underlying_symbol: str
    option_type: OptionType
    strike_price: Decimal
    expiration_date: date
    days_to_expiration: Optional[int] = None
    
    # Pricing
    bid: Optional[Decimal] = None
    ask: Optional[Decimal] = None
    last: Optional[Decimal] = None
    mark: Optional[Decimal] = None
    
    # Volume and Interest
    volume: Optional[int] = None
    open_interest: Optional[int] = None
    
    # Greeks and IV
    greeks: Optional[Greeks] = None
    
    # Metadata
    timestamp: datetime
    source: str
    
    @property
    def bid_ask_spread(self) -> Optional[Decimal]:
        """Calculate bid-ask spread"""
        if self.bid and self.ask:
            return self.ask - self.bid
        return None
    
    @property
    def mid_price(self) -> Optional[Decimal]:
        """Calculate mid price"""
        if self.bid and self.ask:
            return (self.bid + self.ask) / 2
        return None
    
    class Config:
        json_encoders = {
            Decimal: str,
            date: lambda v: v.isoformat(),
            datetime: lambda v: v.isoformat()
        }


class OptionsChain(BaseModel):
    """Complete options chain for an underlying"""
    underlying_symbol: str
    underlying_price: Optional[Decimal] = None
    timestamp: datetime
    source: str
    
    # Options by expiration
    expirations: Dict[str, List[OptionContract]] = Field(default_factory=dict)
    
    # Metadata
    market_hours: bool = True
    total_contracts: int = 0
    
    def get_contracts_by_expiration(self, expiration: date) -> List[OptionContract]:
        """Get contracts for specific expiration"""
        exp_str = expiration.isoformat()
        return self.expirations.get(exp_str, [])
    
    def get_strikes_for_expiration(self, expiration: date) -> List[Decimal]:
        """Get available strikes for expiration"""
        contracts = self.get_contracts_by_expiration(expiration)
        return sorted(set(c.strike_price for c in contracts))
    
    def find_contract(self, strike: Decimal, expiration: date, option_type: OptionType) -> Optional[OptionContract]:
        """Find specific option contract"""
        contracts = self.get_contracts_by_expiration(expiration)
        for contract in contracts:
            if (contract.strike_price == strike and 
                contract.option_type == option_type):
                return contract
        return None
    
    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }


class HistoricalBar(BaseModel):
    """Historical price bar"""
    symbol: str
    timestamp: datetime
    open_price: Decimal
    high: Decimal
    low: Decimal
    close_price: Decimal
    volume: int
    
    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }


class Position(BaseModel):
    """Account position"""
    symbol: str
    quantity: Decimal
    average_price: Optional[Decimal] = None
    market_value: Optional[Decimal] = None
    cost_basis: Optional[Decimal] = None
    unrealized_pnl: Optional[Decimal] = None
    realized_pnl: Optional[Decimal] = None
    
    # For options
    underlying_symbol: Optional[str] = None
    option_type: Optional[OptionType] = None
    strike_price: Optional[Decimal] = None
    expiration_date: Optional[date] = None
    
    # Position details
    position_type: PositionType
    account_id: str
    broker: str
    timestamp: datetime
    
    @property
    def is_option(self) -> bool:
        """Check if position is an option"""
        return self.option_type is not None
    
    class Config:
        json_encoders = {
            Decimal: str,
            date: lambda v: v.isoformat(),
            datetime: lambda v: v.isoformat()
        }


class Order(BaseModel):
    """Trading order"""
    order_id: str
    symbol: str
    quantity: Decimal
    side: OrderSide
    order_type: OrderType
    status: OrderStatus
    
    # Pricing
    limit_price: Optional[Decimal] = None
    stop_price: Optional[Decimal] = None
    filled_price: Optional[Decimal] = None
    filled_quantity: Optional[Decimal] = None
    
    # Timing
    created_at: datetime
    updated_at: datetime
    filled_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
    # Account info
    account_id: str
    broker: str
    
    # For options
    underlying_symbol: Optional[str] = None
    option_type: Optional[OptionType] = None
    strike_price: Optional[Decimal] = None
    expiration_date: Optional[date] = None
    
    # AI context
    strategy_id: Optional[str] = None
    ai_reasoning: Optional[str] = None
    human_approved: bool = False
    
    class Config:
        json_encoders = {
            Decimal: str,
            date: lambda v: v.isoformat(),
            datetime: lambda v: v.isoformat()
        }


class Account(BaseModel):
    """Broker account information"""
    account_id: str
    broker: str
    account_type: str  # margin, cash, etc.
    
    # Balances
    total_value: Optional[Decimal] = None
    cash_balance: Optional[Decimal] = None
    buying_power: Optional[Decimal] = None
    margin_used: Optional[Decimal] = None
    
    # P&L
    day_pnl: Optional[Decimal] = None
    total_pnl: Optional[Decimal] = None
    
    # Status
    is_active: bool = True
    last_updated: datetime
    
    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }


class MarketData(BaseModel):
    """Generic market data container"""
    data_type: MarketDataType
    symbol: str
    timestamp: datetime
    source: str
    data: Dict[str, Any]
    expires_at: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class DataRequest(BaseModel):
    """Data request specification"""
    data_type: MarketDataType
    symbol: str
    source_preference: Optional[str] = None  # broker, polygon, alpha_vantage
    use_cache: bool = True
    max_age_seconds: Optional[int] = None
    
    # Optional filters
    expiration_date: Optional[date] = None
    strike_range: Optional[tuple[Decimal, Decimal]] = None
    option_type: Optional[OptionType] = None


class DataResponse(BaseModel):
    """Standardized data response"""
    success: bool
    data: Optional[Union[Quote, OptionsChain, List[HistoricalBar], Position, Account]] = None
    error: Optional[str] = None
    source: Optional[str] = None
    cached: bool = False
    timestamp: datetime
    latency_ms: Optional[int] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Validation functions

def validate_symbol(symbol: str) -> str:
    """Validate and normalize symbol"""
    if not symbol or len(symbol) < 1:
        raise ValueError("Symbol cannot be empty")
    return symbol.upper().strip()


def validate_strike_price(strike: Decimal) -> Decimal:
    """Validate strike price"""
    if strike <= 0:
        raise ValueError("Strike price must be positive")
    return strike


def validate_expiration_date(exp_date: date) -> date:
    """Validate expiration date"""
    if exp_date <= date.today():
        raise ValueError("Expiration date must be in the future")
    return exp_date


# Helper functions for data transformation

def normalize_option_symbol(symbol: str) -> Dict[str, Any]:
    """Parse option symbol into components"""
    # Basic parsing - extend based on broker symbol formats
    parts = symbol.split('_') if '_' in symbol else [symbol]
    
    return {
        "underlying": parts[0] if parts else symbol,
        "full_symbol": symbol,
        "parsed": len(parts) > 1
    }


def calculate_option_intrinsic_value(
    underlying_price: Decimal,
    strike_price: Decimal,
    option_type: OptionType
) -> Decimal:
    """Calculate option intrinsic value"""
    if option_type == OptionType.CALL:
        return max(underlying_price - strike_price, Decimal('0'))
    else:  # PUT
        return max(strike_price - underlying_price, Decimal('0'))


def estimate_bid_ask_spread_quality(spread: Decimal, price: Decimal) -> str:
    """Estimate bid-ask spread quality"""
    if price <= 0:
        return "unknown"
    
    spread_percent = (spread / price) * 100
    
    if spread_percent <= 1:
        return "excellent"
    elif spread_percent <= 3:
        return "good"
    elif spread_percent <= 5:
        return "fair"
    else:
        return "poor"