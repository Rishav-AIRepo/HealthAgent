"""Agent 4 — Disease Pattern: rule-based multi-parameter condition detection (zero LLM cost)."""
from backend.db.models import HealthRecord


def get_param(records: list[HealthRecord], name: str) -> float | None:
    name_lower = name.lower()
    for r in records:
        if name_lower in r.parameter.lower():
            return r.value
    return None


def run_disease_agent(records: list[HealthRecord]) -> list[str]:
    """Rule-based pattern detection — zero LLM cost."""
    conditions: list[str] = []

    glucose  = get_param(records, "glucose")
    trig     = get_param(records, "triglyceride")
    hdl      = get_param(records, "hdl")
    ldl      = get_param(records, "ldl")
    hba1c    = get_param(records, "hba1c")
    creat    = get_param(records, "creatinine")
    hgb      = get_param(records, "hemoglobin")
    bp_sys   = get_param(records, "systolic")

    # Metabolic Syndrome (≥3 of 5 criteria)
    met_criteria = sum([
        bool(glucose and glucose > 100),
        bool(trig and trig > 150),
        bool(hdl and hdl < 40),
        bool(bp_sys and bp_sys > 130),
    ])
    if met_criteria >= 3:
        conditions.append("Metabolic Syndrome Risk")

    # Pre-diabetes
    if glucose and 100 <= glucose <= 125:
        conditions.append("Pre-diabetes (IFG)")
    if hba1c and 5.7 <= hba1c <= 6.4:
        conditions.append("Pre-diabetes (HbA1c)")

    # Diabetes screening
    if glucose and glucose > 126:
        conditions.append("Possible Diabetes — Refer to physician")

    # Dyslipidemia
    if ldl and ldl > 160:
        conditions.append("High LDL — Dyslipidemia Risk")

    # Anemia screening
    if hgb and hgb < 12:
        conditions.append("Possible Anemia")

    # Kidney function
    if creat and creat > 1.4:
        conditions.append("Elevated Creatinine — Kidney function review needed")

    return conditions
