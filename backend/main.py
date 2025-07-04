"""
Derivagent API - FastAPI Backend for AI-Powered Trading Platform
Main application entry point with market intelligence agent endpoints
"""

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
import asyncio
import uvicorn
import os
import json

# Import our AI agents
from ai.agent_clients import (
    MarketRegimeAgent, 
    VolatilitySurfaceAgent,
    SupportResistanceAgent,
    LiquidityAnalysisAgent,
    AgentFactory
)

# Import data layer
from data.manager import DataManager
import data_api
from ai_live_integration import LiveMarketAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Derivagent API",
    description="AI-Powered Derivatives Trading Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include data API routes
app.include_router(data_api.router)

# Request/Response Models
class AgentRequest(BaseModel):
    """Standard agent analysis request"""
    prompt: str = Field(..., description="Analysis request prompt")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context data")
    user_id: Optional[str] = Field(None, description="User ID for tracking")
    response_format: str = Field("json", description="Response format (json/text)")

class AgentResponse(BaseModel):
    """Standard agent analysis response"""
    agent: str
    success: bool
    timestamp: str
    model_used: Optional[str] = None
    tier: Optional[str] = None
    error: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: str
    version: str
    agents_available: List[str]

# Global agent instances (initialized on startup)
agents = {}
data_manager = None
startup_time = datetime.now()

@app.on_event("startup")
async def startup_event():
    """Initialize agents and data manager on startup"""
    logger.info("🚀 Starting Derivagent API server...")
    
    try:
        # Initialize data manager
        await _init_data_manager()
        
        # Initialize all agents
        agent_types = ["market_regime", "volatility_surface", "support_resistance", "liquidity_analysis"]
        for agent_type in agent_types:
            agents[agent_type] = AgentFactory.create_agent(agent_type)
            logger.info(f"✅ {agent_type} agent initialized")
        
        logger.info("🎯 All systems initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize systems: {str(e)}")
        raise

async def _init_data_manager():
    global data_manager
    """Initialize data manager with configuration"""
    try:
        # Load data configuration
        config_path = "config/data_config.json"
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Resolve environment variables in config
        config = _resolve_env_vars(config)
        
        # Initialize and set global data manager
        manager = DataManager(config)
        await manager.initialize()
        
        # Set global reference for data_api and main module
        data_api.data_manager = manager
        data_manager = manager
        
        logger.info("✅ Data manager initialized")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize data manager: {e}")
        # Don't raise - allow server to start in degraded mode
        
