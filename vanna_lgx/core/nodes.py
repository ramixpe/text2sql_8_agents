# vanna_lgx/core/nodes.py - S5.1 FINAL CORRECTED VERSION

import chromadb
import tiktoken
import json
import re
import pandas as pd
from langchain_ollama import OllamaLLM as Ollama
from langchain_ollama import OllamaEmbeddings

from vanna_lgx.core.state import GraphState
from vanna_lgx.utils.db_utils import get_db_connection, get_schema_info
from vanna_lgx.config import (
    OLLAMA_BASE_URL,
    SYNTHESIS_MODEL,
    EMBEDDING_MODEL,
    CHROMA_PATH,
)

# --- Initialize Constants and Clients ---
SCHEMA_INFO = get_schema_info()
MAX_REPAIR_ATTEMPTS = 2

llm = Ollama(base_url=OLLAMA_BASE_URL, model=SYNTHESIS_MODEL)
embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
tokenizer = tiktoken.get_encoding("cl100k_base")

chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
ddl_collection = chroma_client.get_collection(name="ddl")
sql_collection = chroma_client.get_collection(name="sql_examples")
docs_collection = chroma_client.get_collection(name="docs")


# --- S5: NEW NODE - Query Rewriter (Your Idea!) ---
def query_rewriter(state: GraphState) -> GraphState:
    """
    S5.1 Node: Rewrites the user's question for clarity and better retrieval.
    It uses the 'docs' collection (glossary) to inform the rewrite.
    """
    print("--- S5 Node: Query Rewriter ---")
    question = state['question']
    
    # --- THIS IS THE FIX ---
    # We must use the robust, explicit embedding pattern to query the docs collection.
    print("   - Generating embedding for docs retrieval...")
    query_embedding_for_docs = embeddings.embed_documents([question])[0]
    docs_results = docs_collection.query(
        query_embeddings=[query_embedding_for_docs], 
        n_results=2
    )
    # --- END OF FIX ---
    
    retrieved_docs = docs_results.get('documents', [[]])[0]
    docs_context = "\n".join(retrieved_docs)

    rewrite_prompt = f"""You are an expert system that rewrites a user's question to be more clear, specific, and optimized for a database query.
Use the provided context to resolve acronyms and add specific database terminology.

**Context / Glossary:**
---
{docs_context}
---

**User's Original Question:**
"{question}"

Rewrite the user's question. Do not answer it, just improve it by making it more explicit for a database analyst.

**Rewritten Question:**
"""
    
    rewritten_question = llm.invoke(rewrite_prompt).strip()
    print(f"   - Original Question: '{question}'")
    print(f"   - Rewritten Question: '{rewritten_question}'")
    
    return {**state, "rewritten_question": rewritten_question}


def retrieve_context(state: GraphState) -> GraphState:
    """ S5 Node: Retrieves context using the REWRITTEN question. """
    print("--- S5 Node: Retrieve Context ---")
    question = state['rewritten_question']
    
    print("   - Generating explicit query embedding...")
    query_embedding = embeddings.embed_documents([question])[0]
    
    ddl_results = ddl_collection.query(query_embeddings=[query_embedding], n_results=3)
    example_results = sql_collection.query(query_embeddings=[query_embedding], n_results=3)
    docs_results = docs_collection.query(query_embeddings=[query_embedding], n_results=3)

    retrieved_ddls = ddl_results.get('documents', [[]])[0]
    retrieved_examples = example_results.get('documents', [[]])[0]
    retrieved_docs = docs_results.get('documents', [[]])[0]

    print(f"   - Retrieved {len(retrieved_ddls)} DDLs, {len(retrieved_examples)} examples, {len(retrieved_docs)} docs.")
    
    return {
        **state,
        "db_schema": "\n\n".join(retrieved_ddls),
        "retrieved_examples": retrieved_examples,
        "retrieved_docs": retrieved_docs
    }


