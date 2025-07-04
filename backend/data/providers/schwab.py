"""
Charles Schwab/ThinkorSwim Broker Provider
Implements Schwab API for market data, account data, and trading
"""

import aiohttp
import asyncio
import base64
from typing import Optional, Dict, Any, List
from datetime import datetime, date, timedelta
from decimal import Decimal
import json
import urllib.parse

from .base import BrokerProvider, DataProviderError, AuthenticationError, RateLimitError
from ..models import (
    Quote, OptionsChain, OptionContract, HistoricalBar, Position, Account, Order,
    DataResponse, OptionType, OrderType, OrderSide, OrderStatus, PositionType
)


class SchwabProvider(BrokerProvider):
    """
    Charles Schwab broker provider
    
    Features:
    - OAuth 2.0 authentication
    - Real-time market data
    - Account information and positions
    - Options chains with Greeks
    - Order placement and management
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("schwab", config)
        
        self.client_id = config.get('client_id')
        self.client_secret = config.get('client_secret')
        self.redirect_uri = config.get('redirect_uri', 'https://localhost:8080/callback')
        
        if not self.client_id or not self.client_secret:
            raise ValueError("Schwab client_id and client_secret are required")
        
        self.base_url = "https://api.schwabapi.com"
        self.auth_url = "https://api.schwabapi.com/oauth/authorize"
        self.token_url = "https://api.schwabapi.com/oauth/token"
        
        self.session: Optional[aiohttp.ClientSession] = None
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None
        
        # Rate limiting - Schwab has generous limits
        self.rate_limit = 120  # requests per minute
        self.last_request_time = datetime.now()
        
    async def connect(self) -> bool:
        """Establish connection to Schwab API"""
        try:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={
                    "User-Agent": "Derivagent/1.0"
                }
            )
            
            # Check if we have valid credentials
            if self.access_token and await self._check_token_validity():
                self.is_connected = True
                self.logger.info("✅ Connected to Schwab API with existing token")
                return True
            
            # Need to authenticate
            self.logger.info("🔐 Schwab authentication required")
            return False
            
        except Exception as e:
            self._log_error("Connection failed", e)
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from Schwab API"""
        try:
            if self.session:
                await self.session.close()
                self.session = None
            
            self.is_connected = False
            self.access_token = None
            self.refresh_token = None
            self.token_expires_at = None
            
            self.logger.info("✅ Disconnected from Schwab API")
            return True
            
        except Exception as e:
            self._log_error("Disconnect failed", e)
            return False
    
    async def test_connection(self) -> bool:
        """Test Schwab API connection"""
        try:
            if not self.session or not self.access_token:
                return False
            
            # Test with accounts request
            headers = self._get_auth_headers()
            url = f"{self.base_url}/trader/v1/accounts"
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    return True
                elif response.status == 401:
                    # Token expired, try refresh
                    if await self.refresh_token():
                        return await self.test_connection()
                    return False
                else:
                    return False
                    
        except Exception as e:
            self._log_error("Connection test failed", e)
            return False
    
    async def authenticate(self, credentials: Dict[str, str]) -> bool:
        """
        Authenticate with Schwab using OAuth 2.0
        
        Args:
            credentials: Dict containing 'refresh_token' or 'auth_code'
        """
        try:
            if not self.session:
                await self.connect()
            
            if 'refresh_token' in credentials:
                # Use refresh token
                self.refresh_token = credentials['refresh_token']
                success = await self.refresh_token()
                if success:
                    self.is_connected = True
                return success
            
            elif 'auth_code' in credentials:
                # Exchange authorization code for tokens
                return await self._exchange_auth_code(credentials['auth_code'])
            
            else:
                raise AuthenticationError("No valid credentials provided")
                
        except Exception as e:
            self._log_error("Authentication failed", e)
            return False
    
    def get_auth_url(self) -> str:
        """Get OAuth authorization URL for user authentication"""
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code',
            'scope': 'api'
        }
        
        query_string = urllib.parse.urlencode(params)
        return f"{self.auth_url}?{query_string}"
    
    async def _exchange_auth_code(self, auth_code: str) -> bool:
        """Exchange authorization code for access/refresh tokens"""
        try:
            headers = {
                'Authorization': self._get_basic_auth_header(),
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            data = {
                'grant_type': 'authorization_code',
                'code': auth_code,
                'redirect_uri': self.redirect_uri
            }
            
            async with self.session.post(self.token_url, headers=headers, data=data) as response:
                if response.status == 200:
                    token_data = await response.json()
                    
                    self.access_token = token_data['access_token']
                    self.refresh_token = token_data['refresh_token']
                    expires_in = token_data.get('expires_in', 1800)  # 30 minutes default
                    self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                    
                    self.is_connected = True
                    self.logger.info("✅ Schwab authentication successful")
                    return True
                else:
                    error_text = await response.text()
                    raise AuthenticationError(f"Token exchange failed: {error_text}")
                    
        except Exception as e:
            self._log_error("Token exchange failed", e)
            return False
    
    async def refresh_token(self) -> bool:
        """Refresh access token using refresh token"""
        try:
            if not self.refresh_token:
                return False
            
            headers = {
                'Authorization': self._get_basic_auth_header(),
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            data = {
                'grant_type': 'refresh_token',
                'refresh_token': self.refresh_token
            }
            
            async with self.session.post(self.token_url, headers=headers, data=data) as response:
                if response.status == 200:
                    token_data = await response.json()
                    
                    self.access_token = token_data['access_token']
                    if 'refresh_token' in token_data:
                        self.refresh_token = token_data['refresh_token']
                    
                    expires_in = token_data.get('expires_in', 1800)
                    self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                    
                    self.logger.info("✅ Schwab token refreshed")
                    return True
                else:
                    error_text = await response.text()
                    self._log_error(f"Token refresh failed: {error_text}")
                    return False
                    
        except Exception as e:
            self._log_error("Token refresh failed", e)
            return False
    
    def _get_basic_auth_header(self) -> str:
        """Generate basic auth header for OAuth requests"""
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get headers with authorization for API requests"""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    async def _check_token_validity(self) -> bool:
        """Check if current token is still valid"""
        if not self.access_token or not self.token_expires_at:
            return False
        
        # Check if token expires within 5 minutes
        if datetime.now() + timedelta(minutes=5) >= self.token_expires_at:
            return await self.refresh_token()
        
        return True
    
    async def get_accounts(self) -> DataResponse:
        """Get list of user's Schwab accounts"""
        try:
            await self._ensure_authenticated()
            
            headers = self._get_auth_headers()
            url = f"{self.base_url}/trader/v1/accounts"
            
            async with self.session.get(url, headers=headers) as response:
                self._track_request()
                
                if response.status == 401:
                    if await self.refresh_token():
                        return await self.get_accounts()
                    raise AuthenticationError("Authentication failed")
                
                if response.status != 200:
                    error_text = await response.text()
                    raise DataProviderError(f"API error {response.status}: {error_text}")
                
                data = await response.json()
                
                accounts = []
                for account_data in data:
                    account = self._parse_account(account_data)
                    accounts.append(account)
                    self.connected_accounts.append(account.account_id)
                
                return DataResponse(
                    success=True,
                    data=accounts,
                    source="schwab",
                    timestamp=datetime.now()
                )
                
        except Exception as e:
            self._log_error("Failed to get accounts", e)
            return DataResponse(
                success=False,
                error=str(e),
                timestamp=datetime.now()
            )
    
    async def get_quote(self, symbol: str) -> DataResponse:
        """Get real-time quote from Schwab"""
        try:
            await self._ensure_authenticated()
            
            headers = self._get_auth_headers()
            url = f"{self.base_url}/marketdata/v1/quotes"
            params = {'symbols': symbol}
            
            async with self.session.get(url, headers=headers, params=params) as response:
                self._track_request()
                
                if response.status == 401:
                    if await self.refresh_token():
                        return await self.get_quote(symbol)
                    raise AuthenticationError("Authentication failed")
                
                if response.status != 200:
                    error_text = await response.text()
                    raise DataProviderError(f"API error {response.status}: {error_text}")
                
                data = await response.json()
                
                if symbol in data:
                    quote_data = data[symbol]
                    quote = self._parse_quote(quote_data, symbol)
                    
                    return DataResponse(
                        success=True,
                        data=quote,
                        source="schwab",
                        timestamp=datetime.now()
                    )
                else:
                    raise DataProviderError(f"No data for symbol {symbol}")
                
        except Exception as e:
            self._log_error(f"Failed to get quote for {symbol}", e)
            return DataResponse(
                success=False,
                error=str(e),
                timestamp=datetime.now()
            )
    
    def _parse_quote(self, data: Dict[str, Any], symbol: str) -> Quote:
        """Parse Schwab quote data"""
        return Quote(
            symbol=symbol,
            bid=Decimal(str(data.get('bidPrice', 0))) if data.get('bidPrice') else None,
            ask=Decimal(str(data.get('askPrice', 0))) if data.get('askPrice') else None,
            last=Decimal(str(data.get('lastPrice', 0))) if data.get('lastPrice') else None,
            mark=Decimal(str(data.get('mark', 0))) if data.get('mark') else None,
            bid_size=data.get('bidSize'),
            ask_size=data.get('askSize'),
            volume=data.get('totalVolume'),
            open_price=Decimal(str(data.get('openPrice', 0))) if data.get('openPrice') else None,
            high=Decimal(str(data.get('highPrice', 0))) if data.get('highPrice') else None,
            low=Decimal(str(data.get('lowPrice', 0))) if data.get('lowPrice') else None,
            close_price=Decimal(str(data.get('closePrice', 0))) if data.get('closePrice') else None,
            change=Decimal(str(data.get('netChange', 0))) if data.get('netChange') else None,
            change_percent=Decimal(str(data.get('netPercentChangeInDouble', 0))) if data.get('netPercentChangeInDouble') else None,
            timestamp=datetime.now(),
            market_hours=data.get('tradingHours', 'NORMAL') == 'NORMAL',
            source="schwab"
        )
    
    def _parse_account(self, data: Dict[str, Any]) -> Account:
        """Parse Schwab account data"""
        securitiesAccount = data.get('securitiesAccount', {})
        
        return Account(
            account_id=securitiesAccount.get('accountNumber', ''),
            broker="schwab",
            account_type=securitiesAccount.get('type', 'unknown'),
            total_value=Decimal(str(data.get('aggregatedBalance', {}).get('liquidationValue', 0))),
            cash_balance=Decimal(str(data.get('aggregatedBalance', {}).get('cashBalance', 0))),
            buying_power=Decimal(str(data.get('aggregatedBalance', {}).get('buyingPower', 0))),
            is_active=True,
            last_updated=datetime.now()
        )
    
    async def _ensure_authenticated(self):
        """Ensure we have valid authentication"""
        if not self.is_connected or not await self._check_token_validity():
            raise AuthenticationError("Not authenticated or token expired")
    
    # Placeholder implementations for remaining methods
    # These would be fully implemented based on Schwab API documentation
    
    async def get_options_chain(
        self, 
        underlying: str,
        expiration: Optional[date] = None,
        strike_range: Optional[tuple[float, float]] = None
    ) -> DataResponse:
        """Get options chain from Schwab - Implementation needed"""
        # TODO: Implement Schwab options chain API
        return DataResponse(
            success=False,
            error="Options chain not yet implemented for Schwab",
            timestamp=datetime.now()
        )
    
    async def get_historical_data(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        interval: str = "1d"
    ) -> DataResponse:
        """Get historical data from Schwab - Implementation needed"""
        # TODO: Implement Schwab historical data API
        return DataResponse(
            success=False,
            error="Historical data not yet implemented for Schwab",
            timestamp=datetime.now()
        )
    
    async def get_account_info(self, account_id: str) -> DataResponse:
        """Get detailed account information"""
        # TODO: Implement detailed account info
        return DataResponse(
            success=False,
            error="Account info not yet implemented",
            timestamp=datetime.now()
        )
    
    async def get_positions(self, account_id: str) -> DataResponse:
        """Get account positions"""
        # TODO: Implement positions retrieval
        return DataResponse(
            success=False,
            error="Positions not yet implemented",
            timestamp=datetime.now()
        )
    
    async def get_orders(self, account_id: str) -> DataResponse:
        """Get account orders"""
        # TODO: Implement orders retrieval
        return DataResponse(
            success=False,
            error="Orders not yet implemented",
            timestamp=datetime.now()
        )
    
    async def place_order(self, order_request: Dict[str, Any]) -> DataResponse:
        """Place trading order"""
        # TODO: Implement order placement
        return DataResponse(
            success=False,
            error="Order placement not yet implemented",
            timestamp=datetime.now()
        )