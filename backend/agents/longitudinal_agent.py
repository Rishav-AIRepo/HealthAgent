"""Agent 7 — Longitudinal Health Narrative via GPT-4o."""
import json
from langchain_core.messages import HumanMessage, SystemMessage
from backend.utils.llm_factory import get_llm

_SYSTEM = (
    "You are a specialist health analyst. Synthesise longitudinal health data into clear, "
    "actionable clinical narratives. Never diagnose."
)

_PROMPT = """You are a specialist health analyst reviewing {n} health reports spanning {date_range}.

Parameter trajectories:
{trajectories}

Condition history across reports:
{condition_history}

Risk score progression:
{risk_scores}

Write a 4-6 paragraph clinical summary covering:
1. Overall health trajectory (improving / declining / mixed)
2. Parameters showing sustained improvement — acknowledge positive changes
3. Parameters of concern — worsening trends requiring attention
4. New conditions that have emerged vs conditions that have resolved
5. Priority actions for the patient's next physician visit

Do not diagnose. Recommend physician consultation for all findings.
"""


async def run_longitudinal_agent(
    user_id: str,
    snapshots: list,
    trajectories: dict,
) -> str:
    n = len(snapshots)
    if snapshots:
        first = snapshots[0].snapshot_date.isoformat() if snapshots[0].snapshot_date else "unknown"
        last = snapshots[-1].snapshot_date.isoformat() if snapshots[-1].snapshot_date else "unknown"
        date_range = f"{first} to {last}"
    else:
        date_range = "unknown"

    condition_lines = []
    for s in snapshots:
        d = s.snapshot_date.isoformat() if s.snapshot_date else "unknown"
        try:
            conds = json.loads(s.conditions_json or "[]")
        except Exception:
            conds = []
        condition_lines.append(f"  {d}: {', '.join(conds) if conds else 'None'}")

    risk_lines = []
    for s in snapshots:
        d = s.snapshot_date.isoformat() if s.snapshot_date else "unknown"
        risk_lines.append(f"  {d}: score={s.risk_score} ({s.risk_level})")

    traj_lines = [
        f"  {param}: {data['trend']} | {data['first']} → {data['last']} (Δ {data['delta']})"
        for param, data in trajectories.items()
    ] or ["  Insufficient data for trajectory analysis"]

    prompt = _PROMPT.format(
        n=n,
        date_range=date_range,
        trajectories="\n".join(traj_lines),
        condition_history="\n".join(condition_lines),
        risk_scores="\n".join(risk_lines),
    )

    llm = get_llm()
    response = await llm.ainvoke([SystemMessage(content=_SYSTEM), HumanMessage(content=prompt)])
    return response.content.strip()
