#!/usr/bin/env python3
"""
Live Polygon.io Integration Test
Test real market data and connect to AI agents
"""

import asyncio
import os
from datetime import datetime, date, timedelta
from dotenv import load_dotenv
from data.providers.polygon import PolygonProvider
from data.manager import DataManager
from ai.agent_clients import MarketRegimeAgent, VolatilitySurfaceAgent
import json

# Load environment variables
load_dotenv('.env')


async def test_polygon_with_real_key():
    """Test Polygon with actual API key"""
    print("🔑 Testing Polygon.io with API key...")
    
    # Get API key from environment
    api_key = os.getenv('POLYGON_API_KEY')
    if not api_key or api_key == 'your-polygon-key':
        print("❌ Please set POLYGON_API_KEY environment variable")
        print("   You can get a free key at: https://polygon.io/")
        return False
    
    try:
        # Initialize Polygon provider
        config = {
            'api_key': api_key,
            'rate_limit': 5  # Free tier limit
        }
        
        provider = PolygonProvider(config)
        connected = await provider.connect()
        
        if not connected:
            print("❌ Failed to connect to Polygon.io")
            return False
        
        print("✅ Connected to Polygon.io successfully!")
        
        # Test real market data
        await test_live_quotes(provider)
        await test_live_options(provider)
        await test_historical_data(provider)
        
        await provider.disconnect()
        return True
        
    except Exception as e:
        print(f"❌ Polygon test failed: {e}")
        return False


async def test_live_quotes(provider):
    """Test live quote data"""
    print("\n📊 Testing Live Quotes...")
    
    symbols = ['SPY', 'QQQ', 'IWM', 'VIX']
    
    for symbol in symbols:
        try:
            response = await provider.get_quote(symbol)
            
            if response.success and response.data:
                quote = response.data
                print(f"  {symbol}: ${quote.last} (bid: ${quote.bid}, ask: ${quote.ask})")
                if quote.change:
                    change_str = f"+{quote.change}" if quote.change > 0 else str(quote.change)
                    print(f"    Change: {change_str} ({quote.change_percent:.2f}%)")
            else:
                print(f"  ❌ Failed to get quote for {symbol}: {response.error}")
                
        except Exception as e:
            print(f"  ❌ Error getting quote for {symbol}: {e}")


async def test_live_options(provider):
    """Test live options data"""
    print("\n📈 Testing Live Options Data...")
    
    try:
        # Get SPY options chain for near-term expiration
        today = date.today()
        # Find next Friday (typical option expiration)
        days_ahead = 4 - today.weekday()  # Friday is weekday 4
        if days_ahead <= 0:
            days_ahead += 7
        next_friday = today + timedelta(days=days_ahead)
        
        response = await provider.get_options_chain(
            underlying='SPY',
            expiration=next_friday
        )
        
        if response.success and response.data:
            chain = response.data
            print(f"  ✅ SPY options chain retrieved")
            print(f"    Total contracts: {chain.total_contracts}")
            print(f"    Expirations: {len(chain.expirations)}")
            
            # Show some sample contracts
            for exp_date, contracts in list(chain.expirations.items())[:1]:
                print(f"    Expiration {exp_date}: {len(contracts)} contracts")
                
                # Show calls and puts near the money
                calls = [c for c in contracts if c.option_type.value == 'call']
                puts = [c for c in contracts if c.option_type.value == 'put']
                
                if calls:
                    print(f"      Sample call: {calls[0].symbol} strike ${calls[0].strike_price}")
                if puts:
                    print(f"      Sample put: {puts[0].symbol} strike ${puts[0].strike_price}")
        else:
            print(f"  ❌ Failed to get options chain: {response.error}")
            
    except Exception as e:
        print(f"  ❌ Error getting options data: {e}")


async def test_historical_data(provider):
    """Test historical data"""
    print("\n📉 Testing Historical Data...")
    
    try:
        # Get last 30 days of SPY data
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        
        response = await provider.get_historical_data(
            symbol='SPY',
            start_date=start_date,
            end_date=end_date,
            interval='1d'
        )
        
        if response.success and response.data:
            bars = response.data
            print(f"  ✅ Historical data retrieved: {len(bars)} bars")
            
            if bars:
                latest = bars[-1]
                oldest = bars[0]
                print(f"    Latest: {latest.timestamp.date()} - Close: ${latest.close_price}")
                print(f"    Oldest: {oldest.timestamp.date()} - Close: ${oldest.close_price}")
                
                # Calculate simple statistics
                prices = [float(bar.close_price) for bar in bars]
                avg_price = sum(prices) / len(prices)
                print(f"    30-day average: ${avg_price:.2f}")
        else:
            print(f"  ❌ Failed to get historical data: {response.error}")
            
    except Exception as e:
        print(f"  ❌ Error getting historical data: {e}")


async def test_ai_agents_with_live_data():
    """Test AI agents with live Polygon data"""
    print("\n🤖 Testing AI Agents with Live Data...")
    
    try:
        # Load data configuration
        with open('config/data_config.json', 'r') as f:
            config = json.load(f)
        
        # Set API key from environment
        api_key = os.getenv('POLYGON_API_KEY')
        if config['providers']['polygon']['enabled'] and api_key:
            config['providers']['polygon']['api_key'] = api_key
        
        # Initialize data manager
        manager = DataManager(config)
        await manager.initialize()
        
        print("  ✅ Data manager initialized with Polygon")
        
        # Test market regime agent with live data
        await test_market_regime_with_live_data(manager)
        
        # Test volatility surface agent with live data
        await test_volatility_surface_with_live_data(manager)
        
        await manager.shutdown()
        
    except Exception as e:
        print(f"  ❌ AI agent test failed: {e}")


