"""Launch the Canivue NLP Clinical Inspector & Active Learning Studio.

Usage:
    python tools/nlp_inspector/run.py
"""

from __future__ import annotations

import sys
import threading
import time
import webbrowser
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def open_browser():
    time.sleep(1.2)
    webbrowser.open("http://127.0.0.1:8050")


def main():
    import uvicorn

    print("=" * 70)
    print("🐾 Canivue AI — NLP Clinical Inspector & Active Learning Studio")
    print("=" * 70)
    print("• Inspector UI URL: http://127.0.0.1:8050")
    print("• Model Engine:     SymptomParserPipeline (Multi-Task DistilBERT)")
    print("• Feedback Pool:    data/active_learning_feedback.jsonl")
    print("• Press Ctrl+C to stop server")
    print("=" * 70)

    # Automatically launch browser in background thread
    threading.Thread(target=open_browser, daemon=True).start()

    uvicorn.run("tools.nlp_inspector.app:app", host="127.0.0.1", port=8050, log_level="info")


if __name__ == "__main__":
    main()
