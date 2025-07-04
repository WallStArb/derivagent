"""
Alpha Vantage Market Data Provider
Implements market data via Alpha Vantage API for comprehensive coverage
"""

import aiohttp
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime, date, timedelta
from decimal import Decimal
import json

from .base import MarketDataProvider, DataProviderError, RateLimitError
from ..models import (
    Quote, OptionsChain, OptionContract, HistoricalBar, Greeks,
    DataResponse, OptionType, MarketDataType
)


class AlphaVantageProvider(MarketDataProvider):
    """
    Alpha Vantage market data provider
    
    Features:
    - Real-time and delayed quotes
    - Historical data with multiple timeframes
    - Technical indicators
    - Economic data and earnings
    - Free tier: 25 requests per day, 5 per minute
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("alpha_vantage", config)
        
        self.api_key = config.get('api_key')
        if not self.api_key:
            raise ValueError("Alpha Vantage API key is required")
        
        self.base_url = "https://www.alphavantage.co/query"
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Rate limiting - free tier: 5 requests per minute, 25 per day
        self.rate_limit = config.get('rate_limit', 5)  # requests per minute
        self.daily_limit = config.get('daily_limit', 25)
        self.request_count_today = 0
        self.last_request_time = datetime.now()
        self.daily_reset_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
    async def connect(self) -> bool:
        """Establish connection to Alpha Vantage API"""
        try:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={
                    "User-Agent": "Derivagent/1.0"
                }
            )
            
            # Test connection
            success = await self.test_connection()
            self.is_connected = success
            
            if success:
                self.logger.info("✅ Connected to Alpha Vantage")
            else:
                self.logger.error("❌ Failed to connect to Alpha Vantage")
                
            return success
            
        except Exception as e:
            self._log_error("Connection failed", e)
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from Alpha Vantage API"""
        try:
            if self.session:
                await self.session.close()
                self.session = None
            
            self.is_connected = False
            self.logger.info("✅ Disconnected from Alpha Vantage")
            return True
            
        except Exception as e:
            self._log_error("Disconnect failed", e)
            return False
    
    async def test_connection(self) -> bool:
        """Test Alpha Vantage API connection"""
        try:
            if not self.session:
                return False
            
            # Test with a simple quote request
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': 'SPY',
                'apikey': self.api_key
            }
            
            async with self.session.get(self.base_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    # Check for successful response (not rate limited or error)
                    if 'Global Quote' in data:
                        return True
                    elif 'Information' in data and 'rate limit' in data['Information'].lower():
                        self._log_error("Rate limit exceeded during connection test")
                        return False
                    elif 'Error Message' in data:
                        self._log_error(f"API error: {data['Error Message']}")
                        return False
                    else:
                        return True  # Might be valid but different format
                else:
                    self._log_error(f"HTTP error {response.status}")
                    return False
                    
        except Exception as e:
            self._log_error("Connection test failed", e)
            return False
    
    async def get_quote(self, symbol: str) -> DataResponse:
        """Get real-time quote from Alpha Vantage"""
        try:
            await self._check_rate_limit()
            
            if not self.session:
                await self.connect()
            
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': symbol,
                'apikey': self.api_key
            }
            
            async with self.session.get(self.base_url, params=params) as response:
                self._track_request()
                
                if response.status == 429:
                    raise RateLimitError("Rate limit exceeded")
                
                if response.status != 200:
                    error_text = await response.text()
                    raise DataProviderError(f"API error {response.status}: {error_text}")
                
                data = await response.json()
                
                # Check for API-level errors
                if 'Information' in data and 'rate limit' in data['Information'].lower():
                    raise RateLimitError("API rate limit exceeded")
                
                if 'Error Message' in data:
                    raise DataProviderError(f"API error: {data['Error Message']}")
                
                # Parse global quote response
                global_quote = data.get('Global Quote', {})
                if not global_quote:
                    raise DataProviderError(f"No quote data available for {symbol}")
                
                # Alpha Vantage global quote format
                price = Decimal(str(global_quote.get('05. price', 0))) if global_quote.get('05. price') else None
                open_price = Decimal(str(global_quote.get('02. open', 0))) if global_quote.get('02. open') else None
                high = Decimal(str(global_quote.get('03. high', 0))) if global_quote.get('03. high') else None
                low = Decimal(str(global_quote.get('04. low', 0))) if global_quote.get('04. low') else None
                prev_close = Decimal(str(global_quote.get('08. previous close', 0))) if global_quote.get('08. previous close') else None
                change = Decimal(str(global_quote.get('09. change', 0))) if global_quote.get('09. change') else None
                change_percent = global_quote.get('10. change percent', '0%').replace('%', '')
                
                try:
                    change_percent = Decimal(str(change_percent)) if change_percent else None
                except:
                    change_percent = None
                
                volume = int(global_quote.get('06. volume', 0)) if global_quote.get('06. volume') else None
                latest_day = global_quote.get('07. latest trading day', '')
                
                quote = Quote(
                    symbol=symbol,
                    bid=None,  # Not available in global quote
                    ask=None,  # Not available in global quote
                    last=price,
                    mark=price,  # Use last price as mark
                    open_price=open_price,
                    high=high,
                    low=low,
                    close_price=prev_close,
                    change=change,
                    change_percent=change_percent,
                    volume=volume,
                    timestamp=datetime.now(),
                    market_hours=self._is_market_hours(),
                    source="alpha_vantage"
                )
                
                return DataResponse(
                    success=True,
                    data=quote,
                    source="alpha_vantage",
                    timestamp=datetime.now(),
                    latency_ms=None
                )
                
        except Exception as e:
            self._log_error(f"Failed to get quote for {symbol}", e)
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
        interval: str = "1d"
    ) -> DataResponse:
        """Get historical price data from Alpha Vantage"""
        try:
            await self._check_rate_limit()
            
            if not self.session:
                await self.connect()
            
            # Map interval to Alpha Vantage function
            function_map = {
                '1m': 'TIME_SERIES_INTRADAY',
                '5m': 'TIME_SERIES_INTRADAY', 
                '15m': 'TIME_SERIES_INTRADAY',
                '30m': 'TIME_SERIES_INTRADAY',
                '60m': 'TIME_SERIES_INTRADAY',
                '1d': 'TIME_SERIES_DAILY',
                '1w': 'TIME_SERIES_WEEKLY',
                '1mo': 'TIME_SERIES_MONTHLY'
            }
            
            function = function_map.get(interval, 'TIME_SERIES_DAILY')
            
            params = {
                'function': function,
                'symbol': symbol,
                'apikey': self.api_key,
                'outputsize': 'full'  # Get full history
            }
            
            # Add interval parameter for intraday data
            if function == 'TIME_SERIES_INTRADAY':
                interval_map = {
                    '1m': '1min',
                    '5m': '5min',
                    '15m': '15min',
                    '30m': '30min',
                    '60m': '60min'
                }
                params['interval'] = interval_map.get(interval, '1min')
            
            async with self.session.get(self.base_url, params=params) as response:
                self._track_request()
                
                if response.status == 429:
                    raise RateLimitError("Rate limit exceeded")
                
                if response.status != 200:
                    error_text = await response.text()
                    raise DataProviderError(f"API error {response.status}: {error_text}")
                
                data = await response.json()
                
                # Check for API-level errors
                if 'Information' in data and 'rate limit' in data['Information'].lower():
                    raise RateLimitError("API rate limit exceeded")
                
                if 'Error Message' in data:
                    raise DataProviderError(f"API error: {data['Error Message']}")
                
                # Parse time series data
                time_series_key = None
                for key in data.keys():
                    if 'Time Series' in key:
                        time_series_key = key
                        break
                
                if not time_series_key:
                    raise DataProviderError(f"No time series data found for {symbol}")
                
                time_series = data[time_series_key]
                bars = []
                
                for date_str, ohlcv in time_series.items():
                    try:
                        # Parse timestamp
                        if len(date_str) == 10:  # Daily format: YYYY-MM-DD
                            timestamp = datetime.strptime(date_str, '%Y-%m-%d')
                        else:  # Intraday format: YYYY-MM-DD HH:MM:SS
                            timestamp = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                        
                        # Filter by date range
                        if timestamp.date() < start_date or timestamp.date() > end_date:
                            continue
                        
                        bar = HistoricalBar(
                            symbol=symbol,
                            timestamp=timestamp,
                            open_price=Decimal(str(ohlcv.get('1. open', 0))),
                            high=Decimal(str(ohlcv.get('2. high', 0))),
                            low=Decimal(str(ohlcv.get('3. low', 0))),
                            close_price=Decimal(str(ohlcv.get('4. close', 0))),
                            volume=int(ohlcv.get('5. volume', 0)) if ohlcv.get('5. volume') else 0
                        )
                        bars.append(bar)
                        
                    except Exception as e:
                        self.logger.warning(f"Failed to parse bar data: {e}")
                        continue
                
                # Sort by timestamp
                bars.sort(key=lambda x: x.timestamp)
                
                return DataResponse(
                    success=True,
                    data=bars,
                    source="alpha_vantage",
                    timestamp=datetime.now()
                )
                
        except Exception as e:
            self._log_error(f"Failed to get historical data for {symbol}", e)
            return DataResponse(
                success=False,
                error=str(e),
                timestamp=datetime.now()
            )
    
    async def get_options_chain(
        self, 
        underlying: str,
        expiration: Optional[date] = None,
        strike_range: Optional[tuple[float, float]] = None
    ) -> DataResponse:
        """
        Alpha Vantage doesn't provide options data in free tier
        This method returns a not supported error
        """
        return DataResponse(
            success=False,
            error="Options data not available in Alpha Vantage free tier",
            timestamp=datetime.now()
        )
    
    def _is_market_hours(self) -> bool:
        """Check if it's currently market hours (rough approximation)"""
        now = datetime.now()
        # Rough check: Monday-Friday, 9:30 AM - 4:00 PM ET
        if now.weekday() >= 5:  # Weekend
            return False
        
        hour = now.hour
        return 9 <= hour <= 16  # Simplified market hours check
    
    async def _check_rate_limit(self):
        """Check and enforce rate limiting"""
        now = datetime.now()
        
        # Reset daily counter if it's a new day
        if now.date() > self.daily_reset_time.date():
            self.request_count_today = 0
            self.daily_reset_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Check daily limit
        if self.request_count_today >= self.daily_limit:
            raise RateLimitError(f"Daily request limit of {self.daily_limit} exceeded")
        
        # Check per-minute rate limit
        time_diff = (now - self.last_request_time).total_seconds()
        min_interval = 60 / self.rate_limit  # seconds between requests
        
        if time_diff < min_interval:
            sleep_time = min_interval - time_diff
            await asyncio.sleep(sleep_time)
        
        self.last_request_time = datetime.now()
    
    def _track_request(self):
        """Track API request for rate limiting"""
        super()._track_request()
        self.request_count_today += 1
        
        # Log request count for monitoring
        if self.request_count_today % 5 == 0:
            remaining = self.daily_limit - self.request_count_today
            self.logger.info(f"Alpha Vantage requests today: {self.request_count_today}/{self.daily_limit} (remaining: {remaining})")
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get provider information and limits"""
        return {
            "provider": "alpha_vantage",
            "rate_limit_per_minute": self.rate_limit,
            "daily_limit": self.daily_limit,
            "requests_today": self.request_count_today,
            "requests_remaining": self.daily_limit - self.request_count_today,
            "supports_options": False,
            "supports_real_time": True,
            "supports_historical": True,
            "data_quality": "delayed_15min_or_eod"
        }