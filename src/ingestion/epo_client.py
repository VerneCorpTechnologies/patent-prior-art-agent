import os
import requests
from dotenv import load_dotenv

load_dotenv()

EPO_CONSUMER_KEY = os.getenv("EPO_CONSUMER_KEY")
EPO_CONSUMER_SECRET = os.getenv("EPO_CONSUMER_SECRET")

EPO_AUTH_URL = "https://ops.epo.org/3.2/auth/accesstoken"
EPO_BASE_URL = "https://ops.epo.org/3.2/rest-services"


def get_access_token() -> str:
    """Authenticate with EPO OPS API and return an access token."""
    response = requests.post(
        EPO_AUTH_URL,
        data={"grant_type": "client_credentials"},
        auth=(EPO_CONSUMER_KEY, EPO_CONSUMER_SECRET)
    )
    response.raise_for_status()
    return response.json()["access_token"]


def fetch_patent(patent_number: str) -> dict:
    """
    Fetch a patent by publication number from the EPO OPS API.
    Returns a dict containing the abstract, claims, and description.

    Args:
        patent_number: e.g. "EP1000000" or "GB2500000"
    """
    token = get_access_token()
    headers = {"Authorization": f"Bearer {token}"}

    # Fetch abstract
    abstract = _fetch_section(patent_number, "abstract", headers)

    # Fetch claims
    claims = _fetch_section(patent_number, "claims", headers)

    # Fetch description
    description = _fetch_section(patent_number, "description", headers)

    return {
        "patent_number": patent_number,
        "abstract": abstract,
        "claims": claims,
        "description": description
    }


def _fetch_section(patent_number: str, section: str, headers: dict) -> str:
    """Fetch a specific section of a patent document."""
    url = f"{EPO_BASE_URL}/published-data/publication/epodoc/{patent_number}/{section}"
    response = requests.get(url, headers=headers)

    if response.status_code == 404:
        return f"[{section} not available]"

    response.raise_for_status()
    return response.text