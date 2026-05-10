"""Agent 6 — Medication Interaction Checker via GPT-4o."""
import json
import os
from langchain_core.messages import HumanMessage, SystemMessage
from backend.utils.llm_factory import get_llm

_SYSTEM = (
    "You are a clinical pharmacist AI. Provide evidence-based drug interaction analysis. "
    "Never advise stopping medications without physician guidance."
)

_PROMPT = """You are a clinical pharmacist AI assistant.
Given the patient's active medications and detected health conditions,
identify potential drug interactions, contraindications with their conditions,
and any parameters from their lab results that require monitoring.

Active medications: {medications}
Detected conditions: {conditions}
Flagged lab parameters: {flagged_params}

Drug knowledge context:
{drug_knowledge}

Return ONLY valid JSON with this exact structure:
{{
  "interactions": [{{"drugs": ["drug1", "drug2"], "severity": "mild|moderate|severe", "description": "..."}}],
  "condition_contraindications": [{{"medication": "...", "condition": "...", "warning": "..."}}],
  "monitoring_required": [{{"parameter": "...", "reason": "...", "frequency": "..."}}]
}}

NEVER advise stopping medication. Always recommend consulting a physician.
"""

_FALLBACK = {
    "interactions": [],
    "condition_contraindications": [],
    "monitoring_required": [],
}


def _load_drug_knowledge(path: str) -> str:
    texts: list[str] = []
    if os.path.isdir(path):
        for fname in os.listdir(path):
            if fname.endswith(".txt"):
                try:
                    with open(os.path.join(path, fname), encoding="utf-8") as f:
                        texts.append(f.read()[:2000])
                except OSError:
                    pass
    return "\n---\n".join(texts) if texts else "No drug knowledge base available."


async def run_med_interaction_agent(
    medications: list[str],
    conditions: list[str],
    flagged_params: list[dict],
    drug_knowledge_path: str = "./data/drug_knowledge",
) -> dict:
    drug_knowledge = _load_drug_knowledge(drug_knowledge_path)

    prompt = _PROMPT.format(
        medications=", ".join(medications) if medications else "None",
        conditions=", ".join(conditions) if conditions else "None",
        flagged_params=(
            ", ".join(
                f"{p.get('test_name','')}: {p.get('value','')} {p.get('unit','')} [{p.get('status','')}]"
                for p in flagged_params
            )
            if flagged_params
            else "None"
        ),
        drug_knowledge=drug_knowledge[:4000],
    )

    llm = get_llm()
    response = await llm.ainvoke([SystemMessage(content=_SYSTEM), HumanMessage(content=prompt)])
    raw = response.content.strip()

    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1] if len(parts) > 1 else raw
        if raw.startswith("json"):
            raw = raw[4:]

    try:
        return json.loads(raw.strip())
    except json.JSONDecodeError:
        return _FALLBACK
