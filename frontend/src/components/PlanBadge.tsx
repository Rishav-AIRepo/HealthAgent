import { useStore } from '../store'

const PLAN_STYLES: Record<string, string> = {
  free: 'bg-gray-100 text-gray-600',
  standard: 'bg-indigo-100 text-indigo-700',
  premium: 'bg-yellow-100 text-yellow-700',
}

export default function PlanBadge() {
  const subscription = useStore((s) => s.subscription)
  const plan = subscription?.plan ?? 'free'

  return (
    <span
      className={`text-xs font-semibold px-2 py-0.5 rounded-full capitalize ${PLAN_STYLES[plan] ?? PLAN_STYLES.free}`}
    >
      {plan}
    </span>
  )
}
