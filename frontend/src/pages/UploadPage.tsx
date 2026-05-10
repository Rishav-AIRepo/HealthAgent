import { useState, useRef } from 'react'
import { uploadPdf, getInsights } from '../services/api'
import { useStore } from '../store'
import Card from '../components/Card'
import Spinner from '../components/Spinner'
import { Upload, CheckCircle, AlertCircle } from 'lucide-react'

export default function UploadPage() {
  const { userId, setInsights } = useStore()
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<{ message: string; count: number } | null>(null)
  const [error, setError] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    const dropped = e.dataTransfer.files[0]
    if (dropped?.type === 'application/pdf') setFile(dropped)
  }

  const handleSubmit = async () => {
    if (!file) return
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const res = await uploadPdf(userId, file)
      setResult({ message: res.message, count: res.parameters_extracted })
      // Auto-refresh insights so chat and fitness plan have current data
      try {
        const insights = await getInsights(userId)
        setInsights(insights)
      } catch { /* non-fatal */ }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Upload failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Upload Lab Report</h1>

      <Card>
        {/* Drop zone */}
        <div
          className="border-2 border-dashed border-gray-300 rounded-lg p-10 text-center hover:border-primary-400 transition-colors cursor-pointer"
          onDragOver={(e) => e.preventDefault()}
          onDrop={handleDrop}
          onClick={() => inputRef.current?.click()}
        >
          <Upload className="mx-auto text-gray-400 mb-3" size={36} />
          {file ? (
            <p className="text-sm font-medium text-gray-700">{file.name}</p>
          ) : (
            <>
              <p className="text-sm font-medium text-gray-600">Drop your PDF here or click to browse</p>
              <p className="text-xs text-gray-400 mt-1">Max 20 MB · PDF only</p>
            </>
          )}
          <input
            ref={inputRef}
            type="file"
            accept=".pdf"
            className="hidden"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          />
        </div>

        <button
          onClick={handleSubmit}
          disabled={!file || loading}
          className="mt-4 w-full flex items-center justify-center gap-2 bg-primary-600 hover:bg-primary-700 disabled:opacity-50 text-white text-sm font-semibold py-2.5 rounded-lg transition-colors"
        >
          {loading ? <><Spinner size={16} /> Processing…</> : 'Upload & Analyse'}
        </button>

        {result && (
          <div className="mt-4 flex items-start gap-2 text-green-700 bg-green-50 rounded-lg p-3">
            <CheckCircle size={18} className="shrink-0 mt-0.5" />
            <p className="text-sm">{result.message} — <strong>{result.count}</strong> parameters extracted.</p>
          </div>
        )}

        {error && (
          <div className="mt-4 flex items-start gap-2 text-red-700 bg-red-50 rounded-lg p-3">
            <AlertCircle size={18} className="shrink-0 mt-0.5" />
            <p className="text-sm">{error}</p>
          </div>
        )}
      </Card>
    </div>
  )
}
