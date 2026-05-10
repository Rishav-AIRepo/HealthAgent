import { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Navbar from './components/Navbar'
import Dashboard from './pages/Dashboard'
import UploadPage from './pages/UploadPage'
import ChatPage from './pages/ChatPage'
import InsightsPage from './pages/InsightsPage'
import FitnessPage from './pages/FitnessPage'
import ProfilePage from './pages/ProfilePage'
import LoginPage from './pages/LoginPage'
import AuthSuccess from './pages/AuthSuccess'
import BillingPage from './pages/BillingPage'
import BillingSuccess from './pages/BillingSuccess'
import TrendsPage from './pages/TrendsPage'
import MedicationsPage from './pages/MedicationsPage'
import LongitudinalPage from './pages/LongitudinalPage'
import { useStore } from './store'
import { getMe, getBillingStatus } from './services/api'

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const currentUser = useStore((s) => s.currentUser)
  const token = localStorage.getItem('token')
  if (!token || !currentUser) return <Navigate to="/login" replace />
  return <>{children}</>
}

export default function App() {
  const { setCurrentUser, setSubscription } = useStore()

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (!token) return
    getMe()
      .then((user) => {
        setCurrentUser(user)
        return getBillingStatus(user.sub)
      })
      .then((status) =>
        setSubscription({
          plan: status.plan as 'free' | 'standard' | 'premium',
          status: status.status,
          upload_count: status.upload_count,
        }),
      )
      .catch(() => {
        localStorage.removeItem('token')
        setCurrentUser(null)
      })
  }, [])

  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-50">
        <Routes>
          {/* Public routes — no Navbar */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/auth/success" element={<AuthSuccess />} />

          {/* Protected routes — with Navbar */}
          <Route
            path="/*"
            element={
              <PrivateRoute>
                <Navbar />
                <main>
                  <Routes>
                    <Route path="/"              element={<Dashboard />} />
                    <Route path="/upload"        element={<UploadPage />} />
                    <Route path="/chat"          element={<ChatPage />} />
                    <Route path="/insights"      element={<InsightsPage />} />
                    <Route path="/fitness"       element={<FitnessPage />} />
                    <Route path="/profile"       element={<ProfilePage />} />
                    <Route path="/trends"        element={<TrendsPage />} />
                    <Route path="/medications"   element={<MedicationsPage />} />
                    <Route path="/longitudinal"  element={<LongitudinalPage />} />
                    <Route path="/billing"       element={<BillingPage />} />
                    <Route path="/billing/success" element={<BillingSuccess />} />
                  </Routes>
                </main>
              </PrivateRoute>
            }
          />
        </Routes>
      </div>
    </BrowserRouter>
  )
}
