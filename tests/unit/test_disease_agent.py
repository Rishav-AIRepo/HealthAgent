"""Unit tests for the Disease Pattern Agent (rule engine)."""
import pytest
from backend.agents.disease_agent import run_disease_agent
from backend.db.models import HealthRecord


def make_record(param: str, value: float) -> HealthRecord:
    r = HealthRecord()
    r.parameter = param
    r.value = value
    r.unit = "unit"
    r.reference_range = "0-0"
    r.status = "High"
    return r


def test_prediabetes_ifg():
    records = [make_record("glucose", 110)]
    conditions = run_disease_agent(records)
    assert "Pre-diabetes (IFG)" in conditions


def test_possible_diabetes():
    records = [make_record("glucose", 140)]
    conditions = run_disease_agent(records)
    assert any("Diabetes" in c for c in conditions)


def test_high_ldl_dyslipidemia():
    records = [make_record("ldl", 180)]
    conditions = run_disease_agent(records)
    assert "High LDL — Dyslipidemia Risk" in conditions


def test_possible_anemia():
    records = [make_record("hemoglobin", 10)]
    conditions = run_disease_agent(records)
    assert "Possible Anemia" in conditions


def test_elevated_creatinine():
    records = [make_record("creatinine", 1.8)]
    conditions = run_disease_agent(records)
    assert "Elevated Creatinine — Kidney function review needed" in conditions


def test_metabolic_syndrome():
    records = [
        make_record("glucose", 105),
        make_record("triglyceride", 160),
        make_record("hdl", 35),
        make_record("systolic", 135),
    ]
    conditions = run_disease_agent(records)
    assert "Metabolic Syndrome Risk" in conditions


def test_no_conditions_normal_values():
    records = [make_record("glucose", 85)]
    conditions = run_disease_agent(records)
    assert conditions == []
