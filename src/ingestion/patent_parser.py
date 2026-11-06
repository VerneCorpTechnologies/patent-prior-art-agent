import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Optional


# EPO XML namespaces
NAMESPACES = {
    "ops": "http://ops.epo.org/3.2/rest-services",
    "epo": "http://www.epo.org/exchange",
    "ex": "http://www.epo.org/fulltext",
}


@dataclass
class ParsedPatent:
    """Structured representation of a parsed patent document."""
    patent_number: str
    abstract: Optional[str]
    claims: list[str]        # Each claim as a separate string
    description: Optional[str]


def parse_abstract(xml_text: str) -> Optional[str]:
    """Extract plain text from EPO abstract XML."""
    try:
        root = ET.fromstring(xml_text)
        texts = root.iter()
        parts = []
        for elem in texts:
            if elem.text and elem.text.strip():
                parts.append(elem.text.strip())
        return " ".join(parts) if parts else None
    except ET.ParseError:
        return None


def parse_claims(xml_text: str) -> list[str]:
    """
    Extract individual claims from EPO claims XML.
    Each claim is returned as a separate string — never split mid-claim.
    This is the key chunking decision: claims are atomic units.
    """
    try:
        root = ET.fromstring(xml_text)
        claims = []

        # EPO XML wraps each claim in a <claim> element
        for claim_elem in root.iter():
            if "claim" in claim_elem.tag.lower() and claim_elem.text:
                text = claim_elem.text.strip()
                if text and len(text) > 20:  # filter empty/noise elements
                    claims.append(text)

        # Fallback: if no claim elements found, extract all text blocks
        if not claims:
            parts = []
            for elem in root.iter():
                if elem.text and elem.text.strip() and len(elem.text.strip()) > 20:
                    parts.append(elem.text.strip())
            claims = parts

        return claims
    except ET.ParseError:
        return []


def parse_description(xml_text: str) -> Optional[str]:
    """Extract plain text from EPO description XML."""
    try:
        root = ET.fromstring(xml_text)
        parts = []
        for elem in root.iter():
            if elem.text and elem.text.strip() and len(elem.text.strip()) > 10:
                parts.append(elem.text.strip())
        return " ".join(parts) if parts else None
    except ET.ParseError:
        return None


def parse_patent(raw_patent: dict) -> ParsedPatent:
    """
    Parse a raw patent dict (from epo_client.fetch_patent) into
    a structured ParsedPatent with clean text sections.
    """
    return ParsedPatent(
        patent_number=raw_patent["patent_number"],
        abstract=parse_abstract(raw_patent["abstract"]),
        claims=parse_claims(raw_patent["claims"]),
        description=parse_description(raw_patent["description"])
    )