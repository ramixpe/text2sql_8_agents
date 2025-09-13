import os
import json
import sqlite3
import chromadb
import sys
from langchain_ollama import OllamaEmbeddings, OllamaLLM as Ollama # Import the LLM
from vanna_lgx.config import CHROMA_PATH, EMBEDDING_MODEL, DB_PATH, SYNTHESIS_MODEL, OLLAMA_BASE_URL

# --- Configuration ---
KNOWLEDGE_DOCS_PATH = "knowledge/docs"
KNOWLEDGE_SQL_PATH = "knowledge/sql_examples/examples.json"
COLLECTIONS_TO_REFRESH = ["ddl", "sql_examples", "docs"]

# --- Modular Ingestion Functions ---

def ingest_ddl(client: chromadb.Client, embeddings: OllamaEmbeddings, llm: Ollama):
    """
    S4.1 Upgrade: Deletes, re-creates, and populates the 'ddl' collection.
    It now generates a natural language summary of each table for better embedding.
    """
    print("--- Ingesting DDL (with Summary Generation) ---")
    collection = client.get_or_create_collection(name="ddl")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    conn.close()

    if not tables:
        print("   - No tables found in the database.")
        return

    ddl_strings = [sql for _, sql in tables if sql]
    table_names = [name for name, _ in tables if name]
    
    print(f"   - Found {len(ddl_strings)} tables. Generating summaries for embedding...")
    
    ddl_summaries = []
    for i, ddl in enumerate(ddl_strings):
        table_name = table_names[i]
        print(f"     - Generating summary for table: {table_name}...")
        prompt = f"""
Here is a DDL statement for a table named '{table_name}'.
Please provide a concise, one-paragraph natural language summary of this table's purpose and key columns.
Focus on the business concepts it represents, such as telecom equipment, network operations, OLTs, and ONTs (also known as CPE or user modems).

DDL:
{ddl}

Summary:
"""
        summary = llm.invoke(prompt)
        ddl_summaries.append(summary)
        print(f"     - Summary for {table_name}: {summary[:80]}...")

    # We EMBED the rich summary, but STORE the raw DDL as the document.
    collection.add(
        documents=ddl_strings, # The actual DDL is the document
        ids=table_names,
        embeddings=embeddings.embed_documents(ddl_summaries) # The summary is used for embedding
    )
    print(f"   - Ingested {collection.count()} DDL documents with rich semantic embeddings.")

def ingest_sql_examples(client: chromadb.Client, embeddings: OllamaEmbeddings):
    """Populates the 'sql_examples' collection."""
    print("--- Ingesting SQL Examples ---")
    collection = client.get_or_create_collection(name="sql_examples")
    try:
        with open(KNOWLEDGE_SQL_PATH, 'r') as f:
            examples = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"   - Error loading {KNOWLEDGE_SQL_PATH}: {e}"); return
    questions = [ex["question"] for ex in examples]
    documents = [f"Question: {ex['question']}\nSQL: {ex['sql']}" for ex in examples]
    ids = [f"example_{i}" for i in range(len(examples))]
    collection.add(documents=documents, ids=ids, embeddings=embeddings.embed_documents(questions))
    print(f"   - Ingested {collection.count()} SQL examples.")

def ingest_docs(client: chromadb.Client, embeddings: OllamaEmbeddings):
    """Populates the 'docs' collection."""
    print("--- Ingesting Docs ---")
    collection = client.get_or_create_collection(name="docs")
    doc_contents, doc_ids = [], []
    for filename in os.listdir(KNOWLEDGE_DOCS_PATH):
        if filename.endswith(".txt"):
            filepath = os.path.join(KNOWLEDGE_DOCS_PATH, filename)
            with open(filepath, 'r') as f:
                doc_contents.append(f.read())
                doc_ids.append(filename)
    if not doc_contents: print("   - No .txt documents found."); return
    collection.add(documents=doc_contents, ids=doc_ids, embeddings=embeddings.embed_documents(doc_contents))
    print(f"   - Ingested {collection.count()} doc files.")

# --- Main Execution Logic ---

def main():
    print("🚀 Vanna-LGX Knowledge Base Refresh Script (v2 - with DDL Summaries)")
    print("------------------------------------------------------------------")
    confirm = input(f"This will DELETE and re-create all collections and will call an LLM to generate summaries for DDL. This may take a moment.\nContinue? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Aborted by user."); return

    # Initialize shared components
    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
    llm = Ollama(base_url=OLLAMA_BASE_URL, model=SYNTHESIS_MODEL) # Need an LLM for summaries
    chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)

    for collection_name in COLLECTIONS_TO_REFRESH:
        try:
            print(f"   - Deleting collection '{collection_name}'...")
            chroma_client.delete_collection(name=collection_name)
        except Exception: pass

    # Run all ingestion functions
    ingest_ddl(chroma_client, embeddings, llm)
    ingest_sql_examples(chroma_client, embeddings)
    ingest_docs(chroma_client, embeddings)
    
    print("\n✅ Knowledge base refresh complete!")

if __name__ == "__main__":
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)
    main()