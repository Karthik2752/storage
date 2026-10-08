import os
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from agents.state import AgentState
from services.knowledge_base import (get_knowledge_base_documents,)

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"
load_dotenv(ENV_FILE)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY not found in backend/.env")
client = genai.Client(api_key=GEMINI_API_KEY)

def writer_agent(state: AgentState) -> AgentState:
    question = state["question"]
    research_plan = state.get("research_plan","")
    research_results = state.get("research_results","")
    sources = state.get("sources",[])
    data_analysis = state.get("data_analysis","")
    critic_feedback = state.get("critic_feedback","")

    print()
    print("=" * 60)
    print("WRITER AGENT STARTED")
    print("=" * 60)
    try:
        knowledge_documents = (get_knowledge_base_documents())
        print()
        print("Knowledge Base documents returned:")
        print(knowledge_documents)
    except Exception as error:
        print(f"Knowledge Base document error: {error}")
        knowledge_documents = []
    knowledge_source_names = []
    for document in knowledge_documents:
        if not isinstance(document,dict):
            continue
        filename = str(document.get("filename","")).strip()
        if not filename:
            continue
        clean_filename = filename
        if "_" in clean_filename:
            possible_uuid, original_name = (clean_filename.split("_",1))
            if (len(possible_uuid) == 32and all(character in "0123456789abcdefABCDEF" for character in possible_uuid)):
                clean_filename = (original_name)
        if clean_filename not in (knowledge_source_names):
            knowledge_source_names.append(clean_filename)
    web_sources = []
    for source in sources:
        if not isinstance(source,dict):
            continue
        title = str(source.get("title","")).strip()
        url = str(source.get("url","")).strip()
        if not title and not url:
            continue
        if not (url.startswith("http://") or url.startswith("https://")):
            continue
        source_text = (f"{title} {url}").lower()
        if ("document://" in source_text or ".pdf" in source_text):
            continue
        web_sources.append(
            {"title": (title if title else url),"url": url,})
    unique_web_sources = []
    seen_urls = set()
    for source in web_sources:
        url = source["url"].strip().lower()
        if url in seen_urls:
            continue
        seen_urls.add(url)
        unique_web_sources.append(source)
    web_sources = unique_web_sources
    web_source_text = ""
    for index, source in enumerate(web_sources,start=1):
        web_source_text += (f"{index}. " f"{source['title']}\n" f"   URL: {source['url']}\n")
    if not web_source_text:
        web_source_text = ("No web sources were collected.")
    prompt = f"""
{question}{research_plan}{research_results}{data_analysis}{critic_feedback}{web_source_text}
=============================
REPORT STRUCTURE
=============================
# Research Report
## Executive Summary
# Introduction,
# Key Findings,
# Detailed Analysis,
# Benefits and Opportunities
# ,Risks and Challenges,
# Evidence Assessment,Conclusion
"""
    response = client.models.generate_content(model="gemini-3.5-flash-lite",contents=prompt,)
    if not response or not response.text:
        raise RuntimeError("Gemini Writer returned an empty response.")
    final_report = response.text.strip()
    source_markers = ["\n## Sources", "\n# Sources", "\n## Source", "\n# Source",]
    for marker in source_markers:
        position = final_report.find(marker)
        if position != -1:
            final_report = (final_report[:position].rstrip())
            break
    final_report += "\n\n## Sources\n"
    final_report += ("\n### Knowledge Base Sources\n\n")
    if knowledge_source_names:
        for index, filename in enumerate(knowledge_source_names,start=1):
            final_report += (f"{index}. {filename}\n")
    else:
        final_report += ("No Knowledge Base sources were used.\n")
    final_report += ("\n### Web Sources\n\n")
    if web_sources:
        for index, source in enumerate(web_sources,start=1):
            final_report += (f"{index}. " f"{source['title']}. " f"URL: {source['url']}\n")
    else:
        final_report += ("No Web sources were used.\n")
    state["final_report"] = final_report
    print()
    print("SOURCE SUMMARY")
    print("-" * 60)
    print( f"Knowledge Base sources: " f"{len(knowledge_source_names)}")

    for filename in knowledge_source_names:
        print(f"  KB: {filename}")
    print()
    print(f"Web sources: " f"{len(web_sources)}")

    for source in web_sources:
        print(f"  WEB: {source['title']}")
    print("-" * 60)
    print("WRITER AGENT COMPLETED")
    print("=" * 60)

    return state

