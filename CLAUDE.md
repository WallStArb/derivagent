# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an **Agentic Derivatives Trading Platform** - an autonomous AI-powered system for options and derivatives trading. The platform uses multi-agent coordination with LangGraph orchestration to execute complex trading strategies with sub-second decision-making capabilities.

**Core Mission**: Deploy autonomous GenAI agents that independently identify opportunities, analyze risk, and execute trades across derivative markets with minimal human intervention while maintaining appropriate oversight and compliance.

## High-Level Architecture

### Multi-Agent System Design
- **Market Intelligence Agent**: Continuous market monitoring, regime detection, volatility analysis
- **Strategy Generation Agents**: Specialized agents for iron condors, calendar spreads, gamma scalping
- **Risk Management Agent**: Real-time portfolio monitoring, VaR calculations, emergency controls
- **Execution Agent**: Broker routing, fill optimization, latency minimization

### Technology Stack Foundation
```
Infrastructure: Supabase Cloud + Railway + Redis + HashiCorp Vault
AI Framework: LangGraph + LangChain + LiteLLM (multi-provider routing)
Backend: FastAPI (Python) with async processing
Frontend: React 19+ + TypeScript + Shadcn UI + CopilotKit
Financial: QuantLib + py_vollib + TA-Lib + pandas/numpy
Market Data: Polygon.io + Alpha Vantage + CBOE DataShop
Brokers: TastyTrade, IBKR, TradeStation, MEXEM, Tradier, Schwab
```

## Development Commands

### Backend Development (FastAPI)
```bash
# Start development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Run with auto-reload and debug logging
uvicorn main:app --reload --log-level debug

# Production deployment
uvicorn main:app --host 0.0.0.0 --port $PORT --workers 4

# Health check endpoint
curl http://localhost:8000/health
```

### Frontend Development (React + TypeScript)
```bash
# Start development server
npm run dev
# or
yarn dev

# Build for production
npm run build
yarn build

# Type checking
npm run type-check
yarn type-check

# Linting
npm run lint
yarn lint
```

### AI Agent Development
```bash
# Test LangGraph workflows
python -m pytest tests/agents/ -v

# Run specific agent tests
python -m pytest tests/agents/test_market_intelligence.py::test_regime_detection

# Test AI model routing
python -m pytest tests/ai/test_litellm_routing.py

# Validate agent communication protocols
python -m pytest tests/protocols/test_a2a_communication.py
```

### Database Operations (Supabase)
```bash
# Run database migrations
supabase db push

# Reset database to migration state
supabase db reset

# Generate TypeScript types from schema
supabase gen types typescript --local > types/database.ts

# Start local Supabase instance
supabase start

# View database in dashboard
supabase studio
```

### Financial Calculations Testing
```bash
# Test options pricing accuracy
python -m pytest tests/pricing/test_black_scholes.py

# Validate Greeks calculations
python -m pytest tests/pricing/test_greeks.py

# Test volatility modeling
python -m pytest tests/pricing/test_volatility.py

# Performance benchmark pricing engine
python scripts/benchmark_pricing.py
```

### Integration Testing
```bash
# Test broker integrations
python -m pytest tests/brokers/ -v

# Test market data feeds
python -m pytest tests/market_data/test_polygon_integration.py

# Test real-time WebSocket connections
python -m pytest tests/websockets/

# End-to-end trading workflow test
python -m pytest tests/e2e/test_full_trading_cycle.py
```

### Performance & Load Testing
```bash
# Benchmark agent response times
python scripts/benchmark_agents.py

# Test Redis caching performance
python scripts/test_cache_performance.py

# Load test market data processing
python scripts/load_test_market_data.py

# Validate sub-second decision requirements
python scripts/validate_latency_requirements.py
```

## Critical Performance Requirements

### Speed Targets (Non-Negotiable)
- **Redis Cache Access**: <1ms for market data, positions, cached strategies
- **AI Agent Decisions**: 300-2000ms for complex analysis (with <1ms cached results)
- **Emergency Controls**: <100ms for position halts and risk breaches
- **WebSocket Market Data**: <50ms for live price updates
- **Broker Execution**: 200-1000ms for order routing and fills

### Mathematical Precision Standards
- **Options Pricing Accuracy**: 99%+ accuracy vs market prices
- **Greeks Calculations**: Real-time delta, gamma, theta, vega with <1% error tolerance
- **Risk Calculations**: VaR, correlation analysis updated in real-time
- **Strategy Optimization**: Continuous parameter adjustment during market hours

## Database Schema Principles

### Team Isolation via Row-Level Security (RLS)
All financial data must be automatically isolated by team using Supabase RLS policies:
```sql
-- Example pattern for all financial tables
CREATE POLICY "Team members access team data only" 
ON [table_name] FOR ALL 
USING (team_id IN (
  SELECT team_id FROM team_members 
  WHERE user_id = auth.uid()
));
```

