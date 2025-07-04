import { Wallet, Plus, Settings } from 'lucide-react'

export default function Accounts() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Broker Accounts
          </h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Manage your broker connections and trading accounts
          </p>
        </div>
        <button className="flex items-center space-x-2 px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 transition-colors">
          <Plus className="h-4 w-4" />
          <span>Connect Account</span>
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="trading-card">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-primary-100 dark:bg-primary-900 rounded-lg flex items-center justify-center">
                <Wallet className="h-5 w-5 text-primary-600" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  TastyTrade
                </h3>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Connected
                </p>
              </div>
            </div>
            <button className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
              <Settings className="h-4 w-4" />
            </button>
          </div>
          
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-sm text-gray-500">Account Value:</span>
              <span className="text-sm font-medium">$125,450.00</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-500">Available Cash:</span>
              <span className="text-sm font-medium text-green-600">$25,340.00</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-500">Open Positions:</span>
              <span className="text-sm font-medium">12</span>
            </div>
          </div>
        </div>

        <div className="trading-card border-dashed border-2 border-gray-300 dark:border-gray-600">
          <div className="text-center py-8">
            <Wallet className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              Connect Another Account
            </h3>
            <p className="text-gray-500 dark:text-gray-400 mb-4">
              Add IBKR, Schwab, or other supported brokers
            </p>
            <button className="px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors">
              Choose Broker
            </button>
          </div>
        </div>
      </div>

      <div className="trading-card">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
          Coming Soon: Multi-Broker Features
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
            <h3 className="font-medium text-gray-900 dark:text-white mb-2">
              Unified Portfolio
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              View all positions across brokers in one dashboard
            </p>
          </div>
          <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
            <h3 className="font-medium text-gray-900 dark:text-white mb-2">
              Cross-Account Analytics
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Analyze performance and risk across all accounts
            </p>
          </div>
          <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
            <h3 className="font-medium text-gray-900 dark:text-white mb-2">
              Smart Allocation
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              AI-optimized position allocation across brokers
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}