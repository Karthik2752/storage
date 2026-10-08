from fastapi import (FastAPI,UploadFile,File,HTTPException,)
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
from uuid import uuid4
from agents.graph import build_agent_graph
from services.knowledge_base import (add_pdf,get_knowledge_base_stats,
    get_knowledge_base_documents,search_knowledge_base,delete_knowledge_base_document,)

agent_graph = build_agent_graph()
app = FastAPI(title="AgentFlow API",description="Autonomous Multi-Agent Research & Analysis Platform",version="1.0.0")
app.add_middleware(CORSMiddleware,
    allow_origins=["http://localhost:5173","http://127.0.0.1:5173",],
    allow_credentials=True,allow_methods=["*"],allow_headers=["*"],)

class ResearchRequest(BaseModel):
    question: str

@app.get("/")
def home():
    return {"message": "AgentFlow backend is running","status": "online"}

@app.get("/api/test")
def test():
    return {"status": "success","message": "React can connect to FastAPI"}

@app.get("/api/knowledge/search")
def knowledge_base_search(query: str):
    results = search_knowledge_base(query)
    return {"query": query,"results": results,}

@app.get("/api/knowledge/debug")
def knowledge_base_debug():
    try:
        from services.knowledge_base import collection

        data = collection.get(include=["documents", "metadatas"])
        return {
            "total_chunks": len(data.get("documents", [])),
            "documents": data.get("documents", [])[:3],"metadatas": data.get("metadatas", [])[:3],
        }

    except Exception as error:
        return {
            "error": str(error)
        }

UPLOAD_DIR = (Path(__file__).resolve().parent / "uploads")
UPLOAD_DIR.mkdir(parents=True,exist_ok=True)

@app.post("/api/knowledge/upload")
async def upload_pdf_endpoint(file: UploadFile = File(...)):
    # Check file type
    if (not file.filename or not file.filename.lower().endswith(".pdf")):
        raise HTTPException(status_code=400, detail="Please upload a PDF file.")
    safe_filename = Path(file.filename).name
    stored_filename = f"{uuid4().hex}_{safe_filename}"
    pdf_path = UPLOAD_DIR / stored_filename

    try:
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400,detail="The uploaded PDF is empty.")
        if len(content) > 15 * 1024 * 1024:
            raise HTTPException(status_code=413,detail="PDF must be smaller than 15 MB.")
        pdf_path.write_bytes(content)
        result = add_pdf(pdf_path=str(pdf_path),filename=stored_filename,original_filename=safe_filename)
        return {
            "status": "success",
            "message": "PDF indexed successfully.",
            "filename": safe_filename,
            "chunks": result["chunks"],
            "knowledge_base": get_knowledge_base_stats()
        }
    except HTTPException:
        raise
    except Exception as error:
        print(f"PDF upload error: {error}")
        raise HTTPException(status_code=500,detail=f"Failed to process PDF: {error}")
    finally:
        await file.close()

@app.get("/api/knowledge/stats")
def knowledge_base_stats():
    return get_knowledge_base_stats()

@app.get("/api/knowledge/documents")
def knowledge_base_documents():

    return {
        "documents": (get_knowledge_base_documents())
    }

@app.delete("/api/knowledge/documents/{filename}")
def delete_knowledge_base_document_endpoint(filename: str):
    try:
        result = delete_knowledge_base_document(filename)
        if result["deleted_chunks"] == 0:
            raise HTTPException(status_code=404,detail="Document not found in knowledge base.")
        pdf_path = UPLOAD_DIR / Path(filename).name
        if pdf_path.exists():
            pdf_path.unlink()
            print(f"Deleted PDF file: {pdf_path.name}")

        return {
            "status": "success",
            "message": "PDF deleted successfully.",
            "filename": result["filename"],
            "deleted_chunks": result["deleted_chunks"],
            "knowledge_base": (get_knowledge_base_stats()),
        }

    except HTTPException:
        raise
    except Exception as error:
        print(f"PDF deletion error: {error}")
        raise HTTPException(status_code=500,detail=(f"Failed to delete PDF: {error}"))

@app.post("/api/research")
def start_research(request: ResearchRequest):
    question = request.question.strip()

    if not question:
        return {
            "status": "error",
            "message": ("Research question cannot be empty.")
        }
    try:
        initial_state = {"question": question,"research_attempts": 0}
        print()
        print("=" * 60)
        print("AGENTFLOW RESEARCH STARTED")
        print("=" * 60)
        print(f"Question: {question}")
        print()
        print("Running LangGraph...")
        print("START → PLANNER → RESEARCHER → " "DATA ANALYST → CRITIC → " "CONDITIONAL ROUTING → WRITER")
        print()
        
        result = agent_graph.invoke(initial_state)
        research_plan = result.get("research_plan","")
        research_results = result.get("research_results","")
        sources = result.get("sources",[])
        data_analysis = result.get("data_analysis","")
        critic_feedback = result.get("critic_feedback","")
        evidence_sufficient = result.get("evidence_sufficient",False)
        research_attempts = result.get("research_attempts",0)
        final_report = result.get("final_report","")
        
        if not research_plan:
            return {
                "status": "error",
                "message": ("Planner did not return " "a research plan.")
            }
        if not research_results:
            return {
                "status": "error",
                "message": ("Researcher did not return " "research findings.")
            }
        if not data_analysis:
            return {
                "status": "error",
                "message": ("Data Analyst did not return " "analysis.")
            }
        if not critic_feedback:
            return {
                "status": "error",
                "message": ("Critic did not return " "feedback.")
            }
        if not final_report:
            return {
                "status": "error",
                "message": ("Writer did not return " "a final report.")
            }
        print()
        print("=" * 60)
        print("AGENTFLOW RESEARCH COMPLETED")
        print("=" * 60)

        print(f"Sources collected: " f"{len(sources)}")
        print(f"Research attempts: " f"{research_attempts}")
        print(f"Evidence sufficient: " f"{evidence_sufficient}")
        print("Final report generated: True")
        print()

        return {
            "status": "success",
            "question": question,
            "plan": research_plan,
            "research": research_results,
            "sources": sources,
            "analysis": data_analysis,
            "critic": critic_feedback,
            "evidence_sufficient": (evidence_sufficient),
            "research_attempts": (research_attempts),
            "report": final_report,
        }
    except Exception as error:
        print()

        print("=" * 60)
        print("AGENTFLOW ERROR")
        print("=" * 60)
        print(error)
        return {
            "status": "error",
            "question": question,
            "message": str(error),
        }