def rerank_and_judge(state: GraphState) -> GraphState:
    """ S5 Node: Robust, index-based judge that always keeps retrieved DDL. """
    print("--- S5 Node: Rerank and Judge ---")
    question = state['rewritten_question']
    
    retrieved_ddls = state['db_schema'].split("\n\n")
    other_docs = state['retrieved_docs'] + state['retrieved_examples']
    other_docs = [doc for doc in other_docs if doc.strip()]

    if not other_docs:
        clean_context = {"ddl": retrieved_ddls, "examples": [], "docs": []}
        return {**state, "clean_context": clean_context}

    indexed_context = ""
    for i, doc in enumerate(other_docs):
        indexed_context += f"--- Document {i} ---\n{doc}\n\n"

    judge_prompt = f"""You are a data analyst acting as a context judge. The user wants to query a telecom database. The primary table schema has been automatically included. Your task is to evaluate additional documents (SQL examples, business rules) and decide if they are relevant for answering the user's question.

**Rewritten User Question:** "{question}"

**Numbered Context Documents:**
{indexed_context}

**Instructions:** Return a JSON object with one key: "keep_indices", a list of integers corresponding to the document numbers to keep.

**Your JSON Response:**
"""
    try:
        print("   - Asking LLM Judge to evaluate Examples and Docs...")
        response_str = llm.invoke(judge_prompt)
        json_start = response_str.find('{'); json_end = response_str.rfind('}') + 1
        judgement = json.loads(response_str[json_start:json_end])
        keep_indices = judgement.get('keep_indices', [])
        
        print(f"   - Judge decided to keep indices: {keep_indices}")
        
        kept_docs = [other_docs[i] for i in keep_indices if i < len(other_docs)]
        
        clean_context = {
            "ddl": retrieved_ddls, 
            "examples": [doc for doc in kept_docs if doc.strip().upper().startswith("QUESTION:")],
            "docs": [doc for doc in kept_docs if not doc.strip().upper().startswith("QUESTION:")]
        }
        
        print(f"   - Assembled {len(clean_context['ddl'])} DDLs, {len(clean_context['examples'])} examples, {len(clean_context['docs'])} docs.")
        return {**state, "clean_context": clean_context}
    except Exception as e:
        print(f"Error during context judgement: {e}")
        clean_context = { "ddl": retrieved_ddls, "examples": state["retrieved_examples"], "docs": state["retrieved_docs"]}
        return {**state, "error": "LLM Judge failed.", "clean_context": clean_context}


def synthesize_sql(state: GraphState) -> GraphState:
    """ S5 Node: Generates or refines SQL using rewritten question and judged context. """
    if state.get("repair_attempts", 0) > 0:
        print("--- S5 Node: Refine SQL (Repair Attempt) ---")
        error_context = f"The previous SQL had an error: '{state['validation_error']}'. Please fix it."
        prompt_title = "**Corrected SQL Query:**"
    else:
        print("--- S5 Node: Synthesize SQL ---")
        error_context = ""
        prompt_title = "**SQL Query:**"

    question = state['rewritten_question']
    clean_context = state.get('clean_context', {})
    db_schema = "\n\n".join(clean_context.get("ddl", []))
    examples = "\n\n".join(clean_context.get("examples", []))

    if not db_schema:
        return {**state, "sql_query": "", "error": "Judge discarded all DDL context."}

    prompt = f"""You are an expert SQLite analyst. Create a single, executable query.
{error_context}
Use the verified context below to answer the user's question.

**Verified Schema:**
---
{db_schema}
---
**Verified Examples:**
---
{examples}
---
**User Question:**
{question}

{prompt_title}
"""
    token_count = len(tokenizer.encode(prompt))
    print(f"   - Prompt token count: {token_count}")
    try:
        sql_query = llm.invoke(prompt)
        cleaned_sql = sql_query.strip().replace("```sql", "").replace("```", "")
        print(f"Generated SQL: {cleaned_sql}")
        return {**state, "sql_query": cleaned_sql, "validation_error": None}
    except Exception as e:
        return {**state, "error": f"Failed to generate SQL: {e}"}


