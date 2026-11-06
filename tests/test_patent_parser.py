from src.ingestion.epo_client import fetch_patent
from src.ingestion.patent_parser import parse_patent

def test_parse_patent():
    """Test parsing a real patent into structured sections."""
    raw = fetch_patent("EP1000000")
    parsed = parse_patent(raw)

    print(f"\n Patent number: {parsed.patent_number}")
    print(f" Abstract ({len(parsed.abstract)} chars): {parsed.abstract[:200]}...")
    print(f" Claims found: {len(parsed.claims)}")
    for i, claim in enumerate(parsed.claims[:3], 1):
        print(f"   Claim {i}: {claim[:150]}...")
    print(f" Description ({len(parsed.description)} chars)")

if __name__ == "__main__":
    test_parse_patent()