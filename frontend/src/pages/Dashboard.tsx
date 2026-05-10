import { useStore } from '../store'
import Card from '../components/Card'
import RiskBadge from '../components/RiskBadge'
import { Link } from 'react-router-dom'
import { Upload, MessageSquare, Activity, Dumbbell } from 'lucide-react'

export default function Dashboard() {
  const { userId, insights, fitnessPlan } = useStore()

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Healthcare + Fitness Dashboard</h1>
        <p className="text-sm text-gray-500 mt-1">User: <span className="font-mono">{userId}</span></p>
      </div>

      {/* Quick actions */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { to: '/upload',   label: 'Upload Lab Report', icon: Upload,        color: 'bg-blue-50   text-blue-600' },
          { to: '/chat',     label: 'Ask AI Assistant',  icon: MessageSquare, color: 'bg-purple-50 text-purple-600' },
          { to: '/insights', label: 'View Insights',     icon: Activity,      color: 'bg-green-50  text-green-600' },
          { to: '/fitness',  label: 'Fitness Plan',      icon: Dumbbell,      color: 'bg-orange-50 text-orange-600' },
        ].map(({ to, label, icon: Icon, color }) => (
          <Link key={to} to={to}>
            <Card className="hover:shadow-md transition-shadow cursor-pointer text-center">
              <div className={`inline-flex p-3 rounded-full mb-2 ${color}`}>
                <Icon size={22} />
              </div>
              <p className="text-sm font-medium text-gray-700">{label}</p>
            </Card>
          </Link>
        ))}
      </div>

      {/* Risk summary */}
      {insights && (
        <Card title="Latest Risk Summary">
          <div className="flex items-center gap-3 mb-3">
            <RiskBadge level={insights.risk_level} />
            <span className="text-sm text-gray-600">Score: {insights.risk_score}/100</span>
          </div>
          <p className="text-sm text-gray-700 leading-relaxed">{insights.recommendation}</p>
          {insights.conditions.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-1.5">
              {insights.conditions.map((c) => (
                <span key={c} className="text-xs bg-red-50 text-red-700 px-2 py-0.5 rounded-full">{c}</span>
              ))}
            </div>
          )}
        </Card>
      )}

      {/* Fitness snippet */}
      {fitnessPlan && (
        <Card title="Fitness Plan Snapshot">
          <ul className="text-sm text-gray-700 space-y-1 list-disc list-inside">
            {fitnessPlan.workout.slice(0, 3).map((w, i) => <li key={i}>{w}</li>)}
          </ul>
          <Link to="/fitness" className="text-xs text-primary-600 hover:underline mt-2 inline-block">
            View full plan →
          </Link>
        </Card>
      )}

      {!insights && !fitnessPlan && (
        <Card>
          <p className="text-sm text-gray-500 text-center py-4">
            Upload a lab report PDF to get started with your health analysis.
          </p>
        </Card>
      )}
    </div>
  )
}
