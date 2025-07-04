#!/usr/bin/env python3
"""
Demo: Live Data Integration with Polygon.io
Shows real market data feeding into AI analysis context
"""

import asyncio
import os
from datetime import datetime, date, timedelta
from dotenv import load_dotenv
from data.providers.polygon import PolygonProvider

# Load environment variables
load_dotenv('.env')

async def demo_live_data_integration():
    """Demonstrate live data integration"""
    print("🚀 Derivagent Live Data Integration Demo")
    print("=" * 55)
    
    # Initialize Polygon provider
    api_key = os.getenv('POLYGON_API_KEY')
    if not api_key:
        print("❌ POLYGON_API_KEY not found in .env file")
        return
    
    config = {
        'api_key': api_key,
        'rate_limit': 5
    }
    
    provider = PolygonProvider(config)
    
    try:
        # Connect to Polygon
        connected = await provider.connect()
        if not connected:
            print("❌ Failed to connect to Polygon.io")
            return
        
        print("✅ Connected to Polygon.io API")
        print()
        
        # Get real market data for key symbols
        symbols = ['SPY', 'QQQ', 'IWM']
        market_data = {}
        
        print("📊 Fetching Market Data...")
        for symbol in symbols:
            print(f"  Getting {symbol} data...")
            
            # Get quote (previous day's data with free tier)
            quote_response = await provider.get_quote(symbol)
            if quote_response.success:
                quote = quote_response.data
                market_data[symbol] = {
                    'price': float(quote.last) if quote.last else 0,
                    'open': float(quote.open_price) if quote.open_price else 0,
                    'high': float(quote.high) if quote.high else 0,
                    'low': float(quote.low) if quote.low else 0,
                    'volume': quote.volume or 0,
                    'source': quote.source
                }
                
                print(f"    ✅ {symbol}: ${quote.last} (Vol: {quote.volume:,})")
            else:
                print(f"    ❌ Failed to get {symbol}: {quote_response.error}")
            
            # Rate limiting for free tier
            await asyncio.sleep(12)  # 5 requests/minute = 1 request/12 seconds
        
        print()
        
        # Show market intelligence context
        if market_data:
            print("🎯 Market Intelligence Context:")
            print("─" * 40)
            
            spy_data = market_data.get('SPY', {})
            if spy_data:
                print(f"📈 SPY (S&P 500 ETF):")
                print(f"   Price: ${spy_data['price']:.2f}")
                print(f"   Range: ${spy_data['low']:.2f} - ${spy_data['high']:.2f}")
                print(f"   Volume: {spy_data['volume']:,} shares")
                
                # Calculate daily range
                if spy_data['high'] and spy_data['low']:
                    daily_range = spy_data['high'] - spy_data['low']
                    range_percent = (daily_range / spy_data['price']) * 100
                    print(f"   Daily Range: ${daily_range:.2f} ({range_percent:.2f}%)")
            
            print()
            
            # AI Analysis Context
            print("🤖 AI Analysis Context:")
            print("─" * 40)
            
            # Create context for AI agents
            ai_context = {
                "market_data": market_data,
                "timestamp": datetime.now().isoformat(),
                "data_source": "polygon_daily",
                "market_regime_signals": {
                    "spy_price": spy_data.get('price', 0),
                    "spy_range_percent": range_percent if 'range_percent' in locals() else 0,
                    "volume_normal": spy_data.get('volume', 0) > 20000000,  # Normal SPY volume
                },
                "strategy_context": {
                    "suitable_for_analysis": True,
                    "data_freshness": "previous_trading_day",
                    "confidence_level": "moderate"  # Historical data
                }
            }
            
            print("📊 Market Regime Signals:")
            signals = ai_context["market_regime_signals"]
            print(f"   SPY Price: ${signals['spy_price']:.2f}")
            print(f"   Daily Range: {signals['spy_range_percent']:.2f}%")
            print(f"   Volume Normal: {'✅' if signals['volume_normal'] else '❌'}")
            
            print()
            print("🔮 Ready for AI Analysis:")
            print("   • Market regime classification")
            print("   • Volatility assessment")
            print("   • Strategy recommendations")
            print("   • Risk evaluation")
            
            print()
            print("💡 Sample AI Analysis Prompt:")
            print("─" * 40)
            print(f"""
Analyze current market conditions for derivatives trading:

Market Data (from Polygon.io):
- SPY: ${signals['spy_price']:.2f}
- Daily Range: {signals['spy_range_percent']:.2f}%
- Volume: {'Normal' if signals['volume_normal'] else 'Below Normal'}

Questions for AI:
1. What market regime are we in? (trending/range-bound/volatile)
2. Are conditions favorable for MEIC strategies?
3. What's the recommended approach for options trading?
4. Key risk factors to monitor?
            """)
        
        print("\n" + "=" * 55)
        print("✅ Live Data Integration Demo Complete!")
        print()
        print("🎯 Next Steps:")
        print("1. ✅ Market data successfully retrieved from Polygon.io")
        print("2. ✅ Data formatted for AI agent consumption")
        print("3. 🔄 Connect AI agents to analyze live data")
        print("4. 🔄 Build real-time strategy recommendations")
        print("5. 🔄 Create frontend dashboard display")
        
        await provider.disconnect()
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        if provider:
            await provider.disconnect()

if __name__ == "__main__":
    asyncio.run(demo_live_data_integration())