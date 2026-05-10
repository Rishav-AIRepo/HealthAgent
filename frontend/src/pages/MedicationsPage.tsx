import { useState, useEffect } from 'react'
import { Plus, Trash2, CheckCircle, XCircle, Clock, AlertTriangle } from 'lucide-react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import { useStore } from '../store'
import {
  getMedications,
  addMedication,
  deleteMedication,
  logMedication,
  getAdherence,
  getInteractions,
} from '../services/api'
import type { Medication, AdherenceRecord, InteractionResponse } from '../types'

export default function MedicationsPage() {
  const userId = useStore((s) => s.userId)
  const subscription = useStore((s) => s.subscription)
  const [meds, setMeds] = useState<Medication[]>([])
  const [adherence, setAdherence] = useState<AdherenceRecord[]>([])
  const [interactions, setInteractions] = useState<InteractionResponse | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ name: '', dosage: '', frequency: '', notes: '' })
  const [saving, setSaving] = useState(false)
  const [loadingInteractions, setLoadingInteractions] = useState(false)

  const canCheckInteractions =
    subscription?.plan === 'standard' || subscription?.plan === 'premium'

  const load = () => {
    getMedications(userId).then(setMeds)
    getAdherence(userId).then((r) => setAdherence(r.adherence))
  }

  useEffect(() => {
    if (userId) load()
  }, [userId])

  const handleAdd = async () => {
    if (!form.name || !form.dosage || !form.frequency) return
    setSaving(true)
    await addMedication({ user_id: userId, ...form })
    setForm({ name: '', dosage: '', frequency: '', notes: '' })
    setShowForm(false)
    setSaving(false)
    load()
  }

  const handleDelete = async (id: number) => {
    await deleteMedication(id)
    load()
  }

  const handleLog = async (id: number, status: 'taken' | 'skipped' | 'delayed') => {
    await logMedication(id, status)
    load()
  }

  const handleCheckInteractions = async () => {
    setLoadingInteractions(true)
    try {
      const result = await getInteractions(userId)
      setInteractions(result)
    } finally {
      setLoadingInteractions(false)
    }
  }

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Medications</h1>
        <button
          onClick={() => setShowForm((v) => !v)}
          className="flex items-center gap-2 bg-primary-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-primary-700 transition-colors"
        >
          <Plus size={16} />
          Add Medication
        </button>
      </div>

      {/* Add form */}
      {showForm && (
        <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm space-y-3">
          <h2 className="font-semibold text-gray-800">New Medication</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <input
              placeholder="Name (e.g. Metformin)"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary-400"
            />
            <input
              placeholder="Dosage (e.g. 500mg)"
              value={form.dosage}
              onChange={(e) => setForm({ ...form, dosage: e.target.value })}
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary-400"
            />
            <input
              placeholder="Frequency (e.g. Twice daily)"
              value={form.frequency}
              onChange={(e) => setForm({ ...form, frequency: e.target.value })}
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary-400"
            />
            <input
              placeholder="Notes (optional)"
              value={form.notes}
              onChange={(e) => setForm({ ...form, notes: e.target.value })}
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary-400"
            />
          </div>
          <div className="flex gap-3">
            <button
              onClick={handleAdd}
              disabled={saving}
              className="bg-primary-600 text-white px-5 py-2 rounded-lg text-sm font-medium hover:bg-primary-700 disabled:opacity-60 transition-colors"
            >
              {saving ? 'Saving...' : 'Save'}
            </button>
            <button
              onClick={() => setShowForm(false)}
              className="text-gray-500 text-sm hover:text-gray-700"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Medications list */}
      {meds.length === 0 ? (
        <p className="text-gray-500 text-sm">No medications added yet.</p>
      ) : (
        <div className="space-y-3">
          {meds.map((med) => (
            <div
              key={med.id}
              className="bg-white border border-gray-200 rounded-xl p-4 flex flex-col sm:flex-row sm:items-center gap-3 shadow-sm"
            >
              <div className="flex-1">
                <span className="font-semibold text-gray-800">{med.name}</span>
                <span className="ml-2 text-sm text-gray-500">{med.dosage}</span>
                <span className="ml-2 text-xs text-gray-400">{med.frequency}</span>
                {med.notes && (
                  <p className="text-xs text-gray-400 mt-0.5">{med.notes}</p>
                )}
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleLog(med.id, 'taken')}
                  title="Mark Taken"
                  className="p-1.5 text-green-600 hover:bg-green-50 rounded-lg transition-colors"
                >
                  <CheckCircle size={18} />
                </button>
                <button
                  onClick={() => handleLog(med.id, 'skipped')}
                  title="Mark Skipped"
                  className="p-1.5 text-red-400 hover:bg-red-50 rounded-lg transition-colors"
                >
                  <XCircle size={18} />
                </button>
                <button
                  onClick={() => handleLog(med.id, 'delayed')}
                  title="Mark Delayed"
                  className="p-1.5 text-yellow-500 hover:bg-yellow-50 rounded-lg transition-colors"
                >
                  <Clock size={18} />
                </button>
                <button
                  onClick={() => handleDelete(med.id)}
                  title="Delete"
                  className="p-1.5 text-gray-400 hover:bg-gray-100 hover:text-red-500 rounded-lg transition-colors"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Adherence chart */}
      {adherence.length > 0 && (
        <section className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
          <h2 className="font-semibold text-gray-800 mb-4">Adherence</h2>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={adherence}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="medication_name" tick={{ fontSize: 11 }} />
              <YAxis domain={[0, 100]} unit="%" tick={{ fontSize: 11 }} />
              <Tooltip formatter={(v: number) => `${v.toFixed(0)}%`} />
              <Bar dataKey="adherence_pct" fill="#4f46e5" name="Adherence %" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </section>
      )}

      {/* Drug interactions */}
      <section className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold text-gray-800">Drug Interactions</h2>
          {canCheckInteractions ? (
            <button
              onClick={handleCheckInteractions}
              disabled={loadingInteractions || meds.length === 0}
              className="text-sm bg-primary-600 text-white px-4 py-1.5 rounded-lg hover:bg-primary-700 disabled:opacity-60 transition-colors"
            >
              {loadingInteractions ? 'Checking...' : 'Check Interactions'}
            </button>
          ) : (
            <span className="text-xs text-gray-400 flex items-center gap-1">
              <AlertTriangle size={13} />
              Standard plan required
            </span>
          )}
        </div>

        {interactions && (
          <div className="space-y-3 text-sm text-gray-700">
            {interactions.interactions.length > 0 && (
              <div>
                <p className="font-medium text-red-600 mb-1">Interactions</p>
                <ul className="list-disc list-inside space-y-0.5">
                  {interactions.interactions.map((i, idx) => (
                    <li key={idx}>{i}</li>
                  ))}
                </ul>
              </div>
            )}
            {interactions.condition_contraindications.length > 0 && (
              <div>
                <p className="font-medium text-orange-600 mb-1">Condition Contraindications</p>
                <ul className="list-disc list-inside space-y-0.5">
                  {interactions.condition_contraindications.map((c, idx) => (
                    <li key={idx}>{c}</li>
                  ))}
                </ul>
              </div>
            )}
            {interactions.monitoring_required.length > 0 && (
              <div>
                <p className="font-medium text-blue-600 mb-1">Monitoring Required</p>
                <ul className="list-disc list-inside space-y-0.5">
                  {interactions.monitoring_required.map((m, idx) => (
                    <li key={idx}>{m}</li>
                  ))}
                </ul>
              </div>
            )}
            <p className="text-xs text-gray-400 pt-2 border-t border-gray-100">
              {interactions.disclaimer}
            </p>
          </div>
        )}
      </section>
    </div>
  )
}