async def test_market_regime_with_live_data(manager):
    """Test market regime agent with live market data"""
    print("\n  📊 Market Regime Agent + Live Data:")
    
    try:
        # Get live market data
        spy_quote = await manager.get_quote('SPY')
        vix_quote = await manager.get_quote('VIX')
        
        if spy_quote.success and vix_quote.success:
            # Prepare context with live data
            market_context = {
                "spy_price": float(spy_quote.data.last) if spy_quote.data.last else 500,
                "spy_change": float(spy_quote.data.change) if spy_quote.data.change else 0,
                "spy_change_percent": float(spy_quote.data.change_percent) if spy_quote.data.change_percent else 0,
                "vix_level": float(vix_quote.data.last) if vix_quote.data.last else 16,
                "vix_change": float(vix_quote.data.change) if vix_quote.data.change else 0,
                "timestamp": datetime.now().isoformat(),
                "market_hours": spy_quote.data.market_hours if spy_quote.data else True
            }
            
            print(f"    Live Data: SPY ${market_context['spy_price']:.2f} ({market_context['spy_change_percent']:+.2f}%)")
            print(f"               VIX {market_context['vix_level']:.2f} ({market_context['vix_change']:+.2f})")
            
            # Initialize market regime agent
            agent = MarketRegimeAgent()
            
            # Analyze with live data
            prompt = """Analyze the current market regime based on live market data. 
            
            Consider:
            1. VIX level and market volatility state
            2. SPY price action and trend characteristics  
            3. Market favorability for options strategies
            4. Risk assessment for derivatives trading
            
            Provide specific strategy recommendations based on current conditions."""
            
            result = await agent.analyze(
                prompt=prompt,
                context=market_context,
                response_format="json"
            )
            
            if result.get('success'):
                print(f"    ✅ Agent analysis successful (model: {result.get('model_used')})")
                
                # Try to parse regime data
                if 'regime' in str(result.get('data', {})):
                    print(f"    🎯 Market regime analysis provided")
                else:
                    print(f"    📊 Market analysis completed")
            else:
                print(f"    ❌ Agent analysis failed: {result.get('error')}")
                
        else:
            print("    ⚠️ Live data not available, using sample data")
            
    except Exception as e:
        print(f"    ❌ Market regime test error: {e}")


async def test_volatility_surface_with_live_data(manager):
    """Test volatility surface agent with live options data"""
    print("\n  📈 Volatility Surface Agent + Live Data:")
    
    try:
        # Get live options data
        options_response = await manager.get_options_chain('SPY')
        
        if options_response.success and options_response.data:
            chain = options_response.data
            
            # Prepare options context
            options_context = {
                "underlying": "SPY",
                "underlying_price": 500,  # Would get from quote
                "total_contracts": chain.total_contracts,
                "expirations_count": len(chain.expirations),
                "data_source": options_response.source,
                "timestamp": datetime.now().isoformat()
            }
            
            print(f"    Live Data: {chain.total_contracts} contracts, {len(chain.expirations)} expirations")
            
            # Initialize volatility surface agent
            agent = VolatilitySurfaceAgent()
            
            prompt = """Analyze the options volatility environment based on live options chain data.
            
            Focus on:
            1. Implied volatility levels and relative ranking
            2. Term structure patterns across expirations
            3. Volatility skew characteristics
            4. Premium selling/buying opportunities
            
            Provide specific strategy recommendations."""
            
            result = await agent.analyze(
                prompt=prompt,
                context=options_context,
                response_format="json"
            )
            
            if result.get('success'):
                print(f"    ✅ Volatility analysis successful (model: {result.get('model_used')})")
                print(f"    📊 Options analysis completed")
            else:
                print(f"    ❌ Volatility analysis failed: {result.get('error')}")
                
        else:
            print("    ⚠️ Live options data not available")
            
    except Exception as e:
        print(f"    ❌ Volatility surface test error: {e}")


async def main():
    """Run comprehensive Polygon + AI integration test"""
    print("🚀 Polygon.io + AI Agents Integration Test")
    print("=" * 60)
    
    # Check for API key
    api_key = os.getenv('POLYGON_API_KEY')
    if not api_key or api_key == 'your-polygon-key':
        print("⚠️  POLYGON_API_KEY not set!")
        print()
        print("To get started:")
        print("1. Go to https://polygon.io/")
        print("2. Sign up for a free account")
        print("3. Get your API key")
        print("4. Set environment variable: export POLYGON_API_KEY=your_key")
        print("5. Re-run this test")
        return
    
    # Test basic Polygon functionality
    polygon_success = await test_polygon_with_real_key()
    
    if polygon_success:
        # Test AI agents with live data
        await test_ai_agents_with_live_data()
    
    print("\n" + "=" * 60)
    print("✅ Integration test completed!")
    print("\nNext steps:")
    print("1. Verify AI agents receive live market data")
    print("2. Test options strategies with real chains")
    print("3. Set up real-time WebSocket feeds")
    print("4. Connect to frontend dashboard")


if __name__ == "__main__":
    asyncio.run(main())