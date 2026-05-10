import axios from 'axios'
import type {
  UserProfile,
  UploadResponse,
  InsightResponse,
  FitnessPlan,
  TrendsResponse,
  Medication,
  MedicationCreate,
  AdherenceResponse,
  InteractionResponse,
  LongitudinalResponse,
  BillingStatus,
} from '../types'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  headers: { 'Content-Type': 'application/json' },
})

// Attach JWT from localStorage to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// ── Auth ──────────────────────────────────────────────────
export const getMe = () =>
  api.get<{ sub: string; email: string; name: string; picture?: string }>('/auth/me').then((r) => r.data)

// ── Users ─────────────────────────────────────────────────
export const createUser = (profile: UserProfile) =>
  api.post<UserProfile>('/users/', profile).then((r) => r.data)

export const getUser = (userId: string) =>
  api.get<UserProfile>(`/users/${userId}`).then((r) => r.data)

// ── Upload ────────────────────────────────────────────────
export const uploadPdf = (userId: string, file: File) => {
  const form = new FormData()
  form.append('file', file)
  return api
    .post<UploadResponse>(`/upload/${userId}`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    .then((r) => r.data)
}

// ── Insights ──────────────────────────────────────────────
export const getInsights = (userId: string) =>
  api.get<InsightResponse>(`/insights/${userId}`).then((r) => r.data)

// ── Fitness Plan ──────────────────────────────────────────
export const getFitnessPlan = (userId: string) =>
  api.post<FitnessPlan>('/fitness/plan', { user_id: userId }).then((r) => r.data)

// ── Chat ──────────────────────────────────────────────────
export const sendChat = (userId: string, sessionId: string, query: string) =>
  api
    .post<{ answer: string; disclaimer: string }>('/chat/', {
      user_id: userId,
      session_id: sessionId,
      query,
    })
    .then((r) => r.data)

// ── Trends ────────────────────────────────────────────────
export const getTrends = (
  userId: string,
  params?: { parameters?: string; days?: number },
) =>
  api
    .get<TrendsResponse>(`/trends/${userId}`, { params })
    .then((r) => r.data)

// ── Medications ───────────────────────────────────────────
export const getMedications = (userId: string) =>
  api.get<Medication[]>(`/medications/${userId}`).then((r) => r.data)

export const addMedication = (data: MedicationCreate) =>
  api.post<Medication>('/medications/', data).then((r) => r.data)

export const updateMedication = (
  medId: number,
  data: Partial<MedicationCreate> & { is_active?: boolean },
) => api.put<Medication>(`/medications/${medId}`, data).then((r) => r.data)

export const deleteMedication = (medId: number) =>
  api.delete(`/medications/${medId}`).then((r) => r.data)

export const logMedication = (
  medId: number,
  status: 'taken' | 'skipped' | 'delayed',
) =>
  api
    .post(`/medications/${medId}/log`, { status })
    .then((r) => r.data)

export const getAdherence = (userId: string) =>
  api.get<AdherenceResponse>(`/medications/${userId}/adherence`).then((r) => r.data)

export const getInteractions = (userId: string) =>
  api.get<InteractionResponse>(`/medications/${userId}/interactions`).then((r) => r.data)

// ── Longitudinal ──────────────────────────────────────────
export const getLongitudinal = (userId: string) =>
  api.get<LongitudinalResponse>(`/longitudinal/${userId}`).then((r) => r.data)

// ── Billing ───────────────────────────────────────────────
export const getBillingStatus = (userId: string) =>
  api.get<BillingStatus>(`/billing/status?user_id=${userId}`).then((r) => r.data)

export const createCheckoutSession = (userId: string, plan: 'standard' | 'premium') =>
  api
    .post<{ url: string }>('/billing/create-checkout-session', { user_id: userId, plan })
    .then((r) => r.data)

export const getBillingPortal = (userId: string) =>
  api
    .get<{ url: string }>(`/billing/portal?user_id=${userId}`)
    .then((r) => r.data)
