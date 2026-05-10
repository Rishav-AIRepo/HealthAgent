import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { CheckCircle } from 'lucide-react'
import { getBillingStatus } from '../services/api'
import { useStore } from '../store'

export default function BillingSuccess() {
  const navigate = useNavigate()
  const { currentUser, setSubscription } = useStore()

  useEffect(() => {
    if (!currentUser) return
    const timer = setTimeout(() => {
      getBillingStatus(currentUser.sub)
        .then((status) =>
          setSubscription({
            plan: status.plan as 'free' | 'standard' | 'premium',
            status: status.status,
            upload_count: status.upload_count,
          }),
        )
        .finally(() => navigate('/'))
    }, 2000)
    return () => clearTimeout(timer)
  }, [currentUser])

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <CheckCircle size={56} className="text-green-500 mx-auto mb-4" />
        <h2 className="text-2xl font-bold text-gray-900">Payment successful!</h2>
        <p className="text-gray-500 mt-2">Your plan has been upgraded. Redirecting...</p>
      </div>
    </div>
  )
}
