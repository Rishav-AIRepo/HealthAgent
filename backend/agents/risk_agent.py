"""Agent 3 — Health Risk: scores parameters and generates an LLM risk summary."""
from backend.db.models import HealthRecord
from backend.utils.llm_factory import get_llm
from backend.utils.prompt_templates import RISK_ANALYSIS_PROMPT, SYSTEM_GUARDRAIL
from langchain_core.messages import HumanMessage

RISK_WEIGHTS: dict[str, dict[str, int]] = {
    "glucose":      {"High": 30, "Low": 20, "Critical": 60},
    "hba1c":        {"High": 35, "Low": 15, "Critical": 70},
    "cholesterol":  {"High": 20, "Low": 10, "Critical": 40},
    "triglycerides": {"High": 20, "Low": 10, "Critical": 40},
    "creatinine":   {"High": 25, "Low": 15, "Critical": 50},
    "hemoglobin":   {"High": 15, "Low": 25, "Critical": 45},
}


def compute_risk_score(records: list[HealthRecord]) -> tuple[int, str]:
    score = 0
    for r in records:
        key = r.parameter.lower()
        weights = RISK_WEIGHTS.get(key, {})
        score += weights.get(r.status, 0)

    if score == 0:
        level = "Low"
    elif score < 40:
        level = "Moderate"
    elif score < 70:
        level = "High"
    else:
        level = "Critical"

    return min(score, 100), level


async def run_risk_agent(
    user_id: str,
    age: int,
    gender: str,
    bmi: float,
    records: list[HealthRecord],
    conditions: list[str],
) -> str:
    flagged = [r for r in records if r.status != "Normal"]
    flagged_text = "\n".join(
        f"  - {r.parameter}: {r.value} {r.unit} [{r.reference_range}] → {r.status}"
        for r in flagged
    ) or "None — all parameters within range"

    prompt = RISK_ANALYSIS_PROMPT.format(
        system=SYSTEM_GUARDRAIL,
        age=age,
        gender=gender,
        bmi=bmi,
        flagged_params=flagged_text,
        conditions=", ".join(conditions) or "None detected",
    )

    llm = get_llm()
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    return response.content
