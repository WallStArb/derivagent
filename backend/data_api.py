"""
Data API Endpoints for Derivagent
FastAPI routes for market data, account data, and data management
"""

from fastapi import APIRouter, HTTPException, Depends, Query, status
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, date
from decimal import Decimal
import logging

from data.manager import DataManager
from data.models import (
    Quote, OptionsChain, HistoricalBar, Position, Account, Order,
    DataRequest, DataResponse, MarketDataType, OptionType
)
# from auth.middleware import get_current_user  # Uncomment when auth is integrated

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/data", tags=["market_data"])

# Global data manager instance (will be initialized in main.py)
data_manager: Optional[DataManager] = None

def get_data_manager() -> DataManager:
    """Get global data manager instance"""
    if data_manager is None:
        raise HTTPException(status_code=503, detail="Data manager not initialized")
    return data_manager

# Request/Response Models

class QuoteRequest(BaseModel):
    """Quote request model"""
    symbol: str = Field(..., description="Stock or option symbol")
    source_preference: Optional[str] = Field(None, description="Preferred data source")

class OptionsChainRequest(BaseModel):
    """Options chain request model"""
    underlying: str = Field(..., description="Underlying symbol")
    expiration: Optional[date] = Field(None, description="Specific expiration date")
    strike_min: Optional[float] = Field(None, description="Minimum strike price")
    strike_max: Optional[float] = Field(None, description="Maximum strike price")
    option_type: Optional[OptionType] = Field(None, description="Call or Put filter")
    source_preference: Optional[str] = Field(None, description="Preferred data source")

class HistoricalRequest(BaseModel):
    """Historical data request model"""
    symbol: str = Field(..., description="Symbol to retrieve")
    start_date: date = Field(..., description="Start date")
    end_date: date = Field(..., description="End date")
    interval: str = Field("1d", description="Data interval (1m, 5m, 1h, 1d, etc.)")
    source_preference: Optional[str] = Field(None, description="Preferred data source")

class MultiQuoteRequest(BaseModel):
    """Multiple quotes request"""
    symbols: List[str] = Field(..., description="List of symbols")
    source_preference: Optional[str] = Field(None, description="Preferred data source")

# Market Data Endpoints

@router.get("/quote/{symbol}")
async def get_quote(
    symbol: str,
    source: Optional[str] = Query(None, description="Preferred data source"),
    account_id: Optional[str] = Query(None, description="Account ID for broker-specific pricing"),
    # user: Dict[str, Any] = Depends(get_current_user)  # Uncomment when auth ready
):
    """
    Get real-time quote for a symbol
    
    Uses intelligent routing:
    - Broker API if account_id provided and available
    - Market data provider as fallback
    - Cached data when appropriate
    """
    try:
        manager = get_data_manager()
        
        response = await manager.get_quote(
            symbol=symbol.upper(),
            # user_id=user.get('id'),  # Uncomment when auth ready
            account_id=account_id,
            source_preference=source
        )
        
        if not response.success:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to get quote: {response.error}"
            )
        
        return {
            "success": True,
            "data": response.data,
            "source": response.source,
            "cached": response.cached,
            "timestamp": response.timestamp
        }
        
    except Exception as e:
        logger.error(f"Quote endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/quotes/batch")
async def get_multiple_quotes(
    request: MultiQuoteRequest,
    account_id: Optional[str] = Query(None, description="Account ID for broker-specific pricing"),
    # user: Dict[str, Any] = Depends(get_current_user)
):
    """Get quotes for multiple symbols efficiently"""
    try:
        manager = get_data_manager()
        
        # Process requests concurrently
        import asyncio
        tasks = []
        
        for symbol in request.symbols:
            task = manager.get_quote(
                symbol=symbol.upper(),
                # user_id=user.get('id'),
                account_id=account_id,
                source_preference=request.source_preference
            )
            tasks.append(task)
        
        # Wait for all quotes
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        results = {}
        errors = {}
        
        for i, response in enumerate(responses):
            symbol = request.symbols[i].upper()
            
            if isinstance(response, Exception):
                errors[symbol] = str(response)
            elif response.success:
                results[symbol] = {
                    "data": response.data,
                    "source": response.source,
                    "cached": response.cached,
                    "timestamp": response.timestamp
                }
            else:
                errors[symbol] = response.error
        
        return {
            "success": True,
            "quotes": results,
            "errors": errors,
            "total_requested": len(request.symbols),
            "successful": len(results),
            "failed": len(errors)
        }
        
    except Exception as e:
        logger.error(f"Batch quotes endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/options/{underlying}")
