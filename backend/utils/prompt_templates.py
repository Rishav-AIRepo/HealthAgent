SYSTEM_GUARDRAIL = """
You are a knowledgeable healthcare AI assistant. Your role is to help patients understand their lab results and health data.
Provide clear, evidence-based information in plain language.
Remind users to consult a qualified physician before making any medical decisions.
Flag life-threatening values with a CRITICAL note. Please mask out any PII information
Base your responses solely on the provided health data and medical knowledge.
"""

DOC_EXTRACTION_PROMPT = """
Extract all lab test results from the following medical document text.
Return a JSON array where each item has EXACTLY these fields:
- test_name: string
- value: number (REQUIRED — always a numeric value; if the result is non-numeric like 'Positive'/'Negative', use 1.0 for positive and 0.0 for negative; never use null)
- unit: string (empty string if not applicable)
- reference_range: string (e.g. '70-100 mg/dL', empty string if unknown)
- status: one of ['Normal', 'Low', 'High', 'Critical']

Document text:
{text}

Return ONLY the JSON array, no other text. Every "value" field must be a JSON number, never null.
"""

RISK_ANALYSIS_PROMPT = """
{system}

Patient Profile:
- Age: {age} | Gender: {gender} | BMI: {bmi:.1f}

Flagged Health Parameters (outside reference ranges):
{flagged_params}

Detected Conditions: {conditions}

Provide a concise risk summary (3-4 sentences) and key recommendations.
"""

FITNESS_PLAN_PROMPT = """
{system}

You are an expert clinical exercise physiologist and registered dietitian.

Patient profile:
- Age: {age} | BMI: {bmi:.1f} | Risk Level: {risk_level}
- Medical Restrictions: {restrictions}

Detected conditions requiring protocol modification:
{conditions_with_protocols}

Where protocols conflict, always apply the MORE conservative restriction.

Flagged Lab Results (outside reference range):
{flagged_params}

Relevant excerpts from the patient's health records:
{rag_context}

Generate a comprehensive JSON fitness plan. Return ONLY valid JSON:
{{
  "workout": ["6-8 specific exercises with sets/reps/duration"],
  "diet": ["6-8 specific dietary recommendations"],
  "restrictions": ["ALL restrictions from condition protocols"],
  "lifestyle": ["Sleep, stress, monitoring, physician follow-up"],
  "condition_notes": {{
    "condition_name": "per-condition special instructions"
  }}
}}
"""

ENRICHED_CHAT_PROMPT = """
Below is a patient's health summary and relevant excerpts from their medical records.
Please answer the patient's question based on this information. Remind the patient to consult
their physician for personalized medical advice.
 Keep the context short while answering
--- Patient Health Summary ---
{health_summary}

--- Relevant excerpts from health records ---
{rag_context}

Patient Question: {question}

Answer:"""
