import { useState, useEffect } from 'react'
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import { useStore } from '../store'
import { getTrends } from '../services/api'
import type { TrendsResponse } from '../types'

const COLORS = ['#4f46e5', '#0ea5e9', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']
const DAY_OPTIONS = [30, 60, 90, 180, 365]

export default function TrendsPage() {
  const userId = useStore((s) => s.userId)
  const [data, setData] = useState<TrendsResponse | null>(null)
  const [days, setDays] = useState(180)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!userId) return
    setLoading(true)
    getTrends(userId, { days })
      .then(setData)
      .catch(() => setError('Failed to load trend data'))
      .finally(() => setLoading(false))
  }, [userId, days])

  if (loading) return <LoadingState />
  if (error) return <ErrorState message={error} />
  if (!data || data.series.length === 0) return <EmptyState />

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Health Trends</h1>
        <select
          value={days}
          onChange={(e) => setDays(Number(e.target.value))}
          className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:ring-2 focus:ring-primary-400 outline-none"
        >
          {DAY_OPTIONS.map((d) => (
            <option key={d} value={d}>
              Last {d} days
            </option>
          ))}
        </select>
      </div>

      {/* Risk Score Over Time */}
      {data.risk_over_time.length > 1 && (
        <section className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
          <h2 className="font-semibold text-gray-800 mb-4">Risk Score Over Time</h2>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={data.risk_over_time}>
              <defs>
                <linearGradient id="riskGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#ef4444" stopOpacity={0.2} />
                  <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="date" tick={{ fontSize: 11 }} />
              <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
              <Tooltip />
              <Area
                type="monotone"
                dataKey="risk_score"
                stroke="#ef4444"
                fill="url(#riskGrad)"
                name="Risk Score"
              />
            </AreaChart>
          </ResponsiveContainer>
        </section>
      )}

      {/* Per-parameter line charts */}
      {data.series.map((series, idx) => {
        const chartData = series.data_points.map((pt) => ({
          date: pt.date,
          value: pt.value,
        }))
        const color = COLORS[idx % COLORS.length]
        return (
          <section
            key={series.parameter}
            className="bg-white rounded-xl shadow-sm border border-gray-100 p-5"
          >
            <div className="flex items-baseline gap-2 mb-4">
              <h2 className="font-semibold text-gray-800">{series.parameter}</h2>
              {series.unit && (
                <span className="text-xs text-gray-400">{series.unit}</span>
              )}
            </div>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="value"
                  stroke={color}
                  dot={{ r: 4 }}
                  name={series.parameter}
                />
              </LineChart>
            </ResponsiveContainer>
          </section>
        )
      })}
    </div>
  )
}

function LoadingState() {
  return (
    <div className="flex justify-center items-center h-64">
      <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary-600" />
    </div>
  )
}

function ErrorState({ message }: { message: string }) {
  return (
    <div className="max-w-md mx-auto mt-20 text-center text-red-600">
      <p>{message}</p>
    </div>
  )
}

function EmptyState() {
  return (
    <div className="max-w-md mx-auto mt-20 text-center text-gray-500">
      <p className="text-lg font-medium">No trend data yet</p>
      <p className="text-sm mt-1">Upload at least two lab reports to see trends.</p>
    </div>
  )
}
