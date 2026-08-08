import os
import sys
from pathlib import Path
from django.conf import settings
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings

# Initialize embedding model (runs locally on CPU, ~80 MB RAM)
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

# Initialize ChromaDB client (persistent, file-based)
chroma_client = chromadb.PersistentClient(
    path=str(settings.CHROMA_PERSIST_DIR),
    settings=Settings(anonymized_telemetry=False)
)

def get_or_create_collection(name="knowledge"):
    """Get or create a ChromaDB collection."""
    try:
        collection = chroma_client.get_collection(name)
    except:
        collection = chroma_client.create_collection(name)
    return collection

def chunk_text(text, max_length=500):
    """Simple recursive chunking by paragraphs or fixed length."""
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
    """Read text from common file types."""
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
            print("PyPDF2 not installed. Skipping PDF.")
            return ""
    elif ext in ['.txt', '.md', '.py', '.php', '.html', '.css', '.js']:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    else:
        return ""

def ingest_folder(folder_path, collection_name="knowledge"):
    """Recursively ingest all readable files in a folder."""
    folder = Path(folder_path)
    if not folder.exists():
        print(f"Folder {folder_path} does not exist.")
        return
    
    collection = get_or_create_collection(collection_name)
    files_processed = 0
    
    for file_path in folder.rglob('*'):
        if file_path.is_file():
            print(f"Reading: {file_path}")
            text = read_file(str(file_path))
            if text:
                chunks = chunk_text(text)
                file_id = str(file_path)
                
                # Add to ChromaDB with file path as metadata
                for i, chunk in enumerate(chunks):
                    chunk_id = f"{file_id}_chunk_{i}"
                    collection.add(
                        documents=[chunk],
                        metadatas=[{"source": file_id, "chunk": i}],
                        ids=[chunk_id]
                    )
                files_processed += 1
                print(f"  -> Added {len(chunks)} chunks.")
    
    print(f"✅ Ingestion complete. Processed {files_processed} files.")

def query_knowledge(query, collection_name="knowledge", n_results=5):
    """Retrieve relevant document chunks for a query."""
    collection = get_or_create_collection(collection_name)
    results = collection.query(
        query_texts=[query],
        n_results=n_results
    )
    
    # Extract documents and metadata
    documents = results.get('documents', [[]])[0]
    metadatas = results.get('metadatas', [[]])[0]
    
    return documents, metadatas