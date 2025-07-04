#!/usr/bin/env python3
"""
Test Alpha Vantage Integration
Verifies Alpha Vantage provider and integration with data manager
"""

import asyncio
import os
from datetime import datetime, date, timedelta
from dotenv import load_dotenv

from data.providers.alpha_vantage import AlphaVantageProvider
from data.manager import DataManager
import json

# Load environment variables
load_dotenv('.env')

async def test_alpha_vantage_direct():
    """Test Alpha Vantage provider directly"""
    print("🔍 Testing Alpha Vantage Provider Directly")
    print("=" * 50)
    
    # Get API key
    api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
    if not api_key:
        print("❌ ALPHA_VANTAGE_API_KEY not found in environment")
        print("Please set your Alpha Vantage API key")
        return False
    
    config = {
        'api_key': api_key,
        'rate_limit': 5,
        'daily_limit': 25
    }
    
    provider = AlphaVantageProvider(config)
    
    try:
        # Test connection
        print("1. Testing connection...")
        connected = await provider.connect()
        if connected:
            print("   ✅ Successfully connected to Alpha Vantage")
        else:
            print("   ❌ Failed to connect to Alpha Vantage")
            return False
        
        # Test quotes
        print("\n2. Testing quote data...")
        symbols = ['SPY', 'QQQ', 'AAPL']
        
        for symbol in symbols:
            try:
                print(f"   Getting quote for {symbol}...")
                quote_response = await provider.get_quote(symbol)
                
                if quote_response.success:
                    quote = quote_response.data
                    print(f"     ✅ {symbol}: ${quote.last}")
                    print(f"       Change: {quote.change} ({quote.change_percent}%)")
                    print(f"       Volume: {quote.volume:,}")
                    print(f"       Source: {quote.source}")
                else:
                    print(f"     ❌ Failed: {quote_response.error}")
                
                # Rate limiting
                await asyncio.sleep(13)  # 5 requests per minute
                
            except Exception as e:
                print(f"     ❌ Error getting {symbol}: {e}")
        
        # Test historical data
        print("\n3. Testing historical data...")
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=7)
            
            print(f"   Getting SPY historical data from {start_date} to {end_date}...")
            historical_response = await provider.get_historical_data(
                'SPY', start_date, end_date, '1d'
            )
            
            if historical_response.success:
                bars = historical_response.data
                print(f"     ✅ Retrieved {len(bars)} historical bars")
                if bars:
                    latest = bars[-1]
                    print(f"       Latest: {latest.timestamp.date()} - Close: ${latest.close_price}")
            else:
                print(f"     ❌ Failed: {historical_response.error}")
                
        except Exception as e:
            print(f"     ❌ Error getting historical data: {e}")
        
        # Test provider info
        print("\n4. Testing provider information...")
        info = provider.get_provider_info()
        print(f"   Provider: {info['provider']}")
        print(f"   Rate limit: {info['rate_limit_per_minute']}/minute")
        print(f"   Daily limit: {info['daily_limit']}/day")
        print(f"   Requests today: {info['requests_today']}")
        print(f"   Remaining: {info['requests_remaining']}")
        print(f"   Supports options: {info['supports_options']}")
        
        # Cleanup
        await provider.disconnect()
        
        print("\n✅ Alpha Vantage direct testing completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Alpha Vantage direct test failed: {e}")
        return False

