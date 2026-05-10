import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useStore } from '../store'
import { getMe } from '../services/api'

export default function AuthSuccess() {
  const navigate = useNavigate()
  const setCurrentUser = useStore((s) => s.setCurrentUser)

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const token = params.get('token')
    if (!token) {
      navigate('/login')
      return
    }
    localStorage.setItem('token', token)

    getMe()
      .then((user) => {
        setCurrentUser(user)
        navigate('/')
      })
      .catch(() => {
        localStorage.removeItem('token')
        navigate('/login')
      })
  }, [])

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary-600 mx-auto mb-4" />
        <p className="text-gray-600 text-sm">Completing sign-in...</p>
      </div>
    </div>
  )
}
