#!/usr/bin/env python3
"""
Simple HTTP server to demonstrate Derivagent API structure
Runs without external dependencies for quick demo
"""

import json
import http.server
import socketserver
from datetime import datetime
from urllib.parse import urlparse, parse_qs
import threading
import webbrowser
import time

class DerivagentHandler(http.server.BaseHTTPRequestHandler):
    
    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        # Health check endpoint
        if path == '/health':
            self.send_json_response({
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.0",
                "agents_available": ["market_regime", "volatility_surface", "support_resistance", "liquidity_analysis"]
            })
        
        # Agents info endpoint
        elif path == '/agents/info':
            self.send_json_response({
                "available_agents": ["market_regime", "volatility_surface", "support_resistance", "liquidity_analysis"],
                "total_agents": 4,
                "agent_details": {
                    "market_regime": {
                        "agent_name": "market_regime",
                        "description": "Market regime analysis and strategy favorability",
                        "model_tier": "reasoning"
                    },
                    "volatility_surface": {
                        "agent_name": "volatility_surface", 
                        "description": "Volatility surface analysis and premium opportunities",
                        "model_tier": "speed"
                    },
                    "support_resistance": {
                        "agent_name": "support_resistance",
                        "description": "Support and resistance level identification",
                        "model_tier": "cost"
                    },
                    "liquidity_analysis": {
                        "agent_name": "liquidity_analysis",
                        "description": "Options liquidity and execution quality assessment", 
                        "model_tier": "cost"
                    }
                },
                "timestamp": datetime.now().isoformat()
            })
        
        # Test agents endpoint
        elif path == '/test/agents':
            self.send_json_response({
                "test_completed": True,
                "agents_tested": 4,
                "results": {
                    "market_regime": {
                        "success": True,
                        "model_used": "deepseek-r1-preview",
                        "tier": "reasoning",
                        "has_data": True
                    },
                    "volatility_surface": {
                        "success": True,
                        "model_used": "grok-beta",
                        "tier": "speed", 
                        "has_data": True
                    },
                    "support_resistance": {
                        "success": True,
                        "model_used": "qwq-32b-preview",
                        "tier": "cost",
                        "has_data": True
                    },
                    "liquidity_analysis": {
                        "success": True,
                        "model_used": "qwq-32b-preview", 
                        "tier": "cost",
                        "has_data": True
                    }
                },
                "timestamp": datetime.now().isoformat()
            })
        
        # CORS preflight for frontend
        elif path.startswith('/agents/'):
            self.send_cors_headers()
            self.send_json_response({
                "message": "Use POST method for agent analysis",
                "available_endpoints": [
                    "/agents/market-regime",
                    "/agents/volatility-surface", 
                    "/agents/support-resistance",
                    "/agents/liquidity-analysis"
                ]
            })
        
        else:
            self.send_404()
    
    def do_POST(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        # Read request body
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else '{}'
        
        try:
            request_data = json.loads(post_data) if post_data else {}
        except json.JSONDecodeError:
            request_data = {}
        
        # Agent endpoints
        if path == '/agents/market-regime':
            self.handle_agent_request('market_regime', request_data)
        elif path == '/agents/volatility-surface':
            self.handle_agent_request('volatility_surface', request_data)
        elif path == '/agents/support-resistance':
            self.handle_agent_request('support_resistance', request_data)
        elif path == '/agents/liquidity-analysis':
            self.handle_agent_request('liquidity_analysis', request_data)
        elif path == '/agents/batch-analysis':
            self.handle_batch_analysis(request_data)
        else:
            self.send_404()
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_cors_headers()
        self.end_headers()
    
    def handle_agent_request(self, agent_name, request_data):
        """Handle individual agent analysis requests"""
        
        # Simulate different responses based on agent type
        if agent_name == 'market_regime':
            analysis_data = {
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
                "reasoning": "VIX at 16.5 indicates low volatility environment. SPX trading in established range 5000-5100. Conditions favor premium selling strategies like MEIC."
            }
        
        elif agent_name == 'volatility_surface':
            analysis_data = {
                "iv_analysis": {
                    "current_iv_rank": 23,
                    "classification": "low",
                    "trend": "stable"
                },
                "term_structure": {
                    "shape": "normal",
                    "front_month_iv": 0.17,
                    "back_month_iv": 0.19
                },
                "opportunities": {
                    "premium_selling_favorable": False,
                    "premium_buying_favorable": True,
                    "calendar_spreads_favorable": True
                },
                "confidence": 0.78
            }
        
        elif agent_name == 'support_resistance':
            analysis_data = {
                "key_levels": {
                    "primary_support": 5000,
                    "primary_resistance": 5100,
                    "secondary_support": 4950,
                    "secondary_resistance": 5150
                },
                "range_analysis": {
                    "range_width_points": 100,
                    "range_width_percent": 2.0,
                    "range_stability": "established"
                },
                "strategy_implications": {
                    "iron_condor_viable": True,
                    "range_bound_confidence": 0.82
                },
                "confidence": 0.88
            }
        
        else:  # liquidity_analysis
            analysis_data = {
                "liquidity_assessment": {
                    "overall_rating": "excellent", 
                    "execution_quality": "institutional"
                },
                "spread_analysis": {
                    "average_bid_ask_spread": 0.05,
                    "spread_percentage": 0.1,
                    "spread_rating": "excellent"
                },
                "strategy_implications": {
                    "suitable_for_meic": True,
                    "max_recommended_size": 50
                },
                "confidence": 0.91
            }
        
        response = {
            "agent": agent_name,
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "model_used": "demo-mode",
            "tier": "simulated",
            "data": analysis_data
        }
        
        self.send_json_response(response)
    
    def handle_batch_analysis(self, request_data):
        """Handle batch analysis requests"""
        results = []
        
        # Simulate batch processing
        for i in range(4):
            agent_names = ['market_regime', 'volatility_surface', 'support_resistance', 'liquidity_analysis']
            self.handle_agent_request(agent_names[i], {})
            # Note: In a real implementation, we'd collect these results
            
        response = {
            "batch_analysis": True,
            "total_agents": 4,
            "successful_analyses": 4,
            "results": [
                {"agent": "market_regime", "success": True, "timestamp": datetime.now().isoformat()},
                {"agent": "volatility_surface", "success": True, "timestamp": datetime.now().isoformat()},
                {"agent": "support_resistance", "success": True, "timestamp": datetime.now().isoformat()},
                {"agent": "liquidity_analysis", "success": True, "timestamp": datetime.now().isoformat()}
            ],
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
            "available_endpoints": [
                "/health",
                "/agents/info", 
                "/test/agents",
                "/agents/market-regime",
                "/agents/volatility-surface",
                "/agents/support-resistance", 
                "/agents/liquidity-analysis"
            ]
        }
        
        self.wfile.write(json.dumps(error_response, indent=2).encode('utf-8'))
    
    def log_message(self, format, *args):
        """Custom logging to show API requests"""
        print(f"🔗 {datetime.now().strftime('%H:%M:%S')} - {format % args}")

def start_server(port=8000):
    """Start the simple HTTP server"""
    try:
        with socketserver.TCPServer(("", port), DerivagentHandler) as httpd:
            print("🚀 Derivagent Backend Demo Server Starting...")
            print(f"🔗 Server running on http://localhost:{port}")
            print(f"📖 API endpoints available:")
            print(f"   • Health: http://localhost:{port}/health")
            print(f"   • Agents: http://localhost:{port}/agents/info") 
            print(f"   • Test: http://localhost:{port}/test/agents")
            print(f"   • Docs: http://localhost:{port}/agents/market-regime (POST)")
            print("🎯 This is a demo server - add your API keys for live AI analysis")
            print("⏹️  Press Ctrl+C to stop the server")
            print()
            
            # Open browser automatically after a short delay
            def open_browser():
                time.sleep(2)
                webbrowser.open(f'http://localhost:{port}/health')
            
            browser_thread = threading.Thread(target=open_browser)
            browser_thread.daemon = True
            browser_thread.start()
            
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except OSError as e:
        if e.errno == 98:  # Address already in use
            print(f"❌ Port {port} is already in use. Try a different port or stop the existing server.")
        else:
            print(f"❌ Server error: {e}")

if __name__ == "__main__":
    start_server()