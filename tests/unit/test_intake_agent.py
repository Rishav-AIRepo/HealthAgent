"""Unit tests for the Intake Agent (BMI / BMR calculations)."""
import pytest
from backend.agents.intake_agent import run_intake_agent


def test_normal_bmi():
    result = run_intake_agent(age=30, gender="male", height_cm=175, weight_kg=70)
    assert result.bmi == pytest.approx(22.86, abs=0.1)
    assert result.bmi_category == "Normal"
    assert result.bmr > 0


def test_obese_bmi():
    result = run_intake_agent(age=40, gender="female", height_cm=160, weight_kg=95)
    assert result.bmi_category == "Obese"


def test_underweight_bmi():
    result = run_intake_agent(age=25, gender="male", height_cm=180, weight_kg=55)
    assert result.bmi_category == "Underweight"


def test_overweight_bmi():
    result = run_intake_agent(age=35, gender="female", height_cm=165, weight_kg=75)
    assert result.bmi_category == "Overweight"


def test_bmr_male_vs_female():
    male = run_intake_agent(30, "male", 175, 70)
    female = run_intake_agent(30, "female", 175, 70)
    # Male BMR should be higher (Mifflin-St Jeor: male +5, female -161)
    assert male.bmr > female.bmr
