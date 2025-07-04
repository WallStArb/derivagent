#!/bin/bash
# Install Derivagent React Frontend Stack
# Run this only if you want the advanced React features

echo "🎨 Installing Derivagent React Frontend..."

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required. Install from: https://nodejs.org/"
    exit 1
fi

echo "✅ Node.js $(node --version) detected"

# Navigate to frontend directory
cd frontend || exit 1

echo "📦 Installing React dependencies..."
echo "This includes:"
echo "   • React 19 + TypeScript"
echo "   • Vite (build tool)" 
echo "   • Tailwind CSS (styling)"
echo "   • Lucide React (icons)"
echo "   • React Query (API state)"
echo "   • React Router (navigation)"
echo ""

# Install dependencies
npm install

echo ""
echo "🎯 Frontend installation complete!"
echo ""
echo "🚀 To start the React frontend:"
echo "   cd frontend"
echo "   npm run dev"
echo ""
echo "📱 React app will run on: http://localhost:3000"
echo "🔗 Backend API runs on: http://localhost:8001"
echo ""
echo "💡 Your HTML demo is already working great!"
echo "   Only install React if you need advanced features."