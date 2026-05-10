"""Agent 1 — Intake: computes BMI and BMR from user vitals (no LLM call)."""
from dataclasses import dataclass


@dataclass
class IntakeResult:
    bmi: float
    bmi_category: str
    bmr: float  # Basal Metabolic Rate (kcal/day)


_DEFAULT = IntakeResult(bmi=22.0, bmi_category="Normal", bmr=1800)


def run_intake_agent(
    age: int | None,
    gender: str | None,
    height_cm: float | None,
    weight_kg: float | None,
) -> IntakeResult:
    if not height_cm or not weight_kg or not age:
        return _DEFAULT

    bmi = weight_kg / ((height_cm / 100) ** 2)

    if bmi < 18.5:
        category = "Underweight"
    elif bmi < 25.0:
        category = "Normal"
    elif bmi < 30.0:
        category = "Overweight"
    else:
        category = "Obese"

    # Mifflin-St Jeor equation
    if gender == "male":
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    else:
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161

    return IntakeResult(
        bmi=round(bmi, 2),
        bmi_category=category,
        bmr=round(bmr),
    )
