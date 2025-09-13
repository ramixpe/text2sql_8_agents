# Vanna-LGX: A Local-First, Agentic Text-to-SQL System

Vanna-LGX is a project to build a sophisticated, local-first Text-to-SQL agent using a graph-based architecture. It leverages local LLMs via Ollama and a local vector store to provide a private, powerful, and extensible data analysis tool.

The project is developed in stages, with each stage adding a new layer of intelligence and robustness.

**Current Stage: S2 - Few-shot Example Aware Agent**
* The agent uses RAG to retrieve relevant table schemas (DDL).
* It also retrieves curated, human-approved `Question -> SQL` examples to learn complex query patterns.
* This "few-shot" approach dramatically improves the quality and complexity of the generated SQL.

---

### Architecture (Stage S2)

The agent operates as a state machine orchestrated by LangGraph.

```mermaid
graph TD
    A[Start] --> B(retrieve_context);
    B --> C(synthesize_sql);
    C --> D(execute_sql);
    D --> E(summarize_result);
    E --> F[End];

### Tech Stack

Orchestration: LangGraph

LLM Backend: Ollama (e.g., gpt-oss, llama3)

Embedding Models: Ollama (e.g., mxbai-embed-large, nomic-embed-text)

Vector Database: ChromaDB (local persistence)

Database: SQLite

Tech Stack

Orchestration: LangGraph

LLM Backend: Ollama (e.g., gpt-oss, llama3)

Embedding Models: Ollama (e.g., mxbai-embed-large, nomic-embed-text)

Vector Database: ChromaDB (local persistence)

Database: SQLite

Setup and Installation

1. Clone the Repository

Bash
git clone <your-repo-url>
cd vanna_lgx
2. Set up Environment
It is highly recommended to use a Conda or venv environment.

Bash
# Using Conda
conda create -n vanna_lgx python=3.11
conda activate vanna_lgx
3. Install Dependencies

Bash
pip install -r requirements.txt
4. Set up Ollama
Ensure Ollama is installed and running. Pull the models required for this project:

Bash
# For SQL Synthesis
ollama pull gpt-oss

# For Embeddings
ollama pull mxbai-embed-large
(Note: You can change the models used in vanna_lgx/config.py)

5. Place Your Database
Place your SQLite database file (e.g., unoc_19_jan.db) inside the data/ directory.

Data Ingestion

Before running the agent, you must populate the local knowledge base (ChromaDB).

1. Prepare Knowledge Files

DDL: This is extracted automatically from your database.

SQL Examples: Add your high-quality Question -> SQL pairs to knowledge/sql_examples/examples.json.

2. Run Ingestion Scripts
Execute these commands from the project root directory.

Bash
# Ingest the database schema
python -m scripts.ingest_ddl

# Ingest the SQL examples
python -m scripts.ingest_sql_examples
These scripts will create a chroma/ directory containing the vector store. (This directory is in .gitignore and should not be committed).

Running the Agent

Once setup and ingestion are complete, you can start the agent.

Bash
python -m vanna_lgx.main
Project Structure

.
├── knowledge/
│   └── sql_examples/
│       └── examples.json
├── scripts/
│   ├── ingest_ddl.py
│   └── ingest_sql_examples.py
├── vanna_lgx/
│   ├── core/
│   │   ├── graph.py
│   │   ├── nodes.py
│   │   └── state.py
│   ├── utils/
│   ├── config.py
│   └── main.py
├── data/
│   └── unoc_19_jan.db
├── .gitignore
└── README.md
