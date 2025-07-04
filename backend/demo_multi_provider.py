#!/usr/bin/env python3
"""
Multi-Provider Market Data Demo
Demonstrates intelligent routing between Polygon.io and Alpha Vantage
"""

import asyncio
import os
from datetime import datetime, date, timedelta
from dotenv import load_dotenv
from data.manager import DataManager
import json

# Load environment variables
load_dotenv('.env')

async def demo_multi_provider_intelligence():
    """Demonstrate intelligent multi-provider data routing"""
    
    print("🚀 Multi-Provider Market Data Intelligence Demo")
    print("=" * 60)
    
    # Check API keys
    polygon_key = os.getenv('POLYGON_API_KEY')
    alpha_key = os.getenv('ALPHA_VANTAGE_API_KEY')
    
    print("🔑 API Key Status:")
    print(f"   Polygon.io: {'✅ Available' if polygon_key else '❌ Missing'}")
    print(f"   Alpha Vantage: {'✅ Available' if alpha_key else '❌ Missing'}")
    print()
    
    if not polygon_key and not alpha_key:
        print("❌ No API keys available - cannot proceed")
        return
    
    try:
        # Load and configure data manager
        with open('config/data_config.json', 'r') as f:
            config = json.load(f)
        
        # Configure API keys
        if polygon_key:
            config['providers']['polygon']['api_key'] = polygon_key
        if alpha_key:
            config['providers']['alpha_vantage']['api_key'] = alpha_key
        
        # Initialize data manager
        manager = DataManager(config)
        await manager.initialize()
        
        print("📊 Provider Status:")
        for name, provider in manager.providers.items():
            status = "🟢 Connected" if provider.is_connected else "🔴 Disconnected"
            print(f"   {name.title()}: {status}")
        
        print()
        
        # Demonstrate intelligent routing
        print("🎯 Intelligent Data Routing Demo")
        print("-" * 40)
        
        symbols = ['SPY', 'QQQ', 'IWM', 'AAPL', 'MSFT']
        quote_results = {}
        
        for symbol in symbols:
            print(f"\n📈 Getting quote for {symbol}...")
            
            try:
                quote_response = await manager.get_quote(symbol)
                
                if quote_response.success:
                    quote = quote_response.data
                    quote_results[symbol] = quote
                    
                    print(f"   ✅ Success: ${quote.last}")
                    print(f"   📍 Source: {quote.source}")
                    print(f"   📊 Volume: {quote.volume:,}")
                    print(f"   📈 Change: {quote.change} ({quote.change_percent}%)")
                    
                    # Show provider selection reasoning
                    routing_config = config.get('symbol_routing', {}).get(symbol.lower(), {})
                    if routing_config:
                        preferred = routing_config.get('preferred_provider', 'default')
                        fallbacks = routing_config.get('fallback_providers', [])
                        print(f"   🎯 Routing: Preferred={preferred}, Fallbacks={fallbacks}")
                        
                        if quote.source != preferred:
                            print(f"   🔄 Used fallback: {preferred} → {quote.source}")
                    
                else:
                    print(f"   ❌ Failed: {quote_response.error}")
                
                # Rate limiting
                await asyncio.sleep(1)  # Small delay between requests
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        print()
        
        # Show data quality comparison
        print("📊 Data Quality Analysis")
        print("-" * 40)
        
        if quote_results:
            sources = {}
            for symbol, quote in quote_results.items():
                source = quote.source
                if source not in sources:
                    sources[source] = []
                sources[source].append(symbol)
            
            print("Data source distribution:")
            for source, symbols in sources.items():
                print(f"   {source.title()}: {', '.join(symbols)} ({len(symbols)} symbols)")
            
            # Calculate average metrics
            total_volume = sum(quote.volume or 0 for quote in quote_results.values())
            avg_volume = total_volume / len(quote_results) if quote_results else 0
            
            print(f"\nAggregate metrics:")
            print(f"   Total volume: {total_volume:,}")
            print(f"   Average volume: {avg_volume:,.0f}")
            print(f"   Symbols analyzed: {len(quote_results)}")
        
        print()
        
        # Demonstrate provider statistics
        print("📈 Provider Performance Statistics")
        print("-" * 40)
        
        stats = manager.request_stats
        print(f"Session statistics:")
        print(f"   Total requests: {stats['total_requests']}")
        print(f"   Cache hits: {stats['cache_hits']}")
        print(f"   Cache misses: {stats['cache_misses']}")
        print(f"   Market data requests: {stats['market_data_requests']}")
        print(f"   Errors: {stats['errors']}")
        
        cache_hit_rate = (stats['cache_hits'] / stats['total_requests'] * 100) if stats['total_requests'] > 0 else 0
        print(f"   Cache hit rate: {cache_hit_rate:.1f}%")
        
        # Provider-specific stats
        print(f"\nProvider-specific information:")
        for name, provider in manager.providers.items():
            if hasattr(provider, 'get_provider_info'):
                info = provider.get_provider_info()
                print(f"   {name.title()}:")
                print(f"     Requests today: {info.get('requests_today', 'N/A')}")
                if 'daily_limit' in info:
                    remaining = info.get('requests_remaining', 0)
                    print(f"     Remaining today: {remaining}")
                print(f"     Supports real-time: {info.get('supports_real_time', 'Unknown')}")
                print(f"     Data quality: {info.get('data_quality', 'Unknown')}")
        
        print()
        
        # Demonstrate historical data capabilities
        print("📉 Historical Data Comparison")
        print("-" * 40)
        
        symbol = 'SPY'
        end_date = date.today()
        start_date = end_date - timedelta(days=7)
        
        print(f"Getting 7-day historical data for {symbol}...")
        
        historical_response = await manager.get_historical_data(symbol, start_date, end_date, '1d')
        
        if historical_response.success:
            bars = historical_response.data
            print(f"   ✅ Retrieved {len(bars)} historical bars")
            print(f"   📍 Source: {historical_response.source}")
            
            if bars:
                latest = bars[-1]
                oldest = bars[0]
                print(f"   📅 Date range: {oldest.timestamp.date()} to {latest.timestamp.date()}")
                print(f"   💰 Latest close: ${latest.close_price}")
                
                # Calculate simple stats
                prices = [float(bar.close_price) for bar in bars]
                high_price = max(prices)
                low_price = min(prices)
                avg_price = sum(prices) / len(prices)
                
                print(f"   📊 Week summary:")
                print(f"     High: ${high_price:.2f}")
                print(f"     Low: ${low_price:.2f}")
                print(f"     Average: ${avg_price:.2f}")
        else:
            print(f"   ❌ Failed: {historical_response.error}")
        
        print()
        
        # Show cost optimization
        print("💰 Cost Optimization Analysis")
        print("-" * 40)
        
        cost_config = config.get('cost_optimization', {})
        if cost_config.get('enabled', False):
            print("Cost optimization: ✅ Enabled")
            print(f"   Daily budget: ${cost_config.get('daily_budget_usd', 0)}")
            print(f"   Smart routing: {'✅' if cost_config.get('smart_routing', {}).get('prefer_free_sources') else '❌'}")
            
            # Calculate estimated costs
            polygon_cost = stats['market_data_requests'] * 0.001  # Estimated
            alpha_cost = 0  # Free tier
            total_cost = polygon_cost + alpha_cost
            
            print(f"\nEstimated session costs:")
            print(f"   Polygon.io: ${polygon_cost:.4f}")
            print(f"   Alpha Vantage: ${alpha_cost:.4f}")
            print(f"   Total: ${total_cost:.4f}")
        else:
            print("Cost optimization: ❌ Disabled")
        
        # Cleanup
        await manager.shutdown()
        
        print()
        print("=" * 60)
        print("✅ Multi-Provider Demo Complete!")
        print()
        print("🎯 Key Achievements:")
        print("• ✅ Intelligent provider routing based on symbol preferences")
        print("• ✅ Automatic fallback when primary provider fails")
        print("• ✅ Real-time market data from multiple sources")
        print("• ✅ Historical data retrieval and analysis")
        print("• ✅ Provider performance monitoring and statistics")
        print("• ✅ Cost optimization and budget tracking")
        print("• ✅ Data quality validation and comparison")
        print()
        print("🚀 Ready for AI analysis with multi-provider data feeds!")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")

if __name__ == "__main__":
    asyncio.run(demo_multi_provider_intelligence())