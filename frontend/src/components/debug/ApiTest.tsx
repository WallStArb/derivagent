import { useState } from 'react'
import { api } from '@/lib/api'

export default function ApiTest() {
  const [results, setResults] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const testAPI = async () => {
    setLoading(true)
    setError(null)
    
    try {
      console.log('🧪 Testing API connection...')
      
      // Test health endpoint
      const health = await api.health()
      console.log('✅ Health check:', health)
      
      // Test market regime agent
      const marketAnalysis = await api.analyzeMarketRegime({
        prompt: 'Analyze current market conditions for MEIC strategies',
        context: { 
          vix_level: 16.5, 
          spx_price: 5050,
          test_mode: true,
          source: 'react_frontend'
        }
      })
      console.log('🤖 Market regime analysis:', marketAnalysis)
      
      setResults({
        health,
        marketAnalysis,
        timestamp: new Date().toISOString()
      })
      
    } catch (err: any) {
      console.error('❌ API test failed:', err)
      setError(err.message || 'API test failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-white p-6 rounded-lg shadow-lg border">
      <h3 className="text-lg font-semibold mb-4">🧪 API Connection Test</h3>
      
      <button
        onClick={testAPI}
        disabled={loading}
        className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 mb-4"
      >
        {loading ? '🔄 Testing...' : '🧪 Test Live API'}
      </button>
      
      {error && (
        <div className="bg-red-50 border border-red-200 p-4 rounded mb-4">
          <h4 className="font-medium text-red-800">❌ Error:</h4>
          <p className="text-red-600">{error}</p>
        </div>
      )}
      
      {results && (
        <div className="space-y-4">
          <div className="bg-green-50 border border-green-200 p-4 rounded">
            <h4 className="font-medium text-green-800 mb-2">✅ Health Check:</h4>
            <pre className="text-sm text-green-700 whitespace-pre-wrap">
              Status: {results.health.status}
              Agents: {results.health.agents_available?.length || 0}
              API Keys: {results.health.api_keys_configured ? 'Configured' : 'Missing'}
            </pre>
          </div>
          
          {results.marketAnalysis && (
            <div className="bg-blue-50 border border-blue-200 p-4 rounded">
              <h4 className="font-medium text-blue-800 mb-2">🤖 Market Analysis:</h4>
              <pre className="text-sm text-blue-700 whitespace-pre-wrap">
                Agent: {results.marketAnalysis.agent}
                Success: {results.marketAnalysis.success ? '✅' : '❌'}
                Model: {results.marketAnalysis.model_used}
                Tier: {results.marketAnalysis.tier}
                {results.marketAnalysis.data && (
                  '\nLive AI Response: ' + JSON.stringify(results.marketAnalysis.data, null, 2).substring(0, 200) + '...'
                )}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  )
}