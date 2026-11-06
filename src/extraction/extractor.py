import boto3
import json
import os
from dotenv import load_dotenv

load_dotenv()

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

bedrock = boto3.client("bedrock-runtime", region_name=AWS_REGION)

NOVA_MODEL_ID = "amazon.nova-pro-v1:0"


EXTRACTION_PROMPT = """You are a patent analysis assistant. Your task is to extract the core inventive concept from a patent document in plain, simple English.

Given the following patent text, extract:
1. CONCEPT: The core inventive concept in 2-3 plain English sentences. Avoid legal language entirely.
2. ELEMENTS: The key functional elements of the invention as a numbered list (max 5 elements).
3. PROBLEM: The problem this invention solves in 1 sentence.

Return your response in this exact JSON format:
{{
    "concept": "plain English description of the invention",
    "elements": [
        "element 1",
        "element 2",
        "element 3"
    ],
    "problem": "the problem this invention solves"
}}

Patent text:
{patent_text}

Return only the JSON object, no other text."""


def extract_invention(patent_text: str) -> dict:
    """
    Extract the core inventive concept from patent text using Nova Pro.
    Returns a dict with concept, elements, and problem.
    """
    prompt = EXTRACTION_PROMPT.format(patent_text=patent_text[:3000])

    body = json.dumps({
        "messages": [
            {
                "role": "user",
                "content": [{"text": prompt}]
            }
        ],
        "inferenceConfig": {
            "maxTokens": 1000,
            "temperature": 0.1  # Low temperature for consistent structured output
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

    # Parse the JSON response
    # Strip markdown code blocks if present
    clean = response_text.strip()
    if clean.startswith("```"):
        clean = clean.split("```")[1]
        if clean.startswith("json"):
            clean = clean[4:]
    clean = clean.strip()

    return json.loads(clean)