### Core Data Models
- **Teams & Users**: Multi-tenant architecture with role-based permissions
- **Strategies**: AI-generated and human-designed trading strategies
- **Positions**: Real-time portfolio state with Greeks tracking
- **Executions**: Complete trade history with performance attribution
- **Market Data**: Cached pricing, volatility surfaces, economic indicators
- **Agent Memory**: Temporal knowledge graphs via pgvector integration

## AI Model Management

### Multi-Tier Routing Strategy
```python
# Speed Tier (Real-time Trading)
SPEED_MODELS = {
    'primary': 'grok-3-mini',      # $0.35/M, 96% MATH-500, 0.33s
    'backup': 'qwen3-32b',         # $0.15/M, 93% MATH-500, 0.36s  
    'tertiary': 'gemini-2.5-flash' # $0.17/M, 84% MATH-500, 0.44s
}

# Cost Tier (High-Volume Processing)
COST_MODELS = {
    'primary': 'qwq-32b',          # $0.11/M, 91% MATH-500, 0.43s
    'backup': 'qwen3-32b',         # $0.15/M, 93% MATH-500, 0.36s
}

# Reasoning Tier (Complex Analysis)
REASONING_MODELS = {
    'primary': 'deepseek-r1',      # $0.95/M, 99% MATH-500, 0.38s
    'backup': 'grok-3-mini',       # $0.35/M, 96% MATH-500, 0.33s
}
```

### Cost Optimization Rules
- Use Speed Tier for time-critical trading decisions (<500ms required)
- Use Cost Tier for high-volume market analysis and backtesting
- Use Reasoning Tier for complex mathematical modeling and new strategy generation
- Cache AI responses in Redis to minimize repeat API calls
- Target <$0.005 per user per month across all AI usage

## Security & Compliance Requirements

### Financial Data Protection
- All broker credentials stored in HashiCorp Vault with automatic rotation
- Complete audit logging for every trading decision and human approval
- Team-based data isolation enforced at database level via RLS
- Encryption at rest (AES-256) and in transit (TLS 1.3)

### Human-in-the-Loop (HITL) Triggers
```python
# Risk-based escalation rules
ESCALATION_RULES = {
    'auto_execute': {'max_value': 1000, 'delay': '0ms'},
    'trader_approval': {'max_value': 10000, 'delay': '<30s'},
    'risk_manager': {'max_value': 50000, 'delay': '<2min'},
    'emergency_halt': {'risk_breach': True, 'delay': '<10s'}
}
```

## Multi-Broker Integration

### Supported Brokers
All broker integrations use standardized Pydantic models with intelligent routing:
- **TastyTrade**: Primary for options trading, competitive spreads
- **Interactive Brokers**: Institutional-grade execution, global markets
- **TradeStation**: Advanced options analytics
- **MEXEM**: European market access
- **Tradier**: Commission-free options
- **Charles Schwab**: Full-service integration

### Execution Quality Optimization
The platform continuously monitors fill quality across brokers and routes orders to optimize:
- Bid-ask spread minimization
- Fill probability maximization  
- Latency minimization for time-sensitive strategies
- Commission cost optimization

## Agent Communication Protocols

### A2A (Agent-to-Agent): Millisecond coordination
- Market Intelligence → Strategy Agents: Regime changes, volatility alerts
- Strategy Agents → Risk Manager: Proposed trades, position changes
- Risk Manager → Execution Agent: Approved trades, position limits
- All Agents → Memory System: Decision outcomes, performance data

### AG-UI (Agent-to-User): Real-time notifications
- High-value trade approvals requiring human validation
- Risk breach alerts requiring immediate attention
- Strategy performance summaries and recommendations
- System status and emergency notifications

### MCP (Model Context Protocol): Broker integration
- Standardized order format across all supported brokers
- Real-time position synchronization
- Execution quality feedback for routing optimization
- Emergency halt capabilities across all connections

## Testing Strategy

### Critical Test Categories
1. **Mathematical Accuracy**: Options pricing models vs real market data
2. **Latency Validation**: All operations meet speed requirements
3. **Agent Coordination**: Multi-agent workflows complete successfully
4. **Broker Integration**: Order execution across all supported brokers
5. **Risk Management**: Emergency procedures and position limits
6. **Data Isolation**: Team-based security enforcement
7. **HITL Workflows**: Human approval processes and escalations

### Performance Benchmarks
Run these regularly to ensure platform meets trading requirements:
```bash
# Validate sub-second agent decisions
python scripts/benchmark_agent_speed.py --target-latency 1000

# Test market data processing throughput  
python scripts/test_data_throughput.py --target-msgs-per-sec 10000

# Verify Redis cache performance
python scripts/test_cache_latency.py --target-latency 1

# Validate broker execution speeds
python scripts/test_broker_latency.py --target-latency 500
```

This platform prioritizes defensive security practices and legitimate trading operations while delivering institutional-grade performance for derivatives trading.