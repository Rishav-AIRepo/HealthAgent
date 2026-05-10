"""Agent 2 — Document Analysis: extracts structured lab parameters from PDF text via GPT-4o."""
import json
from langchain_core.messages import HumanMessage, SystemMessage
from backend.utils.llm_factory import get_llm
from backend.utils.prompt_templates import DOC_EXTRACTION_PROMPT


async def extract_parameters(text: str) -> list[dict]:
    """Use GPT-4o to extract structured lab parameters from raw PDF text."""
    llm = get_llm()
    prompt = DOC_EXTRACTION_PROMPT.format(text=text[:6000])  # token guard

    response = await llm.ainvoke([
        SystemMessage(content="You are a medical data extraction assistant."),
        HumanMessage(content=prompt),
    ])

    try:
        raw = response.content.strip()
        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())
    except (json.JSONDecodeError, IndexError):
        return []
