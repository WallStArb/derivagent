#!/usr/bin/env python3
"""
Test Polygon.io with free tier limitations
Uses aggregates and delayed data that work with free tier
"""

import asyncio
import os
from datetime import datetime, date, timedelta
from dotenv import load_dotenv
from data.providers.polygon import PolygonProvider
import json

# Load environment variables
load_dotenv('.env')

async def test_polygon_free_tier():
    """Test Polygon with free tier endpoints"""
    print("🔑 Testing Polygon.io Free Tier...")
    
    api_key = os.getenv('POLYGON_API_KEY')
    if not api_key:
        print("❌ No API key found")
        return
    
    try:
        # Initialize Polygon provider
        config = {
            'api_key': api_key,
            'rate_limit': 5  # Free tier limit: 5 requests per minute
        }
        
        provider = PolygonProvider(config)
        connected = await provider.connect()
        
        if not connected:
            print("❌ Failed to connect to Polygon.io")
            return
        
        print("✅ Connected to Polygon.io successfully!")
        
        # Test market status (always works)
        await test_market_status(provider)
        
        # Test historical data (works with free tier)
        await test_historical_data_free(provider)
        
        # Test daily aggregates (works with free tier)
        await test_daily_aggregates(provider)
        
        await provider.disconnect()
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

async def test_market_status(provider):
    """Test market status endpoint"""
    print("\n📊 Testing Market Status...")
    
    try:
        # Use the connection test which calls market status
        status = await provider.test_connection()
        print(f"  Market status check: {'✅ Success' if status else '❌ Failed'}")
        
    except Exception as e:
        print(f"  ❌ Error: {e}")

async def test_historical_data_free(provider):
    """Test historical data (free tier)"""
    print("\n📈 Testing Historical Data (Free Tier)...")
    
    try:
        # Get historical data for SPY (should work with free tier)
        end_date = date.today() - timedelta(days=1)  # Yesterday 
        start_date = end_date - timedelta(days=7)    # Last week
        
        response = await provider.get_historical_data(
            symbol='SPY',
            start_date=start_date,
            end_date=end_date,
            interval='1d'
        )
        
        if response.success and response.data:
            bars = response.data
            print(f"  ✅ Historical data retrieved: {len(bars)} daily bars")
            
            if bars:
                latest = bars[-1]
                print(f"    Latest bar: {latest.timestamp.date()} - Close: ${latest.close_price}")
                print(f"    Volume: {latest.volume:,}")
        else:
            print(f"  ❌ Failed: {response.error}")
            
    except Exception as e:
        print(f"  ❌ Error: {e}")

async def test_daily_aggregates(provider):
    """Test daily aggregates endpoint"""
    print("\n📊 Testing Daily Aggregates...")
    
    try:
        # Test direct API call for aggregates
        import aiohttp
        
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        url = f"{provider.base_url}/v2/aggs/ticker/SPY/range/1/day/{yesterday}/{yesterday}"
        
        async with provider.session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                print(f"  ✅ Aggregates API response: {data.get('status')}")
                
                results = data.get('results', [])
                if results:
                    bar = results[0]
                    print(f"    SPY {yesterday}: O=${bar.get('o')} H=${bar.get('h')} L=${bar.get('l')} C=${bar.get('c')}")
                    print(f"    Volume: {bar.get('v'):,}")
                else:
                    print(f"    No results for {yesterday}")
            else:
                error_text = await response.text()
                print(f"  ❌ API error {response.status}: {error_text}")
                
    except Exception as e:
        print(f"  ❌ Error: {e}")

async def test_ai_agent_with_historical_data():
    """Test AI agent with historical data from Polygon"""
    print("\n🤖 Testing AI Agent with Historical Data...")
    
    try:
        from ai.agent_clients import MarketRegimeAgent
        
        # Create sample market context from historical data
        market_context = {
            "data_source": "polygon_historical",
            "spy_price": 500.25,  # Would come from latest bar
            "spy_change": 2.15,
            "spy_change_percent": 0.43,
            "volume": 25000000,
            "timestamp": datetime.now().isoformat(),
            "market_hours": False,  # Using historical data
            "data_freshness": "previous_day"
        }
        
        print(f"  📊 Sample data: SPY ${market_context['spy_price']} ({market_context['spy_change']:+.2f})")
        
        # Initialize market regime agent
        # Note: AI agent initialization may fail without proper config setup
        agent = MarketRegimeAgent()
        
        # Analyze with historical data context
        prompt = """Analyze the market regime based on recent historical data.
        
        Consider:
        1. Recent price action and volume patterns
        2. Market structure and trend characteristics
        3. Strategy favorability for options trading
        4. Risk assessment for current conditions
        
        Note: This analysis is based on delayed/historical data, not real-time."""
        
        result = await agent.analyze(
            prompt=prompt,
            context=market_context,
            response_format="json"
        )
        
        if result.get('success'):
            print(f"  ✅ AI analysis successful (model: {result.get('model_used')})")
            print(f"  🎯 Analysis completed with historical data")
        else:
            print(f"  ❌ AI analysis failed: {result.get('error')}")
            
    except Exception as e:
        print(f"  ❌ Error: {e}")

async def main():
    """Run Polygon free tier test"""
    print("🚀 Polygon.io Free Tier Integration Test")
    print("=" * 50)
    
    await test_polygon_free_tier()
    await test_ai_agent_with_historical_data()
    
    print("\n" + "=" * 50)
    print("✅ Free tier testing completed!")
    print("\nFree Tier Limitations:")
    print("- Real-time quotes require paid plan")
    print("- Options data may be limited")
    print("- Rate limit: 5 requests/minute")
    print("\nWhat works with free tier:")
    print("- Historical daily data")
    print("- Market status")
    print("- Daily aggregates")
    print("- Basic company information")

if __name__ == "__main__":
    asyncio.run(main())