from typing import TypedDict

class AgentState(TypedDict, total=False):
    question: str
    research_plan: str
    research_results: str
    sources: list
    data_analysis: str
    critic_feedback: str
    evidence_sufficient: bool
    research_attempts: int
    final_report: str