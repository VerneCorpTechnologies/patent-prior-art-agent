from src.ingestion.epo_client import fetch_patent
from src.ingestion.patent_parser import parse_patent
from src.extraction.extractor import extract_invention
from src.retrieval.retriever import retrieve_prior_art

def test_retriever():
    """Test the full Extract → Retrieve pipeline."""

    # Use EP1000000 (brick manufacturing apparatus) as our input patent
    raw = fetch_patent("EP1000000")
    parsed = parse_patent(raw)

    patent_text = f"""
    ABSTRACT:
    {parsed.abstract}

    CLAIMS:
    {chr(10).join(parsed.claims[:3])}
    """

    # Extract
    print("\n Extracting inventive concept...")
    extraction = extract_invention(patent_text)
    print(f"  Concept: {extraction['concept'][:100]}...")

    # Retrieve
    results = retrieve_prior_art(extraction, max_results=5)

    print(f"\n Retrieved {len(results)} results:")
    for r in results:
        print(f"  [{r['score']}] {r['patent_number']} — {r['section']} {r['claim_number']}")

if __name__ == "__main__":
    test_retriever()