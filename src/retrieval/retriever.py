from src.ingestion.ingest import ingest_patent
from src.ingestion.pinecone_store import get_index
from src.ingestion.embedder import embed_text
from src.retrieval.epo_search import search_patents


def retrieve_prior_art(extracted_concept: dict, max_results: int = 5) -> list[dict]:
    """
    Full retrieval pipeline:
    1. Search EPO for candidate patents using extracted concept
    2. Ingest candidates into Pinecone
    3. Semantic search against ingested patents
    Returns the most relevant chunks with metadata.

    Args:
        extracted_concept: Output from extractor.extract_invention()
        max_results: Number of results to return
    """

    # Step 1 — Build search query from extracted concept
    concept_text = extracted_concept["concept"]
    print(f"\n🔍 Searching EPO for: {concept_text[:100]}...")

    # Step 2 — Search EPO for candidate patents
    candidate_patents = search_patents(
        concept_text,
        elements=extracted_concept.get("elements", []),
        max_results=10
    )
    print(f"  Found {len(candidate_patents)} candidate patents: {candidate_patents}")

    if not candidate_patents:
        print("  No candidates found — try a broader query")
        return []

    # Step 3 — Ingest candidates into Pinecone
    print(f"\n📥 Ingesting candidates into Pinecone...")
    for patent_number in candidate_patents:
        try:
            ingest_patent(patent_number)
        except Exception as e:
            print(f"  ⚠️  Could not ingest {patent_number}: {e}")

    # Step 4 — Semantic search in Pinecone
    print(f"\n🧠 Running semantic search in Pinecone...")
    query_embedding = embed_text(concept_text)
    index = get_index()

    results = index.query(
        vector=query_embedding,
        top_k=max_results,
        include_metadata=True
    )

    # Format results
    matches = []
    for match in results.matches:
        matches.append({
            "patent_number": match.metadata.get("patent_number"),
            "section": match.metadata.get("section"),
            "claim_number": match.metadata.get("claim_number"),
            "score": round(match.score, 3),
            "chunk_id": match.metadata.get("chunk_id"),
            "text": match.metadata.get("text", "")
        })

    return matches