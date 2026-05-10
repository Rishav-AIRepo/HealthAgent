import { useState } from 'react'
import { getFitnessPlan } from '../services/api'
import { useStore } from '../store'
import Card from '../components/Card'
import Spinner from '../components/Spinner'
import UpgradePrompt from '../components/UpgradePrompt'
import { Dumbbell, Apple, Ban, Heart, RefreshCw } from 'lucide-react'

const sections = [
  { key: 'workout',      label: 'Workout Plan',      icon: Dumbbell, color: 'text-blue-600  bg-blue-50'   },
  { key: 'diet',         label: 'Diet Plan',          icon: Apple,    color: 'text-green-600 bg-green-50'  },
  { key: 'restrictions', label: 'Restrictions',       icon: Ban,      color: 'text-red-600   bg-red-50'    },
  { key: 'lifestyle',    label: 'Lifestyle Tips',     icon: Heart,    color: 'text-purple-600 bg-purple-50' },
] as const

export default function FitnessPage() {
  const { userId, fitnessPlan, setFitnessPlan } = useStore()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showUpgrade, setShowUpgrade] = useState(false)

  const fetchPlan = async () => {
    setLoading(true)
    setError(null)
    try {
      const plan = await getFitnessPlan(userId)
      setFitnessPlan(plan)
    } catch (err: any) {
      if (err?.response?.status === 402) {
        setShowUpgrade(true)
      } else {
        setError('Failed to generate fitness plan. Please try again.')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 space-y-6">
      {showUpgrade && (
        <UpgradePrompt requiredPlan="standard" onClose={() => setShowUpgrade(false)} />
      )}

      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Personalised Fitness Plan</h1>
        <button
          onClick={fetchPlan}
          disabled={loading}
          className="flex items-center gap-1.5 bg-primary-600 hover:bg-primary-700 disabled:opacity-50 text-white text-sm font-semibold px-4 py-2 rounded-lg transition-colors"
        >
          {loading ? <Spinner size={14} /> : <RefreshCw size={14} />}
          {loading ? 'Generating…' : 'Generate Plan'}
        </button>
      </div>

      {error && (
        <p className="text-sm text-red-600 bg-red-50 rounded-lg px-4 py-3">{error}</p>
      )}

      {fitnessPlan ? (
        <>
          <div className="grid md:grid-cols-2 gap-5">
            {sections.map(({ key, label, icon: Icon, color }) => (
              <Card key={key} title={label}>
                <div className={`inline-flex p-2 rounded-lg mb-3 ${color}`}>
                  <Icon size={18} />
                </div>
                <ul className="space-y-1.5">
                  {(fitnessPlan[key] as string[]).map((item, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                      <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-gray-400 shrink-0" />
                      {item}
                    </li>
                  ))}
                </ul>
              </Card>
            ))}
          </div>
          <p className="text-xs text-gray-400 text-center">{fitnessPlan.disclaimer}</p>
        </>
      ) : (
        !loading && (
          <Card>
            <p className="text-sm text-gray-500 text-center py-6">
              Click "Generate Plan" to create your personalised fitness and diet plan.
            </p>
          </Card>
        )
      )}
    </div>
  )
}
