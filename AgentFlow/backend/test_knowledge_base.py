from services.knowledge_base import (create_embeddings,collection,get_knowledge_base_stats,)

print("=" * 60)
print("AGENTFLOW KNOWLEDGE BASE TEST")
print("=" * 60)

texts = [
    "Artificial intelligence is transforming cybersecurity.",
    "Machine learning can detect suspicious network activity.",]
print()
print("Creating test embeddings...")
embeddings = create_embeddings(texts)
print(f"Embeddings created: {len(embeddings)}")
print(f"Embedding dimensions: {len(embeddings[0])}")
print()
print("Testing ChromaDB...")

collection.upsert(
    ids=["test_1","test_2",],documents=texts,embeddings=embeddings,
    metadatas=[
        {
            "filename": "test_document.pdf",
            "chunk_index": 0,
        },
        {
            "filename": "test_document.pdf",
            "chunk_index": 1,
        },],)
print()
print("Testing semantic search...")
query = ("How can AI help protect computer networks?")
query_embedding = create_embeddings([query])[0]
results = collection.query(query_embeddings=[query_embedding],n_results=2,)
documents = results.get("documents",[[]])[0]
print()
print("Search results:")

for index, document in enumerate(documents,start=1):

    print()
    print(f"Result {index}:")
    print(document)
stats = get_knowledge_base_stats()
print()
print("Knowledge Base Statistics:")
print(f"Documents: {stats['documents']}")
print(f"Chunks: {stats['chunks']}")

print()
print("=" * 60)
print("KNOWLEDGE BASE TEST COMPLETED")
print("=" * 60)