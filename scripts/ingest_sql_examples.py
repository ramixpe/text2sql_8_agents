# scripts/ingest_sql_examples.py - CORRECTED

import json
import chromadb
from langchain_ollama import OllamaEmbeddings
from vanna_lgx.config import CHROMA_PATH, EMBEDDING_MODEL

KNOWLEDGE_SQL_PATH = "knowledge/sql_examples/examples.json"

def main():
    print("🚀 Starting SQL example ingestion process...")

    # 1. Initialize components
    print(f"   - Initializing embedding model '{EMBEDDING_MODEL}'...")
    # THIS IS THE CORRECTED LINE - removed the 'dimensions' parameter
    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)

    print(f"   - Setting up ChromaDB client at '{CHROMA_PATH}'...")
    chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
    sql_collection = chroma_client.get_or_create_collection(name="sql_examples")

    # 2. Load examples from JSON
    print(f"   - Loading examples from '{KNOWLEDGE_SQL_PATH}'...")
    try:
        with open(KNOWLEDGE_SQL_PATH, 'r') as f:
            examples = json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: The file '{KNOWLEDGE_SQL_PATH}' was not found. Please create it first.")
        return
    except json.JSONDecodeError:
        print(f"❌ Error: The file '{KNOWLEDGE_SQL_PATH}' contains invalid JSON. Please check the syntax.")
        return


    if not examples:
        print("❌ No examples found. Exiting.")
        return

    # 3. Prepare data for ChromaDB
    questions = [ex["question"] for ex in examples]
    documents = [f"Question: {ex['question']}\nSQL: {ex['sql']}" for ex in examples]
    ids = [f"example_{i}" for i in range(len(examples))]

    # 4. Ingest into ChromaDB
    print(f"   - Generating embeddings for {len(questions)} questions and ingesting...")
    
    # We explicitly use .embed_documents to ensure we get the full-dimensional embeddings
    question_embeddings = embeddings.embed_documents(questions)

    sql_collection.add(
        documents=documents,
        ids=ids,
        embeddings=question_embeddings
    )

    print("\n✅ SQL Example Ingestion Complete!")
    print(f"   - Total examples ingested: {sql_collection.count()}")

if __name__ == "__main__":
    main()


    