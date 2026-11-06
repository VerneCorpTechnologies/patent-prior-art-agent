from dataclasses import dataclass
from src.ingestion.patent_parser import ParsedPatent


@dataclass
class PatentChunk:
    """A single chunk of patent text ready for embedding and storage in Pinecone."""
    chunk_id: str           # Unique ID for this chunk
    patent_number: str      # e.g. "EP1000000"
    section: str            # "abstract", "claim", or "description"
    claim_number: int | None  # Only set for claim chunks
    text: str               # The actual text to embed
    metadata: dict          # Full metadata dict for Pinecone


def chunk_patent(parsed_patent: ParsedPatent) -> list[PatentChunk]:
    """
    Convert a ParsedPatent into a list of PatentChunks ready for Pinecone.

    Chunking strategy:
    - Abstract: single chunk
    - Claims: one chunk per claim
    - Description: single chunk (can be extended to paragraph chunks later)
    """
    chunks = []
    pn = parsed_patent.patent_number

    # ── Abstract ──────────────────────────────────────────────
    if parsed_patent.abstract:
        chunk_id = f"{pn}_abstract"
        chunks.append(PatentChunk(
            chunk_id=chunk_id,
            patent_number=pn,
            section="abstract",
            claim_number=None,
            text=parsed_patent.abstract,
            metadata={
                "chunk_id": chunk_id,
                "patent_number": pn,
                "section": "abstract",
                "claim_number": -1,  # Pinecone requires numeric values
            }
        ))

    # ── Claims (one chunk per claim) ──────────────────────────
    for i, claim_text in enumerate(parsed_patent.claims, start=1):
        chunk_id = f"{pn}_claim_{i}"
        chunks.append(PatentChunk(
            chunk_id=chunk_id,
            patent_number=pn,
            section="claim",
            claim_number=i,
            text=claim_text,
            metadata={
                "chunk_id": chunk_id,
                "patent_number": pn,
                "section": "claim",
                "claim_number": i,
            }
        ))

    # ── Description ───────────────────────────────────────────
    if parsed_patent.description:
        # Truncate to 2000 chars to stay within embedding token limits
        description_text = parsed_patent.description[:2000]
        chunk_id = f"{pn}_description"
        chunks.append(PatentChunk(
            chunk_id=chunk_id,
            patent_number=pn,
            section="description",
            claim_number=None,
            text=description_text,
            metadata={
                "chunk_id": chunk_id,
                "patent_number": pn,
                "section": "description",
                "claim_number": -1,
            }
        ))

    return chunks