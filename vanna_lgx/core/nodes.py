# vanna_lgx/core/nodes.py - S2 VERSION

import chromadb
import tiktoken
from langchain_ollama import OllamaLLM as Ollama
from langchain_ollama import OllamaEmbeddings
import pandas as pd

from vanna_lgx.core.state import GraphState
from vanna_lgx.utils.db_utils import get_db_connection
from vanna_lgx.config import (
    OLLAMA_BASE_URL,
    SYNTHESIS_MODEL,
    EMBEDDING_MODEL,
    CHROMA_PATH,
)

# --- Initialize clients ---
llm = Ollama(base_url=OLLAMA_BASE_URL, model=SYNTHESIS_MODEL)
embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL) # Correct initialization
tokenizer = tiktoken.get_encoding("cl100k_base")

chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
ddl_collection = chroma_client.get_collection(name="ddl")
sql_collection = chroma_client.get_collection(name="sql_examples")

def retrieve_context(state: GraphState) -> GraphState:
    """
    S2 Node: Retrieves relevant DDL AND SQL examples from ChromaDB.
    """
    print("--- S2 Node: Retrieve Context (DDL + SQL Examples) ---")
    question = state['question']
    
    # Generate a single embedding for the question to use for both queries
    print("   - Generating explicit query embedding...")
    query_embedding = embeddings.embed_documents([question])[0]
    
    # 1. Retrieve DDL
    print("   - Retrieving DDL...")
    ddl_results = ddl_collection.query(query_embeddings=[query_embedding], n_results=3)
    retrieved_ddls = ddl_results.get('documents', [[]])[0]
    db_schema = "\n\n".join(retrieved_ddls)
    
    # 2. Retrieve SQL Examples
    print("   - Retrieving SQL examples...")
    example_results = sql_collection.query(query_embeddings=[query_embedding], n_results=3)
    retrieved_examples = example_results.get('documents', [[]])[0]

    print(f"Retrieved Schema snippet: {''.join(db_schema.splitlines()[:2])}...")
    print(f"Retrieved {len(retrieved_examples)} examples.")

    if not retrieved_ddls and not retrieved_examples:
        return {**state, "error": "Could not retrieve any context from the database."}

    return {**state, "db_schema": db_schema, "retrieved_examples": retrieved_examples}

def synthesize_sql(state: GraphState) -> GraphState:
    """
    S2 Node: Generates SQL using few-shot examples from the context.
    """
    print("--- S2 Node: Synthesize SQL (with Few-shot RAG) ---")
    if state.get("error"):
        return state
        
    question = state['question']
    db_schema = state['db_schema']
    examples = state['retrieved_examples']
    
    example_prompt_section = "\n\n".join(examples) if examples else "No relevant examples found."

    prompt = f"""You are an expert SQLite data analyst.
Based on the provided database schema and relevant examples, write a single, executable SQLite SQL query to answer the user's question.
Pay close attention to the structure of the provided examples.

**Relevant Database Schema:**
{db_schema}

**Relevant SQL Examples:**
---
{example_prompt_section}
---

**User Question:**
{question}

**SQL Query:**
"""
    token_count = len(tokenizer.encode(prompt))
    print(f"   - Prompt token count: {token_count}")

    try:
        sql_query = llm.invoke(prompt)
        # Clean up potential markdown formatting
        cleaned_sql = sql_query.strip().replace("```sql", "").replace("```", "")
        print(f"Generated SQL: {cleaned_sql}")
        return {**state, "sql_query": cleaned_sql}
    except Exception as e:
        print(f"Error during SQL synthesis: {e}")
        return {**state, "error": "Failed to generate SQL from the LLM."}

# execute_sql and summarize_result are unchanged from S1, but are included here for completeness
def execute_sql(state: GraphState) -> GraphState:
    print("--- S2 Node: Execute SQL ---")
    if state.get("error"):
        return state
    sql_query = state['sql_query']
    conn = get_db_connection()
    try:
        result_df = pd.read_sql_query(sql_query, conn)
        print(f"Execution successful. Result shape: {result_df.shape}")
        return {**state, "result": result_df}
    except Exception as e:
        print(f"Error during SQL execution: {e}")
        return {**state, "error": f"SQL Execution Failed: {str(e)}"}
    finally:
        conn.close()

def summarize_result(state: GraphState) -> GraphState:
    print("--- S2 Node: Summarize Result ---")
    if error := state.get("error"):
        summary = f"I encountered an error: {error}"
        print(summary)
        return {**state, "summary": summary}
    question = state['question']
    result_df = state['result']
    if result_df is None or result_df.empty:
        summary = "The query ran successfully but returned no results."
        print(summary)
        return {**state, "summary": summary}
    prompt = f"""
The user asked the following question: '{question}'.
The system executed a SQL query and got the following result in a pandas DataFrame:

{result_df.to_string(max_rows=10)}

Please provide a concise, natural language summary of this result that directly answers the user's question.
Do not mention SQL or DataFrames. Just state the answer.

**Summary:**
"""
    try:
        summary = llm.invoke(prompt)
        print(f"Generated Summary: {summary.strip()}")
        return {**state, "summary": summary.strip()}
    except Exception as e:
        print(f"Error during summarization: {e}")
        return {**state, "summary": "Successfully fetched data, but failed to generate a summary."}