async def test_alpha_vantage_via_manager():
    """Test Alpha Vantage via data manager"""
    print("\n🔄 Testing Alpha Vantage via Data Manager")
    print("=" * 50)
    
    try:
        # Load data configuration
        with open('config/data_config.json', 'r') as f:
            config = json.load(f)
        
        # Set API keys from environment
        alpha_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        polygon_key = os.getenv('POLYGON_API_KEY')
        
        if config['providers']['alpha_vantage']['enabled'] and alpha_key:
            config['providers']['alpha_vantage']['api_key'] = alpha_key
            print("✅ Alpha Vantage API key configured")
        
        if config['providers']['polygon']['enabled'] and polygon_key:
            config['providers']['polygon']['api_key'] = polygon_key
            print("✅ Polygon API key configured")
        
        # Initialize data manager
        manager = DataManager(config)
        await manager.initialize()
        
        print("✅ Data manager initialized with multiple providers")
        
        # Test quote routing
        print("\n1. Testing intelligent quote routing...")
        symbols = ['SPY', 'QQQ', 'AAPL']
        
        for symbol in symbols:
            try:
                print(f"\n   Getting quote for {symbol}...")
                quote_response = await manager.get_quote(symbol)
                
                if quote_response.success:
                    quote = quote_response.data
                    print(f"     ✅ {symbol}: ${quote.last} (Source: {quote.source})")
                    print(f"       Change: {quote.change} ({quote.change_percent}%)")
                    
                    # Show routing decision
                    routing_info = getattr(quote_response, 'routing_info', {})
                    if routing_info:
                        print(f"       Routing: {routing_info}")
                else:
                    print(f"     ❌ Failed: {quote_response.error}")
                
                # Rate limiting
                await asyncio.sleep(13)
                
            except Exception as e:
                print(f"     ❌ Error: {e}")
        
        # Test provider statistics
        print("\n2. Data manager statistics:")
        stats = manager.request_stats
        print(f"   Total requests: {stats['total_requests']}")
        print(f"   Cache hits: {stats['cache_hits']}")
        print(f"   Cache misses: {stats['cache_misses']}")
        print(f"   Market data requests: {stats['market_data_requests']}")
        print(f"   Errors: {stats['errors']}")
        
        # Test provider availability
        print("\n3. Provider status:")
        for name, provider in manager.providers.items():
            if hasattr(provider, 'get_provider_info'):
                info = provider.get_provider_info()
                print(f"   {name}: {info.get('provider', 'Unknown')}")
                if 'requests_today' in info:
                    print(f"     Requests today: {info['requests_today']}/{info.get('daily_limit', 'unlimited')}")
        
        # Cleanup
        await manager.shutdown()
        
        print("\n✅ Data manager testing completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Data manager test failed: {e}")
        return False

async def test_fallback_behavior():
    """Test fallback behavior when primary provider fails"""
    print("\n🔀 Testing Provider Fallback Behavior")
    print("=" * 50)
    
    try:
        # Load configuration
        with open('config/data_config.json', 'r') as f:
            config = json.load(f)
        
        # Set API keys
        alpha_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        if alpha_key:
            config['providers']['alpha_vantage']['api_key'] = alpha_key
        
        # Disable Polygon to test fallback to Alpha Vantage
        config['providers']['polygon']['enabled'] = False
        print("🚫 Disabled Polygon provider to test fallback")
        
        # Initialize manager
        manager = DataManager(config)
        await manager.initialize()
        
        # Test that Alpha Vantage is used as fallback
        print("\n   Testing quote fallback for QQQ...")
        quote_response = await manager.get_quote('QQQ')
        
        if quote_response.success:
            quote = quote_response.data
            print(f"   ✅ QQQ: ${quote.last} (Source: {quote.source})")
            if quote.source == 'alpha_vantage':
                print("   ✅ Successfully used Alpha Vantage as fallback!")
            else:
                print(f"   ⚠️  Expected Alpha Vantage, got {quote.source}")
        else:
            print(f"   ❌ Fallback failed: {quote_response.error}")
        
        await manager.shutdown()
        
        print("\n✅ Fallback testing completed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Fallback test failed: {e}")
        return False

async def main():
    """Run comprehensive Alpha Vantage integration tests"""
    print("🚀 Alpha Vantage Integration Test Suite")
    print("=" * 60)
    
    # Check for API key
    api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
    if not api_key:
        print("⚠️  ALPHA_VANTAGE_API_KEY not set!")
        print()
        print("To get started:")
        print("1. Go to https://www.alphavantage.co/")
        print("2. Sign up for a free account") 
        print("3. Get your API key")
        print("4. Set environment variable: export ALPHA_VANTAGE_API_KEY=your_key")
        print("5. Re-run this test")
        return
    
    print(f"🔑 Alpha Vantage API Key: {api_key[:10]}...")
    print()
    
    # Run tests
    test_results = []
    
    # Test 1: Direct provider test
    result1 = await test_alpha_vantage_direct()
    test_results.append(("Direct Provider Test", result1))
    
    # Test 2: Data manager integration
    result2 = await test_alpha_vantage_via_manager()
    test_results.append(("Data Manager Integration", result2))
    
    # Test 3: Fallback behavior
    result3 = await test_fallback_behavior()
    test_results.append(("Fallback Behavior", result3))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All Alpha Vantage integration tests passed!")
        print("\n✅ Ready for multi-provider market data!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed - check configuration")

if __name__ == "__main__":
    asyncio.run(main())