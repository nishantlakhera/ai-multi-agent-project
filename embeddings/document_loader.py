from pathlib import Path
from typing import List, Dict
import uuid

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """
    Split text into overlapping chunks for better context retention.
    """
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size

        # Try to break at sentence or paragraph boundary
        if end < len(text):
            # Look for paragraph break first
            last_para = text[start:end].rfind('\n\n')
            if last_para > chunk_size * 0.5:  # At least 50% through chunk
                end = start + last_para
            else:
                # Look for sentence break
                last_period = text[start:end].rfind('. ')
                if last_period > chunk_size * 0.5:
                    end = start + last_period + 1

        chunks.append(text[start:end].strip())
        start = end - overlap  # Overlap for context

    return chunks

def load_text_files(folder: str, chunk_documents: bool = True) -> List[Dict]:
    """
    Load text files from a folder and optionally chunk them.

    Args:
        folder: Path to folder containing .txt files
        chunk_documents: Whether to split large documents into chunks

    Returns:
        List of document dictionaries with id, text, and metadata
    """
    docs = []
    folder_path = Path(folder)
    if not folder_path.exists():
        print(f"Warning: Folder {folder} does not exist")
        return []

    txt_files = list(folder_path.rglob("*.txt"))
    if not txt_files:
        print(f"Warning: No .txt files found in {folder}")
        return []

    for path in txt_files:
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")

            if chunk_documents and len(text) > 1000:
                # Split large documents into chunks
                chunks = chunk_text(text, chunk_size=1000, overlap=200)
                for i, chunk in enumerate(chunks):
                    if chunk.strip():  # Skip empty chunks
                        docs.append({
                            "id": str(uuid.uuid4()),
                            "text": chunk,
                            "meta": {
                                "path": str(path),
                                "source": "local_file",
                                "filename": path.name,
                                "chunk_index": i,
                                "total_chunks": len(chunks),
                            },
                        })
            else:
                # Keep document as single piece
                docs.append({
                    "id": str(uuid.uuid4()),
                    "text": text,
                    "meta": {
                        "path": str(path),
                        "source": "local_file",
                        "filename": path.name,
                    },
                })
        except Exception as e:
            print(f"Error loading {path}: {e}")
            continue

    print(f"Loaded {len(docs)} document chunks from {len(txt_files)} files")
    return docs
