import { Activity } from 'lucide-react'

export default function LoginPage() {
  const handleLogin = () => {
    const base = import.meta.env.VITE_API_BASE_URL || '/api'
    window.location.href = `${base}/auth/login`
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 to-blue-50 flex items-center justify-center">
      <div className="bg-white rounded-2xl shadow-lg p-10 w-full max-w-sm text-center">
        <div className="flex justify-center items-center gap-2 mb-6">
          <Activity size={32} className="text-primary-600" />
          <span className="text-2xl font-bold text-primary-700">HealthAgent</span>
        </div>
        <h1 className="text-xl font-semibold text-gray-800 mb-2">
          AI-Powered Health Analysis
        </h1>
        <p className="text-sm text-gray-500 mb-8">
          Sign in to access personalised fitness plans, medication tracking, and longitudinal health insights.
        </p>
        <button
          onClick={handleLogin}
          className="w-full flex items-center justify-center gap-3 border border-gray-300 rounded-lg px-4 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
        >
          <img
            src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg"
            alt="Google"
            className="w-5 h-5"
          />
          Continue with Google
        </button>
        <p className="mt-6 text-xs text-gray-400">
          By signing in you agree to our Terms of Service and Privacy Policy.
        </p>
      </div>
    </div>
  )
}
