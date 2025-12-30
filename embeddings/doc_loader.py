from pathlib import Path
from typing import List, Dict, Optional
import uuid
import subprocess
from embeddings.document_loader import chunk_text

def _extract_doc_text(path: Path) -> Optional[str]:
    try:
        import textract
        data = textract.process(str(path))
        return data.decode("utf-8", errors="ignore")
    except Exception:
        pass

    try:
        result = subprocess.run(
            ["antiword", str(path)],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.stdout:
            return result.stdout
    except Exception:
        return None

    return None

def load_doc_files(folder: str, chunk_documents: bool = True) -> List[Dict]:
    """
    Load .doc files from a folder, extract text, and optionally chunk them.
    """
    docs: List[Dict] = []
    folder_path = Path(folder)
    if not folder_path.exists():
        print(f"Warning: Folder {folder} does not exist")
        return []

    doc_files = list(folder_path.rglob("*.doc"))
    if not doc_files:
        print(f"Warning: No .doc files found in {folder}")
        return []

    for path in doc_files:
        try:
            text = _extract_doc_text(path) or ""
            if not text.strip():
                print(f"Warning: No text extracted from {path}")
                continue

            if chunk_documents and len(text) > 1000:
                chunks = chunk_text(text, chunk_size=1000, overlap=200)
                for i, chunk in enumerate(chunks):
                    if chunk.strip():
                        docs.append({
                            "id": str(uuid.uuid4()),
                            "text": chunk,
                            "meta": {
                                "path": str(path),
                                "source": "doc_file",
                                "filename": path.name,
                                "doc_type": "testcase",
                                "chunk_index": i,
                                "total_chunks": len(chunks),
                            },
                        })
            else:
                docs.append({
                    "id": str(uuid.uuid4()),
                    "text": text,
                    "meta": {
                        "path": str(path),
                        "source": "doc_file",
                        "filename": path.name,
                        "doc_type": "testcase",
                    },
                })
        except Exception as e:
            print(f"Error loading {path}: {e}")
            continue

    print(f"Loaded {len(docs)} document chunks from {len(doc_files)} files")
    return docs
