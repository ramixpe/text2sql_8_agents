# scripts/ingest_ddl.py

import sqlite3
import chromadb
# from langchain_community.embeddings import OllamaEmbeddings
from langchain_ollama import OllamaEmbeddings

# Import configurations and utility functions from our package
from vanna_lgx.config import DB_PATH, CHROMA_PATH, EMBEDDING_MODEL

def get_table_ddl(conn: sqlite3.Connection) -> dict[str, str]:
    """Extracts the DDL for each individual table in the database."""
    cursor = conn.cursor()
    cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    return {name: sql for name, sql in tables if sql}

def main():
    print("🚀 Starting DDL ingestion process...")

    # 1. Initialize components
    print(f"   - Initializing embedding model '{EMBEDDING_MODEL}'...")
    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)

    
    print(f"   - Setting up ChromaDB client at '{CHROMA_PATH}'...")
    chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
    ddl_collection = chroma_client.get_or_create_collection(name="ddl")

    # 2. Extract DDLs from the database
    print(f"   - Connecting to database '{DB_PATH}' and extracting schema...")
    conn = sqlite3.connect(DB_PATH)
    table_ddls = get_table_ddl(conn)
    conn.close()
    
    if not table_ddls:
        print("❌ No tables found in the database. Exiting.")
        return

    print(f"   - Found {len(table_ddls)} tables to process.")

    # 3. Ingest DDLs into ChromaDB
    print("   - Generating embeddings and ingesting into ChromaDB...")
    table_names = list(table_ddls.keys())
    ddl_strings = list(table_ddls.values())

    # Generate embeddings in a batch (more efficient)
    embedded_ddls = embeddings.embed_documents(ddl_strings)

    ddl_collection.add(
        embeddings=embedded_ddls,
        documents=ddl_strings,
        metadatas=[{"table_name": name} for name in table_names],
        ids=table_names # Use table names as unique IDs
    )
    
    print("\n✅ DDL Ingestion Complete!")
    print(f"   - Total tables ingested: {ddl_collection.count()}")

if __name__ == "__main__":
    main()