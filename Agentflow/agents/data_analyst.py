import pandas as pd
from agents.state import AgentState

def data_analyst_agent(state: AgentState) -> AgentState:
    question = state["question"]
    research_results = state.get("research_results", "")
    sources = state.get("sources", [])

    print()
    print("=" * 60)
    print("DATA ANALYST AGENT STARTED")
    print("=" * 60)

    if sources:
        df = pd.DataFrame(sources)
        total_sources = len(df)
        unique_domains = (df["url"].str.extract(r"https?://(?:www\.)?([^/]+)")[0].dropna().nunique())
    else:
        df = pd.DataFrame()
        total_sources = 0
        unique_domains = 0
    analysis = f"""
## Data Analysis
### Research Question
{question}
### Source Statistics
- Total sources analyzed: {total_sources}
- Unique domains identified: {unique_domains}
### Source Dataset
"""
    if not df.empty:
        for index, row in df.iterrows():
            analysis += f""" {index + 1}. **{row.get("title", "Untitled")}** - URL: {row.get("url", "")}
"""
    analysis += f"""
    
### Research Evidence Review

The Data Analyst reviewed the research findings provided by the Researcher Agent.
The research material contains:
{research_results}
### Analytical Observations
- The collected evidence should be compared across multiple sources.
- Important claims should be supported by identifiable sources.
- Conflicting information should be flagged for the Critic Agent.
- Areas with insufficient evidence should be identified before final report generation.
"""
    print(f"Sources analyzed: {total_sources}")
    print(f"Unique domains: {unique_domains}")
    print("DATA ANALYST AGENT COMPLETED")
    print("=" * 60)
    state["data_analysis"] = analysis
    return state