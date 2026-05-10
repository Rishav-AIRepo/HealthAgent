import { useState } from 'react'
import { getInsights } from '../services/api'
import { useStore } from '../store'
import Card from '../components/Card'
import RiskBadge from '../components/RiskBadge'
import Spinner from '../components/Spinner'
import { RefreshCw, AlertTriangle } from 'lucide-react'
import type { HealthParameter } from '../types'

const statusColour = (s: HealthParameter['status']) =>
  ({ Normal: 'text-green-600', Low: 'text-blue-600', High: 'text-orange-600', Critical: 'text-red-600' }[s])

export default function InsightsPage() {
  const { userId, insights, setInsights } = useStore()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchInsights = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await getInsights(userId)
      setInsights(data)
    } catch {
      setError('Failed to fetch insights. Ensure a PDF has been uploaded.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Health Insights</h1>
        <button
          onClick={fetchInsights}
          disabled={loading}
          className="flex items-center gap-1.5 bg-primary-600 hover:bg-primary-700 disabled:opacity-50 text-white text-sm font-semibold px-4 py-2 rounded-lg transition-colors"
        >
          {loading ? <Spinner size={14} /> : <RefreshCw size={14} />}
          {loading ? 'Analysing…' : 'Refresh'}
        </button>
      </div>

      {error && (
        <div className="flex items-start gap-2 text-red-700 bg-red-50 rounded-lg p-3">
          <AlertTriangle size={16} className="shrink-0 mt-0.5" />
          <p className="text-sm">{error}</p>
        </div>
      )}

      {insights ? (
        <>
          {/* Risk overview */}
          <Card title="Risk Overview">
            <div className="flex items-center gap-4 flex-wrap">
              <div>
                <p className="text-xs text-gray-500 mb-1">Risk Level</p>
                <RiskBadge level={insights.risk_level} />
              </div>
              <div>
                <p className="text-xs text-gray-500 mb-1">Risk Score</p>
                <div className="flex items-center gap-2">
                  <div className="w-40 h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${
                        insights.risk_level === 'Low'      ? 'bg-green-500' :
                        insights.risk_level === 'Moderate' ? 'bg-yellow-500' :
                        insights.risk_level === 'High'     ? 'bg-orange-500' :
                                                             'bg-red-500'
                      }`}
                      style={{ width: `${insights.risk_score}%` }}
                    />
                  </div>
                  <span className="text-sm font-semibold">{insights.risk_score}/100</span>
                </div>
              </div>
            </div>
            <p className="text-sm text-gray-700 mt-4 leading-relaxed">{insights.recommendation}</p>
          </Card>

          {/* Detected conditions */}
          {insights.conditions.length > 0 && (
            <Card title="Detected Conditions">
              <div className="flex flex-wrap gap-2">
                {insights.conditions.map((c) => (
                  <span key={c} className="text-sm bg-red-50 text-red-700 border border-red-200 px-3 py-1 rounded-full">
                    {c}
                  </span>
                ))}
              </div>
            </Card>
          )}

          {/* Flagged parameters */}
          {insights.flagged_parameters.length > 0 && (
            <Card title="Flagged Parameters">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-xs text-gray-500 border-b">
                      <th className="pb-2 pr-4 font-medium">Test</th>
                      <th className="pb-2 pr-4 font-medium">Value</th>
                      <th className="pb-2 pr-4 font-medium">Unit</th>
                      <th className="pb-2 pr-4 font-medium">Reference</th>
                      <th className="pb-2 font-medium">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {insights.flagged_parameters.map((p, i) => (
                      <tr key={i} className="border-b last:border-0">
                        <td className="py-2 pr-4 font-medium text-gray-800">{p.test_name}</td>
                        <td className="py-2 pr-4">{p.value}</td>
                        <td className="py-2 pr-4 text-gray-500">{p.unit}</td>
                        <td className="py-2 pr-4 text-gray-500">{p.reference_range}</td>
                        <td className={`py-2 font-semibold ${statusColour(p.status)}`}>{p.status}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          )}
        </>
      ) : (
        !loading && (
          <Card>
            <p className="text-sm text-gray-500 text-center py-6">
              Click "Refresh" to load your health insights.
            </p>
          </Card>
        )
      )}
    </div>
  )
}
