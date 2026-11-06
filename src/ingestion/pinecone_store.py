import os
from pinecone import Pinecone
from dotenv import load_dotenv
from src.ingestion.chunker import PatentChunk
from src.ingestion.embedder import embed_text

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "patent-prior-art")


def get_index():
    """Return the Pinecone index."""
    pc = Pinecone(api_key=PINECONE_API_KEY)
    return pc.Index(PINECONE_INDEX_NAME)


def store_chunks(chunks: list[PatentChunk]) -> None:
    """
    Embed each chunk and upsert into Pinecone.
    Uses batch upsert for efficiency.
    """
    index = get_index()
    vectors = []

    for chunk in chunks:
        print(f"  Embedding {chunk.chunk_id}...")
        embedding = embed_text(chunk.text)
        vectors.append({
            "id": chunk.chunk_id,
            "values": embedding,
            "metadata": {**chunk.metadata, "text": chunk.text[:1000]}
        })

    # Upsert in batches of 100
    batch_size = 100
    for i in range(0, len(vectors), batch_size):
        batch = vectors[i:i + batch_size]
        index.upsert(vectors=batch)
        print(f" Upserted batch of {len(batch)} vectors")


def patent_exists(patent_number: str) -> bool:
    """Check if a patent is already stored in Pinecone."""
    index = get_index()
    results = index.fetch(ids=[f"{patent_number}_abstract"])
    return len(results.vectors) > 0