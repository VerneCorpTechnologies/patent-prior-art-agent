import boto3
import json
import os
from dotenv import load_dotenv

load_dotenv()

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
bedrock = boto3.client("bedrock-runtime", region_name=AWS_REGION)
NOVA_MODEL_ID = "amazon.nova-pro-v1:0"


MAPPING_PROMPT = """You are a patent attorney assistant specialising in prior art analysis.

You are given:
1. A CLIENT PATENT with its extracted inventive concept and key elements
2. A PRIOR ART PATENT with its claim text

Your task is to compare them element by element and assess novelty.

For each element of the client patent, determine:
- MATCH: Does the prior art disclose this element?
- STATUS: "prior_art" / "ambiguous" / "novel"
- EVIDENCE: Quote the specific part of the prior art that matches (or state "No matching text found")

Then provide an OVERALL ASSESSMENT of whether this prior art patent poses a novelty risk.

Return your response in this exact JSON format:
{{
    "prior_art_patent": "{prior_art_number}",
    "element_mapping": [
        {{
            "element": "element description from client patent",
            "status": "prior_art|ambiguous|novel",
            "evidence": "relevant quote from prior art or No matching text found",
            "explanation": "one sentence explanation"
        }}
    ],
    "overall_assessment": "A 2-3 sentence summary of whether this prior art poses a novelty risk and why",
    "risk_level": "high|medium|low"
}}

CLIENT PATENT CONCEPT:
{concept}

CLIENT PATENT ELEMENTS:
{elements}

PRIOR ART PATENT ({prior_art_number}) CLAIMS:
{prior_art_claims}

Return only the JSON object, no other text."""


def map_claims(
    extraction: dict,
    prior_art_number: str,
    prior_art_chunks: list[dict]
) -> dict:
    """
    Compare client patent elements against a prior art patent.
    Returns structured element-by-element mapping with novelty assessment.

    Args:
        extraction: Output from extractor.extract_invention()
        prior_art_number: Patent number of the prior art
        prior_art_chunks: Relevant chunks from Pinecone for this patent
    """
    # Build prior art claims text from retrieved chunks
    prior_art_text = "\n\n".join([
        f"[{c['section'].upper()} {c.get('claim_number', '')}]: "
        f"{c.get('text', c.get('chunk_id', ''))}"
        for c in prior_art_chunks
        if c.get("text")
    ])

    if not prior_art_text:
        return {
            "prior_art_patent": prior_art_number,
            "element_mapping": [],
            "overall_assessment": "Could not retrieve prior art text for comparison.",
            "risk_level": "unknown"
        }

    elements_text = "\n".join([
        f"{i+1}. {el}"
        for i, el in enumerate(extraction.get("elements", []))
    ])

    prompt = MAPPING_PROMPT.format(
        prior_art_number=prior_art_number,
        concept=extraction.get("concept", ""),
        elements=elements_text,
        prior_art_claims=prior_art_text[:3000]
    )

    body = json.dumps({
        "messages": [
            {
                "role": "user",
                "content": [{"text": prompt}]
            }
        ],
        "inferenceConfig": {
            "maxTokens": 2000,
            "temperature": 0.1
        }
    })

    response = bedrock.invoke_model(
        modelId=NOVA_MODEL_ID,
        contentType="application/json",
        accept="application/json",
        body=body
    )

    result = json.loads(response["body"].read())
    response_text = result["output"]["message"]["content"][0]["text"]

    # Clean and parse JSON response
    clean = response_text.strip()
    if clean.startswith("```"):
        clean = clean.split("```")[1]
        if clean.startswith("json"):
            clean = clean[4:]
    clean = clean.strip()

    return json.loads(clean)