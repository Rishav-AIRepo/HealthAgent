CONDITION_PROTOCOLS: dict[str, dict] = {
    "Possible Diabetes": {
        "exercise_restrictions": ["Avoid high-impact HIIT during glucose spikes"],
        "exercise_mandates": ["Post-meal walking 10-15 min", "Resistance training 2x/week"],
        "diet_mandates": ["Low glycaemic index foods", "Limit refined carbs to <130g/day"],
        "diet_restrictions": ["No sugary drinks", "Limit fruit juice"],
        "monitoring": ["Check blood glucose before and after exercise"],
    },
    "Pre-diabetes (IFG)": {
        "exercise_restrictions": ["Avoid prolonged inactivity"],
        "exercise_mandates": ["150 min moderate cardio/week", "Strength training 2x/week"],
        "diet_mandates": ["High-fibre foods", "Portion control at every meal"],
        "diet_restrictions": ["Limit refined carbohydrates", "Reduce added sugars"],
        "monitoring": ["Track fasting glucose monthly"],
    },
    "Pre-diabetes (HbA1c)": {
        "exercise_restrictions": ["Avoid exercising when unwell"],
        "exercise_mandates": ["Daily 30 min brisk walking", "Yoga or Pilates 2x/week"],
        "diet_mandates": ["Mediterranean diet pattern", "Increase vegetable intake"],
        "diet_restrictions": ["Limit white bread, pasta, and rice", "Avoid sugary beverages"],
        "monitoring": ["HbA1c check every 3 months"],
    },
    "Possible Anemia": {
        "exercise_restrictions": ["Avoid high-intensity exercise until Hb > 10 g/dL"],
        "exercise_mandates": ["Light yoga", "Walking as tolerated"],
        "diet_mandates": ["Iron-rich foods: leafy greens, lentils, red meat (if not vegetarian)"],
        "diet_restrictions": ["Reduce coffee/tea around meals (inhibits iron absorption)"],
        "monitoring": ["Monitor fatigue and shortness of breath"],
    },
    "Elevated Creatinine": {
        "exercise_restrictions": [
            "Avoid protein loading supplements",
            "No heavy compound lifts",
        ],
        "exercise_mandates": ["Low-intensity cardio 30 min 3x/week"],
        "diet_mandates": ["Limit dietary protein to 0.6-0.8g/kg body weight"],
        "diet_restrictions": ["Avoid high-potassium foods if advised by physician"],
        "monitoring": ["Recheck creatinine in 4 weeks"],
    },
    "High LDL — Dyslipidemia Risk": {
        "exercise_restrictions": [
            "Avoid very intense exercise without cardiac clearance"
        ],
        "exercise_mandates": [
            "Aerobic exercise 5x/week (30-45 min)",
            "Swimming or cycling preferred",
        ],
        "diet_mandates": [
            "Increase soluble fibre (oats, beans, fruits)",
            "Omega-3 rich foods (salmon, walnuts, flaxseed)",
        ],
        "diet_restrictions": [
            "Avoid saturated and trans fats",
            "Limit red meat to 1x/week",
        ],
        "monitoring": ["Lipid panel recheck in 3 months"],
    },
    "Metabolic Syndrome Risk": {
        "exercise_restrictions": [
            "No high-impact exercise until cardiovascular clearance"
        ],
        "exercise_mandates": [
            "Daily 45 min moderate cardio",
            "Resistance training 3x/week",
        ],
        "diet_mandates": [
            "DASH diet pattern",
            "High-fibre whole grains",
            "Lean protein sources",
        ],
        "diet_restrictions": [
            "Restrict sodium to <2300mg/day",
            "Avoid processed foods and alcohol",
        ],
        "monitoring": [
            "Weekly blood pressure monitoring",
            "Monthly waist circumference check",
        ],
    },
}


def build_condition_context(conditions: list[str]) -> str:
    lines = []
    for condition in conditions:
        protocol = CONDITION_PROTOCOLS.get(condition, {})
        if protocol:
            lines.append(f"  {condition}:")
            for k, v in protocol.items():
                lines.append(f"    {k}: {v}")
    return (
        "\n".join(lines) if lines else "No conditions detected — general wellness plan"
    )
