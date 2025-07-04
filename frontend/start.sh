#!/bin/bash
# Derivagent Frontend Startup Script

echo "🎨 Starting Derivagent Frontend..."

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+ first."
    echo "💡 You can install it from: https://nodejs.org/"
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo "❌ Please run this script from the frontend directory"
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Copy environment file if it doesn't exist
if [ ! -f ".env.local" ]; then
    echo "⚙️  Creating .env.local file from template..."
    cp .env.example .env.local
fi

# Start the development server
echo "🌟 Starting Vite development server..."
echo "🔗 Frontend will be available at: http://localhost:3000"
echo "🔄 API proxy configured to: http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

npm run dev