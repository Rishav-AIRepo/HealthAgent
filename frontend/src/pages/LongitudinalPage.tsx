import { useState, useEffect } from 'react'
import {
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  ResponsiveContainer,
  Tooltip,
} from 'recharts'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'
import { useStore } from '../store'
import { getLongitudinal } from '../services/api'
import UpgradePrompt from '../components/UpgradePrompt'
import type { LongitudinalResponse, TrajectoryItem } from '../types'

export default function LongitudinalPage() {
  const userId = useStore((s) => s.userId)
  const [data, setData] = useState<LongitudinalResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showUpgrade, setShowUpgrade] = useState(false)

  useEffect(() => {
    if (!userId) return
    setLoading(true)
    getLongitudinal(userId)
      .then(setData)
      .catch((err) => {
        if (err?.response?.status === 402) {
          setShowUpgrade(true)
        } else {
          const msg = err?.response?.data?.detail ?? 'Failed to load longitudinal analysis'
          setError(msg)
        }
      })
      .finally(() => setLoading(false))
  }, [userId])

  if (showUpgrade)
    return <UpgradePrompt requiredPlan="standard" onClose={() => setShowUpgrade(false)} />

  if (loading)
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary-600" />
      </div>
    )

  if (error)
    return (
      <div className="max-w-md mx-auto mt-20 text-center">
        <p className="text-gray-600">{error}</p>
      </div>
    )

  if (!data)
    return (
      <div className="max-w-md mx-auto mt-20 text-center text-gray-500">
        <p className="text-lg font-medium">No longitudinal data yet</p>
        <p className="text-sm mt-1">Upload at least two lab reports to enable analysis.</p>
      </div>
    )

  const radarData = data.trajectories.slice(0, 8).map((t) => ({
    subject: t.parameter,
    correlation: Math.abs(t.correlation * 100),
  }))

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Longitudinal Analysis</h1>
        <p className="text-sm text-gray-500 mt-1">
          {data.date_range.start} → {data.date_range.end} &middot;{' '}
          {data.snapshots_analysed} reports analysed
        </p>
      </div>

      {/* Trajectory table */}
      <section className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-100">
            <tr>
              <th className="text-left px-4 py-3 font-semibold text-gray-600">Parameter</th>
              <th className="text-left px-4 py-3 font-semibold text-gray-600">Trend</th>
              <th className="text-right px-4 py-3 font-semibold text-gray-600">Correlation</th>
              <th className="text-left px-4 py-3 font-semibold text-gray-600">Latest Values</th>
            </tr>
          </thead>
          <tbody>
            {data.trajectories.map((t) => (
              <tr key={t.parameter} className="border-b border-gray-50 hover:bg-gray-50">
                <td className="px-4 py-3 font-medium text-gray-800">{t.parameter}</td>
                <td className="px-4 py-3">
                  <TrendIndicator trend={t.trend} />
                </td>
                <td className="px-4 py-3 text-right text-gray-500 font-mono text-xs">
                  {t.correlation.toFixed(3)}
                </td>
                <td className="px-4 py-3 text-gray-500 text-xs">
                  {t.values.slice(-3).join(' → ')}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      {/* Radar chart */}
      {radarData.length >= 3 && (
        <section className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
          <h2 className="font-semibold text-gray-800 mb-4">Parameter Trend Strength</h2>
          <ResponsiveContainer width="100%" height={300}>
            <RadarChart data={radarData}>
              <PolarGrid />
              <PolarAngleAxis dataKey="subject" tick={{ fontSize: 11 }} />
              <Radar
                name="Trend Strength"
                dataKey="correlation"
                stroke="#4f46e5"
                fill="#4f46e5"
                fillOpacity={0.3}
              />
              <Tooltip formatter={(v: number) => `${v.toFixed(1)}%`} />
            </RadarChart>
          </ResponsiveContainer>
        </section>
      )}

      {/* Condition history */}
      {data.condition_history.length > 0 && (
        <section className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
          <h2 className="font-semibold text-gray-800 mb-4">Condition History</h2>
          <div className="space-y-2">
            {data.condition_history.map((ch, idx) => (
              <div key={idx} className="flex items-start gap-3 text-sm">
                <span className="text-gray-400 w-24 shrink-0">{ch.date}</span>
                <span className="text-gray-700">
                  {ch.conditions.length > 0 ? ch.conditions.join(', ') : 'No conditions detected'}
                </span>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* GPT-4o narrative */}
      {data.narrative && (
        <section className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
          <h2 className="font-semibold text-gray-800 mb-4">Clinical Narrative</h2>
          <div className="prose prose-sm max-w-none text-gray-700 whitespace-pre-line leading-relaxed">
            {data.narrative}
          </div>
        </section>
      )}
    </div>
  )
}

function TrendIndicator({ trend }: { trend: TrajectoryItem['trend'] }) {
  if (trend === 'improving')
    return (
      <span className="flex items-center gap-1 text-green-600 font-medium">
        <TrendingUp size={14} /> Improving
      </span>
    )
  if (trend === 'worsening')
    return (
      <span className="flex items-center gap-1 text-red-500 font-medium">
        <TrendingDown size={14} /> Worsening
      </span>
    )
  return (
    <span className="flex items-center gap-1 text-gray-400">
      <Minus size={14} /> Stable
    </span>
  )
}
