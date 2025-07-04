"""
Base Data Provider Interface
Abstract base class for all data providers (brokers and market data)
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, date
import logging

from ..models import (
    Quote, OptionsChain, HistoricalBar, Position, Account, Order,
    DataRequest, DataResponse, MarketDataType, OrderType, OrderSide
)


class DataProviderError(Exception):
    """Base exception for data provider errors"""
    pass


class AuthenticationError(DataProviderError):
    """Authentication failed"""
    pass


class RateLimitError(DataProviderError):
    """Rate limit exceeded"""
    pass


class DataNotAvailableError(DataProviderError):
    """Requested data not available"""
    pass


class BaseDataProvider(ABC):
    """
    Abstract base class for all data providers
    
    Defines standard interface for:
    - Market data retrieval
    - Account data (for brokers)
    - Order management (for brokers)
    - Authentication and connection management
    """
    
    def __init__(self, provider_name: str, config: Dict[str, Any]):
        self.provider_name = provider_name
        self.config = config
        self.logger = logging.getLogger(f"data.{provider_name}")
        self.is_connected = False
        self.last_error: Optional[str] = None
        self.request_count = 0
        self.rate_limit_remaining: Optional[int] = None
        
    # Connection Management
    
    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to data provider"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """Disconnect from data provider"""
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """Test if connection is active and working"""
        pass
    
    # Market Data Methods
    
    @abstractmethod
    async def get_quote(self, symbol: str) -> DataResponse:
        """Get real-time quote for symbol"""
        pass
    
    @abstractmethod
    async def get_options_chain(
        self, 
        underlying: str,
        expiration: Optional[date] = None,
        strike_range: Optional[tuple[float, float]] = None
    ) -> DataResponse:
        """Get options chain for underlying"""
        pass
    
    @abstractmethod
    async def get_historical_data(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        interval: str = "1d"
    ) -> DataResponse:
        """Get historical price data"""
        pass
    
    # Account Data Methods (for brokers)
    
    async def get_account_info(self, account_id: str) -> DataResponse:
        """Get account information - default implementation for non-brokers"""
        return DataResponse(
            success=False,
            error="Account data not supported by this provider",
            timestamp=datetime.now()
        )
    
    async def get_positions(self, account_id: str) -> DataResponse:
        """Get account positions - default implementation for non-brokers"""
        return DataResponse(
            success=False,
            error="Position data not supported by this provider",
            timestamp=datetime.now()
        )
    
    async def get_orders(self, account_id: str) -> DataResponse:
        """Get account orders - default implementation for non-brokers"""
        return DataResponse(
            success=False,
            error="Order data not supported by this provider",
            timestamp=datetime.now()
        )
    
    # Order Management Methods (for brokers)
    
    async def place_order(self, order_request: Dict[str, Any]) -> DataResponse:
        """Place trading order - default implementation for non-brokers"""
        return DataResponse(
            success=False,
            error="Order placement not supported by this provider",
            timestamp=datetime.now()
        )
    
    async def cancel_order(self, order_id: str, account_id: str) -> DataResponse:
        """Cancel order - default implementation for non-brokers"""
        return DataResponse(
            success=False,
            error="Order cancellation not supported by this provider",
            timestamp=datetime.now()
        )
    
    async def modify_order(self, order_id: str, modifications: Dict[str, Any]) -> DataResponse:
        """Modify order - default implementation for non-brokers"""
        return DataResponse(
            success=False,
            error="Order modification not supported by this provider",
            timestamp=datetime.now()
        )
    
    # Utility Methods
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get provider information and status"""
        return {
            "name": self.provider_name,
            "connected": self.is_connected,
            "last_error": self.last_error,
            "request_count": self.request_count,
            "rate_limit_remaining": self.rate_limit_remaining,
            "supports_market_data": self._supports_market_data(),
            "supports_account_data": self._supports_account_data(),
            "supports_trading": self._supports_trading()
        }
    
    def _supports_market_data(self) -> bool:
        """Check if provider supports market data"""
        return True  # All providers should support basic market data
    
    def _supports_account_data(self) -> bool:
        """Check if provider supports account data"""
        # Override in broker implementations
        return False
    
    def _supports_trading(self) -> bool:
        """Check if provider supports trading"""
        # Override in broker implementations
        return False
    
    async def _handle_rate_limit(self, retry_after: Optional[int] = None):
        """Handle rate limiting"""
        import asyncio
        
        if retry_after:
            self.logger.warning(f"Rate limited, waiting {retry_after} seconds")
            await asyncio.sleep(retry_after)
        else:
            # Default backoff
            await asyncio.sleep(1)
    
    def _track_request(self):
        """Track API request for monitoring"""
        self.request_count += 1
    
    def _log_error(self, error: str, exception: Optional[Exception] = None):
        """Log error and update last_error"""
        self.last_error = error
        if exception:
            self.logger.error(f"{error}: {str(exception)}")
        else:
            self.logger.error(error)


