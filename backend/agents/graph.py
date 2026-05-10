"""LangGraph StateGraph wiring all health agents into a sequential pipeline."""
from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Optional


class AgentState(TypedDict):
    user_id: str
    age: int
    gender: str
    bmi: float
    records: list
    conditions: List[str]
    risk_score: int
    risk_level: str
    risk_summary: str
    flagged_params: List[dict]
    rag_context: str
    fitness_plan: Optional[dict]


def build_health_graph() -> StateGraph:
    from backend.agents.disease_agent import run_disease_agent
    from backend.agents.risk_agent import compute_risk_score, run_risk_agent
    from backend.agents.fitness_agent import run_fitness_agent

    async def node_disease(state: AgentState) -> AgentState:
        state["conditions"] = run_disease_agent(state["records"])
        flagged = [
            {
                "test_name": r.parameter,
                "value": r.value,
                "unit": r.unit,
                "status": r.status,
            }
            for r in state["records"]
            if r.status != "Normal"
        ]
        state["flagged_params"] = flagged
        return state

    async def node_risk(state: AgentState) -> AgentState:
        score, level = compute_risk_score(state["records"])
        state["risk_score"] = score
        state["risk_level"] = level
        summary = await run_risk_agent(
            state["user_id"],
            state["age"],
            state["gender"],
            state["bmi"],
            state["records"],
            state["conditions"],
        )
        state["risk_summary"] = summary
        return state

    async def node_fitness(state: AgentState) -> AgentState:
        plan = await run_fitness_agent(
            state["age"],
            state["bmi"],
            state["risk_level"],
            state["conditions"],
            risk_score=state.get("risk_score", 0),
            flagged_params=state.get("flagged_params", []),
            rag_context=state.get("rag_context", ""),
        )
        state["fitness_plan"] = plan
        return state

    graph = StateGraph(AgentState)
    graph.add_node("disease_detection", node_disease)
    graph.add_node("risk_analysis", node_risk)
    graph.add_node("fitness_planning", node_fitness)

    graph.set_entry_point("disease_detection")
    graph.add_edge("disease_detection", "risk_analysis")
    graph.add_edge("risk_analysis", "fitness_planning")
    graph.add_edge("fitness_planning", END)

    return graph.compile()
