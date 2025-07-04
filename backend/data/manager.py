"""
Data Manager - Intelligent routing between broker APIs and market data providers
Implements hybrid data strategy with failover and caching
"""

import asyncio
import redis.asyncio as redis
from typing import Optional, Dict, Any, List, Union
from datetime import datetime, date, timedelta
import json
import logging
from decimal import Decimal

from .providers.base import BaseDataProvider, create_provider
from .models import (
    Quote, OptionsChain, HistoricalBar, Position, Account, Order,
    DataRequest, DataResponse, MarketDataType
)


class DataManagerError(Exception):
    """Data manager specific errors"""
    pass


class DataManager:
    """
    Intelligent data manager that routes requests between multiple sources
    
    Features:
    - Smart routing: Broker APIs → Market Data fallback
    - Redis caching for performance
    - Data quality validation
    - Source preference management
    - Performance monitoring
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger("data.manager")
        
        # Data providers
        self.providers: Dict[str, BaseDataProvider] = {}
        self.broker_providers: Dict[str, BaseDataProvider] = {}
        self.market_data_providers: Dict[str, BaseDataProvider] = {}
        
        # Redis cache
        self.redis_client: Optional[redis.Redis] = None
        self.cache_enabled = config.get('cache_enabled', True)
        self.default_cache_ttl = config.get('default_cache_ttl', 300)  # 5 minutes
        
        # Request routing preferences
        self.routing_config = config.get('routing', {})
        self.default_market_data_provider = config.get('default_market_data_provider', 'polygon')
        
        # Performance tracking
        self.request_stats = {
            'total_requests': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'broker_requests': 0,
            'market_data_requests': 0,
            'errors': 0
        }
        
    async def initialize(self):
        """Initialize data manager and providers"""
        try:
            # Initialize Redis cache
            if self.cache_enabled:
                await self._init_redis()
            
            # Initialize data providers
            await self._init_providers()
            
            self.logger.info("✅ Data Manager initialized successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Data Manager: {e}")
            raise DataManagerError(f"Initialization failed: {e}")
    
    async def _init_redis(self):
        """Initialize Redis connection"""
        try:
            redis_config = self.config.get('redis', {})
            self.redis_client = redis.Redis(
                host=redis_config.get('host', 'localhost'),
                port=redis_config.get('port', 6379),
                db=redis_config.get('db', 0),
                password=redis_config.get('password'),
                decode_responses=True
            )
            
            # Test connection
            await self.redis_client.ping()
            self.logger.info("✅ Redis cache connected")
            
        except Exception as e:
            self.logger.warning(f"⚠️ Redis cache unavailable: {e}")
            self.cache_enabled = False
    
    async def _init_providers(self):
        """Initialize data providers"""
        providers_config = self.config.get('providers', {})
        
        for provider_name, provider_config in providers_config.items():
            try:
                if not provider_config.get('enabled', True):
                    continue
                
                provider = create_provider(provider_name, provider_config)
                self.providers[provider_name] = provider
                
                # Categorize providers
                if provider._supports_account_data():
                    self.broker_providers[provider_name] = provider
                else:
                    self.market_data_providers[provider_name] = provider
                
                # Connect to provider
                connected = await provider.connect()
                if connected:
                    self.logger.info(f"✅ {provider_name} provider connected")
                else:
                    self.logger.warning(f"⚠️ {provider_name} provider connection failed")
                    
            except Exception as e:
                self.logger.error(f"❌ Failed to initialize {provider_name}: {e}")
    
    async def shutdown(self):
        """Shutdown data manager and close connections"""
        # Disconnect all providers
        for provider in self.providers.values():
            try:
                await provider.disconnect()
            except:
                pass
        
        # Close Redis connection
        if self.redis_client:
            await self.redis_client.close()
        
        self.logger.info("✅ Data Manager shutdown complete")
    
    # Core data retrieval methods
    
    async def get_quote(
        self, 
        symbol: str, 
        user_id: Optional[str] = None,
        account_id: Optional[str] = None,
        source_preference: Optional[str] = None
    ) -> DataResponse:
        """
        Get real-time quote with intelligent source routing
        
        Args:
            symbol: Stock/option symbol
            user_id: User ID for personalization
            account_id: Account ID for broker-specific data
            source_preference: Preferred data source
        """
        try:
            self.request_stats['total_requests'] += 1
            
            # Check cache first
            if self.cache_enabled:
                cached_data = await self._get_cached_quote(symbol)
                if cached_data:
                    self.request_stats['cache_hits'] += 1
                    return cached_data
            
            self.request_stats['cache_misses'] += 1
            
            # Route request to appropriate provider
            provider = self._select_quote_provider(symbol, account_id, source_preference)
            
            if not provider:
                raise DataManagerError("No available providers for quote data")
            
            # Get quote from provider
            response = await provider.get_quote(symbol)
            
            # Track request type
            if provider.provider_name in self.broker_providers:
                self.request_stats['broker_requests'] += 1
            else:
                self.request_stats['market_data_requests'] += 1
            
            # Cache successful response
            if response.success and self.cache_enabled:
                await self._cache_quote(symbol, response)
            
            return response
            
        except Exception as e:
            self.request_stats['errors'] += 1
            self.logger.error(f"Failed to get quote for {symbol}: {e}")
            return DataResponse(
                success=False,
                error=str(e),
                timestamp=datetime.now()
            )
    
    async def get_options_chain(
        self,
        underlying: str,
        expiration: Optional[date] = None,
        strike_range: Optional[tuple[float, float]] = None,
        user_id: Optional[str] = None,
        account_id: Optional[str] = None,
        source_preference: Optional[str] = None
    ) -> DataResponse:
        """Get options chain with intelligent routing"""
        try:
            self.request_stats['total_requests'] += 1
            
            # Check cache
            if self.cache_enabled:
                cached_data = await self._get_cached_options_chain(underlying, expiration)
                if cached_data:
                    self.request_stats['cache_hits'] += 1
                    return cached_data
            
            self.request_stats['cache_misses'] += 1
            
            # Route request
            provider = self._select_options_provider(underlying, account_id, source_preference)
            
            if not provider:
                raise DataManagerError("No available providers for options data")
            
            # Get options chain
            response = await provider.get_options_chain(
                underlying=underlying,
                expiration=expiration,
                strike_range=strike_range
            )
            
            # Track and cache
            if provider.provider_name in self.broker_providers:
                self.request_stats['broker_requests'] += 1
            else:
                self.request_stats['market_data_requests'] += 1
            
            if response.success and self.cache_enabled:
                await self._cache_options_chain(underlying, expiration, response)
            
            return response
            
        except Exception as e:
            self.request_stats['errors'] += 1
            self.logger.error(f"Failed to get options chain for {underlying}: {e}")
            return DataResponse(
                success=False,
                error=str(e),
                timestamp=datetime.now()
            )
    
    async def get_historical_data(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        interval: str = "1d",
        source_preference: Optional[str] = None
    ) -> DataResponse:
        """Get historical data with source routing"""
        try:
            self.request_stats['total_requests'] += 1
            
            # Historical data is typically cached longer
            if self.cache_enabled:
                cached_data = await self._get_cached_historical(symbol, start_date, end_date, interval)
                if cached_data:
                    self.request_stats['cache_hits'] += 1
                    return cached_data
            
            self.request_stats['cache_misses'] += 1
            
            # Route to market data provider (brokers typically have limited historical data)
            provider = self._select_historical_provider(source_preference)
            
            if not provider:
                raise DataManagerError("No available providers for historical data")
            
            response = await provider.get_historical_data(symbol, start_date, end_date, interval)
            
            self.request_stats['market_data_requests'] += 1
            
            # Cache with longer TTL for historical data
            if response.success and self.cache_enabled:
                await self._cache_historical_data(symbol, start_date, end_date, interval, response)
            
            return response
            
        except Exception as e:
            self.request_stats['errors'] += 1
            self.logger.error(f"Failed to get historical data for {symbol}: {e}")
            return DataResponse(
                success=False,
                error=str(e),
                timestamp=datetime.now()
            )
    
    # Account data methods (broker-only)
    
    async def get_account_info(self, account_id: str, broker: str) -> DataResponse:
        """Get account information from specific broker"""
        try:
            provider = self.broker_providers.get(broker)
            if not provider:
                raise DataManagerError(f"Broker {broker} not available")
            
            return await provider.get_account_info(account_id)
            
        except Exception as e:
            self.logger.error(f"Failed to get account info for {account_id}: {e}")
            return DataResponse(
                success=False,
                error=str(e),
                timestamp=datetime.now()
            )
    
    async def get_positions(self, account_id: str, broker: str) -> DataResponse:
        """Get positions from specific broker"""
        try:
            provider = self.broker_providers.get(broker)
            if not provider:
                raise DataManagerError(f"Broker {broker} not available")
            
            return await provider.get_positions(account_id)
            
        except Exception as e:
            self.logger.error(f"Failed to get positions for {account_id}: {e}")
            return DataResponse(
                success=False,
                error=str(e),
                timestamp=datetime.now()
            )
    
    # Provider selection logic
    
    def _select_quote_provider(
        self, 
        symbol: str, 
        account_id: Optional[str], 
        source_preference: Optional[str]
    ) -> Optional[BaseDataProvider]:
        """Select best provider for quote data"""
        
        # If user specifies preference, try that first
        if source_preference and source_preference in self.providers:
            provider = self.providers[source_preference]
            if provider.is_connected:
                return provider
        
        # If account_id provided, try broker first for account-specific pricing
        if account_id:
            for broker_name, provider in self.broker_providers.items():
                if provider.is_connected and account_id in provider.connected_accounts:
                    return provider
        
        # Fall back to market data providers
        # Try default first
        if self.default_market_data_provider in self.market_data_providers:
            provider = self.market_data_providers[self.default_market_data_provider]
            if provider.is_connected:
                return provider
        
        # Try any available market data provider
        for provider in self.market_data_providers.values():
            if provider.is_connected:
                return provider
        
        return None
    
    def _select_options_provider(
        self, 
        underlying: str, 
        account_id: Optional[str], 
        source_preference: Optional[str]
    ) -> Optional[BaseDataProvider]:
        """Select best provider for options data"""
        
        # Similar logic to quote provider but prioritize brokers for options
        if source_preference and source_preference in self.providers:
            provider = self.providers[source_preference]
            if provider.is_connected:
                return provider
        
        # Brokers often have better options data
        if account_id:
            for broker_name, provider in self.broker_providers.items():
                if provider.is_connected and account_id in provider.connected_accounts:
                    return provider
        
        # Market data providers as fallback
        for provider in self.market_data_providers.values():
            if provider.is_connected:
                return provider
        
        return None
    
    def _select_historical_provider(self, source_preference: Optional[str]) -> Optional[BaseDataProvider]:
        """Select provider for historical data (prefer market data providers)"""
        
        if source_preference and source_preference in self.providers:
            provider = self.providers[source_preference]
            if provider.is_connected:
                return provider
        
        # Market data providers typically have better historical data
        if self.default_market_data_provider in self.market_data_providers:
            provider = self.market_data_providers[self.default_market_data_provider]
            if provider.is_connected:
                return provider
        
        for provider in self.market_data_providers.values():
            if provider.is_connected:
                return provider
        
        return None
    
    # Caching methods
    
    async def _get_cached_quote(self, symbol: str) -> Optional[DataResponse]:
        """Get cached quote data"""
        if not self.redis_client:
            return None
        
        try:
            key = f"quote:{symbol}"
            cached = await self.redis_client.get(key)
            if cached:
                data = json.loads(cached)
                return DataResponse(**data, cached=True)
        except Exception as e:
            self.logger.debug(f"Cache read error: {e}")
        
        return None
    
    async def _cache_quote(self, symbol: str, response: DataResponse):
        """Cache quote data"""
        if not self.redis_client:
            return
        
        try:
            key = f"quote:{symbol}"
            # Cache quotes for shorter time (real-time data)
            ttl = 30  # 30 seconds for quotes
            
            # Convert response to cacheable format
            cache_data = response.dict()
            await self.redis_client.setex(key, ttl, json.dumps(cache_data, default=str))
            
        except Exception as e:
            self.logger.debug(f"Cache write error: {e}")
    
    async def _get_cached_options_chain(self, underlying: str, expiration: Optional[date]) -> Optional[DataResponse]:
        """Get cached options chain"""
        if not self.redis_client:
            return None
        
        try:
            exp_str = expiration.isoformat() if expiration else "all"
            key = f"options:{underlying}:{exp_str}"
            cached = await self.redis_client.get(key)
            if cached:
                data = json.loads(cached)
                return DataResponse(**data, cached=True)
        except Exception as e:
            self.logger.debug(f"Cache read error: {e}")
        
        return None
    
    async def _cache_options_chain(self, underlying: str, expiration: Optional[date], response: DataResponse):
        """Cache options chain data"""
        if not self.redis_client:
            return
        
        try:
            exp_str = expiration.isoformat() if expiration else "all"
            key = f"options:{underlying}:{exp_str}"
            ttl = 300  # 5 minutes for options chains
            
            cache_data = response.dict()
            await self.redis_client.setex(key, ttl, json.dumps(cache_data, default=str))
            
        except Exception as e:
            self.logger.debug(f"Cache write error: {e}")
    
    async def _get_cached_historical(self, symbol: str, start_date: date, end_date: date, interval: str) -> Optional[DataResponse]:
        """Get cached historical data"""
        if not self.redis_client:
            return None
        
        try:
            key = f"historical:{symbol}:{start_date}:{end_date}:{interval}"
            cached = await self.redis_client.get(key)
            if cached:
                data = json.loads(cached)
                return DataResponse(**data, cached=True)
        except Exception as e:
            self.logger.debug(f"Cache read error: {e}")
        
        return None
    
    async def _cache_historical_data(self, symbol: str, start_date: date, end_date: date, interval: str, response: DataResponse):
        """Cache historical data"""
        if not self.redis_client:
            return
        
        try:
            key = f"historical:{symbol}:{start_date}:{end_date}:{interval}"
            ttl = 3600  # 1 hour for historical data
            
            cache_data = response.dict()
            await self.redis_client.setex(key, ttl, json.dumps(cache_data, default=str))
            
        except Exception as e:
            self.logger.debug(f"Cache write error: {e}")
    
    # Monitoring and health
    
    def get_stats(self) -> Dict[str, Any]:
        """Get data manager statistics"""
        return {
            'request_stats': self.request_stats.copy(),
            'providers': {
                name: provider.get_provider_info() 
                for name, provider in self.providers.items()
            },
            'cache_enabled': self.cache_enabled,
            'cache_hit_rate': (
                self.request_stats['cache_hits'] / 
                max(self.request_stats['total_requests'], 1)
            ) * 100
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status"""
        connected_providers = sum(
            1 for provider in self.providers.values() 
            if provider.is_connected
        )
        
        return {
            'status': 'healthy' if connected_providers > 0 else 'degraded',
            'total_providers': len(self.providers),
            'connected_providers': connected_providers,
            'broker_providers': len(self.broker_providers),
            'market_data_providers': len(self.market_data_providers),
            'cache_enabled': self.cache_enabled,
            'total_requests': self.request_stats['total_requests'],
            'error_rate': (
                self.request_stats['errors'] / 
                max(self.request_stats['total_requests'], 1)
            ) * 100
        }