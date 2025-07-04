import React, { useState, useEffect } from 'react';
import { Activity, Wifi, WifiOff, AlertTriangle, CheckCircle, Server, Brain, TrendingUp, Clock } from 'lucide-react';

interface MonitoringData {
  timestamp: string;
  system_status: 'healthy' | 'degraded' | 'critical';
  data_providers: Record<string, any>;
  ai_agents: Record<string, any>;
  performance_metrics: {
    uptime_seconds: number;
    active_connections: number;
    cache_enabled: boolean;
    request_stats: Record<string, number>;
  };
  recent_activity: Array<{
    timestamp: string;
    event: string;
    details: string;
  }>;
}

const MonitoringDashboard: React.FC = () => {
  const [monitoringData, setMonitoringData] = useState<MonitoringData | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchMonitoringData = async () => {
      try {
        const response = await fetch('/api/monitoring/status');
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        const data = await response.json();
        setMonitoringData(data);
        setLastUpdate(new Date());
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch monitoring data');
        console.error('Monitoring fetch error:', err);
      } finally {
        setIsLoading(false);
      }
    };

    // Initial fetch
    fetchMonitoringData();

    // Set up periodic updates every 5 seconds
    const interval = setInterval(fetchMonitoringData, 5000);

    return () => clearInterval(interval);
  }, []);

  const formatUptime = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    return `${hours}h ${minutes}m ${secs}s`;
  };

  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'healthy': return 'text-green-500';
      case 'degraded': return 'text-yellow-500';
      case 'critical': return 'text-red-500';
      default: return 'text-gray-500';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy': return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'degraded': return <AlertTriangle className="w-5 h-5 text-yellow-500" />;
      case 'critical': return <AlertTriangle className="w-5 h-5 text-red-500" />;
      default: return <Activity className="w-5 h-5 text-gray-500" />;
    }
  };

  if (isLoading) {
    return (
      <div className="bg-black/50 backdrop-blur-sm border border-cyan-500/20 rounded-lg p-6">
        <div className="flex items-center justify-center space-x-2">
          <Activity className="w-5 h-5 text-cyan-400 animate-pulse" />
          <span className="text-cyan-400">Loading monitoring data...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-black/50 backdrop-blur-sm border border-red-500/20 rounded-lg p-6">
        <div className="flex items-center space-x-2 text-red-400">
          <AlertTriangle className="w-5 h-5" />
          <span>Monitoring Error: {error}</span>
        </div>
      </div>
    );
  }

  if (!monitoringData) {
    return (
      <div className="bg-black/50 backdrop-blur-sm border border-gray-500/20 rounded-lg p-6">
        <span className="text-gray-400">No monitoring data available</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* System Status Header */}
      <div className="bg-black/50 backdrop-blur-sm border border-cyan-500/20 rounded-lg p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            {getStatusIcon(monitoringData.system_status)}
            <div>
              <h2 className="text-xl font-semibold text-white">System Status</h2>
              <p className={`text-sm ${getStatusColor(monitoringData.system_status)}`}>
                {monitoringData.system_status.charAt(0).toUpperCase() + monitoringData.system_status.slice(1)}
              </p>
            </div>
          </div>
          <div className="text-right">
            <p className="text-sm text-gray-400">Last Updated</p>
            <p className="text-sm text-white font-mono">
              {lastUpdate.toLocaleTimeString()}
            </p>
          </div>
        </div>
      </div>

      {/* Performance Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-black/50 backdrop-blur-sm border border-blue-500/20 rounded-lg p-4">
          <div className="flex items-center space-x-2">
            <Clock className="w-5 h-5 text-blue-400" />
            <span className="text-sm text-gray-400">Uptime</span>
          </div>
          <p className="text-lg font-semibold text-white mt-1">
            {formatUptime(monitoringData.performance_metrics.uptime_seconds)}
          </p>
        </div>

        <div className="bg-black/50 backdrop-blur-sm border border-green-500/20 rounded-lg p-4">
          <div className="flex items-center space-x-2">
            <Server className="w-5 h-5 text-green-400" />
            <span className="text-sm text-gray-400">Connections</span>
          </div>
          <p className="text-lg font-semibold text-white mt-1">
            {monitoringData.performance_metrics.active_connections}
          </p>
        </div>

        <div className="bg-black/50 backdrop-blur-sm border border-purple-500/20 rounded-lg p-4">
          <div className="flex items-center space-x-2">
            <TrendingUp className="w-5 h-5 text-purple-400" />
            <span className="text-sm text-gray-400">Requests</span>
          </div>
          <p className="text-lg font-semibold text-white mt-1">
            {monitoringData.performance_metrics.request_stats.total_requests || 0}
          </p>
        </div>

        <div className="bg-black/50 backdrop-blur-sm border border-orange-500/20 rounded-lg p-4">
          <div className="flex items-center space-x-2">
            <Activity className="w-5 h-5 text-orange-400" />
            <span className="text-sm text-gray-400">Cache</span>
          </div>
          <p className="text-lg font-semibold text-white mt-1">
            {monitoringData.performance_metrics.cache_enabled ? 'Enabled' : 'Disabled'}
          </p>
        </div>
      </div>

      {/* Data Providers */}
      <div className="bg-black/50 backdrop-blur-sm border border-cyan-500/20 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center space-x-2">
          <Server className="w-5 h-5 text-cyan-400" />
          <span>Data Providers</span>
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Object.entries(monitoringData.data_providers).map(([name, provider]) => (
            <div key={name} className="bg-gray-900/50 border border-gray-700/50 rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <h4 className="font-medium text-white capitalize">{name}</h4>
                {provider.connected ? (
                  <Wifi className="w-4 h-4 text-green-400" />
                ) : (
                  <WifiOff className="w-4 h-4 text-red-400" />
                )}
              </div>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-400">Status:</span>
                  <span className={provider.connected ? 'text-green-400' : 'text-red-400'}>
                    {provider.connected ? 'Connected' : 'Disconnected'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Rate Limit:</span>
                  <span className="text-white font-mono">
                    {provider.rate_limit === 'unlimited' ? '∞' : `${provider.rate_limit}/min`}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Daily Limit:</span>
                  <span className="text-white font-mono">
                    {provider.daily_limit === 'unlimited' ? '∞' : provider.daily_limit}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Today:</span>
                  <span className="text-white font-mono">
                    {provider.requests_today || 0}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Real-time:</span>
                  <span className={provider.supports_real_time ? 'text-green-400' : 'text-yellow-400'}>
                    {provider.supports_real_time ? 'Yes' : 'Delayed'}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* AI Agents */}
      <div className="bg-black/50 backdrop-blur-sm border border-cyan-500/20 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center space-x-2">
          <Brain className="w-5 h-5 text-cyan-400" />
          <span>AI Agents</span>
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {Object.entries(monitoringData.ai_agents).map(([name, agent]) => (
            <div key={name} className="bg-gray-900/50 border border-gray-700/50 rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <h4 className="font-medium text-white capitalize">
                  {name.replace('_', ' ')}
                </h4>
                {agent.available ? (
                  <CheckCircle className="w-4 h-4 text-green-400" />
                ) : (
                  <AlertTriangle className="w-4 h-4 text-red-400" />
                )}
              </div>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-400">Status:</span>
                  <span className={agent.available ? 'text-green-400' : 'text-red-400'}>
                    {agent.available ? 'Available' : 'Offline'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Model Tier:</span>
                  <span className="text-white font-mono text-xs">
                    {agent.model_tier || 'unknown'}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Request Statistics */}
      {monitoringData.performance_metrics.request_stats && (
        <div className="bg-black/50 backdrop-blur-sm border border-cyan-500/20 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Request Statistics</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(monitoringData.performance_metrics.request_stats).map(([key, value]) => (
              <div key={key} className="text-center">
                <p className="text-2xl font-bold text-white">{value as number}</p>
                <p className="text-sm text-gray-400 capitalize">
                  {key.replace(/_/g, ' ')}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default MonitoringDashboard;