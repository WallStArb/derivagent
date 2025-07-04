"""
Polygon.io Market Data Provider
Implements real-time and historical market data via Polygon.io API
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


class PolygonProvider(MarketDataProvider):
    """
    Polygon.io market data provider
    
    Features:
    - Real-time quotes for stocks and options
    - Historical data with multiple timeframes
    - Options chains with Greeks
    - Market status and calendar data
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("polygon", config)
        
        self.api_key = config.get('api_key')
        if not self.api_key:
            raise ValueError("Polygon API key is required")
        
        self.base_url = "https://api.polygon.io"
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Rate limiting
        self.rate_limit = config.get('rate_limit', 5)  # requests per minute
        self.last_request_time = datetime.now()
        
    async def connect(self) -> bool:
        """Establish connection to Polygon API"""
        try:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "User-Agent": "Derivagent/1.0"
                }
            )
            
            # Test connection
            success = await self.test_connection()
            self.is_connected = success
            
            if success:
                self.logger.info("✅ Connected to Polygon.io")
            else:
                self.logger.error("❌ Failed to connect to Polygon.io")
                
            return success
            
        except Exception as e:
            self._log_error("Connection failed", e)
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from Polygon API"""
        try:
            if self.session:
                await self.session.close()
                self.session = None
            
            self.is_connected = False
            self.logger.info("✅ Disconnected from Polygon.io")
            return True
            
        except Exception as e:
            self._log_error("Disconnect failed", e)
            return False
    
    async def test_connection(self) -> bool:
        """Test Polygon API connection"""
        try:
            if not self.session:
                return False
            
            # Test with market status request (free tier compatible)
            url = f"{self.base_url}/v1/marketstatus/now"
            params = {'apikey': self.api_key}
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    # Market status endpoint doesn't return 'status'='OK', just check for valid response
                    return 'market' in data
                elif response.status == 401 or response.status == 403:
                    self._log_error("Invalid or insufficient API key permissions")
                    return False
                else:
                    error_text = await response.text()
                    self._log_error(f"API test failed with status {response.status}: {error_text}")
                    return False
                    
        except Exception as e:
            self._log_error("Connection test failed", e)
            return False
    
    async def get_quote(self, symbol: str) -> DataResponse:
        """Get quote from Polygon (uses daily aggregates for free tier)"""
        try:
            await self._check_rate_limit()
            
            if not self.session:
                await self.connect()
            
            # Use previous day's daily aggregate (free tier compatible)
            from datetime import date, timedelta
            yesterday = (date.today() - timedelta(days=1)).isoformat()
            url = f"{self.base_url}/v2/aggs/ticker/{symbol}/range/1/day/{yesterday}/{yesterday}"
            params = {'apikey': self.api_key}
            
            async with self.session.get(url, params=params) as response:
                self._track_request()
                
                if response.status == 429:
                    raise RateLimitError("Rate limit exceeded")
                
                if response.status != 200:
                    error_text = await response.text()
                    raise DataProviderError(f"API error {response.status}: {error_text}")
                
                data = await response.json()
                
                if data.get('status') != 'OK':
                    raise DataProviderError(f"API returned error: {data.get('error', 'Unknown error')}")
                
                # Parse daily aggregate response
                results = data.get('results', [])
                if not results:
                    raise DataProviderError(f"No data available for {symbol}")
                
                bar = results[0]  # Get the daily bar
                close_price = Decimal(str(bar.get('c', 0))) if bar.get('c') else None
                
                quote = Quote(
                    symbol=symbol,
                    bid=None,  # Not available in daily aggregates
                    ask=None,  # Not available in daily aggregates
                    last=close_price,
                    mark=close_price,  # Use close as mark price
                    open_price=Decimal(str(bar.get('o', 0))) if bar.get('o') else None,
                    high=Decimal(str(bar.get('h', 0))) if bar.get('h') else None,
                    low=Decimal(str(bar.get('l', 0))) if bar.get('l') else None,
                    close_price=close_price,
                    volume=bar.get('v'),
                    timestamp=datetime.now(),
                    market_hours=False,  # Historical data
                    source="polygon"
                )
                
                return DataResponse(
                    success=True,
                    data=quote,
                    source="polygon",
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
    
    async def _enrich_quote(self, quote: Quote, symbol: str):
        """Enrich quote with additional data"""
        try:
            # Get last trade
            url = f"{self.base_url}/v2/last/trade/{symbol}"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('status') == 'OK':
                        results = data.get('results', {})
                        quote.last = Decimal(str(results.get('p', 0))) if results.get('p') else None
            
            # Get daily bar for OHLC and volume
            today = date.today()
            url = f"{self.base_url}/v2/aggs/ticker/{symbol}/range/1/day/{today}/{today}"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('status') == 'OK' and data.get('results'):
                        bar = data['results'][0]
                        quote.open_price = Decimal(str(bar.get('o', 0))) if bar.get('o') else None
                        quote.high = Decimal(str(bar.get('h', 0))) if bar.get('h') else None
                        quote.low = Decimal(str(bar.get('l', 0))) if bar.get('l') else None
                        quote.close_price = Decimal(str(bar.get('c', 0))) if bar.get('c') else None
                        quote.volume = bar.get('v')
                        
                        # Calculate change
                        if quote.last and quote.close_price:
                            prev_close = quote.close_price
                            quote.change = quote.last - prev_close
                            if prev_close > 0:
                                quote.change_percent = (quote.change / prev_close) * 100
                                
        except Exception as e:
            self.logger.warning(f"Failed to enrich quote for {symbol}: {e}")
    
    async def get_options_chain(
        self, 
        underlying: str,
        expiration: Optional[date] = None,
        strike_range: Optional[tuple[float, float]] = None
    ) -> DataResponse:
        """Get options chain from Polygon"""
        try:
            await self._check_rate_limit()
            
            if not self.session:
                await self.connect()
            
            # Build request parameters
            params = {
                'underlying': underlying,
                'order': 'asc',
                'limit': 1000,
                'sort': 'strike_price'
            }
            
            if expiration:
                params['expiration_date'] = expiration.isoformat()
            
            if strike_range:
                params['strike_price.gte'] = strike_range[0]
                params['strike_price.lte'] = strike_range[1]
            
            url = f"{self.base_url}/v3/reference/options/contracts"
            
            async with self.session.get(url, params=params) as response:
                self._track_request()
                
                if response.status == 429:
                    raise RateLimitError("Rate limit exceeded")
                
                if response.status != 200:
                    error_text = await response.text()
                    raise DataProviderError(f"API error {response.status}: {error_text}")
                
                data = await response.json()
                
                if data.get('status') != 'OK':
                    raise DataProviderError(f"API returned error: {data.get('error', 'Unknown error')}")
                
                contracts = []
                results = data.get('results', [])
                
                for contract_data in results:
                    try:
                        contract = self._parse_option_contract(contract_data, underlying)
                        contracts.append(contract)
                    except Exception as e:
                        self.logger.warning(f"Failed to parse contract: {e}")
                        continue
                
                # Get quotes for contracts (limited to avoid rate limits)
                if len(contracts) <= 50:  # Only for small chains
                    await self._enrich_options_with_quotes(contracts)
                
                # Organize by expiration
                chain = OptionsChain(
                    underlying_symbol=underlying,
                    timestamp=datetime.now(),
                    source="polygon",
                    total_contracts=len(contracts)
                )
                
                for contract in contracts:
                    exp_str = contract.expiration_date.isoformat()
                    if exp_str not in chain.expirations:
                        chain.expirations[exp_str] = []
                    chain.expirations[exp_str].append(contract)
                
                return DataResponse(
                    success=True,
                    data=chain,
                    source="polygon",
                    timestamp=datetime.now()
                )
                
        except Exception as e:
            self._log_error(f"Failed to get options chain for {underlying}", e)
            return DataResponse(
                success=False,
                error=str(e),
                timestamp=datetime.now()
            )
    
    def _parse_option_contract(self, data: Dict[str, Any], underlying: str) -> OptionContract:
        """Parse Polygon option contract data"""
        
        # Extract contract details
        ticker = data.get('ticker', '')
        strike = Decimal(str(data.get('strike_price', 0)))
        expiration_str = data.get('expiration_date', '')
        contract_type = data.get('contract_type', '').lower()
        
        # Parse expiration date
        try:
            exp_date = datetime.strptime(expiration_str, '%Y-%m-%d').date()
        except:
            exp_date = date.today() + timedelta(days=30)  # Default fallback
        
        # Calculate days to expiration
        days_to_exp = (exp_date - date.today()).days
        
        return OptionContract(
            symbol=ticker,
            underlying_symbol=underlying,
            option_type=OptionType.CALL if contract_type == 'call' else OptionType.PUT,
            strike_price=strike,
            expiration_date=exp_date,
            days_to_expiration=days_to_exp,
            timestamp=datetime.now(),
            source="polygon"
        )
    
    async def _enrich_options_with_quotes(self, contracts: List[OptionContract]):
        """Add quote data to option contracts"""
        # Batch request quotes for efficiency
        tasks = []
        for contract in contracts[:10]:  # Limit to avoid rate limits
            task = self._get_option_quote(contract)
            tasks.append(task)
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _get_option_quote(self, contract: OptionContract):
        """Get quote for individual option contract"""
        try:
            url = f"{self.base_url}/v2/last/nbbo/{contract.symbol}"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('status') == 'OK':
                        results = data.get('results', {})
                        contract.bid = Decimal(str(results.get('bid', 0))) if results.get('bid') else None
                        contract.ask = Decimal(str(results.get('ask', 0))) if results.get('ask') else None
                        
        except Exception as e:
            self.logger.debug(f"Failed to get quote for {contract.symbol}: {e}")
    
    async def get_historical_data(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        interval: str = "1d"
    ) -> DataResponse:
        """Get historical price data from Polygon"""
        try:
            await self._check_rate_limit()
            
            if not self.session:
                await self.connect()
            
            # Map interval to Polygon format
            multiplier, timespan = self._parse_interval(interval)
            
            # Build URL
            url = f"{self.base_url}/v2/aggs/ticker/{symbol}/range/{multiplier}/{timespan}/{start_date}/{end_date}"
            
            params = {
                'adjusted': 'true',
                'sort': 'asc',
                'limit': 5000
            }
            
            async with self.session.get(url, params=params) as response:
                self._track_request()
                
                if response.status == 429:
                    raise RateLimitError("Rate limit exceeded")
                
                if response.status != 200:
                    error_text = await response.text()
                    raise DataProviderError(f"API error {response.status}: {error_text}")
                
                data = await response.json()
                
                if data.get('status') != 'OK':
                    raise DataProviderError(f"API returned error: {data.get('error', 'Unknown error')}")
                
                bars = []
                results = data.get('results', [])
                
                for bar_data in results:
                    bar = HistoricalBar(
                        symbol=symbol,
                        timestamp=datetime.fromtimestamp(bar_data['t'] / 1000),
                        open_price=Decimal(str(bar_data['o'])),
                        high=Decimal(str(bar_data['h'])),
                        low=Decimal(str(bar_data['l'])),
                        close_price=Decimal(str(bar_data['c'])),
                        volume=bar_data['v']
                    )
                    bars.append(bar)
                
                return DataResponse(
                    success=True,
                    data=bars,
                    source="polygon",
                    timestamp=datetime.now()
                )
                
        except Exception as e:
            self._log_error(f"Failed to get historical data for {symbol}", e)
            return DataResponse(
                success=False,
                error=str(e),
                timestamp=datetime.now()
            )
    
    def _parse_interval(self, interval: str) -> tuple[int, str]:
        """Parse interval string to Polygon format"""
        # Default mappings
        mappings = {
            '1m': (1, 'minute'),
            '5m': (5, 'minute'),
            '15m': (15, 'minute'),
            '30m': (30, 'minute'),
            '1h': (1, 'hour'),
            '1d': (1, 'day'),
            '1w': (1, 'week'),
            '1mo': (1, 'month')
        }
        
        return mappings.get(interval, (1, 'day'))
    
    async def _check_rate_limit(self):
        """Check and enforce rate limiting"""
        now = datetime.now()
        time_diff = (now - self.last_request_time).total_seconds()
        
        min_interval = 60 / self.rate_limit  # seconds between requests
        
        if time_diff < min_interval:
            sleep_time = min_interval - time_diff
            await asyncio.sleep(sleep_time)
        
        self.last_request_time = datetime.now()