def _resolve_env_vars(config: dict) -> dict:
    """Recursively resolve environment variables in configuration"""
    import copy
    resolved_config = copy.deepcopy(config)
    
    def resolve_value(value):
        if isinstance(value, str) and value.startswith("os.environ/"):
            env_var = value.replace("os.environ/", "")
            return os.getenv(env_var)
        elif isinstance(value, dict):
            return {k: resolve_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [resolve_value(item) for item in value]
        return value
    
    return resolve_value(resolved_config)

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources on shutdown"""
    logger.info("🔄 Shutting down Derivagent API server...")
    
    try:
        # Shutdown data manager
        if data_api.data_manager:
            await data_api.data_manager.shutdown()
        
        logger.info("✅ Shutdown completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Error during shutdown: {e}")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for better error responses"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "timestamp": datetime.now().isoformat()
        }
    )

# Health Check Endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="1.0.0",
        agents_available=list(agents.keys())
    )

# Agent Endpoints
@app.post("/agents/market-regime", response_model=AgentResponse)
async def analyze_market_regime(request: AgentRequest):
    """
    Market Regime Analysis Endpoint
    
    Analyzes market conditions to determine optimal trading environment.
    Specializes in MEIC strategy favorability and volatility regime classification.
    """
    try:
        agent = agents.get("market_regime")
        if not agent:
            raise HTTPException(status_code=503, detail="Market regime agent not available")
        
        logger.info(f"📊 Market regime analysis requested: {request.prompt[:50]}...")
        
        result = await agent.analyze(
            prompt=request.prompt,
            context=request.context,
            user_id=request.user_id,
            response_format=request.response_format
        )
        
        return AgentResponse(
            agent=result.get("agent", "market_regime"),
            success=result.get("success", False),
            timestamp=result.get("timestamp", datetime.now().isoformat()),
            model_used=result.get("model_used"),
            tier=result.get("tier"),
            error=result.get("error"),
            data=result if result.get("success") else None
        )
        
    except Exception as e:
        logger.error(f"❌ Market regime analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/agents/volatility-surface", response_model=AgentResponse)
async def analyze_volatility_surface(request: AgentRequest):
    """
    Volatility Surface Analysis Endpoint
    
    Analyzes implied volatility patterns across strikes and expirations.
    Identifies premium selling/buying opportunities and term structure analysis.
    """
    try:
        agent = agents.get("volatility_surface")
        if not agent:
            raise HTTPException(status_code=503, detail="Volatility surface agent not available")
        
        logger.info(f"📈 Volatility surface analysis requested: {request.prompt[:50]}...")
        
        result = await agent.analyze(
            prompt=request.prompt,
            context=request.context,
            user_id=request.user_id,
            response_format=request.response_format
        )
        
        return AgentResponse(
            agent=result.get("agent", "volatility_surface"),
            success=result.get("success", False),
            timestamp=result.get("timestamp", datetime.now().isoformat()),
            model_used=result.get("model_used"),
            tier=result.get("tier"),
            error=result.get("error"),
            data=result if result.get("success") else None
        )
        
    except Exception as e:
        logger.error(f"❌ Volatility surface analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/agents/support-resistance", response_model=AgentResponse)
async def analyze_support_resistance(request: AgentRequest):
    """
    Support & Resistance Analysis Endpoint
    
    Identifies key price levels and validates their strength.
    Provides range analysis for options strategies and breakout probability.
    """
    try:
        agent = agents.get("support_resistance")
        if not agent:
            raise HTTPException(status_code=503, detail="Support resistance agent not available")
        
        logger.info(f"📉 Support/resistance analysis requested: {request.prompt[:50]}...")
        
        result = await agent.analyze(
            prompt=request.prompt,
            context=request.context,
            user_id=request.user_id,
            response_format=request.response_format
        )
        
        return AgentResponse(
            agent=result.get("agent", "support_resistance"),
            success=result.get("success", False),
            timestamp=result.get("timestamp", datetime.now().isoformat()),
            model_used=result.get("model_used"),
            tier=result.get("tier"),
            error=result.get("error"),
            data=result if result.get("success") else None
        )
        
    except Exception as e:
        logger.error(f"❌ Support/resistance analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/agents/liquidity-analysis", response_model=AgentResponse)
async def analyze_liquidity(request: AgentRequest):
    """
    Liquidity Analysis Endpoint
    
    Analyzes options liquidity to ensure tradeable execution.
    Evaluates bid-ask spreads, volume, and market maker presence.
    """
    try:
        agent = agents.get("liquidity_analysis")
        if not agent:
            raise HTTPException(status_code=503, detail="Liquidity analysis agent not available")
        
        logger.info(f"💧 Liquidity analysis requested: {request.prompt[:50]}...")
        
        result = await agent.analyze(
            prompt=request.prompt,
            context=request.context,
            user_id=request.user_id,
            response_format=request.response_format
        )
        
        return AgentResponse(
            agent=result.get("agent", "liquidity_analysis"),
            success=result.get("success", False),
            timestamp=result.get("timestamp", datetime.now().isoformat()),
            model_used=result.get("model_used"),
            tier=result.get("tier"),
            error=result.get("error"),
            data=result if result.get("success") else None
        )
        
    except Exception as e:
        logger.error(f"❌ Liquidity analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

# Batch Analysis Endpoint
@app.post("/agents/batch-analysis")
async def batch_analysis(requests: List[AgentRequest]):
    """
    Batch Analysis Endpoint
    
    Runs multiple agent analyses concurrently for comprehensive market assessment.
    Useful for getting complete market intelligence in one request.
    """
    try:
        logger.info(f"🔄 Batch analysis requested: {len(requests)} agents")
        
        # Create tasks for concurrent execution
        tasks = []
        for req in requests:
            if req.context and "agent_type" in req.context:
                agent_type = req.context["agent_type"]
                if agent_type in agents:
                    task = agents[agent_type].analyze(
                        prompt=req.prompt,
                        context=req.context,
                        user_id=req.user_id,
                        response_format=req.response_format
                    )
                    tasks.append(task)
        
        # Execute all analyses concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        batch_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                batch_results.append({
                    "agent": f"agent_{i}",
                    "success": False,
                    "error": str(result),
                    "timestamp": datetime.now().isoformat()
                })
            else:
                batch_results.append(result)
        
        return {
            "batch_analysis": True,
            "total_agents": len(requests),
            "successful_analyses": sum(1 for r in batch_results if r.get("success")),
            "results": batch_results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Batch analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Batch analysis failed: {str(e)}")

# Agent Information Endpoints
@app.get("/agents/info")
async def get_agents_info():
    """Get information about all available agents"""
    try:
        agents_info = {}
        for agent_type, agent in agents.items():
            agents_info[agent_type] = agent.get_capabilities()
        
        return {
            "available_agents": list(agents.keys()),
            "total_agents": len(agents),
            "agent_details": agents_info,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get agent info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get agent info: {str(e)}")

@app.get("/agents/{agent_type}/capabilities")
async def get_agent_capabilities(agent_type: str):
    """Get capabilities for a specific agent"""
    try:
        if agent_type not in agents:
            raise HTTPException(status_code=404, detail=f"Agent type '{agent_type}' not found")
        
        return agents[agent_type].get_capabilities()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get capabilities for {agent_type}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get capabilities: {str(e)}")

# Live Market Analysis Endpoints
class LiveAnalysisRequest(BaseModel):
    """Live market analysis request"""
    symbols: Optional[List[str]] = Field(["SPY", "QQQ"], description="Symbols to analyze")
    user_id: Optional[str] = Field(None, description="User ID for tracking")

class LiveAnalysisResponse(BaseModel):
    """Live market analysis response"""
    success: bool
    timestamp: str
    symbols_analyzed: List[str]
    market_data: Optional[Dict[str, Any]] = None
    ai_analysis: Optional[Dict[str, Any]] = None
    trading_recommendations: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

@app.post("/market/live-analysis", response_model=LiveAnalysisResponse)
async def get_live_market_analysis(request: LiveAnalysisRequest):
    """
    Live Market Analysis with AI Integration
    
    Combines real-time market data from Polygon.io with AI agent analysis
    to provide comprehensive market intelligence for derivatives trading.
    """
    try:
        logger.info(f"🔍 Live market analysis requested for: {', '.join(request.symbols)}")
        
        # Initialize live analyzer
        analyzer = LiveMarketAnalyzer()
        
        # Initialize and run analysis
        init_success = await analyzer.initialize()
        if not init_success:
            raise HTTPException(status_code=503, detail="Failed to initialize live data connection")
        
        # Run comprehensive analysis
        analysis_report = await analyzer.analyze_live_market(request.symbols)
        
        # Cleanup
        await analyzer.shutdown()
        
        if analysis_report.get('error'):
            return LiveAnalysisResponse(
                success=False,
                timestamp=datetime.now().isoformat(),
                symbols_analyzed=request.symbols,
                error=analysis_report['error']
            )
        
        return LiveAnalysisResponse(
            success=True,
            timestamp=analysis_report.get('analysis_timestamp', datetime.now().isoformat()),
            symbols_analyzed=analysis_report.get('symbols_analyzed', request.symbols),
            market_data=analysis_report.get('market_data'),
            ai_analysis=analysis_report.get('ai_analysis'),
            trading_recommendations=analysis_report.get('trading_recommendations')
        )
        
    except Exception as e:
        logger.error(f"❌ Live market analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Live analysis failed: {str(e)}")

@app.get("/market/live-quote/{symbol}")
async def get_live_quote(symbol: str):
    """
    Get live quote for a specific symbol
    
    Returns real-time price data from Polygon.io
    """
    try:
        logger.info(f"📊 Live quote requested for: {symbol}")
        
        # Use global data manager
        if not data_manager:
            raise HTTPException(status_code=503, detail="Data manager not initialized")
        
        # Get quote
        quote_response = await data_manager.get_quote(symbol)
        
        if not quote_response.success:
            raise HTTPException(status_code=404, detail=f"Failed to get quote for {symbol}: {quote_response.error}")
        
        quote = quote_response.data
        return {
            "symbol": symbol,
            "price": float(quote.last) if quote.last else None,
            "bid": float(quote.bid) if quote.bid else None,
            "ask": float(quote.ask) if quote.ask else None,
            "open": float(quote.open_price) if quote.open_price else None,
            "high": float(quote.high) if quote.high else None,
            "low": float(quote.low) if quote.low else None,
            "volume": quote.volume,
            "change": float(quote.change) if quote.change else None,
            "change_percent": float(quote.change_percent) if quote.change_percent else None,
            "timestamp": quote.timestamp.isoformat(),
            "source": quote.source,
            "market_hours": quote.market_hours
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get live quote for {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Quote request failed: {str(e)}")

# Real-time Monitoring Endpoints
class MonitoringResponse(BaseModel):
    """System monitoring response"""
    timestamp: str
    system_status: str
    data_providers: Dict[str, Any]
    ai_agents: Dict[str, Any]
    performance_metrics: Dict[str, Any]
    recent_activity: List[Dict[str, Any]]

@app.get("/monitoring/status", response_model=MonitoringResponse)
async def get_system_monitoring():
    """
    Get comprehensive system monitoring status
    
    Returns real-time status of all components:
    - Data provider connections and health
    - AI agent availability and performance
    - System performance metrics
    - Recent activity logs
    """
    try:
        # Gather system status
        current_time = datetime.now()
        
        # Check data provider status
        data_providers = {}
        if data_manager:
            for name, provider in data_manager.providers.items():
                status_info = {
                    "connected": provider.is_connected,
                    "provider_type": getattr(provider, 'provider_name', name),
                    "last_request": getattr(provider, 'last_request_time', None),
                    "request_count": getattr(provider, 'request_count', 0),
                    "error_count": getattr(provider, 'error_count', 0)
                }
                
                # Add provider-specific info
                if hasattr(provider, 'get_provider_info'):
                    provider_info = provider.get_provider_info()
                    status_info.update({
                        "rate_limit": provider_info.get('rate_limit_per_minute', 'unlimited'),
                        "daily_limit": provider_info.get('daily_limit', 'unlimited'),
                        "requests_today": provider_info.get('requests_today', 0),
                        "supports_real_time": provider_info.get('supports_real_time', False),
                        "data_quality": provider_info.get('data_quality', 'unknown')
                    })
                
                data_providers[name] = status_info
        
        # Check AI agent status
        ai_agents = {}
        for agent_name, agent in agents.items():
            ai_agents[agent_name] = {
                "available": agent is not None,
                "agent_type": agent.agent_name if agent else None,
                "model_tier": getattr(agent.router, 'agent_routes', {}).get(agent_name, 'unknown') if agent else None,
                "capabilities": agent.get_capabilities() if agent and hasattr(agent, 'get_capabilities') else {}
            }
        
        # Performance metrics
        performance_metrics = {
            "uptime_seconds": (current_time - startup_time).total_seconds() if 'startup_time' in globals() else 0,
            "memory_usage_mb": 0,  # Would need psutil for real memory metrics
            "active_connections": len(data_manager.providers) if data_manager else 0,
            "cache_enabled": data_manager.cache_enabled if data_manager else False,
            "request_stats": data_manager.request_stats if data_manager else {}
        }
        
        # Recent activity (simplified)
        recent_activity = [
            {
                "timestamp": current_time.isoformat(),
                "event": "system_status_check",
                "details": "Monitoring endpoint accessed"
            }
        ]
        
        # Determine overall system status
        provider_health = all(p.get('connected', False) for p in data_providers.values()) if data_providers else False
        agent_health = all(a.get('available', False) for a in ai_agents.values()) if ai_agents else False
        
        if provider_health and agent_health:
            system_status = "healthy"
        elif provider_health or agent_health:
            system_status = "degraded"
        else:
            system_status = "critical"
        
        return MonitoringResponse(
            timestamp=current_time.isoformat(),
            system_status=system_status,
            data_providers=data_providers,
            ai_agents=ai_agents,
            performance_metrics=performance_metrics,
            recent_activity=recent_activity
        )
        
    except Exception as e:
        logger.error(f"❌ Monitoring status failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Monitoring failed: {str(e)}")

@app.get("/monitoring/heartbeat")
async def get_heartbeat():
    """Simple heartbeat endpoint for uptime monitoring"""
    return {
        "status": "alive",
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": (datetime.now() - startup_time).total_seconds() if 'startup_time' in globals() else 0
    }

@app.get("/monitoring/providers")
async def get_provider_status():
    """Get detailed data provider status"""
    if not data_manager:
        raise HTTPException(status_code=503, detail="Data manager not available")
    
    provider_status = {}
    
    for name, provider in data_manager.providers.items():
        # Test connection
        try:
            test_result = await provider.test_connection()
            
            status = {
                "name": name,
                "connected": provider.is_connected,
                "connection_test": test_result,
                "provider_type": getattr(provider, 'provider_name', name),
                "capabilities": getattr(provider, 'capabilities', []),
                "last_error": getattr(provider, 'last_error', None)
            }
            
            # Add provider-specific metrics
            if hasattr(provider, 'get_provider_info'):
                status.update(provider.get_provider_info())
            
            provider_status[name] = status
            
        except Exception as e:
            provider_status[name] = {
                "name": name,
                "connected": False,
                "connection_test": False,
                "error": str(e)
            }
    
    return {
        "timestamp": datetime.now().isoformat(),
        "providers": provider_status,
        "total_providers": len(provider_status),
        "connected_providers": sum(1 for p in provider_status.values() if p.get('connected', False))
    }

# Development/Testing Endpoints
@app.get("/test/agents")
async def test_all_agents():
    """Test all agents with sample data - for development only"""
    try:
        logger.info("🧪 Testing all agents with sample data...")
        
        # Sample market data
        test_data = {
            "market_regime": {
                "vix_level": 16.5,
                "spx_price": 5050,
                "market_breadth": "neutral",
                "adx": 22.5,
                "rsi": 48
            },
            "volatility_surface": {
                "current_iv": 0.18,
                "iv_52_week_high": 0.35,
                "iv_52_week_low": 0.12,
                "front_month_iv": 0.17,
                "back_month_iv": 0.19
            },
            "support_resistance": {
                "current_price": 5050,
                "recent_high": 5100,
                "recent_low": 5000,
                "volume_profile": "balanced"
            },
            "liquidity_analysis": {
                "bid_ask_spread": 0.05,
                "volume": 12500,
                "open_interest": 45000,
                "market_hours": True
            }
        }
        
        # Test all agents
        results = {}
        for agent_type, agent in agents.items():
            try:
                result = await agent.analyze(
                    prompt=f"Analyze current market conditions for {agent_type}",
                    context=test_data.get(agent_type, {}),
                    user_id="test_user",
                    response_format="json"
                )
                results[agent_type] = {
                    "success": result.get("success", False),
                    "model_used": result.get("model_used"),
                    "tier": result.get("tier"),
                    "has_data": "data" in result if result.get("success") else False
                }
            except Exception as e:
                results[agent_type] = {
                    "success": False,
                    "error": str(e)
                }
        
        return {
            "test_completed": True,
            "agents_tested": len(agents),
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Agent testing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Agent testing failed: {str(e)}")

if __name__ == "__main__":
    # Development server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )