import os
from dotenv import load_dotenv
from google import genai
from agents.state import AgentState

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY is not configured. " "Please check backend/.env")
client = genai.Client(api_key=GEMINI_API_KEY)
def planner_agent(state: AgentState) -> AgentState:
    question = state["question"]
    print()
    print("=" * 60)
    print("PLANNER AGENT STARTED")
    print("=" * 60)

    prompt = f"""
The user wants to research:
{question}
Create a structured research plan.
The plan must contain:

1. Main Research Objective
2. Key Questions to Investigate
3. Data and Evidence Required
4. Important Areas for Analysis
5. Fact-Checking Requirements
6. Expected Final Report Structure
Do not perform the research itself.
Only create the research plan that will be
given to the other agents.
"""
    response = client.models.generate_content(model="gemini-3.5-flash-lite",contents=prompt,)
    if not response or not response.text:
        raise RuntimeError("Gemini Planner returned an empty response.")
    print("PLANNER AGENT COMPLETED")
    print("=" * 60)
    state["research_plan"] = response.text
    return state