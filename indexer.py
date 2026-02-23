import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import chromadb

# Setup DB
path_db = "./chroma_db"
client = chromadb.PersistentClient(path=path_db)
collection = client.get_or_create_collection(name="tdah_resources")

class DocumentManager(FileSystemEventHandler):
    def on_created(self, event):
        # Process only new .txt files
        if not event.is_directory and event.src_path.endswith('.txt'):
            print(f"\n[!] NEW_DOCUMENT: {event.src_path}")
            self.process_document(event.src_path) # FIXED: Updated to English name

    def process_document(self, filepath):
        filename = os.path.basename(filepath)
        
        # Check if already indexed
        res = collection.get(where={"source": filename})
        if res and len(res.get('ids', [])) > 0:
            print(f"[-] '{filename}' already indexed.")
            return

        print(f"[+] Processing/indexing '{filename}'...")
        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()

        # Chunk text by single lines
        parr = [p for p in text.split('\n') if p.strip()]
        
        # Save chunks in DB
        for i, p in enumerate(parr):
            doc_id = f"{filename}_chunk_{i}"
            collection.add(
                documents=[p],
                metadatas=[{"source": filename}],
                ids=[doc_id]
            )
            
        print(f"[v] '{filename}' indexed correctly with {len(parr)} fragments.")

# Watchdog setup
if __name__ == "__main__":
    watch_dir = "./documents_tdah"
    os.makedirs(watch_dir, exist_ok=True)
    
    event_handler = DocumentManager()
    observer = Observer()
    observer.schedule(event_handler, watch_dir, recursive=False)
    observer.start()
    
    print(f"=== AUTOMATIC INDEXER ===")
    print(f"Watching '{watch_dir}' directory...")
    print("Save a .txt file in the directory to test. (Ctrl+C to exit)\n")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\nTurning Off...")
    observer.join()