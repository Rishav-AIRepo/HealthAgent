type Level = 'Low' | 'Moderate' | 'High' | 'Critical'

const colours: Record<Level, string> = {
  Low:      'bg-green-100 text-green-700',
  Moderate: 'bg-yellow-100 text-yellow-700',
  High:     'bg-orange-100 text-orange-700',
  Critical: 'bg-red-100 text-red-700',
}

export default function RiskBadge({ level }: { level: Level }) {
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${colours[level]}`}>
      {level}
    </span>
  )
}
