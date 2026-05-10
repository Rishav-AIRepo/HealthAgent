"""Unit tests for the risk scoring engine."""
import pytest
from backend.agents.risk_agent import compute_risk_score
from backend.db.models import HealthRecord


def make_record(param: str, status: str) -> HealthRecord:
    r = HealthRecord()
    r.parameter = param
    r.value = 0.0
    r.unit = "unit"
    r.reference_range = "0-0"
    r.status = status
    return r


def test_low_risk_all_normal():
    records = [make_record("glucose", "Normal"), make_record("hdl", "Normal")]
    score, level = compute_risk_score(records)
    assert level == "Low"
    assert score == 0


def test_moderate_risk():
    records = [make_record("cholesterol", "High")]
    score, level = compute_risk_score(records)
    assert score == 20
    assert level == "Moderate"


def test_high_risk_glucose_hba1c():
    records = [make_record("glucose", "High"), make_record("hba1c", "High")]
    score, level = compute_risk_score(records)
    assert score >= 40
    assert level in ["High", "Critical"]


def test_critical_cap():
    records = [
        make_record("glucose", "Critical"),
        make_record("hba1c", "Critical"),
    ]
    score, level = compute_risk_score(records)
    assert score <= 100  # score is capped
    assert level == "Critical"


def test_unknown_parameter_ignored():
    records = [make_record("unknown_test", "High")]
    score, level = compute_risk_score(records)
    assert score == 0
    assert level == "Low"


def test_empty_records():
    score, level = compute_risk_score([])
    assert score == 0
    assert level == "Low"
