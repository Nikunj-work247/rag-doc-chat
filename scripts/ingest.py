import argparse

from docchat.ingestion import ingest
from docchat.retrieval import reset_collection

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--reset", action="store_true", help="delete the collection before indexing"
    )
    args = parser.parse_args()

    if args.reset:
        reset_collection()
        print("Collection deleted.")

    n = ingest()
    print(f"Indexed {n} chunks.")