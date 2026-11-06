import os
from fastapi import FastAPI, HTTPException, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security.api_key import APIKeyHeader
from mangum import Mangum
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

from src.extraction.extractor import extract_invention
from src.retrieval.retriever import retrieve_prior_art
from src.mapping.mapper import map_claims

app = FastAPI(title="Patent Prior Art Search API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API Key Security ──────────────────────────────────────────
API_KEY = os.getenv("APP_API_KEY")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(key: str = Security(api_key_header)):
    if not API_KEY or key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return key

class ExtractRequest(BaseModel):
    patent_text: str

class RetrieveRequest(BaseModel):
    extraction: dict
    max_results: int = 5

class MapRequest(BaseModel):
    extraction: dict
    prior_art_number: str
    prior_art_chunks: list[dict]

@app.get("/health")
def health():
    """Public endpoint — no API key required."""
    return {"status": "ok"}

@app.post("/extract")
def extract(request: ExtractRequest, key: str = Security(verify_api_key)):
    extraction = extract_invention(request.patent_text)
    return {"extraction": extraction}

@app.post("/retrieve")
def retrieve(request: RetrieveRequest, key: str = Security(verify_api_key)):
    results = retrieve_prior_art(request.extraction, request.max_results)
    return {"results": results}

@app.post("/map")
def map_patent(request: MapRequest, key: str = Security(verify_api_key)):
    mapping = map_claims(
        request.extraction,
        request.prior_art_number,
        request.prior_art_chunks
    )
    return {"mapping": mapping}

# Lambda handler
handler = Mangum(app, lifespan="off", api_gateway_base_path="/prod")