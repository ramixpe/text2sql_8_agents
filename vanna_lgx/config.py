# config.py
import os

# --- LLM Configuration ---
OLLAMA_BASE_URL = "http://localhost:11434"
# The powerful model for SQL synthesis and summarization
SYNTHESIS_MODEL = "gpt-oss:latest" 

# --- Database Configuration ---
DB_PATH = os.path.join("data", "database_19_jan.db")

# --- Vector Store Configuration (for future stages) ---
CHROMA_PATH = "chroma"
EMBEDDING_MODEL = "mxbai-embed-large:latest"
KNOWLEDGE_BASE_PATH = "knowledge"
