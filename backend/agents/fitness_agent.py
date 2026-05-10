"""Agent 5 — Fitness Plan: generates personalised workout + diet plan via GPT-4o."""
import json
from langchain_core.messages import HumanMessage
from backend.utils.llm_factory import get_llm
from backend.utils.prompt_templates import FITNESS_PLAN_PROMPT, SYSTEM_GUARDRAIL
from backend.utils.condition_protocols import build_condition_context

_FALLBACK_PLAN = {
    "workout": ["Walking 30 min/day", "Light stretching 10 min/day"],
    "diet": ["Balanced meals", "Reduce processed sugar", "Increase vegetables"],
    "restrictions": ["Consult physician before starting any new exercise regimen"],
    "lifestyle": ["7-8 hours sleep", "Stress management", "Stay hydrated"],
    "condition_notes": {},
}


def get_bmi_category(bmi: float) -> str:
    if bmi < 18.5:
        return "Underweight"
    if bmi < 25:
        return "Normal"
    if bmi < 30:
        return "Overweight"
    return "Obese"


def get_fitness_level(bmi: float, risk_level: str) -> str:
    if risk_level == "Critical":
        return "Sedentary Recovery"
    if bmi < 25 and risk_level == "Low":
        return "Intermediate"
    if bmi >= 30 or risk_level == "High":
        return "Beginner"
    return "Beginner-Intermediate"


async def run_fitness_agent(
    age: int,
    bmi: float,
    risk_level: str,
    conditions: list[str],
    risk_score: int = 0,
    flagged_params: list[dict] | None = None,
    rag_context: str = "",
) -> dict:
    fitness_level = get_fitness_level(bmi, risk_level)
    restrictions = ", ".join(conditions) if conditions else "None"
    conditions_with_protocols = build_condition_context(conditions)

    flagged_str = "\n".join(
        f"  - {p['test_name']}: {p['value']} {p.get('unit', '')} [{p['status']}]"
        for p in (flagged_params or [])
    ) or "  None"

    prompt = FITNESS_PLAN_PROMPT.format(
        system=SYSTEM_GUARDRAIL,
        age=age,
        bmi=bmi,
        bmi_category=get_bmi_category(bmi),
        risk_level=f"{risk_level} (score: {risk_score}/100, Fitness Level: {fitness_level})",
        risk_score=risk_score,
        restrictions=restrictions,
        conditions_with_protocols=conditions_with_protocols,
        flagged_params=flagged_str,
        rag_context=rag_context or "No additional document context available.",
    )

    llm = get_llm()
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    raw = response.content.strip()

    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    try:
        result = json.loads(raw.strip())
        result.setdefault("condition_notes", {})
        return result
    except json.JSONDecodeError:
        return _FALLBACK_PLAN
