from langgraph.graph import (StateGraph,START,END)

from agents.state import AgentState
from agents.planner import planner_agent
from agents.researcher import researcher_agent
from agents.data_analyst import data_analyst_agent
from agents.critic import critic_agent
from agents.writer import writer_agent

MAX_RESEARCH_ATTEMPTS = 2
def route_after_critic(state: AgentState):
    evidence_sufficient = state.get("evidence_sufficient",False)
    research_attempts = state.get("research_attempts",0)

    print()
    print("=" * 60)
    print("LANGGRAPH ROUTER")
    print("=" * 60)
    print(f"Evidence sufficient: " f"{evidence_sufficient}")
    print(f"Research attempts: " f"{research_attempts}")
    
    if evidence_sufficient:
        print("Decision: WRITER " "(evidence sufficient)")
        print("=" * 60)
        return "writer"
    if research_attempts < MAX_RESEARCH_ATTEMPTS:
        print("Decision: RESEARCHER " "(additional evidence required)")
        print("=" * 60)
        return "researcher"
    print("Decision: WRITER " "(maximum research attempts reached)")
    print("=" * 60)
    return "writer"

def build_agent_graph():
    graph = StateGraph(AgentState)
    graph.add_node("planner",planner_agent)
    graph.add_node("researcher",researcher_agent)
    graph.add_node("data_analyst",data_analyst_agent)
    graph.add_node("critic",critic_agent)
    graph.add_node("writer",writer_agent)

    graph.add_edge(START,"planner")
    graph.add_edge("planner","researcher")
    graph.add_edge("researcher","data_analyst")
    graph.add_edge("data_analyst","critic")

    graph.add_conditional_edges("critic",route_after_critic,
        {
            "researcher": "researcher","writer": "writer",
        })
    graph.add_edge("writer",END)
    return graph.compile()