#!/bin/bash
# Railway Deployment Script for Derivagent Backend

echo "🚂 Setting up Railway deployment for Derivagent..."

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Installing..."
    npm install -g @railway/cli
fi

# Check if we're in the right directory
if [ ! -f "railway.json" ]; then
    echo "❌ Please run this script from the project root directory"
    exit 1
fi

echo "✅ Railway configuration files created:"
echo "   - railway.json (project config)"
echo "   - backend/railway.toml (service config)"
echo "   - backend/Procfile (deployment command)"

echo ""
echo "📋 Next steps to deploy:"
echo ""
echo "1. Install Railway CLI (if not already installed):"
echo "   npm install -g @railway/cli"
echo ""
echo "2. Login to Railway:"
echo "   railway login"
echo ""
echo "3. Initialize Railway project:"
echo "   railway init"
echo ""
echo "4. Add environment variables:"
echo "   railway variables set DEEPSEEK_API_KEY=your-key-here"
echo "   railway variables set OPENROUTER_API_KEY=your-key-here"
echo "   railway variables set SUPABASE_URL=your-supabase-url"
echo "   railway variables set SUPABASE_ANON_KEY=your-supabase-key"
echo ""
echo "5. Deploy to Railway:"
echo "   railway up"
echo ""
echo "6. Get your deployment URL:"
echo "   railway status"
echo ""
echo "🎯 Your API will be available at: https://your-app-name.railway.app"
echo "📖 API docs will be at: https://your-app-name.railway.app/docs"
echo "💚 Health check: https://your-app-name.railway.app/health" 