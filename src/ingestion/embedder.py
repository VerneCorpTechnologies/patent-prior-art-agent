import boto3
import json
import os
from dotenv import load_dotenv

load_dotenv()

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

# Bedrock client
bedrock = boto3.client("bedrock-runtime", region_name=AWS_REGION)

TITAN_MODEL_ID = "amazon.titan-embed-text-v2:0"


def embed_text(text: str) -> list[float]:
    """
    Generate a vector embedding for a piece of text using
    Amazon Titan Text Embeddings V2 via Bedrock.
    Returns a list of 1024 floats.
    """
    body = json.dumps({
        "inputText": text,
        "dimensions": 1024,
        "normalize": True
    })

    response = bedrock.invoke_model(
        modelId=TITAN_MODEL_ID,
        contentType="application/json",
        accept="application/json",
        body=body
    )

    result = json.loads(response["body"].read())
    return result["embedding"]