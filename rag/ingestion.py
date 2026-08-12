import os
import json
import numpy as np
from pathlib import Path
from django.conf import settings
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from .lancedb_client import get_table, embed_text

# ============================================================
# TEXT CHUNKING & FILE READING
# ============================================================
def chunk_text(text, max_length=500):
    words = text.split()
    chunks = []
    current_chunk = []
    current_length = 0
    
    for word in words:
        current_length += len(word) + 1
        if current_length > max_length and current_chunk:
            chunks.append(' '.join(current_chunk))
            current_chunk = [word]
            current_length = len(word)
        else:
            current_chunk.append(word)
    
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    return chunks

def read_file(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.pdf':
        try:
            import PyPDF2
            text = ""
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text()
            return text
        except ImportError:
            return ""
    elif ext in ['.txt', '.md', '.py', '.php', '.html', '.css', '.js', '.json']:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    return ""

# ============================================================
# INGESTION
# ============================================================
def ingest_folder(folder_path, table_name="knowledge"):
    folder = Path(folder_path)
    if not folder.exists():
        print(f"❌ Folder {folder_path} does not exist.")
        return
    
    table = get_table(table_name)
    files_processed = 0
    
    for file_path in folder.rglob('*'):
        if file_path.is_file():
            print(f"📄 Reading: {file_path}")
            text = read_file(str(file_path))
            if text:
                chunks = chunk_text(text)
                file_id = str(file_path)
                data = []
                for i, chunk in enumerate(chunks):
                    vector = embed_text(chunk)
                    data.append({
                        "text": chunk,
                        "vector": vector,
                        "metadata": json.dumps({"source": file_id, "chunk": i})
                    })
                if data:
                    table.add(data)
                files_processed += 1
                print(f"  -> Added {len(chunks)} chunks.")
    
    print(f"✅ Ingestion complete. Processed {files_processed} files.")

# ============================================================
# CHAIN-OF-RANK RERANKING (Sprint 6)
# ============================================================
def rerank_results(query: str, documents: list, metadatas: list, n_results: int = 3) -> tuple:
    """
    Chain-of-Rank: Rerank RAG results to filter contradictions.
    Returns (reranked_docs, reranked_metadatas)
    """
    if len(documents) <= 1:
        return documents, metadatas
    
    query_embedding = embed_text(query)
    doc_embeddings = [embed_text(doc) for doc in documents]
    
    scores = [cosine_similarity([query_embedding], [emb])[0][0] for emb in doc_embeddings]
    
    pairs = list(zip(documents, metadatas, scores))
    sorted_pairs = sorted(pairs, key=lambda x: x[2], reverse=True)
    
    top_pairs = sorted_pairs[:n_results]
    
    if top_pairs and top_pairs[0][2] < 0.3:
        return ["No relevant documents found."], [{}]
    
    reranked_docs = [p[0] for p in top_pairs]
    reranked_metadatas = [p[1] for p in top_pairs]
    
    return reranked_docs, reranked_metadatas

# ============================================================
# QUERY KNOWLEDGE (with Chain-of-Rank)
# ============================================================
def query_knowledge(query_text, table_name="knowledge", n_results=5):
    """Retrieve relevant chunks using LanceDB and rerank."""
    table = get_table(table_name)
    query_vector = embed_text(query_text)
    
    results = table.search(query_vector).limit(n_results * 2).to_pandas()
    
    documents = []
    metadatas = []
    if not results.empty:
        for idx, row in results.iterrows():
            documents.append(row['text'])
            try:
                metadatas.append(json.loads(row['metadata']))
            except:
                metadatas.append({})
    
    if documents:
        reranked_docs, reranked_metadatas = rerank_results(query_text, documents, metadatas, n_results)
        return reranked_docs, reranked_metadatas
    
    return documents, metadatas