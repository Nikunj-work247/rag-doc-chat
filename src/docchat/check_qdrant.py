from config import settings
from retrieval import get_client

print("=== QDRANT DIAGNOSTICS ===")

print("Configured URL:", settings.qdrant_url)
print("API key loaded:", bool(settings.qdrant_api_key))
print("Expected collection:", settings.collection_name)

if not settings.qdrant_url:
    raise RuntimeError(
        "QDRANT_URL is missing. The application would use local storage."
    )

client = get_client()

print("\nConnection successful!")

print("\n=== COLLECTIONS ===")
collections = client.get_collections()

for collection in collections.collections:
    print("-", collection.name)

print("\n=== TARGET COLLECTION ===")

name = settings.collection_name

if not client.collection_exists(name):
    print(f"Collection '{name}' does not exist in this cluster.")
else:
    info = client.get_collection(name)

    print("Collection:", name)
    print("Points count:", info.points_count)
    print("Indexed vectors count:", info.indexed_vectors_count)

    points, _ = client.scroll(
        collection_name=name,
        limit=3,
        with_payload=True,
        with_vectors=False,
    )

    print("\n=== SAMPLE CHUNKS ===")

    for point in points:
        print("\nPoint ID:", point.id)
        print("Payload:", point.payload)