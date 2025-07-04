import { Settings as SettingsIcon, User, Shield, Bell, Zap } from 'lucide-react'

export default function Settings() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          Settings
        </h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          Manage your account, AI agents, and trading preferences
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Settings Navigation */}
        <div className="space-y-2">
          <div className="trading-card p-3 border-primary-200 dark:border-primary-800">
            <div className="flex items-center space-x-3">
              <User className="h-5 w-5 text-primary-600" />
              <span className="font-medium text-gray-900 dark:text-white">Profile</span>
            </div>
          </div>
          <div className="trading-card p-3">
            <div className="flex items-center space-x-3">
              <Zap className="h-5 w-5 text-gray-400" />
              <span className="text-gray-700 dark:text-gray-300">AI Agents</span>
            </div>
          </div>
          <div className="trading-card p-3">
            <div className="flex items-center space-x-3">
              <Shield className="h-5 w-5 text-gray-400" />
              <span className="text-gray-700 dark:text-gray-300">Security</span>
            </div>
          </div>
          <div className="trading-card p-3">
            <div className="flex items-center space-x-3">
              <Bell className="h-5 w-5 text-gray-400" />
              <span className="text-gray-700 dark:text-gray-300">Notifications</span>
            </div>
          </div>
        </div>

        {/* Settings Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Profile Settings */}
          <div className="trading-card">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Profile Information
            </h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Full Name
                </label>
                <input
                  type="text"
                  defaultValue="Demo User"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Email
                </label>
                <input
                  type="email"
                  defaultValue="demo@derivagent.com"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Trading Experience
                </label>
                <select className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500">
                  <option>Intermediate</option>
                  <option>Beginner</option>
                  <option>Advanced</option>
                  <option>Expert</option>
                </select>
              </div>
            </div>
          </div>

          {/* AI Agent Configuration */}
          <div className="trading-card">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              AI Agent Configuration
            </h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <div>
                  <p className="font-medium text-gray-900 dark:text-white">Market Regime Agent</p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">Advanced market analysis</p>
                </div>
                <div className="flex items-center">
                  <input type="checkbox" defaultChecked className="mr-2" />
                  <span className="text-sm text-green-600">Active</span>
                </div>
              </div>

              <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <div>
                  <p className="font-medium text-gray-900 dark:text-white">Volatility Surface Agent</p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">IV analysis and opportunities</p>
                </div>
                <div className="flex items-center">
                  <input type="checkbox" defaultChecked className="mr-2" />
                  <span className="text-sm text-green-600">Active</span>
                </div>
              </div>

              <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <div>
                  <p className="font-medium text-gray-900 dark:text-white">Support & Resistance Agent</p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">Key level identification</p>
                </div>
                <div className="flex items-center">
                  <input type="checkbox" defaultChecked className="mr-2" />
                  <span className="text-sm text-green-600">Active</span>
                </div>
              </div>

              <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <div>
                  <p className="font-medium text-gray-900 dark:text-white">Liquidity Analysis Agent</p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">Execution quality assessment</p>
                </div>
                <div className="flex items-center">
                  <input type="checkbox" defaultChecked className="mr-2" />
                  <span className="text-sm text-green-600">Active</span>
                </div>
              </div>
            </div>
          </div>

          {/* Risk Preferences */}
          <div className="trading-card">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Risk Preferences
            </h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Risk Tolerance
                </label>
                <select className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500">
                  <option>Moderate</option>
                  <option>Conservative</option>
                  <option>Aggressive</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Maximum Position Size (%)
                </label>
                <input
                  type="number"
                  defaultValue="10"
                  min="1"
                  max="100"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>
            </div>
          </div>

          {/* Save Button */}
          <div className="flex justify-end">
            <button className="px-6 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 transition-colors">
              Save Changes
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}