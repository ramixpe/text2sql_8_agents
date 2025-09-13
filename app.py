# app.py - The Streamlit UI for Vanna-LGX (CORRECTED)

import streamlit as st
import json
from vanna_lgx.core.graph import build_s5_graph # Import our final agent graph

# --- Page Configuration ---
st.set_page_config(
    page_title="Vanna-LGX",
    page_icon="🤖",
    layout="wide"
)

# --- Title and Description ---
st.title("🤖 Vanna-LGX: The Local Text-to-SQL Agent")
st.markdown("""
*This application is the culmination of our staged development process (S0-S5).
It uses a local, agentic graph built with LangGraph and Ollama to answer questions about your database.
Enter a question below and watch the agent's reasoning process unfold in real-time.*
""")

# --- Main Application Logic ---

# Initialize the LangGraph agent. We use st.cache_resource to ensure this
# only runs once, making the app much faster on subsequent interactions.
@st.cache_resource
def get_agent_app():
    print("--- Initializing Vanna-LGX Agent ---")
    return build_s5_graph()

app = get_agent_app()

# Get user input from a text box
user_question = st.text_input("Ask a question about your database:", placeholder="e.g., how many ont per vendor?")

if user_question:
    st.subheader("Agent's Thought Process")
    
    # --- THIS IS THE FIX ---
    # We create all the expanders at once and put a placeholder in each.
    # We will fill these placeholders as the stream runs.
    with st.expander("Agent 1: Query Rewriter", expanded=True) as expander:
        rewriter_placeholder = st.empty()
    with st.expander("Agent 2: Retrieve Context", expanded=True) as expander:
        retriever_placeholder = st.empty()
    with st.expander("Agent 3: Rerank and Judge", expanded=True) as expander:
        judge_placeholder = st.empty()
    with st.expander("Agent 4: Synthesize SQL", expanded=True) as expander:
        sql_placeholder = st.empty()
    
    st.subheader("Final Answer")
    final_result_container = st.container()

    # The initial state for the graph
    inputs = {
        "question": user_question,
        "repair_attempts": 0
    }

    # Fill the placeholders with an initial "waiting" message
    rewriter_placeholder.info("Waiting for agent to start...")
    retriever_placeholder.info("Waiting for previous Agent...")
    judge_placeholder.info("Waiting for previous Agent...")
    sql_placeholder.info("Waiting for previous Agent...")
    
    try:
        with st.spinner("The agent is thinking... This may take a moment."):
            # --- LangGraph Streaming ---
            for event in app.stream(inputs):
                node_name = list(event.keys())[0]
                node_output = event[node_name]

                # Update the UI with the output from each node
                if node_name == "query_rewriter":
                    with rewriter_placeholder.container():
                        st.markdown("**Original Question:**")
                        st.info(node_output['question'])
                        st.markdown("**Rewritten Question:**")
                        st.success(node_output['rewritten_question'])
                    retriever_placeholder.info("Retrieving context based on rewritten question...")

                elif node_name == "retrieve_context":
                    with retriever_placeholder.container():
                        st.markdown(f"**Retrieved {len(node_output['db_schema'].split('CREATE TABLE')) - 1} DDLs, {len(node_output['retrieved_examples'])} examples, and {len(node_output['retrieved_docs'])} docs.**")
                        with st.popover("View Retrieved DDL"):
                            st.code(node_output['db_schema'], language="sql")
                    judge_placeholder.info("Judging the retrieved context...")

                elif node_name == "rerank_and_judge":
                    with judge_placeholder.container():
                        clean_context = node_output.get('clean_context', {})
                        ddl_count = len(clean_context.get('ddl', []))
                        ex_count = len(clean_context.get('examples', []))
                        doc_count = len(clean_context.get('docs', []))
                        st.markdown(f"**Judge decided to keep {ddl_count} DDLs, {ex_count} examples, and {doc_count} docs.**")
                        if node_output.get("error"):
                            st.error(f"Judge Error: {node_output['error']}")
                    sql_placeholder.info("Synthesizing SQL from clean context...")

                elif node_name == "synthesize_sql" or node_name == "auto_repair":
                     with sql_placeholder.container():
                        if sql := node_output.get('sql_query'):
                            st.markdown("**Final SQL Query:**")
                            st.code(sql, language="sql")
                        if error := node_output.get('error'):
                            st.error(error)
                        if error := node_output.get('validation_error'):
                            st.warning(f"SQL Validation Error: {error} - Attempting to repair.")
                
                # The final state is in the last node's output
                elif node_name == "summarize_and_visualize":
                    with final_result_container:
                        st.markdown(node_output['summary'])
                        if vis_spec := node_output.get('visualization_spec'):
                            st.markdown("---")
                            st.subheader("Visualization")
                            try:
                                st.vega_lite_chart(vis_spec, use_container_width=True)
                            except Exception as e:
                                st.error(f"Failed to render chart: {e}")
                                st.json(vis_spec)

    except Exception as e:
        st.error(f"An unexpected error occurred during the agent run: {e}")
