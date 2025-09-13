# scripts/inject_noise.py

import chromadb
from langchain_ollama import OllamaEmbeddings
from vanna_lgx.config import CHROMA_PATH, EMBEDDING_MODEL

# --- Define our "noisy" data ---

NOISY_DDLS = [
    {
        "name": "employees",
        "ddl": """CREATE TABLE employees (
    employee_id INTEGER PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    hire_date DATE,
    department TEXT,
    salary REAL
);"""
    },
    {
        "name": "sales_records",
        "ddl": """CREATE TABLE sales_records (
    sale_id TEXT PRIMARY KEY,
    product_id INTEGER,
    sale_date TIMESTAMP,
    sale_amount DECIMAL(10, 2),
    customer_id TEXT,
    region TEXT
);"""
    }
]

NOISY_SQL_EXAMPLES = [
    {
        "question": "Who are the top 5 highest-paid employees?",
        "sql": "SELECT first_name, last_name, salary FROM employees ORDER BY salary DESC LIMIT 5;"
    },
    {
        "question": "What were the total sales for the 'North' region last quarter?",
        "sql": "SELECT SUM(sale_amount) FROM sales_records WHERE region = 'North' AND sale_date >= date('now', '-3 months');"
    }
]


def main():
    print("🚀 Starting noise injection process...")

    # 1. Initialize components
    print(f"   - Initializing embedding model '{EMBEDDING_MODEL}'...")
    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)

    print(f"   - Setting up ChromaDB client at '{CHROMA_PATH}'...")
    chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
    ddl_collection = chroma_client.get_or_create_collection(name="ddl")
    sql_collection = chroma_client.get_or_create_collection(name="sql_examples")

    # --- Inject Noisy DDLs ---
    print(f"\n💉 Injecting {len(NOISY_DDLS)} noisy DDL documents...")
    ddl_docs = [d["ddl"] for d in NOISY_DDLS]
    ddl_ids = [f"noise_ddl_{d['name']}" for d in NOISY_DDLS]
    
    ddl_collection.add(
        documents=ddl_docs,
        ids=ddl_ids,
        embeddings=embeddings.embed_documents(ddl_docs) # Embed the DDL content
    )
    print("   - Noisy DDLs added.")

    # --- Inject Noisy SQL Examples ---
    print(f"\n💉 Injecting {len(NOISY_SQL_EXAMPLES)} noisy SQL examples...")
    example_questions = [ex["question"] for ex in NOISY_SQL_EXAMPLES]
    example_docs = [f"Question: {ex['question']}\nSQL: {ex['sql']}" for ex in NOISY_SQL_EXAMPLES]
    example_ids = [f"noise_sql_{i}" for i in range(len(NOISY_SQL_EXAMPLES))]

    sql_collection.add(
        documents=example_docs,
        ids=example_ids,
        embeddings=embeddings.embed_documents(example_questions) # Embed the questions
    )
    print("   - Noisy SQL examples added.")
    
    print("\n✅ Noise Injection Complete!")
    print(f"   - DDL collection now contains: {ddl_collection.count()} documents.")
    print(f"   - SQL example collection now contains: {sql_collection.count()} documents.")


if __name__ == "__main__":
    main()