def sql_linter_verifier(state: GraphState) -> GraphState:
    """ S4 Node: Performs static checks on the SQL for common errors. """
    print("--- S4 Node: SQL Linter/Verifier ---")
    if state.get("error"): return state
    
    sql = state.get("sql_query", "").strip()
    if not sql:
        return {**state, "validation_error": None}

    used_tables = re.findall(r'FROM\s+([`"\']?\w+[`"\']?)|JOIN\s+([`"\']?\w+[`"\']?)', sql, re.IGNORECASE)
    used_tables_flat = {t.strip('`"\'') for pair in used_tables for t in pair if t}
    
    for table in used_tables_flat:
        if table not in SCHEMA_INFO:
            error = f"Validation Error: Table '{table}' does not exist."
            print(f"   - {error}")
            return {**state, "validation_error": error}
    
    print("   - SQL passed basic static checks.")
    return {**state, "validation_error": None}


def auto_repair(state: GraphState) -> GraphState:
    """ S4 Node: Increments the repair counter. """
    print("--- S4 Node: Auto-Repair ---")
    attempts = state.get("repair_attempts", 0) + 1
    print(f"   - Repair attempt #{attempts}")
    return {**state, "repair_attempts": attempts}


def execute_sql(state: GraphState) -> GraphState:
    """ S4 Node: Executes the final SQL query. """
    print("--- S4 Node: Execute SQL ---")
    if state.get("error"): return state
    sql_query = state.get('sql_query')
    if not sql_query: 
        return {**state, "summary": "No SQL query was generated to execute."}

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


def summarize_and_visualize(state: GraphState) -> GraphState:
    """ S5 Node: Creates a text summary and a Vega-Lite chart spec if possible. """
    print("--- S5 Node: Summarize and Visualize ---")
    if error := (state.get("validation_error") or state.get("error")):
        summary = f"I could not successfully answer the question. The final error was: {error}"
        print(summary)
        return {**state, "summary": summary}
    
    question = state['question']
    result_df = state.get('result') 
    
    if result_df is None: return {**state, "summary": "The query did not produce a result."}
    if result_df.empty: return {**state, "summary": "The query ran successfully but returned no results."}
    
    # 1. Generate Text Summary
    summary_prompt = f"User question: '{question}'.\nQuery result:\n{result_df.to_string(max_rows=10)}\nProvide a concise, natural language summary of the result.\n**Summary:**"
    summary = llm.invoke(summary_prompt).strip()
    print(f"Generated Summary: {summary}")
    state['summary'] = summary

    # 2. Attempt to Generate Visualization
    vis_spec = None
    try:
        if 1 < len(result_df) <= 30 and len(result_df.columns) == 2:
            cols = result_df.columns
            if pd.api.types.is_string_dtype(result_df[cols[0]]) and pd.api.types.is_numeric_dtype(result_df[cols[1]]):
                print("   - Data is suitable for visualization. Generating chart spec...")
                data_for_prompt = result_df.to_dict(orient='records')
                vis_prompt = f"""Create a Vega-Lite JSON spec for a bar chart for this data.
- The x-axis should be '{cols[0]}', type nominal, with a title.
- The y-axis should be '{cols[1]}', type quantitative, with a title.
- Title: "{question}"
Data:
{json.dumps(data_for_prompt)}

Vega-Lite JSON Spec:
"""
                vis_response = llm.invoke(vis_prompt)
                json_start = vis_response.find('{'); json_end = vis_response.rfind('}') + 1
                vis_spec = json.loads(vis_response[json_start:json_end])
                print("   - Successfully generated Vega-Lite spec.")
    except Exception as e:
        print(f"   - Visualization generation failed: {e}")
        vis_spec = None

    return {**state, "visualization_spec": vis_spec}