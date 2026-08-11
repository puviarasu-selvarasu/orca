import os
import json
import lancedb
import numpy as np
import pyarrow as pa
from pathlib import Path
from django.conf import settings
from sentence_transformers import SentenceTransformer

# ============================================================
# 1. LOAD EMBEDDING MODEL (BGE Small - 33MB)
# ============================================================
embedding_model = SentenceTransformer('BAAI/bge-small-en-v1.5')

# ============================================================
# 2. INITIALIZE LANCEDB
# ============================================================
DB_PATH = settings.CHROMA_PERSIST_DIR  # Reusing the same config var for simplicity
Path(DB_PATH).mkdir(parents=True, exist_ok=True)

db = lancedb.connect(str(DB_PATH))

# ============================================================
# 3. GET OR CREATE TABLE (Using PyArrow Schema)
# ============================================================
def get_table(table_name="knowledge"):
    """Get or create a LanceDB table."""
    if table_name in db.table_names():
        return db.open_table(table_name)
    else:
        # Define the schema using pyarrow
        schema = pa.schema([
            pa.field("text", pa.string()),
            pa.field("vector", pa.list_(pa.float32(), 384)),  # 384 dims for bge-small
            pa.field("metadata", pa.string()),
        ])
        return db.create_table(table_name, schema=schema)

def embed_text(text: str):
    """Generate embedding for a single text."""
    return embedding_model.encode(text).tolist()

def embed_batch(texts: list):
    """Generate embeddings for a batch of texts."""
    return embedding_model.encode(texts).tolist()