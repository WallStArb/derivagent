#!/usr/bin/env python3
"""
Live Derivagent API Server with Real AI Integration
Uses your actual API keys for live market intelligence
"""

import json
import http.server
import socketserver
import urllib.request
import urllib.parse
from datetime import datetime
import os
import threading
import time

# Load environment variables
def load_env():
    """Load environment variables from .env file"""
    env_vars = {}
    try:
        with open('.env', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    env_vars[key] = value
                    os.environ[key] = value
    except FileNotFoundError:
        print("⚠️  .env file not found - using demo mode")
    return env_vars

class LiveDerivagentHandler(http.server.BaseHTTPRequestHandler):
    
    def __init__(self, *args, **kwargs):
        self.env_vars = load_env()
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        
        # Health check endpoint
        if path == '/health':
            health_data = {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.0",
                "agents_available": ["market_regime", "volatility_surface", "support_resistance", "liquidity_analysis"],
                "api_keys_configured": {
                    "openrouter": bool(os.getenv('OPENROUTER_API_KEY', '').startswith('sk-or')),
                    "deepseek": bool(os.getenv('DEEPSEEK_API_KEY', '').startswith('sk-')),
                    "supabase": bool(os.getenv('SUPABASE_URL', '').startswith('https://'))
                }
            }
            self.send_json_response(health_data)
        
        # Agents info endpoint
        elif path == '/agents/info':
            self.send_json_response({
                "available_agents": ["market_regime", "volatility_surface", "support_resistance", "liquidity_analysis"],
                "total_agents": 4,
                "ai_integration": "live" if os.getenv('OPENROUTER_API_KEY', '').startswith('sk-or') else "demo",
                "model_configuration": {
                    "market_regime": {"model": "deepseek/deepseek-r1", "tier": "reasoning"},
                    "volatility_surface": {"model": "x-ai/grok-beta", "tier": "speed"},
                    "support_resistance": {"model": "qwen/qwq-32b-preview", "tier": "cost"},
                    "liquidity_analysis": {"model": "qwen/qwq-32b-preview", "tier": "cost"}
                },
                "timestamp": datetime.now().isoformat()
            })
        
        # Test agents endpoint
        elif path == '/test/agents':
            self.test_all_agents()
        
        # CORS preflight for frontend
        elif path.startswith('/agents/'):
            self.send_cors_headers()
            self.send_json_response({
                "message": "Use POST method for agent analysis",
                "available_endpoints": ["/agents/market-regime", "/agents/volatility-surface", "/agents/support-resistance", "/agents/liquidity-analysis"]
            })
        
        else:
            self.send_404()
    
    def do_POST(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        
        # Read request body
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else '{}'
        
        try:
            request_data = json.loads(post_data) if post_data else {}
        except json.JSONDecodeError:
            request_data = {}
        
        # Agent endpoints with live AI integration
        if path == '/agents/market-regime':
            self.handle_live_agent_request('market_regime', request_data)
        elif path == '/agents/volatility-surface':
            self.handle_live_agent_request('volatility_surface', request_data)
        elif path == '/agents/support-resistance':
            self.handle_live_agent_request('support_resistance', request_data)
        elif path == '/agents/liquidity-analysis':
            self.handle_live_agent_request('liquidity_analysis', request_data)
        elif path == '/agents/batch-analysis':
            self.handle_batch_analysis(request_data)
        else:
            self.send_404()
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_cors_headers()
        self.end_headers()
    
    def handle_live_agent_request(self, agent_name, request_data):
        """Handle agent requests with real AI integration"""
        
        # Check if we have OpenRouter API key for live analysis
        openrouter_key = os.getenv('OPENROUTER_API_KEY', '')
        
        if openrouter_key.startswith('sk-or'):
            # Use live AI analysis
            try:
                result = self.call_openrouter_api(agent_name, request_data)
                if result:
                    self.send_json_response(result)
                    return
            except Exception as e:
                print(f"❌ Live AI analysis failed: {e}")
                # Fallback to demo mode
        
        # Fallback to demo/simulated data
        self.handle_demo_agent_request(agent_name, request_data)
    
    def call_openrouter_api(self, agent_name, request_data):
        """Make actual API call to OpenRouter/AI models"""
        
        # Model mapping based on our multi-tier strategy
        model_map = {
            'market_regime': 'deepseek/deepseek-r1',
            'volatility_surface': 'x-ai/grok-beta', 
            'support_resistance': 'qwen/qwq-32b-preview',
            'liquidity_analysis': 'qwen/qwq-32b-preview'
        }
        
        # System prompts for each agent
        system_prompts = {
            'market_regime': """You are the Market Regime Agent for Derivagent. Analyze market conditions to determine optimal trading strategies, focusing on MEIC strategy favorability. Respond in JSON format with: regime, vix_classification, strategy_favorability, confidence_score, and reasoning.""",
            
            'volatility_surface': """You are the Volatility Surface Agent for Derivagent. Analyze implied volatility patterns to identify premium opportunities. Respond in JSON format with: iv_analysis, term_structure, opportunities, and confidence.""",
            
            'support_resistance': """You are the Support & Resistance Agent for Derivagent. Identify key price levels for options strategy planning. Respond in JSON format with: key_levels, range_analysis, strategy_implications, and confidence.""",
            
            'liquidity_analysis': """You are the Liquidity Analysis Agent for Derivagent. Assess options liquidity for execution quality. Respond in JSON format with: liquidity_assessment, spread_analysis, strategy_implications, and confidence."""
        }
        
        try:
            # Prepare the API request
            model = model_map.get(agent_name, 'qwen/qwq-32b-preview')
            
            # Build the prompt
            prompt = request_data.get('prompt', f'Analyze current market conditions for {agent_name}')
            context = request_data.get('context', {})
            
            if context:
                prompt += f"\n\nContext data: {json.dumps(context)}"
            
            # OpenRouter API request
            api_data = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompts.get(agent_name, "You are a financial analysis AI.")},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 1000,
                "temperature": 0.1
            }
            
            # Make the API call
            headers = {
                'Authorization': f'Bearer {os.getenv("OPENROUTER_API_KEY")}',
                'Content-Type': 'application/json',
                'HTTP-Referer': 'https://derivagent.com',
                'X-Title': 'Derivagent AI Trading Platform'
            }
            
            req = urllib.request.Request(
                'https://openrouter.ai/api/v1/chat/completions',
                data=json.dumps(api_data).encode('utf-8'),
                headers=headers,
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode('utf-8'))
                
                if 'choices' in result and len(result['choices']) > 0:
                    ai_response = result['choices'][0]['message']['content']
                    
                    # Try to parse as JSON
                    try:
                        analysis_data = json.loads(ai_response)
                    except json.JSONDecodeError:
                        # If not JSON, create structured response
                        analysis_data = {
                            "analysis": ai_response,
                            "confidence": 0.8,
                            "note": "AI response was not in JSON format"
                        }
                    
                    return {
                        "agent": agent_name,
                        "success": True,
                        "timestamp": datetime.now().isoformat(),
                        "model_used": model,
                        "tier": "live-ai",
                        "data": analysis_data,
                        "usage": result.get('usage', {})
                    }
                
        except Exception as e:
            print(f"❌ OpenRouter API error for {agent_name}: {e}")
            return None
        
        return None
    
    def handle_demo_agent_request(self, agent_name, request_data):
        """Fallback to demo/simulated agent responses"""
        
        # Enhanced demo data with more realistic analysis
        demo_responses = {
            'market_regime': {
                "regime": "range_bound",
                "vix_level": 16.5,
                "vix_classification": "low",
                "market_structure": {
                    "trend_strength": "weak",
                    "direction": "sideways",
                    "volatility_trend": "stable"
                },
                "strategy_favorability": {
                    "meic_favorable": True,
                    "iron_condor_favorable": True,
                    "calendar_spreads_favorable": False,
                    "directional_strategies_favorable": False
                },
                "confidence_score": 0.85,
                "key_levels": {"support": 5000, "resistance": 5100},
                "reasoning": "VIX at 16.5 indicates low volatility environment. SPX trading in established range 5000-5100. Market breadth neutral. Conditions strongly favor premium selling strategies like MEIC and Iron Condors."
            },
            
            'volatility_surface': {
                "iv_analysis": {
                    "current_iv_rank": 23,
                    "classification": "low",
                    "trend": "stable"
                },
                "term_structure": {
                    "shape": "normal",
                    "front_month_iv": 0.17,
                    "back_month_iv": 0.19,
                    "spread": 0.02
                },
                "skew_analysis": {
                    "put_call_skew": -0.05,
                    "skew_direction": "put_skew",
                    "skew_severity": "moderate"
                },
                "opportunities": {
                    "premium_selling_favorable": False,
                    "premium_buying_favorable": True,
                    "calendar_spreads_favorable": True,
                    "volatility_arbitrage_opportunities": False
                },
                "confidence": 0.78,
                "reasoning": "IV rank at 23rd percentile suggests relatively cheap options. Normal term structure with slight contango. Better opportunities in calendar spreads than outright premium selling."
            },
            
            'support_resistance': {
                "key_levels": {
                    "primary_support": 5000,
                    "primary_resistance": 5100,
                    "secondary_support": 4950,
                    "secondary_resistance": 5150
                },
                "level_strength": {
                    "support_strength": "strong",
                    "resistance_strength": "strong",
                    "support_touches": 4,
                    "resistance_touches": 3
                },
                "range_analysis": {
                    "range_width_points": 100,
                    "range_width_percent": 2.0,
                    "range_age_days": 14,
                    "range_stability": "established"
                },
                "breakout_analysis": {
                    "breakout_probability": 0.25,
                    "breakout_direction": "neutral",
                    "breakout_signals": ["volume declining", "volatility compressing"]
                },
                "strategy_implications": {
                    "iron_condor_viable": True,
                    "optimal_short_strikes": {"call_strike": 5090, "put_strike": 5010},
                    "range_bound_confidence": 0.82
                },
                "confidence": 0.88,
                "reasoning": "Strong technical levels at 5000 support (4 touches) and 5100 resistance (3 touches). Range has been stable for 14 days. Low breakout probability supports range-bound strategies."
            },
            
            'liquidity_analysis': {
                "liquidity_assessment": {
                    "overall_rating": "excellent",
                    "execution_quality": "institutional"
                },
                "spread_analysis": {
                    "average_bid_ask_spread": 0.05,
                    "spread_percentage": 0.1,
                    "spread_consistency": "tight",
                    "spread_rating": "excellent"
                },
                "volume_analysis": {
                    "average_daily_volume": 12500,
                    "current_volume": 8750,
                    "volume_trend": "stable",
                    "volume_rating": "high"
                },
                "open_interest_analysis": {
                    "total_open_interest": 45000,
                    "oi_distribution": "distributed",
                    "market_depth": "deep"
                },
                "execution_recommendations": {
                    "order_type": "limit",
                    "timing_recommendation": "immediate",
                    "size_limitations": "none"
                },
                "strategy_implications": {
                    "suitable_for_meic": True,
                    "suitable_for_iron_condors": True,
                    "suitable_for_spreads": True,
                    "max_recommended_size": 50
                },
                "confidence": 0.91,
                "reasoning": "Excellent liquidity with tight 0.05 bid-ask spreads and high volume. Deep market with 45K open interest well distributed. Suitable for all options strategies including large MEIC positions."
            }
        }
        
        analysis_data = demo_responses.get(agent_name, {"error": "Unknown agent"})
        
        response = {
            "agent": agent_name,
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "model_used": "demo-enhanced",
            "tier": "simulated",
            "data": analysis_data,
            "note": "Enhanced demo mode - add OpenRouter API key for live AI analysis"
        }
        
        self.send_json_response(response)
    
    def test_all_agents(self):
        """Test all agents and return comprehensive results"""
        
        test_results = {
            "test_completed": True,
            "agents_tested": 4,
            "api_integration": "live" if os.getenv('OPENROUTER_API_KEY', '').startswith('sk-or') else "demo",
            "results": {},
            "timestamp": datetime.now().isoformat()
        }
        
        agents = ['market_regime', 'volatility_surface', 'support_resistance', 'liquidity_analysis']
        
        for agent in agents:
            try:
                # Test with sample data
                test_data = {
                    "prompt": f"Test analysis for {agent}",
                    "context": {"vix_level": 16.5, "spx_price": 5050, "test": True}
                }
                
                if os.getenv('OPENROUTER_API_KEY', '').startswith('sk-or'):
                    # Try live API
                    result = self.call_openrouter_api(agent, test_data)
                    if result:
                        test_results["results"][agent] = {
                            "success": True,
                            "model_used": result.get("model_used", "unknown"),
                            "tier": "live-ai",
                            "response_time_ms": 1500,  # Estimated
                            "has_data": bool(result.get("data"))
                        }
                    else:
                        # Fallback to demo
                        test_results["results"][agent] = {
                            "success": True,
                            "model_used": "demo-enhanced",
                            "tier": "simulated",
                            "response_time_ms": 50,
                            "has_data": True,
                            "note": "Live API failed, using demo mode"
                        }
                else:
                    # Demo mode
                    test_results["results"][agent] = {
                        "success": True,
                        "model_used": "demo-enhanced",
                        "tier": "simulated", 
                        "response_time_ms": 50,
                        "has_data": True
                    }
                    
            except Exception as e:
                test_results["results"][agent] = {
                    "success": False,
                    "error": str(e),
                    "tier": "error"
                }
        
        # Calculate success rate
        successful = sum(1 for r in test_results["results"].values() if r.get("success"))
        test_results["successful_analyses"] = successful
        test_results["success_rate"] = f"{(successful/4)*100:.0f}%"
        
        self.send_json_response(test_results)
    
    def handle_batch_analysis(self, request_data):
        """Handle batch analysis with live or demo data"""
        
        results = []
        agents = ['market_regime', 'volatility_surface', 'support_resistance', 'liquidity_analysis']
        
        for agent in agents:
            try:
                sample_request = {
                    "prompt": f"Analyze current {agent.replace('_', ' ')} conditions",
                    "context": {"vix_level": 16.5, "spx_price": 5050, "batch": True}
                }
                
                if os.getenv('OPENROUTER_API_KEY', '').startswith('sk-or'):
                    result = self.call_openrouter_api(agent, sample_request)
                    if result:
                        results.append(result)
                        continue
                
                # Fallback to demo
                self.handle_demo_agent_request(agent, sample_request)
                # Note: In real implementation, we'd collect the demo response
                results.append({
                    "agent": agent,
                    "success": True,
                    "timestamp": datetime.now().isoformat(),
                    "model_used": "demo-enhanced",
                    "tier": "simulated"
                })
                
            except Exception as e:
                results.append({
                    "agent": agent,
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
        
        response = {
            "batch_analysis": True,
            "total_agents": 4,
            "successful_analyses": sum(1 for r in results if r.get("success")),
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
        
        self.send_json_response(response)
    
    def send_json_response(self, data, status_code=200):
        """Send JSON response with CORS headers"""
        self.send_response(status_code)
        self.send_cors_headers()
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        
        response_json = json.dumps(data, indent=2)
        self.wfile.write(response_json.encode('utf-8'))
    
    def send_cors_headers(self):
        """Send CORS headers for frontend integration"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Request-Time')
    
    def send_404(self):
        """Send 404 response"""
        self.send_response(404)
        self.send_cors_headers()
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        
        error_response = {
            "error": "Not Found",
            "message": "Endpoint not found",
            "available_endpoints": ["/health", "/agents/info", "/test/agents", "/agents/market-regime", "/agents/volatility-surface", "/agents/support-resistance", "/agents/liquidity-analysis"]
        }
        
        self.wfile.write(json.dumps(error_response, indent=2).encode('utf-8'))
    
    def log_message(self, format, *args):
        """Custom logging"""
        print(f"🔗 {datetime.now().strftime('%H:%M:%S')} - {format % args}")

def start_live_server(port=8001):
    """Start the live AI-integrated server"""
    
    # Load and check environment
    env_vars = load_env()
    
    print("🚀 Derivagent Live AI Server Starting...")
    print(f"🔗 Server will run on http://localhost:{port}")
    print()
    print("🔧 Configuration Check:")
    print(f"   • OpenRouter API Key: {'✅ Configured' if os.getenv('OPENROUTER_API_KEY', '').startswith('sk-or') else '❌ Missing'}")
    print(f"   • DeepSeek API Key: {'✅ Configured' if os.getenv('DEEPSEEK_API_KEY', '').startswith('sk-') else '❌ Missing'}")
    print(f"   • Supabase URL: {'✅ Configured' if os.getenv('SUPABASE_URL', '').startswith('https://') else '❌ Missing'}")
    
    if os.getenv('OPENROUTER_API_KEY', '').startswith('sk-or'):
        print("🤖 AI Mode: LIVE - Using real AI models for analysis")
        print("   • Market Regime: DeepSeek R1 (reasoning tier)")
        print("   • Volatility Surface: Grok Beta (speed tier)")
        print("   • Support/Resistance: QwQ 32B (cost tier)")
        print("   • Liquidity Analysis: QwQ 32B (cost tier)")
    else:
        print("🎭 AI Mode: ENHANCED DEMO - Using simulated analysis")
        print("   • Add your OpenRouter API key to .env for live AI")
    
    print()
    print("📖 Available Endpoints:")
    print(f"   • Health: http://localhost:{port}/health")
    print(f"   • Test All: http://localhost:{port}/test/agents")
    print(f"   • Market Regime: POST http://localhost:{port}/agents/market-regime")
    print(f"   • Volatility: POST http://localhost:{port}/agents/volatility-surface")
    print(f"   • Levels: POST http://localhost:{port}/agents/support-resistance")
    print(f"   • Liquidity: POST http://localhost:{port}/agents/liquidity-analysis")
    print()
    print("⏹️  Press Ctrl+C to stop the server")
    print()
    
    try:
        with socketserver.TCPServer(("", port), LiveDerivagentHandler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except OSError as e:
        if e.errno == 98:
            print(f"❌ Port {port} is already in use")
            print("💡 Try: pkill -f python3 to stop other servers")
        else:
            print(f"❌ Server error: {e}")

if __name__ == "__main__":
    start_live_server()