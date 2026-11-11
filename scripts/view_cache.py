import json
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "llm_cache.db"


def main():
    if not DB_PATH.exists():
        print(f"No cache database found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if "--clear" in sys.argv:
        cursor.execute("DELETE FROM full_llm_cache;")
        cursor.execute("DELETE FROM full_md5_llm_cache;")
        conn.commit()
        print("LLM cache cleared successfully.")
        return

    cursor.execute("SELECT prompt, response, llm FROM full_llm_cache")
    rows = cursor.fetchall()

    print(f"\n================ LLM CACHE INSPECTOR ================")
    print(f"Database: {DB_PATH}")
    print(f"Total Cached Entries: {len(rows)}")
    print(f"=====================================================\n")

    if not rows:
        print("Cache is currently empty.")
        return

    for i, (prompt_json, response_json, llm_info) in enumerate(rows, 1):
        try:
            resp_obj = json.loads(response_json)
            # Langchain serialized message text
            answer = (
                resp_obj.get("kwargs", {})
                .get("message", {})
                .get("kwargs", {})
                .get("content", "")
            )
            if not answer:
                answer = resp_obj.get("text", "")
        except Exception:
            answer = response_json

        print(f"--- Entry #{i} ---")
        print(f"Cached Answer:\n{answer}\n")
        print("-" * 55)

    print("\nTip: Run with '--clear' to wipe all cached items:")
    print("  .venv/bin/python scripts/view_cache.py --clear\n")


if __name__ == "__main__":
    main()
