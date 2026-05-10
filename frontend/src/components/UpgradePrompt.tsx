import { useNavigate } from 'react-router-dom'
import { Zap, X } from 'lucide-react'

interface Props {
  requiredPlan: 'standard' | 'premium'
  onClose: () => void
}

export default function UpgradePrompt({ requiredPlan, onClose }: Props) {
  const navigate = useNavigate()

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
      <div className="bg-white rounded-2xl shadow-xl p-7 w-full max-w-sm relative">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-400 hover:text-gray-600"
        >
          <X size={18} />
        </button>
        <div className="flex items-center gap-3 mb-4">
          <div className="bg-indigo-100 p-2 rounded-full">
            <Zap size={20} className="text-indigo-600" />
          </div>
          <h2 className="font-bold text-lg text-gray-900 capitalize">
            {requiredPlan} plan required
          </h2>
        </div>
        <p className="text-sm text-gray-500 mb-6">
          This feature is available on the{' '}
          <strong className="capitalize">{requiredPlan}</strong> plan and above.
          Upgrade to unlock it.
        </p>
        <div className="flex gap-3">
          <button
            onClick={() => navigate('/billing')}
            className="flex-1 bg-primary-600 text-white py-2 rounded-lg text-sm font-semibold hover:bg-primary-700 transition-colors"
          >
            View Plans
          </button>
          <button
            onClick={onClose}
            className="flex-1 border border-gray-200 text-gray-600 py-2 rounded-lg text-sm hover:bg-gray-50 transition-colors"
          >
            Not now
          </button>
        </div>
      </div>
    </div>
  )
}
