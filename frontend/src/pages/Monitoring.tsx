import React from 'react';
import MonitoringDashboard from '@/components/MonitoringDashboard';
import { Activity } from 'lucide-react';

const Monitoring: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex items-center space-x-3">
        <Activity className="w-8 h-8 text-cyan-400" />
        <div>
          <h1 className="text-2xl font-bold text-white">System Monitoring</h1>
          <p className="text-gray-400">
            Real-time monitoring of data feeds, AI agents, and system performance
          </p>
        </div>
      </div>

      <MonitoringDashboard />
    </div>
  );
};

export default Monitoring;