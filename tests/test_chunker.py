from src.ingestion.epo_client import fetch_patent
from src.ingestion.patent_parser import parse_patent
from src.ingestion.chunker import chunk_patent

def test_chunker():
    """Test that a patent is correctly chunked into atomic units."""
    raw = fetch_patent("EP1000000")
    parsed = parse_patent(raw)
    chunks = chunk_patent(parsed)

    print(f"\n Total chunks: {len(chunks)}")

    for chunk in chunks:
        print(f"\n [{chunk.section.upper()}] {chunk.chunk_id}")
        print(f"Text ({len(chunk.text)} chars): {chunk.text[:100]}...")
        print(f"Metadata: {chunk.metadata}")

if __name__ == "__main__":
    test_chunker()