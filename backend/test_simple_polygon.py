#!/usr/bin/env python3
"""
Simple Polygon.io API test
"""

import asyncio
import aiohttp
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env')

async def test_polygon_api():
    """Test Polygon API directly"""
    api_key = os.getenv('POLYGON_API_KEY')
    print(f"🔑 Testing Polygon API with key: {api_key[:10]}...")
    
    if not api_key:
        print("❌ No API key found")
        return
    
    # Test with market status endpoint (free tier)
    url = f"https://api.polygon.io/v1/marketstatus/now?apikey={api_key}"
    
    try:
        async with aiohttp.ClientSession() as session:
            print(f"📡 Making request to: {url[:50]}...")
            async with session.get(url) as response:
                print(f"📊 Response status: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Success! Data: {data}")
                else:
                    error_text = await response.text()
                    print(f"❌ Error: {error_text}")
                    
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_polygon_api())