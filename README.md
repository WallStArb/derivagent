# Derivagent - AI-Powered Derivatives Trading Platform

**Democratizing institutional-grade derivatives trading through autonomous AI agents**

## 🚀 Quick Start

### Prerequisites
- **Python 3.11+** (for backend)
- **Node.js 18+** (for frontend)
- **API Keys**: DeepSeek and OpenRouter (optional for demo mode)

### 1. Start the Backend

```bash
cd backend
./start.sh
```

The backend will be available at:
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### 2. Start the Frontend

```bash
cd frontend
./start.sh
```

The frontend will be available at:
- **Dashboard**: http://localhost:3000

### 3. Explore the Platform

**🎯 Dashboard**: Real-time market intelligence from 4 AI agents
- Market Regime Analysis (DeepSeek R1)
- Volatility Surface Analysis (Grok 3 Mini)  
- Support & Resistance Levels (QwQ 32B)
- Liquidity Assessment (QwQ 32B)

**🧠 Market Intelligence**: Agent details and capabilities

**💼 Accounts**: Multi-broker account management (demo)

**👥 Teams**: Collaborative trading team features (demo)

**⚙️ Settings**: AI agent configuration and preferences

## 🔑 API Keys Setup (Optional)

For live AI analysis, add your API keys to `backend/.env`:

```bash
# Copy the template
cp .env.example backend/.env

# Edit with your keys
DEEPSEEK_API_KEY=sk-your-deepseek-key-here
OPENROUTER_API_KEY=sk-or-v1-your-openrouter-key-here
```

**Without API keys**: The platform runs in demo mode with simulated data.

## 🧪 Testing the API

Test all agents at once:
```bash
curl http://localhost:8000/test/agents
```

Test individual agents:
```bash
# Market Regime Agent
curl -X POST http://localhost:8000/agents/market-regime \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Analyze current market conditions", "context": {"vix_level": 16.5}}'
```

## 📚 Architecture

**Backend**: FastAPI + LiteLLM + Multi-tier AI routing
**Frontend**: React 19 + TypeScript + Vite + Tailwind CSS
**AI Models**: DeepSeek R1 (reasoning) + QwQ 32B (cost) + Grok 3 Mini (speed)

## 🚂 Railway Deployment

Deploy your backend to Railway for production hosting:

### Quick Deploy
```bash
# Run the deployment script
./deploy_railway.sh

# Or deploy manually:
npm install -g @railway/cli
railway login
railway init
railway up
```

### Environment Variables
Set these in Railway dashboard or via CLI:
```bash
railway variables set DEEPSEEK_API_KEY=your-key-here
railway variables set OPENROUTER_API_KEY=your-key-here
railway variables set SUPABASE_URL=your-supabase-url
railway variables set SUPABASE_ANON_KEY=your-supabase-key
```

### Deployment URLs
- **API**: `https://your-app-name.railway.app`
- **API Docs**: `https://your-app-name.railway.app/docs`
- **Health Check**: `https://your-app-name.railway.app/health`

## 🎯 Current Status

✅ **Week 1 Complete**: AI agents + basic UI  
✅ **Week 2 In Progress**: Polish + Railway deployment  

## 🆘 Troubleshooting

**Backend won't start?**
- Check Python 3.11+ is installed: `python3 --version`
- Install dependencies manually: `pip install -r requirements.txt`

**Frontend won't start?**
- Check Node.js 18+ is installed: `node --version`
- Install dependencies manually: `npm install`

**API errors?**
- Check backend is running on port 8000
- Verify `.env` file exists in backend directory
- Check API health: http://localhost:8000/health

## 📞 Support

See `CLAUDE.md` for detailed development guidance and architecture documentation.

---

**🎉 You're now running Derivagent locally!**