class MarketDataProvider(BaseDataProvider):
    """
    Base class for market data providers (Polygon, Alpha Vantage, etc.)
    
    These providers only supply market data, not account or trading functionality
    """
    
    def __init__(self, provider_name: str, config: Dict[str, Any]):
        super().__init__(provider_name, config)
    
    def _supports_account_data(self) -> bool:
        return False
    
    def _supports_trading(self) -> bool:
        return False


class BrokerProvider(BaseDataProvider):
    """
    Base class for broker providers (Schwab, IBKR, TastyTrade, etc.)
    
    These providers supply market data, account data, and trading functionality
    """
    
    def __init__(self, provider_name: str, config: Dict[str, Any]):
        super().__init__(provider_name, config)
        self.connected_accounts: List[str] = []
    
    def _supports_account_data(self) -> bool:
        return True
    
    def _supports_trading(self) -> bool:
        return True
    
    # Abstract methods that brokers must implement
    
    @abstractmethod
    async def authenticate(self, credentials: Dict[str, str]) -> bool:
        """Authenticate with broker API"""
        pass
    
    @abstractmethod
    async def refresh_token(self) -> bool:
        """Refresh authentication token"""
        pass
    
    @abstractmethod
    async def get_accounts(self) -> DataResponse:
        """Get list of available accounts"""
        pass
    
    # Broker-specific implementations required
    
    async def get_account_info(self, account_id: str) -> DataResponse:
        """Get account information - must be implemented by brokers"""
        raise NotImplementedError("Broker must implement get_account_info")
    
    async def get_positions(self, account_id: str) -> DataResponse:
        """Get account positions - must be implemented by brokers"""
        raise NotImplementedError("Broker must implement get_positions")
    
    async def get_orders(self, account_id: str) -> DataResponse:
        """Get account orders - must be implemented by brokers"""
        raise NotImplementedError("Broker must implement get_orders")
    
    async def place_order(self, order_request: Dict[str, Any]) -> DataResponse:
        """Place trading order - must be implemented by brokers"""
        raise NotImplementedError("Broker must implement place_order")


# Factory function for provider creation

def create_provider(provider_type: str, config: Dict[str, Any]) -> BaseDataProvider:
    """
    Factory function to create data provider instances
    
    Args:
        provider_type: Type of provider ('polygon', 'schwab', 'ibkr', etc.)
        config: Provider configuration
        
    Returns:
        Configured provider instance
    """
    from .polygon import PolygonProvider
    from .schwab import SchwabProvider
    from .alpha_vantage import AlphaVantageProvider
    # Import other providers as they're implemented
    
    providers = {
        'polygon': PolygonProvider,
        'schwab': SchwabProvider,
        'alpha_vantage': AlphaVantageProvider,
        # Add more providers here
    }
    
    if provider_type not in providers:
        raise ValueError(f"Unknown provider type: {provider_type}")
    
    return providers[provider_type](config)