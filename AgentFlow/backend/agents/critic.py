import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from agents.state import AgentState

# -----------------------------------
# Load backend/.env
# -----------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"

load_dotenv(ENV_FILE)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY not found in backend/.env")

# -----------------------------------
# Gemini Client
# -----------------------------------

client = genai.Client(api_key=GEMINI_API_KEY)

# -----------------------------------
# Critic Agent
# -----------------------------------

def critic_agent(state: AgentState) -> AgentState:
    question = state["question"]
    research_results = state.get("research_results","")
    sources = state.get("sources",[])
    data_analysis = state.get("data_analysis","")
    print()
    print("=" * 60)
    print("CRITIC AGENT STARTED")
    print("=" * 60)
    
# -----------------------------------
# Prepare source information
# -----------------------------------

    source_text = ""

    for index, source in enumerate(sources,start=1):
        source_text += f"""SOURCE {index}

Title:
{source.get("title", "Untitled")}

URL:
{source.get("url", "")}

-----------------------------------
"""
    # -----------------------------------
    # Critic Prompt
    # -----------------------------------
    prompt = f"""
You are the Critic and Fact-Checking Agent
in AgentFlow.
Your job is to evaluate the research collected
by the previous agents.
Research Question:
{question}
-----------------------------------
RESEARCH FINDINGS
-----------------------------------
{research_results}
-----------------------------------
DATA ANALYSIS
-----------------------------------
{data_analysis}
-----------------------------------
SOURCES
----------------------------------
{source_text}
-----------------------------------
Evaluate the research carefully.
Check:
1. Whether the research actually addresses the user's question.
2. Whether important claims have supporting evidence.
3. Whether multiple sources support the findings.
4. Whether there are contradictions or inconsistencies.
5. Whether the data analysis is reasonable.
6. Whether important information is missing.
7. Whether the evidence is sufficient for writing a final report.
Return your evaluation using exactly this structure:

EVIDENCE_STATUS:
SUFFICIENT or INSUFFICIENT

CRITIC_FEEDBACK:
Explain the strengths, weaknesses,
unsupported claims, missing evidence,
and issues that should be addressed.

REQUIRED_ACTIONS:
List what should be researched or corrected
before writing the final report.

Do not write the final report.
"""

# -----------------------------------
# Gemini Evaluation
# -----------------------------------

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt,)

    if not response or not response.text:
        raise RuntimeError("Gemini Critic returned an empty response.")
#checking evidence
    critic_output = response.text
    evidence_sufficient = (
        "EVIDENCE_STATUS:\nSUFFICIENT" in critic_output.upper())
#store result
    state["critic_feedback"] = critic_output
    state["evidence_sufficient"] = (evidence_sufficient)
    print()
    print(f"Evidence sufficient: " f"{evidence_sufficient}")
    print("CRITIC AGENT COMPLETED")
    print("=" * 60)

    return state