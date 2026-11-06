from src.ingestion.epo_client import fetch_patent
from src.ingestion.patent_parser import parse_patent
from src.extraction.extractor import extract_invention
from src.retrieval.retriever import retrieve_prior_art
from src.mapping.mapper import map_claims

def test_mapper():
    """Test the full Extract → Retrieve → Map pipeline."""

    # Extract from EP1000000
    raw = fetch_patent("EP1000000")
    parsed = parse_patent(raw)
    patent_text = f"""
    ABSTRACT: {parsed.abstract}
    CLAIMS: {chr(10).join(parsed.claims[:3])}
    """

    print("\n Extracting inventive concept...")
    extraction = extract_invention(patent_text)
    print(f"  Concept: {extraction['concept'][:100]}...")

    # Retrieve
    print("\n Retrieving prior art...")
    results = retrieve_prior_art(extraction, max_results=3)
    print(f"  Top result: {results[0]['patent_number']} [{results[0]['score']}]")

    # Map against top result only
    top_patent = results[0]["patent_number"]
    top_chunks = [r for r in results if r["patent_number"] == top_patent]

    print(f"\n Mapping claims against {top_patent}...")
    mapping = map_claims(extraction, top_patent, top_chunks)

    # Display results
    print(f"\n Mapping complete")
    print(f"\n RISK LEVEL: {mapping['risk_level'].upper()}")
    print(f"\n OVERALL ASSESSMENT:\n{mapping['overall_assessment']}")
    print(f"\n ELEMENT MAPPING:")
    for em in mapping["element_mapping"]:
        status_emoji = {"prior_art": "🔴", "ambiguous": "🟡", "novel": "🟢"}.get(em["status"], "⚪")
        print(f"\n  {status_emoji} {em['element']}")
        print(f"     Status: {em['status']}")
        print(f"     Evidence: {em['evidence'][:100]}...")
        print(f"     Explanation: {em['explanation']}")

if __name__ == "__main__":
    test_mapper()