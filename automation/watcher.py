import time
import subprocess
from pathlib import Path
from django.conf import settings
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class KnowledgeFileHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if not event.is_directory:
            self.ingest()

    def on_created(self, event):
        if not event.is_directory:
            self.ingest()

    def ingest(self):
        print("🔄 Auto-ingesting knowledge folder...")
        try:
            from rag.ingestion import ingest_folder
            ingest_folder(settings.BASE_DIR / 'knowledge')
        except Exception as e:
            print(f"⚠️ Auto-ingest failed: {e}")

def start_watcher():
    """Start the watchdog observer in a background thread."""
    path = settings.BASE_DIR / 'knowledge'
    if not path.exists():
        path.mkdir(parents=True)
    
    event_handler = KnowledgeFileHandler()
    observer = Observer()
    observer.schedule(event_handler, path=str(path), recursive=True)
    observer.start()
    print(f"👁️ Watching {path} for changes...")
    return observer