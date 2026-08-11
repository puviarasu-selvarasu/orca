import os
import json
from pathlib import Path
from django.conf import settings
from .lancedb_client import get_table, embed_batch, embed_text

def chunk_text(text, max_length=500):
    """Simple chunking by words."""
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
            return ""
    elif ext in ['.txt', '.md', '.py', '.php', '.html', '.css', '.js', '.json']:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    return ""

def ingest_folder(folder_path, table_name="knowledge"):
    """Ingest all files in a folder into LanceDB."""
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

def query_knowledge(query_text, table_name="knowledge", n_results=5):
    """Retrieve relevant chunks using LanceDB."""
    table = get_table(table_name)
    query_vector = embed_text(query_text)
    
    # LanceDB native vector search
    results = table.search(query_vector).limit(n_results).to_pandas()
    
    documents = []
    metadatas = []
    if not results.empty:
        for idx, row in results.iterrows():
            documents.append(row['text'])
            try:
                metadatas.append(json.loads(row['metadata']))
            except:
                metadatas.append({})
    
    return documents, metadatas