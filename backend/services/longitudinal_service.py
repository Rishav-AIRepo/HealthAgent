"""Trajectory analysis + narrative for multi-report longitudinal data."""
import json
from backend.agents.longitudinal_agent import run_longitudinal_agent


async def analyse(user_id: str, snapshots: list, db) -> dict:
    snapshots_sorted = sorted(snapshots, key=lambda s: s.snapshot_date)

    # 1. Build per-parameter time series from snapshot parameters_json
    param_groups: dict[str, list] = {}
    for s in snapshots_sorted:
        try:
            params = json.loads(s.parameters_json or "{}")
        except Exception:
            params = {}
        for name, raw_val in params.items():
            try:
                val = float(raw_val)
            except (TypeError, ValueError):
                continue
            if name not in param_groups:
                param_groups[name] = []
            param_groups[name].append({"date": s.snapshot_date, "value": val})

    # 2. Compute Pearson correlation per parameter (pure Python, no scipy)
    trajectories = []
    traj_dict: dict = {}  # for the narrative agent
    for param, grp in param_groups.items():
        if len(grp) < 2:
            continue
        grp_sorted = sorted(grp, key=lambda x: x["date"])
        values = [r["value"] for r in grp_sorted]
        dates = [r["date"].isoformat() for r in grp_sorted]
        n = len(values)

        x = list(range(n))
        x_mean = sum(x) / n
        y_mean = sum(values) / n
        cov = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        var_x = sum((xi - x_mean) ** 2 for xi in x)
        var_y = sum((yi - y_mean) ** 2 for yi in values)
        pearson = cov / ((var_x * var_y) ** 0.5) if var_x > 0 and var_y > 0 else 0.0

        trend = (
            "improving" if pearson < -0.1
            else "worsening" if pearson > 0.1
            else "stable"
        )

        trajectories.append({
            "parameter": param,
            "values": values,
            "dates": dates,
            "trend": trend,
            "correlation": round(pearson, 3),
        })
        traj_dict[param] = {"trend": trend, "slope": round(pearson, 3),
                            "first": values[0], "last": values[-1]}

    # 3. GPT-4o narrative
    narrative = await run_longitudinal_agent(user_id, snapshots_sorted, traj_dict)

    return {
        "user_id": user_id,
        "snapshots_analysed": len(snapshots_sorted),
        "date_range": {
            "start": snapshots_sorted[0].snapshot_date.isoformat(),
            "end": snapshots_sorted[-1].snapshot_date.isoformat(),
        },
        "trajectories": trajectories,
        "risk_progression": [
            {
                "date": s.snapshot_date.isoformat(),
                "risk_score": s.risk_score or 0,
                "risk_level": s.risk_level or "Low",
            }
            for s in snapshots_sorted
        ],
        "condition_history": [
            {
                "date": s.snapshot_date.isoformat(),
                "conditions": json.loads(s.conditions_json or "[]"),
            }
            for s in snapshots_sorted
        ],
        "narrative": narrative,
    }
