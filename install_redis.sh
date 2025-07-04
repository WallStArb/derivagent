#!/bin/bash
# Install Redis for Derivagent Platform
# Run this if you want caching and real-time features

echo "🔴 Installing Redis for Derivagent..."

# Check OS and install Redis
if command -v apt &> /dev/null; then
    echo "📦 Installing Redis via apt..."
    sudo apt update
    sudo apt install redis-server -y
elif command -v brew &> /dev/null; then
    echo "📦 Installing Redis via Homebrew..."
    brew install redis
else
    echo "❌ Package manager not found. Install Redis manually."
    exit 1
fi

# Start Redis service
echo "🚀 Starting Redis service..."
if command -v systemctl &> /dev/null; then
    sudo systemctl start redis-server
    sudo systemctl enable redis-server
else
    redis-server --daemonize yes
fi

# Test Redis connection
echo "🧪 Testing Redis connection..."
sleep 2
if redis-cli ping; then
    echo "✅ Redis successfully installed and running!"
    echo "🔗 Redis URL: redis://localhost:6379"
    echo ""
    echo "💡 Redis is now ready for:"
    echo "   • Market data caching"
    echo "   • Session management" 
    echo "   • Real-time updates"
else
    echo "❌ Redis installation failed"
    exit 1
fi