async def get_options_chain(
    underlying: str,
    expiration: Optional[date] = Query(None, description="Specific expiration date"),
    strike_min: Optional[float] = Query(None, description="Minimum strike price"),
    strike_max: Optional[float] = Query(None, description="Maximum strike price"),
    source: Optional[str] = Query(None, description="Preferred data source"),
    account_id: Optional[str] = Query(None, description="Account ID for broker-specific data"),
    # user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get options chain for underlying symbol
    
    Supports filtering by expiration and strike range
    """
    try:
        manager = get_data_manager()
        
        # Build strike range tuple if provided
        strike_range = None
        if strike_min is not None and strike_max is not None:
            strike_range = (strike_min, strike_max)
        
        response = await manager.get_options_chain(
            underlying=underlying.upper(),
            expiration=expiration,
            strike_range=strike_range,
            # user_id=user.get('id'),
            account_id=account_id,
            source_preference=source
        )
        
        if not response.success:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to get options chain: {response.error}"
            )
        
        return {
            "success": True,
            "data": response.data,
            "source": response.source,
            "cached": response.cached,
            "timestamp": response.timestamp
        }
        
    except Exception as e:
        logger.error(f"Options chain endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/historical/{symbol}")
async def get_historical_data(
    symbol: str,
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date (YYYY-MM-DD)"),
    interval: str = Query("1d", description="Data interval (1m, 5m, 1h, 1d)"),
    source: Optional[str] = Query(None, description="Preferred data source"),
    # user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get historical price data for symbol
    
    Supports multiple timeframes and date ranges
    """
    try:
        manager = get_data_manager()
        
        # Validate date range
        if start_date >= end_date:
            raise HTTPException(
                status_code=400,
                detail="Start date must be before end date"
            )
        
        # Validate interval
        valid_intervals = ['1m', '5m', '15m', '30m', '1h', '1d', '1w', '1mo']
        if interval not in valid_intervals:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid interval. Must be one of: {valid_intervals}"
            )
        
        response = await manager.get_historical_data(
            symbol=symbol.upper(),
            start_date=start_date,
            end_date=end_date,
            interval=interval,
            source_preference=source
        )
        
        if not response.success:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to get historical data: {response.error}"
            )
        
        return {
            "success": True,
            "data": response.data,
            "source": response.source,
            "cached": response.cached,
            "timestamp": response.timestamp,
            "bars_count": len(response.data) if response.data else 0
        }
        
    except Exception as e:
        logger.error(f"Historical data endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Account Data Endpoints (Broker-specific)

@router.get("/accounts/{broker}")
async def get_broker_accounts(
    broker: str,
    # user: Dict[str, Any] = Depends(get_current_user)
):
    """Get user's accounts from specific broker"""
    try:
        manager = get_data_manager()
        
        if broker not in manager.broker_providers:
            raise HTTPException(
                status_code=404,
                detail=f"Broker '{broker}' not supported or not configured"
            )
        
        provider = manager.broker_providers[broker]
        response = await provider.get_accounts()
        
        if not response.success:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to get accounts: {response.error}"
            )
        
        return {
            "success": True,
            "accounts": response.data,
            "broker": broker,
            "timestamp": response.timestamp
        }
        
    except Exception as e:
        logger.error(f"Accounts endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/positions/{broker}/{account_id}")
async def get_account_positions(
    broker: str,
    account_id: str,
    # user: Dict[str, Any] = Depends(get_current_user)
):
    """Get positions for specific account"""
    try:
        manager = get_data_manager()
        
        response = await manager.get_positions(account_id, broker)
        
        if not response.success:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to get positions: {response.error}"
            )
        
        return {
            "success": True,
            "positions": response.data,
            "account_id": account_id,
            "broker": broker,
            "timestamp": response.timestamp
        }
        
    except Exception as e:
        logger.error(f"Positions endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Data Management Endpoints

@router.get("/providers")
async def get_data_providers():
    """Get information about available data providers"""
    try:
        manager = get_data_manager()
        return manager.get_stats()
        
    except Exception as e:
        logger.error(f"Providers endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def get_data_health():
    """Get data layer health status"""
    try:
        manager = get_data_manager()
        return manager.get_health_status()
        
    except Exception as e:
        logger.error(f"Health endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_data_stats():
    """Get detailed data usage statistics"""
    try:
        manager = get_data_manager()
        stats = manager.get_stats()
        
        return {
            "success": True,
            "stats": stats,
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Stats endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Market Status and Utility Endpoints

@router.get("/market/status")
async def get_market_status():
    """Get current market status and trading hours"""
    try:
        # This could be enhanced to use provider-specific market status
        now = datetime.now()
        
        # Simple market hours check (NYSE/NASDAQ)
        # 9:30 AM - 4:00 PM ET on weekdays
        is_weekday = now.weekday() < 5
        hour = now.hour
        is_trading_hours = is_weekday and 9 <= hour < 16
        
        return {
            "market_open": is_trading_hours,
            "is_weekday": is_weekday,
            "current_time": now,
            "next_open": "Next trading day 9:30 AM ET" if not is_trading_hours else None,
            "timezone": "ET"
        }
        
    except Exception as e:
        logger.error(f"Market status endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/symbols/search")
async def search_symbols(
    query: str = Query(..., description="Symbol search query"),
    limit: int = Query(10, description="Maximum results to return")
):
    """Search for symbols (placeholder implementation)"""
    try:
        # This would integrate with provider symbol search APIs
        # For now, return a simple response
        
        query_upper = query.upper()
        
        # Mock some common symbols for demonstration
        mock_symbols = [
            {"symbol": "SPY", "name": "SPDR S&P 500 ETF", "type": "ETF"},
            {"symbol": "SPX", "name": "S&P 500 Index", "type": "INDEX"},
            {"symbol": "VIX", "name": "CBOE Volatility Index", "type": "INDEX"},
            {"symbol": "QQQ", "name": "Invesco QQQ ETF", "type": "ETF"},
            {"symbol": "IWM", "name": "iShares Russell 2000 ETF", "type": "ETF"}
        ]
        
        # Filter results based on query
        results = [
            symbol for symbol in mock_symbols
            if query_upper in symbol["symbol"] or query_upper in symbol["name"].upper()
        ][:limit]
        
        return {
            "success": True,
            "query": query,
            "results": results,
            "total": len(results)
        }
        
    except Exception as e:
        logger.error(f"Symbol search endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))