from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Any


# ── Users ─────────────────────────────────────────────────────────────────────

class UserProfile(BaseModel):
    user_id: str
    age: int = Field(ge=1, le=120)
    gender: Literal["male", "female", "other"]
    height_cm: float = Field(ge=50, le=250)
    weight_kg: float = Field(ge=20, le=300)


class UserProfileResponse(UserProfile):
    email: Optional[str] = None


# ── Health Data ───────────────────────────────────────────────────────────────

class HealthParameter(BaseModel):
    test_name: str
    value: float
    unit: str
    reference_range: str
    status: Literal["Normal", "Low", "High", "Critical"]


class UploadResponse(BaseModel):
    message: str
    file_id: str
    parameters_extracted: int


# ── Chat ──────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    user_id: str
    session_id: str
    query: str


class ChatResponse(BaseModel):
    answer: str
    disclaimer: str = "This is not medical advice. Consult a qualified physician."
    sources: List[str] = []


# ── Insights ──────────────────────────────────────────────────────────────────

class InsightResponse(BaseModel):
    user_id: str
    risk_score: int
    risk_level: Literal["Low", "Moderate", "High", "Critical"]
    flagged_parameters: List[HealthParameter]
    conditions: List[str]
    recommendation: str


# ── Fitness Plan ──────────────────────────────────────────────────────────────

class FitnessPlanRequest(BaseModel):
    user_id: str
    include_diet: bool = True
    include_workout: bool = True


class FitnessPlanResponse(BaseModel):
    workout: List[str]
    diet: List[str]
    restrictions: List[str]
    lifestyle: List[str]
    condition_notes: dict = {}
    disclaimer: str = "Consult a physician before starting any new exercise regimen."


# ── Billing (F2) ──────────────────────────────────────────────────────────────

class CheckoutRequest(BaseModel):
    plan: Literal["standard", "premium"]


class BillingStatusResponse(BaseModel):
    user_id: str
    plan: str
    status: str
    upload_count: int
    upload_limit: int
    current_period_end: Optional[str] = None


# ── Trends (F3) ───────────────────────────────────────────────────────────────

class TrendDataPoint(BaseModel):
    date: str
    value: float
    status: str


class TrendSeries(BaseModel):
    parameter: str
    data: List[TrendDataPoint]


class TrendsResponse(BaseModel):
    user_id: str
    series: List[TrendSeries]
    risk_series: List[dict] = []


# ── Medications (F4) ──────────────────────────────────────────────────────────

class MedicationCreate(BaseModel):
    name: str
    dosage: str
    frequency: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    notes: Optional[str] = None


class MedicationUpdate(BaseModel):
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    end_date: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class MedicationLogCreate(BaseModel):
    status: Literal["taken", "skipped", "delayed"]
    notes: Optional[str] = None


class MedicationResponse(BaseModel):
    id: int
    user_id: str
    name: str
    dosage: str
    frequency: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_active: bool
    notes: Optional[str] = None
    created_at: Optional[str] = None


class AdherenceResponse(BaseModel):
    user_id: str
    period_days: int
    total_logs: int
    taken_count: int
    skipped_count: int
    delayed_count: int
    adherence_percentage: float


class InteractionResponse(BaseModel):
    user_id: str
    interactions: List[Any] = []
    condition_contraindications: List[Any] = []
    monitoring_required: List[Any] = []
    disclaimer: str


# ── Longitudinal (F5) ─────────────────────────────────────────────────────────

class TrajectoryItem(BaseModel):
    parameter: str
    values: List[float]
    dates: List[str]
    trend: Literal["improving", "worsening", "stable"]
    correlation: float


class LongitudinalResponse(BaseModel):
    user_id: str
    snapshots_analysed: int
    date_range: dict
    trajectories: List[TrajectoryItem]
    risk_progression: List[dict]
    condition_history: List[dict]
    narrative: str
