"""
Agent Client Framework for Derivagent Market Intelligence
Implements base classes and specific agents for market analysis
"""

from .model_router import get_router
from typing import Dict, Any, List, Optional, Union
import json
import logging
from datetime import datetime
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class AgentError(Exception):
    """Raised when agent operations fail"""
    pass

class BaseAgent(ABC):
    """
    Base class for all Derivagent AI agents
    
    Provides common functionality:
    - Secure model routing via LiteLLM
    - Structured response handling
    - Error handling and fallbacks
    - Usage tracking
    """
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.router = get_router()
        self.logger = logging.getLogger(f"agent.{agent_name}")
        
        self.logger.info(f"✅ {agent_name} agent initialized")
    
    async def analyze(
        self, 
        prompt: str, 
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        response_format: str = "json",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Standard agent analysis method
        
        Args:
            prompt: Analysis request prompt
            context: Additional context data
            user_id: User ID for tracking
            response_format: "json" or "text"
            **kwargs: Additional model parameters
            
        Returns:
            Analysis result dictionary
        """
        
        try:
            messages = self._build_messages(prompt, context)
            
            self.logger.info(f"🔍 {self.agent_name} analyzing: {prompt[:100]}...")
            
            # Get completion from router
            result = await self.router.get_completion(
                agent_name=self.agent_name,
                messages=messages,
                user_id=user_id,
                **kwargs
            )
            
            if not result.get('success', False):
                raise AgentError(f"Model completion failed: {result.get('error', 'Unknown error')}")
            
            # Parse response based on format
            if response_format == "json":
                parsed_response = self._parse_json_response(
                    result['response'].choices[0].message.content
                )
            else:
                parsed_response = {
                    "response": result['response'].choices[0].message.content
                }
            
            # Add metadata
            parsed_response.update({
                "agent": self.agent_name,
                "model_used": result.get('model', 'unknown'),
                "tier": result.get('tier', 'unknown'),
                "timestamp": result.get('timestamp', datetime.now().isoformat()),
                "success": True
            })
            
            self.logger.info(f"✅ {self.agent_name} analysis completed successfully")
            return parsed_response
            
        except Exception as e:
            self.logger.error(f"❌ {self.agent_name} analysis failed: {str(e)}")
            return {
                "agent": self.agent_name,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _build_messages(self, prompt: str, context: Optional[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Build message list for model completion"""
        messages = [
            {
                "role": "system",
                "content": self._get_system_prompt()
            }
        ]
        
        # Add context if provided
        user_content = prompt
        if context:
            context_str = json.dumps(context, indent=2)
            user_content = f"Context Data:\n{context_str}\n\nAnalysis Request:\n{prompt}"
        
        messages.append({
            "role": "user",
            "content": user_content
        })
        
        return messages
    
    @abstractmethod
    def _get_system_prompt(self) -> str:
        """Get system prompt for this agent - must be implemented by subclasses"""
        pass
    
    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """Parse JSON response with error handling"""
        try:
            # Try to extract JSON from response
            content = content.strip()
            
            # Handle markdown code blocks
            if content.startswith("```json"):
                content = content[7:-3].strip()
            elif content.startswith("```"):
                content = content[3:-3].strip()
            
            return json.loads(content)
            
        except json.JSONDecodeError as e:
            self.logger.warning(f"Failed to parse JSON response: {e}")
            return {
                "error": "Invalid JSON response",
                "raw_content": content,
                "parse_error": str(e)
            }
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get agent capabilities and metadata"""
        return {
            "agent_name": self.agent_name,
            "description": self.__doc__ or "No description available",
            "response_formats": ["json", "text"],
            "model_tier": self.router.agent_routes.get(self.agent_name, "cost")
        }

class MarketRegimeAgent(BaseAgent):
    """
    Market Regime Analysis Agent
    
    Analyzes market conditions to determine if they favor specific trading strategies.
    Key capabilities:
    - VIX level analysis and volatility regime classification
    - Trend vs range-bound market detection
    - MEIC strategy favorability assessment
    - Market breadth and momentum analysis
    """
    
    def __init__(self):
        super().__init__("market_regime")
    
    def _get_system_prompt(self) -> str:
        return """You are the Market Regime Agent for Derivagent, a professional derivatives trading platform.

Your role is to analyze market conditions and determine the optimal trading environment classification. You specialize in identifying conditions that favor different options strategies, particularly MEIC (Modified Enhanced Iron Condor) strategies.

ANALYSIS FRAMEWORK:
1. Volatility Environment (VIX-based classification)
2. Market Structure (trending vs range-bound vs chaotic)
3. Strategy Favorability (which options strategies are optimal)
4. Risk Assessment (current market stability and predictability)

RESPOND IN JSON FORMAT:
{
    "regime": "range_bound" | "trending_up" | "trending_down" | "high_volatility" | "transitional",
    "vix_level": number,
    "vix_classification": "low" | "moderate" | "high" | "extreme",
    "market_structure": {
        "trend_strength": "weak" | "moderate" | "strong",
        "direction": "up" | "down" | "sideways",
        "volatility_trend": "expanding" | "contracting" | "stable"
    },
    "strategy_favorability": {
        "meic_favorable": boolean,
        "iron_condor_favorable": boolean,
        "calendar_spreads_favorable": boolean,
        "directional_strategies_favorable": boolean
    },
    "confidence_score": 0.0-1.0,
    "key_levels": {
        "support": number,
        "resistance": number,
        "range_width_percent": number
    },
    "reasoning": "Detailed explanation of analysis and recommendations",
    "alerts": ["list of important market condition alerts"],
    "optimal_strategies": ["list of recommended strategies for current conditions"]
}

Focus on mathematical precision and institutional-grade analysis. Consider SPX, VIX, market breadth, and technical indicators in your assessment."""
    
    async def analyze_current_conditions(
        self, 
        market_data: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze current market conditions for regime classification"""
        
        prompt = """Analyze the current market regime based on the provided data. 
        
        Consider:
        1. VIX level and recent volatility patterns
        2. SPX price action and trend characteristics
        3. Market breadth and momentum indicators
        4. Optimal strategy recommendations for current conditions
        
        Provide a comprehensive assessment suitable for professional derivatives trading."""
        
        return await self.analyze(
            prompt=prompt,
            context=market_data,
            user_id=user_id,
            response_format="json"
        )

class VolatilitySurfaceAgent(BaseAgent):
    """
    Volatility Surface Analysis Agent
    
    Analyzes implied volatility across strikes and expirations.
    Key capabilities:
    - IV rank and percentile analysis
    - Term structure analysis (front month vs back month)
    - Volatility skew assessment
    - Premium selling/buying opportunity identification
    """
    
    def __init__(self):
        super().__init__("volatility_surface")
    
    def _get_system_prompt(self) -> str:
        return """You are the Volatility Surface Agent for Derivagent.

Your expertise is in analyzing implied volatility patterns across different strikes and expirations to identify optimal options trading opportunities.

ANALYSIS FOCUS:
1. IV Rank Analysis (current IV vs historical range)
2. Term Structure (front month vs back month relationships)
3. Volatility Skew (put/call IV differences)
4. Premium Opportunities (selling vs buying scenarios)

RESPOND IN JSON FORMAT:
{
    "iv_analysis": {
        "current_iv_rank": 0-100,
        "classification": "very_low" | "low" | "moderate" | "high" | "very_high",
        "trend": "expanding" | "contracting" | "stable"
    },
    "term_structure": {
        "shape": "normal" | "inverted" | "flat",
        "front_month_iv": number,
        "back_month_iv": number,
        "spread": number
    },
    "skew_analysis": {
        "put_call_skew": number,
        "skew_direction": "put_skew" | "call_skew" | "neutral",
        "skew_severity": "low" | "moderate" | "high"
    },
    "opportunities": {
        "premium_selling_favorable": boolean,
        "premium_buying_favorable": boolean,
        "calendar_spreads_favorable": boolean,
        "volatility_arbitrage_opportunities": boolean
    },
    "recommended_strategies": ["list of optimal strategies"],
    "risk_warnings": ["list of volatility-related risks"],
    "confidence": 0.0-1.0,
    "reasoning": "Detailed volatility analysis explanation"
}

Provide institutional-grade volatility analysis suitable for professional options trading."""
    
    async def analyze_iv_environment(
        self,
        options_data: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze implied volatility environment"""
        
        prompt = """Analyze the implied volatility environment for options trading opportunities.
        
        Focus on:
        1. Current IV rank and historical context
        2. Term structure relationships and arbitrage opportunities
        3. Volatility skew patterns and their implications
        4. Optimal strategy recommendations based on IV conditions"""
        
        return await self.analyze(
            prompt=prompt,
            context=options_data,
            user_id=user_id,
            response_format="json"
        )

class SupportResistanceAgent(BaseAgent):
    """
    Support & Resistance Level Analysis Agent
    
    Identifies key price levels and validates their strength.
    Key capabilities:
    - Technical level identification
    - Level strength and reliability assessment
    - Range analysis for options strategies
    - Breakout/breakdown probability analysis
    """
    
    def __init__(self):
        super().__init__("support_resistance")
    
    def _get_system_prompt(self) -> str:
        return """You are the Support & Resistance Agent for Derivagent.

You specialize in identifying and validating key price levels that are crucial for options strategy planning, particularly for range-bound strategies like iron condors and MEIC.

ANALYSIS FRAMEWORK:
1. Level Identification (support/resistance zones)
2. Strength Assessment (touch count, volume, age)
3. Range Analysis (width, stability, breakout probability)
4. Strategy Implications (optimal strike placement)

RESPOND IN JSON FORMAT:
{
    "key_levels": {
        "primary_support": number,
        "primary_resistance": number,
        "secondary_support": number,
        "secondary_resistance": number
    },
    "level_strength": {
        "support_strength": "weak" | "moderate" | "strong" | "very_strong",
        "resistance_strength": "weak" | "moderate" | "strong" | "very_strong",
        "support_touches": number,
        "resistance_touches": number
    },
    "range_analysis": {
        "range_width_points": number,
        "range_width_percent": number,
        "range_age_days": number,
        "range_stability": "unstable" | "forming" | "established" | "mature"
    },
    "breakout_analysis": {
        "breakout_probability": 0.0-1.0,
        "breakout_direction": "up" | "down" | "neutral",
        "breakout_signals": ["list of technical signals"]
    },
    "strategy_implications": {
        "iron_condor_viable": boolean,
        "optimal_short_strikes": {
            "call_strike": number,
            "put_strike": number
        },
        "range_bound_confidence": 0.0-1.0
    },
    "alerts": ["important level break warnings"],
    "confidence": 0.0-1.0,
    "reasoning": "Technical analysis explanation"
}

Focus on actionable levels that can be used for precise options strategy execution."""
    
    async def analyze_key_levels(
        self,
        price_data: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze support and resistance levels"""
        
        prompt = """Analyze the chart data to identify key support and resistance levels.
        
        Consider:
        1. Historical price reactions at specific levels
        2. Volume confirmation at key levels
        3. Multiple timeframe level confluence
        4. Implications for options strategy strike selection
        
        Provide precise levels suitable for professional options trading."""
        
        return await self.analyze(
            prompt=prompt,
            context=price_data,
            user_id=user_id,
            response_format="json"
        )

class LiquidityAnalysisAgent(BaseAgent):
    """
    Options Liquidity Analysis Agent
    
    Analyzes options liquidity to ensure tradeable execution.
    Key capabilities:
    - Bid-ask spread analysis
    - Volume and open interest assessment
    - Market maker presence evaluation
    - Execution quality prediction
    """
    
    def __init__(self):
        super().__init__("liquidity_analysis")
    
    def _get_system_prompt(self) -> str:
        return """You are the Liquidity Analysis Agent for Derivagent.

Your role is to assess options liquidity to ensure strategies can be executed efficiently with minimal slippage and acceptable bid-ask spreads.

ANALYSIS CRITERIA:
1. Bid-Ask Spread Analysis (tightness and consistency)
2. Volume Assessment (average daily volume vs current)
3. Open Interest Evaluation (market depth and stability)
4. Market Maker Presence (electronic vs floor trading characteristics)

RESPOND IN JSON FORMAT:
{
    "liquidity_assessment": {
        "overall_rating": "excellent" | "good" | "fair" | "poor",
        "execution_quality": "institutional" | "retail" | "limited" | "avoid"
    },
    "spread_analysis": {
        "average_bid_ask_spread": number,
        "spread_percentage": number,
        "spread_consistency": "tight" | "variable" | "wide",
        "spread_rating": "excellent" | "good" | "fair" | "poor"
    },
    "volume_analysis": {
        "average_daily_volume": number,
        "current_volume": number,
        "volume_trend": "increasing" | "stable" | "decreasing",
        "volume_rating": "high" | "moderate" | "low"
    },
    "open_interest_analysis": {
        "total_open_interest": number,
        "oi_distribution": "concentrated" | "distributed" | "thin",
        "market_depth": "deep" | "moderate" | "shallow"
    },
    "execution_recommendations": {
        "order_type": "market" | "limit" | "midpoint" | "avoid",
        "timing_recommendation": "immediate" | "patient" | "wait_for_volume",
        "size_limitations": "none" | "moderate" | "significant"
    },
    "strategy_implications": {
        "suitable_for_meic": boolean,
        "suitable_for_iron_condors": boolean,
        "suitable_for_spreads": boolean,
        "max_recommended_size": number
    },
    "warnings": ["liquidity-related risks and considerations"],
    "confidence": 0.0-1.0
}

Ensure analysis supports institutional-grade execution requirements."""
    
    async def analyze_options_liquidity(
        self,
        options_chain_data: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze options chain liquidity"""
        
        prompt = """Analyze the options chain liquidity to determine execution quality.
        
        Evaluate:
        1. Bid-ask spreads across relevant strikes
        2. Volume patterns and open interest distribution
        3. Market maker activity and depth
        4. Suitability for different strategy types
        
        Provide liquidity assessment suitable for professional trading decisions."""
        
        return await self.analyze(
            prompt=prompt,
            context=options_chain_data,
            user_id=user_id,
            response_format="json"
        )

# Agent factory for easy instantiation
class AgentFactory:
    """Factory class for creating agent instances"""
    
    @staticmethod
    def create_agent(agent_type: str) -> BaseAgent:
        """Create agent instance by type"""
        agents = {
            "market_regime": MarketRegimeAgent,
            "volatility_surface": VolatilitySurfaceAgent,
            "support_resistance": SupportResistanceAgent,
            "liquidity_analysis": LiquidityAnalysisAgent
        }
        
        if agent_type not in agents:
            raise ValueError(f"Unknown agent type: {agent_type}. Available: {list(agents.keys())}")
        
        return agents[agent_type]()
    
    @staticmethod
    def get_available_agents() -> List[str]:
        """Get list of available agent types"""
        return ["market_regime", "volatility_surface", "support_resistance", "liquidity_analysis"]

# Convenience functions for direct agent access
async def analyze_market_regime(market_data: Dict[str, Any], user_id: Optional[str] = None) -> Dict[str, Any]:
    """Convenience function for market regime analysis"""
    agent = MarketRegimeAgent()
    return await agent.analyze_current_conditions(market_data, user_id)

async def analyze_volatility_surface(options_data: Dict[str, Any], user_id: Optional[str] = None) -> Dict[str, Any]:
    """Convenience function for volatility surface analysis"""
    agent = VolatilitySurfaceAgent()
    return await agent.analyze_iv_environment(options_data, user_id)

async def analyze_support_resistance(price_data: Dict[str, Any], user_id: Optional[str] = None) -> Dict[str, Any]:
    """Convenience function for support/resistance analysis"""
    agent = SupportResistanceAgent()
    return await agent.analyze_key_levels(price_data, user_id)

async def analyze_liquidity(options_chain_data: Dict[str, Any], user_id: Optional[str] = None) -> Dict[str, Any]:
    """Convenience function for liquidity analysis"""
    agent = LiquidityAnalysisAgent()
    return await agent.analyze_options_liquidity(options_chain_data, user_id)