import os
import requests
from dotenv import load_dotenv
from src.ingestion.epo_client import get_access_token

load_dotenv()

EPO_BASE_URL = "https://ops.epo.org/3.2/rest-services"


def build_cql_query(concept: str, elements: list[str]) -> str:
    """
    Build a CQL query targeting EP and GB patents with technical keywords.
    """
    stop_words = {
        "a", "an", "the", "and", "or", "for", "of", "in", "on",
        "to", "with", "that", "this", "is", "are", "it", "its",
        "by", "as", "at", "be", "has", "have", "from", "into",
        "also", "which", "when", "where", "not", "above", "below",
        "means", "includes", "including", "comprising", "apparatus",
        "making", "using", "used", "made", "feature", "features",
        "system", "method", "device", "process", "provides"
    }

    # Extract technical words from elements (more specific than concept)
    words = []
    for element in elements[:3]:
        for w in element.split():
            clean = w.strip(".,()").lower()
            if len(clean) >= 5 and clean not in stop_words:
                words.append(clean)

    # Deduplicate and take top 3
    keywords = list(dict.fromkeys(words))[:3]

    if not keywords:
        # Fallback to concept words
        keywords = [
            w.strip(".,()").lower()
            for w in concept.split()
            if len(w.strip(".,()")) >= 5
            and w.strip(".,()").lower() not in stop_words
        ][:3]

    keyword_str = " AND ".join(keywords)

    # Restrict to EP and GB patents only
    return f"txt=({keyword_str}) AND (pn=EP OR pn=GB)"


def search_patents(query: str, elements: list[str] = None, max_results: int = 10) -> list[str]:
    """
    Search the EPO database for patents similar to the query.
    Returns a list of patent numbers.

    Args:
        query: Plain English description of the invention concept
        elements: Key functional elements from extraction
        max_results: Maximum number of patents to return
    """
    token = get_access_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }

    # Build a concise CQL query from key terms
    if elements:
        cql_query = build_cql_query(query, elements)
    else:
        # Fallback: use first 5 words of concept only
        short_query = " ".join(query.split()[:5])
        cql_query = f'txt="{short_query}"'

    print(f"  CQL query: {cql_query}")

    params = {
        "q": cql_query,
        "Range": f"1-{max_results}"
    }

    url = f"{EPO_BASE_URL}/published-data/search"
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()

    return _parse_search_results(response.json())


def _parse_search_results(response_data: dict) -> list[str]:
    """Extract patent numbers from EPO search response."""
    patent_numbers = []

    try:
        results = (
            response_data
            .get("ops:world-patent-data", {})
            .get("ops:biblio-search", {})
            .get("ops:search-result", {})
            .get("ops:publication-reference", [])
        )

        # Handle single result (dict) vs multiple results (list)
        if isinstance(results, dict):
            results = [results]

        for ref in results:
            doc_id = ref.get("document-id", {})
            if isinstance(doc_id, list):
                doc_id = doc_id[0]

            country = doc_id.get("country", {}).get("$", "")
            number = doc_id.get("doc-number", {}).get("$", "")

            # Deliberately omit kind code — EPO API works better without it
            if country and number:
                patent_numbers.append(f"{country}{number}")

    except (KeyError, AttributeError) as e:
        print(f"  Warning: Could not parse search results: {e}")

    return patent_numbers