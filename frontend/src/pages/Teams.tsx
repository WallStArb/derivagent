import { Users, Plus, Crown, Shield, Eye } from 'lucide-react'

export default function Teams() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Team Management
          </h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Collaborate with your trading team and manage permissions
          </p>
        </div>
        <button className="flex items-center space-x-2 px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 transition-colors">
          <Plus className="h-4 w-4" />
          <span>Create Team</span>
        </button>
      </div>

      <div className="trading-card">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-3">
            <div className="w-12 h-12 bg-gradient-to-r from-primary-500 to-accent-500 rounded-lg flex items-center justify-center">
              <Users className="h-6 w-6 text-white" />
            </div>
            <div>
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white">
                Alpha Trading Team
              </h3>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                4 members • Created 2 weeks ago
              </p>
            </div>
          </div>
          <span className="px-3 py-1 bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 rounded-full text-sm font-medium">
            Active
          </span>
        </div>

        <div className="space-y-4">
          <h4 className="font-medium text-gray-900 dark:text-white">Team Members</h4>
          
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-gradient-to-r from-primary-500 to-accent-500 rounded-full flex items-center justify-center">
                  <span className="text-sm font-medium text-white">DU</span>
                </div>
                <div>
                  <p className="font-medium text-gray-900 dark:text-white">Demo User</p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">demo@derivagent.com</p>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <Crown className="h-4 w-4 text-yellow-500" />
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Team Lead</span>
              </div>
            </div>

            <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-gray-400 rounded-full flex items-center justify-center">
                  <span className="text-sm font-medium text-white">ST</span>
                </div>
                <div>
                  <p className="font-medium text-gray-900 dark:text-white">Senior Trader</p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">trader@derivagent.com</p>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <Shield className="h-4 w-4 text-blue-500" />
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Risk Manager</span>
              </div>
            </div>

            <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-gray-400 rounded-full flex items-center justify-center">
                  <span className="text-sm font-medium text-white">JT</span>
                </div>
                <div>
                  <p className="font-medium text-gray-900 dark:text-white">Junior Trader</p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">junior@derivagent.com</p>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <Eye className="h-4 w-4 text-green-500" />
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Analyst</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="trading-card">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Role Permissions
          </h3>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Team Lead</span>
              <span className="text-sm text-gray-500">Full Access</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Risk Manager</span>
              <span className="text-sm text-gray-500">Strategy Approval</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Senior Trader</span>
              <span className="text-sm text-gray-500">Trade Execution</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Analyst</span>
              <span className="text-sm text-gray-500">View Only</span>
            </div>
          </div>
        </div>

        <div className="trading-card">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Team Performance
          </h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-sm text-gray-500">Total Strategies:</span>
              <span className="text-sm font-medium">23</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-500">Success Rate:</span>
              <span className="text-sm font-medium text-green-600">78%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-500">Avg Return:</span>
              <span className="text-sm font-medium text-green-600">+12.5%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-500">Risk Score:</span>
              <span className="text-sm font-medium text-blue-600">Moderate</span>
            </div>
          </div>
        </div>
      </div>

      <div className="trading-card">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
          Coming Soon: Advanced Team Features
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
            <h3 className="font-medium text-gray-900 dark:text-white mb-2">
              Team Chat
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Real-time communication and strategy discussions
            </p>
          </div>
          <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
            <h3 className="font-medium text-gray-900 dark:text-white mb-2">
              Approval Workflows
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Multi-level strategy approval and risk management
            </p>
          </div>
          <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
            <h3 className="font-medium text-gray-900 dark:text-white mb-2">
              Performance Analytics
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Individual and team performance tracking
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}