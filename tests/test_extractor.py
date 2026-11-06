from src.ingestion.epo_client import fetch_patent
from src.ingestion.patent_parser import parse_patent
from src.extraction.extractor import extract_invention

def test_extract_invention():
    """Test invention extraction on a real patent."""
    raw = fetch_patent("EP1000000")
    parsed = parse_patent(raw)

    # Use abstract + first 3 claims as input
    patent_text = f"""
    ABSTRACT:
    {parsed.abstract}

    CLAIMS:
    {chr(10).join(parsed.claims[:3])}
    """

    extraction = extract_invention(patent_text)

    print(f"\n Extraction successful")
    print(f"\n CONCEPT:\n{extraction['concept']}")
    print(f"\n ELEMENTS:")
    for i, el in enumerate(extraction['elements'], 1):
        print(f"  {i}. {el}")
    print(f"\n PROBLEM:\n{extraction['problem']}")

if __name__ == "__main__":
    test_extract_invention()