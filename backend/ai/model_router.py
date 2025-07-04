"""
Secure Model Router for Derivagent AI Agents
Implements multi-tier LiteLLM routing with DeepSeek + OpenRouter
"""

import litellm
from litellm import Router
import os
import json
import logging
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
from datetime import datetime
import asyncio

# Load environment variables securely
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SecurityError(Exception):
    """Raised when security requirements are not met"""
    pass

class ModelRouterError(Exception):
    """Raised when model routing fails"""
    pass

class SecureModelRouter:
    """
    Secure LiteLLM router implementing Derivagent's multi-tier AI strategy
    
    Features:
    - DeepSeek R1 for complex reasoning (99% MATH-500)
    - OpenRouter for cost optimization and backups
    - Automatic failover and retry logic
    - Usage tracking and cost monitoring
    - Security-first implementation
    """
    
    def __init__(self, config_path: str = "config/model_config.json"):
        """Initialize secure model router with validation"""
        self.logger = logging.getLogger(__name__)
        self._validate_environment()
        self._load_configuration(config_path)
        self._initialize_router()
        self._setup_monitoring()
        
        # Test connections without exposing sensitive data
        self._test_connections()
        
        self.logger.info("✅ Derivagent Secure Model Router initialized successfully")
    
    def _validate_environment(self):
        """Validate all required environment variables are present"""
        required_keys = [
            'DEEPSEEK_API_KEY',
            'OPENROUTER_API_KEY',
            'LITELLM_MASTER_KEY'
        ]
        
        missing_keys = []
        for key in required_keys:
            value = os.getenv(key)
            if not value:
                missing_keys.append(key)
            elif len(value) < 10:  # Basic validation
                self.logger.warning(f"Suspiciously short key for {key}")
        
        if missing_keys:
            raise SecurityError(f"Missing required environment variables: {missing_keys}")
        
        self.logger.info("✅ Environment variables validated")
    
    def _load_configuration(self, config_path: str):
        """Load and validate model configuration"""
        try:
            with open(config_path, 'r') as f:
                self.config = json.load(f)
            
            # Validate configuration structure
            required_sections = ['model_list', 'router_settings', 'agent_routing']
            for section in required_sections:
                if section not in self.config:
                    raise ValueError(f"Missing configuration section: {section}")
            
            self.agent_routes = self.config['agent_routing']
            self.cost_config = self.config.get('cost_tracking', {})
            
            self.logger.info(f"✅ Configuration loaded: {len(self.config['model_list'])} models")
            
        except FileNotFoundError:
            raise ModelRouterError(f"Configuration file not found: {config_path}")
        except json.JSONDecodeError as e:
            raise ModelRouterError(f"Invalid JSON in configuration: {e}")
    
    def _initialize_router(self):
        """Initialize LiteLLM router with loaded configuration"""
        try:
            # Create router with just the model list (other settings are for internal use)
            self.router = Router(
                model_list=self.config['model_list']
            )
            
            # Set global LiteLLM settings
            litellm.drop_params = True  # Drop unsupported parameters
            litellm.set_verbose = False  # Reduce logging noise
            
            self.logger.info("✅ LiteLLM router initialized")
            
        except Exception as e:
            raise ModelRouterError(f"Failed to initialize router: {e}")
    
    def _setup_monitoring(self):
        """Setup usage monitoring and cost tracking"""
        self.usage_stats = {
            'total_requests': 0,
            'total_tokens': 0,
            'total_cost_usd': 0.0,
            'requests_by_agent': {},
            'requests_by_model': {},
            'daily_cost': 0.0,
            'last_reset': datetime.now().date()
        }
        
        self.logger.info("✅ Monitoring system initialized")
    
    def _test_connections(self):
        """Test API connections without exposing keys"""
        try:
            # Test DeepSeek connection
            test_messages = [{"role": "user", "content": "1+1=?"}]
            
            response = litellm.completion(
                model="deepseek/deepseek-r1",
                messages=test_messages,
                max_tokens=10,
                api_key=os.getenv('DEEPSEEK_API_KEY')
            )
            self.logger.info("✅ DeepSeek connection: OK")
            
        except Exception as e:
            self.logger.error(f"❌ DeepSeek connection failed: {str(e)[:100]}...")
            # Don't raise - allow degraded operation
        
        try:
            # Test OpenRouter connection  
            response = litellm.completion(
                model="openrouter/qwen/qwq-32b-preview",
                messages=test_messages,
                max_tokens=10,
                api_key=os.getenv('OPENROUTER_API_KEY')
            )
            self.logger.info("✅ OpenRouter connection: OK")
            
        except Exception as e:
            self.logger.error(f"❌ OpenRouter connection failed: {str(e)[:100]}...")
    
    async def get_completion(
        self,
        agent_name: str,
        messages: List[Dict[str, str]],
        user_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Get AI completion for specified agent
        
        Args:
            agent_name: Name of the requesting agent
            messages: List of message dicts for the conversation
            user_id: Optional user ID for tracking
            **kwargs: Additional parameters for the model
            
        Returns:
            Dictionary containing response and metadata
        """
        
        # Route to appropriate model tier
        tier = self.agent_routes.get(agent_name, "cost")
        model_name = f"{tier}-primary"
        
        self.logger.info(f"🤖 Agent '{agent_name}' → {model_name} ({tier} tier)")
        
        try:
            # Track request
            self._track_request_start(agent_name, model_name, user_id)
            
            # Get completion from router
            response = await self.router.acompletion(
                model=model_name,
                messages=messages,
                temperature=kwargs.get('temperature', 0.1),
                max_tokens=kwargs.get('max_tokens', 2000),
                **{k: v for k, v in kwargs.items() if k not in ['temperature', 'max_tokens']}
            )
            
            # Track usage and costs
            self._track_completion(agent_name, model_name, response, user_id)
            
            return {
                'success': True,
                'response': response,
                'agent': agent_name,
                'model': model_name,
                'tier': tier,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Model error for agent '{agent_name}': {str(e)[:150]}...")
            
            # Attempt fallback
            try:
                fallback_result = await self._handle_fallback(agent_name, messages, **kwargs)
                return fallback_result
            except Exception as fallback_error:
                self.logger.error(f"❌ All fallbacks failed: {str(fallback_error)[:100]}...")
                
                return {
                    'success': False,
                    'error': str(e),
                    'agent': agent_name,
                    'timestamp': datetime.now().isoformat()
                }
    
    async def _handle_fallback(
        self, 
        agent_name: str, 
        messages: List[Dict[str, str]], 
        **kwargs
    ) -> Dict[str, Any]:
        """Handle model failures with intelligent fallback"""
        
        tier = self.agent_routes.get(agent_name, "cost")
        fallback_models = self.config['router_settings']['fallback_models'][tier]
        
        for model in fallback_models[1:]:  # Skip primary (already failed)
            try:
                self.logger.info(f"🔄 Attempting fallback: {model}")
                
                response = await self.router.acompletion(
                    model=model,
                    messages=messages,
                    temperature=kwargs.get('temperature', 0.1),
                    max_tokens=kwargs.get('max_tokens', 2000)
                )
                
                self._track_completion(agent_name, model, response, None, is_fallback=True)
                
                return {
                    'success': True,
                    'response': response,
                    'agent': agent_name,
                    'model': model,
                    'tier': tier,
                    'fallback': True,
                    'timestamp': datetime.now().isoformat()
                }
                
            except Exception as e:
                self.logger.warning(f"⚠️ Fallback model {model} failed: {str(e)[:100]}...")
                continue
        
        raise ModelRouterError(f"All fallback models failed for agent {agent_name}")
    
    def _track_request_start(self, agent_name: str, model_name: str, user_id: Optional[str]):
        """Track request initiation"""
        self.usage_stats['total_requests'] += 1
        
        if agent_name not in self.usage_stats['requests_by_agent']:
            self.usage_stats['requests_by_agent'][agent_name] = 0
        self.usage_stats['requests_by_agent'][agent_name] += 1
        
        if model_name not in self.usage_stats['requests_by_model']:
            self.usage_stats['requests_by_model'][model_name] = 0
        self.usage_stats['requests_by_model'][model_name] += 1
    
    def _track_completion(
        self, 
        agent_name: str, 
        model_name: str, 
        response: Any, 
        user_id: Optional[str],
        is_fallback: bool = False
    ):
        """Track completion usage and costs"""
        
        if not hasattr(response, 'usage') or not response.usage:
            return
        
        usage = response.usage
        total_tokens = getattr(usage, 'total_tokens', 0)
        
        # Update token count
        self.usage_stats['total_tokens'] += total_tokens
        
        # Estimate cost based on model
        cost_per_million = self._get_model_cost(model_name)
        estimated_cost = (total_tokens / 1_000_000) * cost_per_million
        
        self.usage_stats['total_cost_usd'] += estimated_cost
        self.usage_stats['daily_cost'] += estimated_cost
        
        # Reset daily cost if new day
        today = datetime.now().date()
        if today != self.usage_stats['last_reset']:
            self.usage_stats['daily_cost'] = estimated_cost
            self.usage_stats['last_reset'] = today
        
        # Log usage (without sensitive data)
        status = "FALLBACK" if is_fallback else "SUCCESS"
        self.logger.info(
            f"📊 {status} | Agent: {agent_name} | Tokens: {total_tokens} | "
            f"Cost: ${estimated_cost:.4f} | Daily: ${self.usage_stats['daily_cost']:.2f}"
        )
        
        # Check budget alerts
        self._check_budget_alerts()
    
    def _get_model_cost(self, model_name: str) -> float:
        """Get cost per million tokens for model"""
        for model_config in self.config['model_list']:
            if model_config['model_name'] == model_name:
                return model_config['model_info'].get('cost_per_million_tokens', 1.0)
        return 1.0  # Default fallback cost
    
    def _check_budget_alerts(self):
        """Check if budget thresholds are exceeded"""
        daily_budget = self.cost_config.get('daily_budget_usd', 10.0)
        threshold = self.cost_config.get('alert_threshold_percent', 80.0) / 100.0
        
        if self.usage_stats['daily_cost'] > (daily_budget * threshold):
            self.logger.warning(
                f"⚠️ BUDGET ALERT: Daily cost ${self.usage_stats['daily_cost']:.2f} "
                f"exceeds {threshold*100}% of ${daily_budget} budget"
            )
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics"""
        return self.usage_stats.copy()
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get router health status"""
        return {
            'status': 'healthy',
            'models_configured': len(self.config['model_list']),
            'agents_configured': len(self.agent_routes),
            'total_requests': self.usage_stats['total_requests'],
            'daily_cost_usd': self.usage_stats['daily_cost'],
            'router_initialized': hasattr(self, 'router')
        }

# Global router instance (singleton pattern)
_router: Optional[SecureModelRouter] = None

def get_router() -> SecureModelRouter:
    """Get or create secure router singleton"""
    global _router
    if _router is None:
        _router = SecureModelRouter()
    return _router

async def test_router():
    """Test function for router functionality"""
    router = get_router()
    
    test_messages = [
        {
            "role": "user", 
            "content": "Analyze if current market conditions favor MEIC strategies. Consider VIX at 16.5 and SPX trading in a 5000-5100 range."
        }
    ]
    
    result = await router.get_completion(
        agent_name="market_regime",
        messages=test_messages
    )
    
    print("Test Result:", result)
    return result

if __name__ == "__main__":
    # Test the router
    asyncio.run(test_router())