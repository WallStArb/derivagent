import { Brain, Activity, Target, TrendingUp } from 'lucide-react'

export default function MarketIntelligence() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          Market Intelligence
        </h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          Deep AI analysis of market conditions and trading opportunities
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="trading-card">
          <div className="flex items-center space-x-2 mb-4">
            <Brain className="h-6 w-6 text-primary-600" />
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              Market Regime Agent
            </h2>
          </div>
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            Advanced analysis of market conditions to determine optimal trading strategies.
          </p>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-sm text-gray-500">Status:</span>
              <span className="agent-badge active">Active</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-500">Model:</span>
              <span className="text-sm">DeepSeek R1</span>
            </div>
          </div>
        </div>

        <div className="trading-card">
          <div className="flex items-center space-x-2 mb-4">
            <Activity className="h-6 w-6 text-accent-600" />
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              Volatility Surface Agent
            </h2>
          </div>
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            Analyzes implied volatility patterns across strikes and expirations.
          </p>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-sm text-gray-500">Status:</span>
              <span className="agent-badge active">Active</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-500">Model:</span>
              <span className="text-sm">Grok 3 Mini</span>
            </div>
          </div>
        </div>

        <div className="trading-card">
          <div className="flex items-center space-x-2 mb-4">
            <Target className="h-6 w-6 text-green-600" />
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              Support & Resistance Agent
            </h2>
          </div>
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            Identifies key price levels and validates their strength for strategy planning.
          </p>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-sm text-gray-500">Status:</span>
              <span className="agent-badge active">Active</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-500">Model:</span>
              <span className="text-sm">QwQ 32B</span>
            </div>
          </div>
        </div>

        <div className="trading-card">
          <div className="flex items-center space-x-2 mb-4">
            <TrendingUp className="h-6 w-6 text-blue-600" />
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              Liquidity Analysis Agent
            </h2>
          </div>
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            Evaluates options liquidity to ensure tradeable execution quality.
          </p>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-sm text-gray-500">Status:</span>
              <span className="agent-badge active">Active</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-500">Model:</span>
              <span className="text-sm">QwQ 32B</span>
            </div>
          </div>
        </div>
      </div>

      <div className="trading-card">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
          Coming Soon: Interactive Analysis
        </h2>
        <p className="text-gray-600 dark:text-gray-400">
          Real-time agent analysis, custom prompts, and detailed market intelligence reports will be available in the next sprint.
        </p>
      </div>
    </div>
  )
}