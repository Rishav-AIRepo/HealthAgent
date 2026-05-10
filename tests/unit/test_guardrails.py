"""Unit tests for the medical guardrails module."""
from backend.utils.guardrails import wrap_with_disclaimer, check_critical, apply_guardrails


def test_disclaimer_appended():
    result = wrap_with_disclaimer("Your glucose is normal.")
    assert "DISCLAIMER" in result
    assert "qualified healthcare professional" in result


def test_check_critical_true():
    assert check_critical("You may have diabetes, please see a doctor.") is True


def test_check_critical_false():
    assert check_critical("Your cholesterol is slightly elevated.") is False


def test_apply_guardrails_critical():
    result = apply_guardrails("Patient shows signs of cardiac emergency.")
    assert result["requires_doctor"] is True
    assert "URGENT" in result["content"]
    assert "DISCLAIMER" in result["content"]


def test_apply_guardrails_normal():
    result = apply_guardrails("All parameters are within normal range.")
    assert result["requires_doctor"] is False
    assert "DISCLAIMER" in result["content"]
