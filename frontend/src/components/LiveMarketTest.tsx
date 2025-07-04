import React, { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, Activity, RefreshCw } from 'lucide-react';

interface MarketQuote {
  symbol: string;
  price: number;
  change: number;
  change_percent: number;
  volume: number;
  source: string;
  timestamp: string;
}

const LiveMarketTest: React.FC = () => {
  const [quotes, setQuotes] = useState<MarketQuote[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  const symbols = ['SPY', 'QQQ', 'IWM', 'AAPL', 'MSFT'];

  const fetchMarketData = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const quotePromises = symbols.map(async (symbol) => {
        const response = await fetch(`/api/market/live-quote/${symbol}`);
        if (!response.ok) {
          throw new Error(`Failed to fetch ${symbol}: ${response.statusText}`);
        }
        return response.json() as Promise<MarketQuote>;
      });

      const results = await Promise.all(quotePromises);
      setQuotes(results);
      setLastUpdate(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch market data');
      console.error('Market data fetch error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    // Initial fetch
    fetchMarketData();

    // Set up periodic updates every 30 seconds
    const interval = setInterval(fetchMarketData, 30000);

    return () => clearInterval(interval);
  }, []);

  const formatPrice = (price: number): string => {
    return `$${price.toFixed(2)}`;
  };

  const formatChange = (change: number | null, changePercent: number | null): JSX.Element => {
    if (change === null || changePercent === null) {
      return <span className="text-gray-400">—</span>;
    }

    const isPositive = change >= 0;
    const colorClass = isPositive ? 'text-green-400' : 'text-red-400';
    const icon = isPositive ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />;

    return (
      <div className={`flex items-center space-x-1 ${colorClass}`}>
        {icon}
        <span>
          {isPositive ? '+' : ''}{change.toFixed(2)} ({changePercent.toFixed(2)}%)
        </span>
      </div>
    );
  };

  return (
    <div className="bg-black/50 backdrop-blur-sm border border-cyan-500/20 rounded-lg p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <Activity className="w-6 h-6 text-cyan-400" />
          <h2 className="text-xl font-semibold text-white">Live Market Data</h2>
        </div>
        <div className="flex items-center space-x-4">
          {lastUpdate && (
            <span className="text-sm text-gray-400">
              Last updated: {lastUpdate.toLocaleTimeString()}
            </span>
          )}
          <button
            onClick={fetchMarketData}
            disabled={isLoading}
            className="flex items-center space-x-2 px-3 py-1 bg-cyan-600 hover:bg-cyan-700 
                     disabled:bg-gray-600 disabled:cursor-not-allowed rounded-md text-white text-sm
                     transition-colors duration-200"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-900/20 border border-red-500/20 rounded-lg">
          <p className="text-red-400 text-sm">Error: {error}</p>
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
        {quotes.map((quote) => (
          <div
            key={quote.symbol}
            className="bg-gray-900/50 border border-gray-700/50 rounded-lg p-4 hover:border-cyan-500/30 
                     transition-colors duration-200"
          >
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-semibold text-white text-lg">{quote.symbol}</h3>
              <span className="text-xs text-gray-400 px-2 py-1 bg-gray-800 rounded">
                {quote.source}
              </span>
            </div>
            
            <div className="space-y-2">
              <p className="text-2xl font-bold text-white">
                {formatPrice(quote.price)}
              </p>
              
              <div className="text-sm">
                {formatChange(quote.change, quote.change_percent)}
              </div>
              
              <div className="text-sm text-gray-400">
                <span>Volume: </span>
                <span className="font-mono">
                  {quote.volume ? quote.volume.toLocaleString() : 'N/A'}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {isLoading && quotes.length === 0 && (
        <div className="flex items-center justify-center py-12">
          <div className="flex items-center space-x-3">
            <RefreshCw className="w-5 h-5 text-cyan-400 animate-spin" />
            <span className="text-cyan-400">Loading market data...</span>
          </div>
        </div>
      )}

      {quotes.length === 0 && !isLoading && !error && (
        <div className="text-center py-12">
          <p className="text-gray-400">No market data available</p>
        </div>
      )}
    </div>
  );
};

export default LiveMarketTest;