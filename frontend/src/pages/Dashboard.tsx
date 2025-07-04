import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { 
  TrendingUp, 
  TrendingDown, 
  Activity, 
  Target, 
  Brain,
  RefreshCw,
  AlertTriangle,
  CheckCircle
} from 'lucide-react'

import { api } from '@/lib/api'
import { cn, formatTimeAgo, getVixClassification } from '@/lib/utils'
import LiveMarketTest from '@/components/LiveMarketTest'

interface MarketMetric {
  label: string
  value: string
  change: string
  positive: boolean
  icon: React.ElementType
}

const sampleMarketData = {
  vix_level: 16.5,
  spx_price: 5050,
  market_breadth: 'neutral',
  adx: 22.5,
  rsi: 48,
  volume: 1250000
}

export default function Dashboard() {
  const [isRefreshing, setIsRefreshing] = useState(false)

  // Health check query
  const { data: healthData, isLoading: healthLoading } = useQuery({
    queryKey: ['health'],
    queryFn: () => api.health(),
    refetchInterval: 30000, // Refresh every 30 seconds
  })

  // Market intelligence query
  const { 
    data: marketIntelligence, 
    isLoading: intelligenceLoading, 
    error: intelligenceError,
    refetch: refetchIntelligence 
  } = useQuery({
    queryKey: ['market-intelligence'],
    queryFn: () => api.getMarketIntelligence(sampleMarketData),
    refetchInterval: 5 * 60 * 1000, // Refresh every 5 minutes
    retry: 1,
  })

  // Manual refresh handler
  const handleRefresh = async () => {
    setIsRefreshing(true)
    await refetchIntelligence()
    setTimeout(() => setIsRefreshing(false), 1000) // Visual feedback
  }

  // Sample market metrics
  const marketMetrics: MarketMetric[] = [
    {
      label: 'SPX Price',
      value: '5,050.25',
      change: '+0.65%',
      positive: true,
      icon: TrendingUp
    },
    {
      label: 'VIX Level',
      value: '16.5',
      change: '-2.1%',
      positive: true,
      icon: Activity
    },
    {
      label: 'Volume',
      value: '1.25M',
      change: '+15.2%',
      positive: true,
      icon: Target
    },
    {
      label: 'IV Rank',
      value: '23%',
      change: '-8.5%',
      positive: false,
      icon: TrendingDown
    }
  ]

  const vixClassification = getVixClassification(16.5)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Trading Dashboard
          </h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            AI-powered market intelligence and trading insights
          </p>
        </div>
        
        <div className="flex items-center space-x-3">
          {/* System status */}
          <div className="flex items-center space-x-2">
            {healthLoading ? (
              <div className="status-indicator status-analyzing" />
            ) : healthData?.status === 'healthy' ? (
              <CheckCircle className="h-5 w-5 text-green-500" />
            ) : (
              <AlertTriangle className="h-5 w-5 text-red-500" />
            )}
            <span className="text-sm text-gray-600 dark:text-gray-400">
              {healthLoading ? 'Checking...' : healthData?.status || 'Unknown'}
            </span>
          </div>

          {/* Refresh button */}
          <button
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="flex items-center space-x-2 px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:opacity-50 transition-colors"
          >
            <RefreshCw className={cn('h-4 w-4', isRefreshing && 'animate-spin')} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Market Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {marketMetrics.map((metric, index) => (
          <div key={index} className="trading-card">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-gray-100 dark:bg-gray-700 rounded-lg">
                  <metric.icon className="h-5 w-5 text-gray-600 dark:text-gray-400" />
                </div>
                <div>
                  <div className="market-metric">
                    <div className="market-metric-label">{metric.label}</div>
                    <div className="market-metric-value">{metric.value}</div>
                  </div>
                </div>
              </div>
              <div className={cn(
                'market-metric-change',
                metric.positive ? 'positive' : 'negative'
              )}>
                {metric.positive ? (
                  <TrendingUp className="h-4 w-4 mr-1" />
                ) : (
                  <TrendingDown className="h-4 w-4 mr-1" />
                )}
                {metric.change}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Market Intelligence */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Market Regime Analysis */}
        <div className="trading-card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center">
              <Brain className="h-5 w-5 mr-2 text-primary-600" />
              Market Regime
            </h3>
            <span className={cn(
              'agent-badge',
              intelligenceLoading ? 'analyzing' : 
              marketIntelligence?.marketRegime?.success ? 'active' : 'error'
            )}>
              {intelligenceLoading ? 'Analyzing...' : 
               marketIntelligence?.marketRegime?.success ? 'Active' : 'Error'}
            </span>
          </div>

          {intelligenceLoading ? (
            <div className="space-y-3">
              <div className="loading-shimmer h-4 rounded"></div>
              <div className="loading-shimmer h-4 rounded w-3/4"></div>
              <div className="loading-shimmer h-4 rounded w-1/2"></div>
            </div>
          ) : intelligenceError ? (
            <div className="flex items-center space-x-2 text-red-600 dark:text-red-400">
              <AlertTriangle className="h-4 w-4" />
              <span>Failed to load market regime analysis</span>
            </div>
          ) : marketIntelligence?.marketRegime?.success ? (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  Current Regime
                </span>
                <span className="px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded-md text-sm font-medium">
                  Range-bound
                </span>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  VIX Classification
                </span>
                <span className={cn('text-sm font-medium', vixClassification.color)}>
                  {vixClassification.level}
                </span>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  MEIC Favorable
                </span>
                <CheckCircle className="h-5 w-5 text-green-500" />
              </div>
              
              <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Last updated: {formatTimeAgo(marketIntelligence.marketRegime.timestamp)}
                </p>
              </div>
            </div>
          ) : (
            <div className="text-center py-4">
              <p className="text-gray-500 dark:text-gray-400">No data available</p>
            </div>
          )}
        </div>

        {/* Volatility Surface */}
        <div className="trading-card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center">
              <Activity className="h-5 w-5 mr-2 text-accent-600" />
              Volatility Surface
            </h3>
            <span className={cn(
              'agent-badge',
              intelligenceLoading ? 'analyzing' : 
              marketIntelligence?.volatilitySurface?.success ? 'active' : 'error'
            )}>
              {intelligenceLoading ? 'Analyzing...' : 
               marketIntelligence?.volatilitySurface?.success ? 'Active' : 'Error'}
            </span>
          </div>

          {intelligenceLoading ? (
            <div className="space-y-3">
              <div className="loading-shimmer h-4 rounded"></div>
              <div className="loading-shimmer h-4 rounded w-3/4"></div>
              <div className="loading-shimmer h-4 rounded w-1/2"></div>
            </div>
          ) : (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  IV Rank
                </span>
                <span className="text-sm font-medium text-yellow-600">
                  23rd percentile
                </span>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  Term Structure
                </span>
                <span className="text-sm font-medium text-green-600">
                  Normal
                </span>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  Premium Selling
                </span>
                <span className="text-sm font-medium text-red-600">
                  Unfavorable
                </span>
              </div>
              
              <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Simulated data - Connect API for live analysis
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Support/Resistance and Liquidity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Support & Resistance */}
        <div className="trading-card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center">
              <Target className="h-5 w-5 mr-2 text-green-600" />
              Support & Resistance
            </h3>
            <span className="agent-badge active">Simulated</span>
          </div>

          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                Resistance
              </span>
              <span className="text-sm font-medium text-red-600">
                5,100
              </span>
            </div>
            
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                Current Price
              </span>
              <span className="text-sm font-medium text-gray-900 dark:text-white">
                5,050
              </span>
            </div>
            
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                Support
              </span>
              <span className="text-sm font-medium text-green-600">
                5,000
              </span>
            </div>
            
            <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  Range Width
                </span>
                <span className="text-sm font-medium text-blue-600">
                  100 points (2.0%)
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Liquidity Analysis */}
        <div className="trading-card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center">
              <Activity className="h-5 w-5 mr-2 text-blue-600" />
              Liquidity Analysis
            </h3>
            <span className="agent-badge active">Simulated</span>
          </div>

          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                Overall Rating
              </span>
              <span className="text-sm font-medium text-green-600">
                Excellent
              </span>
            </div>
            
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                Bid-Ask Spread
              </span>
              <span className="text-sm font-medium text-green-600">
                $0.05 (0.1%)
              </span>
            </div>
            
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                Volume (24h)
              </span>
              <span className="text-sm font-medium text-blue-600">
                12.5K contracts
              </span>
            </div>
            
            <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  MEIC Suitable
                </span>
                <CheckCircle className="h-5 w-5 text-green-500" />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* AI Agent Status */}
      <div className="trading-card">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          AI Agent Status
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {healthData?.agents_available?.map((agent, index) => (
            <div key={agent} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <div>
                <p className="text-sm font-medium text-gray-900 dark:text-white capitalize">
                  {agent.replace('_', ' ')}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  {marketIntelligence ? 'Reasoning Tier' : 'Available'}
                </p>
              </div>
              <div className="status-indicator status-bullish" />
            </div>
          )) || (
            <div className="col-span-4 text-center py-4">
              <p className="text-gray-500 dark:text-gray-400">Loading agent status...</p>
            </div>
          )}
        </div>
      </div>

      {/* Live Market Data Test */}
      <LiveMarketTest />
    </div>
  )
}