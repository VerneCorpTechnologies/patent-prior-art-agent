from src.ingestion.epo_client import get_access_token, fetch_patent

def test_authentication():
    """Test that we can authenticate with the EPO OPS API."""
    token = get_access_token()
    assert token is not None
    assert len(token) > 0
    print(f"\n Authentication successful. Token: {token[:20]}...")

def test_fetch_patent():
    """Test fetching a real patent."""
    # EP1000000 is a real granted European patent - safe to use for testing
    patent = fetch_patent("EP1000000")
    assert patent["patent_number"] == "EP1000000"
    assert patent["abstract"] is not None
    print(f"\n Patent fetched successfully")
    print(f"Abstract preview: {patent['abstract'][:200]}...")

if __name__ == "__main__":
    test_authentication()
    test_fetch_patent()