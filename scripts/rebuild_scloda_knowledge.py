"""Rebuild Scloda's DB-backed knowledge index."""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.services.scloda_memory import rebuild_knowledge_index


def main() -> None:
    app = create_app()
    with app.app_context():
        result = rebuild_knowledge_index(force=True)
        print(result)


if __name__ == "__main__":
    main()
