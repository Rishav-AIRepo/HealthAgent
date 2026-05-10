import { useState } from 'react'
import { Check, Zap, Star } from 'lucide-react'
import { useStore } from '../store'
import { createCheckoutSession, getBillingPortal } from '../services/api'

const PLANS = [
  {
    key: 'free' as const,
    name: 'Free',
    price: '$0',
    period: '',
    icon: null,
    features: [
      '2 PDF uploads / month',
      'Health insights',
      'AI chat assistant',
      'Basic risk analysis',
    ],
    cta: null,
    color: 'border-gray-200',
  },
  {
    key: 'standard' as const,
    name: 'Standard',
    price: '$9',
    period: '/ month',
    icon: Zap,
    features: [
      '15 PDF uploads / month',
      'Everything in Free',
      'Trend charts & analytics',
      'Longitudinal analysis',
      'Fitness plan generation',
      'Medication tracking',
    ],
    cta: 'Upgrade to Standard',
    color: 'border-primary-400',
  },
  {
    key: 'premium' as const,
    name: 'Premium',
    price: '$29',
    period: '/ month',
    icon: Star,
    features: [
      'Unlimited PDF uploads',
      'Everything in Standard',
      'Drug interaction checks',
      'Priority AI processing',
      'Export reports',
    ],
    cta: 'Upgrade to Premium',
    color: 'border-yellow-400',
  },
]

export default function BillingPage() {
  const { currentUser, subscription } = useStore()
  const [loading, setLoading] = useState<string | null>(null)
  const currentPlan = subscription?.plan ?? 'free'

  const handleUpgrade = async (plan: 'standard' | 'premium') => {
    if (!currentUser) return
    setLoading(plan)
    try {
      const { url } = await createCheckoutSession(currentUser.sub, plan)
      window.location.href = url
    } catch {
      setLoading(null)
    }
  }

  const handlePortal = async () => {
    if (!currentUser) return
    setLoading('portal')
    try {
      const { url } = await getBillingPortal(currentUser.sub)
      window.location.href = url
    } catch {
      setLoading(null)
    }
  }

  return (
    <div className="max-w-5xl mx-auto px-4 py-10">
      <div className="mb-8 text-center">
        <h1 className="text-3xl font-bold text-gray-900">Choose your plan</h1>
        <p className="text-gray-500 mt-2">
          Current plan:{' '}
          <span className="font-semibold capitalize text-primary-600">{currentPlan}</span>
          {subscription && subscription.plan !== 'free' && (
            <button
              onClick={handlePortal}
              disabled={loading === 'portal'}
              className="ml-4 text-sm underline text-gray-500 hover:text-gray-700"
            >
              Manage subscription
            </button>
          )}
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {PLANS.map((plan) => {
          const isActive = currentPlan === plan.key
          const PlanIcon = plan.icon
          return (
            <div
              key={plan.key}
              className={`rounded-2xl border-2 ${plan.color} bg-white p-6 flex flex-col gap-4 shadow-sm`}
            >
              <div className="flex items-center gap-2">
                {PlanIcon && <PlanIcon size={20} className="text-primary-500" />}
                <span className="font-bold text-lg text-gray-900">{plan.name}</span>
                {isActive && (
                  <span className="ml-auto text-xs bg-primary-100 text-primary-700 px-2 py-0.5 rounded-full">
                    Active
                  </span>
                )}
              </div>

              <div className="flex items-baseline gap-1">
                <span className="text-3xl font-extrabold text-gray-900">{plan.price}</span>
                <span className="text-gray-400 text-sm">{plan.period}</span>
              </div>

              <ul className="flex flex-col gap-2 flex-1">
                {plan.features.map((f) => (
                  <li key={f} className="flex items-center gap-2 text-sm text-gray-600">
                    <Check size={14} className="text-green-500 shrink-0" />
                    {f}
                  </li>
                ))}
              </ul>

              {plan.cta && !isActive && (
                <button
                  onClick={() => handleUpgrade(plan.key as 'standard' | 'premium')}
                  disabled={loading === plan.key}
                  className="mt-2 w-full py-2 rounded-lg bg-primary-600 text-white text-sm font-semibold hover:bg-primary-700 transition-colors disabled:opacity-60"
                >
                  {loading === plan.key ? 'Redirecting...' : plan.cta}
                </button>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
