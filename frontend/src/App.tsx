import { Routes, Route } from 'react-router-dom'
import { useEffect } from 'react'

// Layout components
import Sidebar from '@/components/layout/Sidebar'
import Header from '@/components/layout/Header'

// Page components
import Dashboard from '@/pages/Dashboard'
import MarketIntelligence from '@/pages/MarketIntelligence'
import Monitoring from '@/pages/Monitoring'
import Accounts from '@/pages/Accounts'
import Teams from '@/pages/Teams'
import Settings from '@/pages/Settings'

// Utility imports
import { cn } from '@/lib/utils'

function App() {
  useEffect(() => {
    // Set up theme detection
    const isDark = localStorage.getItem('theme') === 'dark' || 
      (!localStorage.getItem('theme') && window.matchMedia('(prefers-color-scheme: dark)').matches)
    
    if (isDark) {
      document.documentElement.classList.add('dark')
    }
  }, [])

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="flex h-screen">
        {/* Sidebar */}
        <Sidebar />
        
        {/* Main content area */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Header */}
          <Header />
          
          {/* Page content */}
          <main className="flex-1 overflow-auto">
            <div className="container mx-auto px-4 py-6">
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/market-intelligence" element={<MarketIntelligence />} />
                <Route path="/monitoring" element={<Monitoring />} />
                <Route path="/accounts" element={<Accounts />} />
                <Route path="/teams" element={<Teams />} />
                <Route path="/settings" element={<Settings />} />
              </Routes>
            </div>
          </main>
        </div>
      </div>
    </div>
  )
}

export default App