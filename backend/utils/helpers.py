from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

def load_prompt(name: str) -> str:
    path = BASE_DIR / "prompts" / f"{name}.txt"
    return path.read_text(encoding="utf-8")
