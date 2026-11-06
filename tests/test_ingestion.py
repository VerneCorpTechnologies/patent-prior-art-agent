import time
from src.ingestion.ingest import ingest_patent
from src.ingestion.pinecone_store import patent_exists

def test_ingest_patent():
    """Test the full ingestion pipeline end to end."""
    patent_number = "EP1000000"

    ingest_patent(patent_number)

    # Wait briefly for Pinecone to index the vectors
    print("\n Waiting for Pinecone to index...")
    time.sleep(5)

    # Verify it landed in Pinecone
    assert patent_exists(patent_number), "Patent not found in Pinecone after ingestion"
    print(f"\n {patent_number} confirmed in Pinecone")

if __name__ == "__main__":
    test_ingest_patent()