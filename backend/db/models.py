from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Text, DateTime,
    Date, Boolean, ForeignKey,
)
from sqlalchemy.sql import func
from backend.db.database import Base


class User(Base):
    __tablename__ = "users"

    user_id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=True)
    age = Column(Integer)
    gender = Column(String)
    height_cm = Column(Float)
    weight_kg = Column(Float)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())


class HealthRecord(Base):
    __tablename__ = "health_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, index=True)
    parameter = Column(String)
    value = Column(Float)
    unit = Column(String)
    reference_range = Column(String)
    status = Column(String)  # Normal | Low | High | Critical
    file_id = Column(String)
    recorded_at = Column(DateTime, server_default=func.now())


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    session_id = Column(String, primary_key=True)
    user_id = Column(String, index=True)
    started_at = Column(DateTime, server_default=func.now())


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, index=True)
    user_id = Column(String)
    role = Column(String)  # user | assistant
    content = Column(Text)
    created_at = Column(DateTime, server_default=func.now())


# ── F2: Stripe Subscriptions ──────────────────────────────────────────────────

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.user_id"), unique=True, index=True)
    stripe_customer_id = Column(String, nullable=True)
    stripe_subscription_id = Column(String, nullable=True)
    plan = Column(String, default="free")      # free | standard | premium
    status = Column(String, default="active")  # active | cancelled | past_due
    upload_count = Column(Integer, default=0)
    current_period_end = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ── F4: Medication Tracking ───────────────────────────────────────────────────

class Medication(Base):
    __tablename__ = "medications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.user_id"), index=True)
    name = Column(String, nullable=False)
    dosage = Column(String)
    frequency = Column(String)
    start_date = Column(Date)
    end_date = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class MedicationLog(Base):
    __tablename__ = "medication_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    medication_id = Column(Integer, ForeignKey("medications.id"), index=True)
    user_id = Column(String, ForeignKey("users.user_id"), index=True)
    taken_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String)  # taken | skipped | delayed
    notes = Column(String, nullable=True)


# ── F5: Longitudinal Analysis ─────────────────────────────────────────────────

class LongitudinalSnapshot(Base):
    __tablename__ = "longitudinal_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.user_id"), index=True)
    snapshot_date = Column(Date, nullable=False)
    risk_score = Column(Integer)
    risk_level = Column(String)
    bmi = Column(Float, nullable=True)
    parameters_json = Column(Text)   # {test_name: value, ...}
    conditions_json = Column(Text)   # [condition_name, ...]
    file_id = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


# ── F6: Condition-Specific Plan Versioning ────────────────────────────────────

class ConditionProtocol(Base):
    __tablename__ = "condition_protocols"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.user_id"), index=True)
    generated_at = Column(DateTime, default=datetime.utcnow)
    conditions_json = Column(Text)   # conditions at time of generation
    risk_level = Column(String)
    plan_json = Column(Text)         # full FitnessPlanResponse JSON
    file_id = Column(String, nullable=True)
