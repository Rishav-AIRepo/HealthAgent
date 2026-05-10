import { Link, useLocation, useNavigate } from 'react-router-dom'
import {
  Activity,
  Upload,
  MessageSquare,
  BarChart2,
  Dumbbell,
  TrendingUp,
  Pill,
  LineChart,
  CreditCard,
  LogOut,
} from 'lucide-react'
import { useStore } from '../store'
import PlanBadge from './PlanBadge'

const links = [
  { to: '/',             label: 'Dashboard',    icon: BarChart2 },
  { to: '/upload',       label: 'Upload',       icon: Upload },
  { to: '/chat',         label: 'Chat',         icon: MessageSquare },
  { to: '/insights',     label: 'Insights',     icon: Activity },
  { to: '/fitness',      label: 'Fitness',      icon: Dumbbell },
  { to: '/trends',       label: 'Trends',       icon: TrendingUp },
  { to: '/medications',  label: 'Medications',  icon: Pill },
  { to: '/longitudinal', label: 'Longitudinal', icon: LineChart },
]

export default function Navbar() {
  const { pathname } = useLocation()
  const navigate = useNavigate()
  const { currentUser, logout } = useStore()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <nav className="bg-white border-b border-gray-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 flex items-center h-14 gap-1 overflow-x-auto">
        <div className="flex items-center gap-2 font-bold text-primary-600 mr-3 shrink-0">
          <Activity size={20} />
          <span>HealthAgent</span>
        </div>

        {links.map(({ to, label, icon: Icon }) => (
          <Link
            key={to}
            to={to}
            className={`flex items-center gap-1.5 text-sm font-medium px-2 py-1 rounded transition-colors shrink-0
              ${pathname === to
                ? 'text-primary-600 bg-primary-50'
                : 'text-gray-600 hover:text-primary-600 hover:bg-gray-50'
              }`}
          >
            <Icon size={14} />
            {label}
          </Link>
        ))}

        <div className="ml-auto flex items-center gap-3 shrink-0">
          <Link
            to="/billing"
            className={`flex items-center gap-1 text-sm font-medium px-2 py-1 rounded transition-colors
              ${pathname === '/billing'
                ? 'text-primary-600 bg-primary-50'
                : 'text-gray-500 hover:text-primary-600 hover:bg-gray-50'
              }`}
          >
            <CreditCard size={14} />
            Plans
          </Link>
          <PlanBadge />
          {currentUser?.picture && (
            <img
              src={currentUser.picture}
              alt={currentUser.name}
              className="w-7 h-7 rounded-full border border-gray-200"
            />
          )}
          <button
            onClick={handleLogout}
            title="Sign out"
            className="p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
          >
            <LogOut size={15} />
          </button>
        </div>
      </div>
    </nav>
  )
}
