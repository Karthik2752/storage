
import os
import re
from pathlib import Path

import chromadb
from dotenv import load_dotenv
from google import genai
from pypdf import PdfReader

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"
CHROMA_DIR = BASE_DIR / "chroma_db"
load_dotenv(ENV_FILE)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY not found in backend/.env")
gemini_client = genai.Client(api_key=GEMINI_API_KEY)
chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
collection = chroma_client.get_or_create_collection(name="agentflow_knowledge")
def extract_pdf_text(pdf_path: str) -> str:
    reader = PdfReader(pdf_path)
    pages = []

    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text)

    return "\n".join(pages)
def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    return text.strip()
def create_chunks(text: str,chunk_size: int = 1200,overlap: int = 200):
    text = clean_text(text)
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk.strip())
        if end >= len(text):
            break
        start = end - overlap
    return chunks
def create_embeddings(texts: list[str]):
    if not texts:
        return []
    response = gemini_client.models.embed_content(model="gemini-embedding-001",contents=texts,)
    return [ embedding.values for embedding in response.embeddings]
def add_pdf(pdf_path: str,filename: str,original_filename: str | None = None):
    print()
    print("=" * 60)
    print("KNOWLEDGE BASE")
    print("=" * 60)
    display_filename = Path(original_filename or filename).name
    print(f"Processing PDF: {display_filename}")
    text = extract_pdf_text(pdf_path)
    if not text.strip():
        raise ValueError("Could not extract text from PDF.")
    print(f"Extracted characters: {len(text)}")
    chunks = create_chunks(text)
    if not chunks:
        raise ValueError("PDF did not contain usable text.")
    print(f"Created chunks: {len(chunks)}")
    print("Creating Gemini embeddings...")
    embeddings = create_embeddings(chunks)
    if len(embeddings) != len(chunks):
        raise RuntimeError("Embedding count does not match chunk count.")
    ids = []
    documents = []
    metadatas = []
    for index, chunk in enumerate(chunks):
        document_id = f"{filename}_{index}"
        ids.append(document_id)
        documents.append(chunk)
        metadatas.append({"filename": filename,"original_filename": display_filename,"chunk_index": index,
        })
    collection.upsert(ids=ids,documents=documents,embeddings=embeddings,metadatas=metadatas,)
    print(f"Stored {len(chunks)} chunks in ChromaDB.")
    print("KNOWLEDGE BASE PROCESSING COMPLETED")
    print("=" * 60)
    return {
        "filename": filename,"original_filename": display_filename,"chunks": len(chunks),
    }
def search_knowledge_base(query: str,top_k: int = 5):
    print()
    print("=" * 60)
    print(f"Knowledge Base search: {query}")
    print("=" * 60)

    if not query or not query.strip():
        print("Empty knowledge base query.")
        return []
    print("Creating query embedding...")
    embeddings = create_embeddings([query])
    if not embeddings:
        print("Could not create query embedding.")
        return []
    query_embedding = embeddings[0]
    print("Query embedding created.")
    collection_count = collection.count()
    print(f"Knowledge base chunks available: "f"{collection_count}")
    if collection_count == 0:
        print("Knowledge base is empty.")
        return []
    results = collection.query(query_embeddings=[query_embedding],
        n_results=min(top_k, collection_count),
        include=["documents","metadatas","distances",],)
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]
    matches = []
    for index, document in enumerate(documents):
        if not document:
            continue
        metadata = (metadatas[index]if index < len(metadatas) and metadatas[index] else {})
        distance = (distances[index]if index < len(distances)else None)
        matches.append({
            "text": document,"filename": metadata.get("filename", "Unknown"),
            "original_filename": metadata.get("original_filename",Path(metadata.get("filename", "Unknown")).name),"chunk_index": metadata.get("chunk_index", 0),"distance": distance,
        })
    print(f"Knowledge Base matches: {len(matches)}")
    for match in matches:
        print(f"- {match['original_filename']} "f"(chunk {match['chunk_index']}, "f"distance={match['distance']})")
    return matches
def get_knowledge_base_stats():
    data = collection.get(include=["metadatas"])
    metadatas = data.get("metadatas", [])
    filenames = set()
    for metadata in metadatas:
        if metadata:
            filename = metadata.get("filename")
            if filename:
                filenames.add(filename)
    return {
        "documents": len(filenames),
        "chunks": len(metadatas),
    }
def get_knowledge_base_documents():
    data = collection.get(include=["metadatas"])
    document_chunks = {}
    for metadata in data.get("metadatas", []):
        if not metadata:
            continue
        stored_filename = metadata.get("filename")
        if not stored_filename:
            continue
        original_filename = metadata.get("original_filename",Path(stored_filename).name)
        if stored_filename not in document_chunks:
            document_chunks[stored_filename] = {"filename": original_filename,"chunks": 0,
            }
        document_chunks[stored_filename]["chunks"] += 1
    return sorted(document_chunks.values(),key=lambda document: document["filename"].lower())
def delete_knowledge_base_document(filename: str):
    if not filename:
        raise ValueError("Filename is required.")
    data = collection.get(include=["metadatas"])
    ids_to_delete = []
    for index, metadata in enumerate(data.get("metadatas", [])):
        if not metadata:
            continue
        stored_filename = metadata.get("filename", "")
        original_filename = metadata.get("original_filename",Path(stored_filename).name)
        if filename in (stored_filename, original_filename):
            ids_to_delete.append(data["ids"][index])
    if not ids_to_delete:
        return {
            "filename": filename,
            "deleted_chunks": 0,
        }
    collection.delete(ids=ids_to_delete)
    return {
        "filename": filename,
        "deleted_chunks": len(ids_to_delete),
    }