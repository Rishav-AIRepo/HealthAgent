export interface UserProfile {
  user_id: string
  age: number
  gender: 'male' | 'female' | 'other'
  height_cm: number
  weight_kg: number
  email?: string
}

export interface CurrentUser {
  sub: string
  email: string
  name: string
  picture?: string
}

export interface Subscription {
  plan: 'free' | 'standard' | 'premium'
  status: string
  upload_count: number
}

export interface HealthParameter {
  test_name: string
  value: number
  unit: string
  reference_range: string
  status: 'Normal' | 'Low' | 'High' | 'Critical'
}

export interface UploadResponse {
  message: string
  file_id: string
  parameters_extracted: number
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  disclaimer?: string
}

export interface InsightResponse {
  user_id: string
  risk_score: number
  risk_level: 'Low' | 'Moderate' | 'High' | 'Critical'
  flagged_parameters: HealthParameter[]
  conditions: string[]
  recommendation: string
}

export interface FitnessPlan {
  workout: string[]
  diet: string[]
  restrictions: string[]
  lifestyle: string[]
  condition_notes?: Record<string, string>
  disclaimer?: string
}

// Trends
export interface TrendDataPoint {
  date: string
  value: number
  file_id: string
}

export interface TrendSeries {
  parameter: string
  unit: string
  data_points: TrendDataPoint[]
}

export interface TrendsResponse {
  user_id: string
  series: TrendSeries[]
  risk_over_time: Array<{ date: string; risk_score: number; risk_level: string }>
  days: number
}

// Medications
export interface Medication {
  id: number
  user_id: string
  name: string
  dosage: string
  frequency: string
  start_date?: string
  end_date?: string
  notes?: string
  is_active: boolean
}

export interface MedicationCreate {
  user_id: string
  name: string
  dosage: string
  frequency: string
  start_date?: string
  end_date?: string
  notes?: string
}

export interface AdherenceRecord {
  medication_id: number
  medication_name: string
  total_logs: number
  taken_count: number
  adherence_pct: number
}

export interface AdherenceResponse {
  user_id: string
  adherence: AdherenceRecord[]
}

export interface InteractionResponse {
  user_id: string
  interactions: string[]
  condition_contraindications: string[]
  monitoring_required: string[]
  disclaimer: string
}

// Longitudinal
export interface TrajectoryItem {
  parameter: string
  values: number[]
  dates: string[]
  trend: 'improving' | 'worsening' | 'stable'
  correlation: number
}

export interface LongitudinalResponse {
  user_id: string
  snapshots_analysed: number
  date_range: { start: string; end: string }
  trajectories: TrajectoryItem[]
  risk_progression: Array<{ date: string; risk_score: number; risk_level: string }>
  condition_history: Array<{ date: string; conditions: string[] }>
  narrative: string
}

// Billing
export interface CheckoutRequest {
  user_id: string
  plan: 'standard' | 'premium'
}

export interface BillingStatus {
  user_id: string
  plan: string
  status: string
  upload_count: number
  upload_limit: number
}
