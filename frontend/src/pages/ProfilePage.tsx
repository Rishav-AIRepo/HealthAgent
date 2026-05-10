import { useState } from 'react'
import { createUser } from '../services/api'
import { useStore } from '../store'
import Card from '../components/Card'
import Spinner from '../components/Spinner'
import { CheckCircle } from 'lucide-react'

export default function ProfilePage() {
  const { userId, setUser } = useStore()
  const [form, setForm] = useState({
    age: '',
    gender: 'male' as 'male' | 'female' | 'other',
    height_cm: '',
    weight_kg: '',
  })
  const [loading, setLoading] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setForm((f) => ({ ...f, [e.target.name]: e.target.value }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setSaved(false)
    try {
      const profile = await createUser({
        user_id: userId,
        age: Number(form.age),
        gender: form.gender,
        height_cm: Number(form.height_cm),
        weight_kg: Number(form.weight_kg),
      })
      setUser(profile)
      setSaved(true)
    } catch {
      setError('Failed to save profile.')
    } finally {
      setLoading(false)
    }
  }

  const field = (label: string, name: string, type = 'number', placeholder = '') => (
    <div>
      <label className="block text-xs font-medium text-gray-600 mb-1">{label}</label>
      <input
        type={type}
        name={name}
        value={(form as Record<string, string>)[name]}
        onChange={handleChange}
        placeholder={placeholder}
        required
        className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
      />
    </div>
  )

  return (
    <div className="max-w-lg mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">User Profile</h1>
      <Card>
        <form onSubmit={handleSubmit} className="space-y-4">
          {field('Age', 'age', 'number', '30')}
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Gender</label>
            <select
              name="gender"
              value={form.gender}
              onChange={handleChange}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="male">Male</option>
              <option value="female">Female</option>
              <option value="other">Other</option>
            </select>
          </div>
          {field('Height (cm)', 'height_cm', 'number', '170')}
          {field('Weight (kg)', 'weight_kg', 'number', '70')}

          <button
            type="submit"
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 bg-primary-600 hover:bg-primary-700 disabled:opacity-50 text-white text-sm font-semibold py-2.5 rounded-lg transition-colors"
          >
            {loading ? <Spinner size={16} /> : null}
            {loading ? 'Saving…' : 'Save Profile'}
          </button>

          {saved && (
            <div className="flex items-center gap-2 text-green-700 text-sm">
              <CheckCircle size={16} /> Profile saved successfully.
            </div>
          )}
          {error && <p className="text-sm text-red-600">{error}</p>}
        </form>
      </Card>
    </div>
  )
}
