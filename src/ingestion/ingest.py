from src.ingestion.epo_client import fetch_patent
from src.ingestion.patent_parser import parse_patent
from src.ingestion.chunker import chunk_patent
from src.ingestion.pinecone_store import store_chunks, patent_exists


def ingest_patent(patent_number: str) -> None:
    """
    Full ingestion pipeline for a single patent:
    Fetch → Parse → Chunk → Embed → Store in Pinecone
    """
    print(f"\n Ingesting {patent_number}...")

    if patent_exists(patent_number):
        print(f" Already ingested — skipping")
        return

    print(f" Fetching from EPO API...")
    raw = fetch_patent(patent_number)

    print(f" Parsing XML...")
    parsed = parse_patent(raw)

    print(f" Chunking...")
    chunks = chunk_patent(parsed)
    print(f" {len(chunks)} chunks created")

    print(f" Embedding and storing in Pinecone...")
    store_chunks(chunks)

    print(f" {patent_number} ingested successfully")


def ingest_patents(patent_numbers: list[str]) -> None:
    """Ingest a list of patents."""
    print(f"\n Starting ingestion of {len(patent_numbers)} patents...")
    for patent_number in patent_numbers:
        ingest_patent(patent_number)
    print(f"\n Ingestion complete")