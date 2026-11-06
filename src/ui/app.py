import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import requests
from dotenv import load_dotenv
from ingestion.pdf_parser import extract_text_from_pdf


load_dotenv()

# ── API Configuration ─────────────────────────────────────────
API_BASE_URL = st.secrets.get("API_BASE_URL") or os.getenv("API_BASE_URL")
APP_API_KEY = st.secrets.get("APP_API_KEY") or os.getenv("APP_API_KEY")

if not API_BASE_URL:
    st.error("API_BASE_URL not configured.")
    st.stop()

# ── API Calls ─────────────────────────────────────────────────
def api_extract(patent_text: str) -> dict:
    response = requests.post(
        f"{API_BASE_URL}/extract",
        json={"patent_text": patent_text},
        headers={"X-API-Key": APP_API_KEY},
        timeout=120
    )
    response.raise_for_status()
    return response.json()["extraction"]


def api_retrieve(extraction: dict, max_results: int) -> list:
    response = requests.post(
        f"{API_BASE_URL}/retrieve",
        json={"extraction": extraction, "max_results": max_results},
        headers={"X-API-Key": APP_API_KEY},
        timeout=120
    )
    response.raise_for_status()
    return response.json()["results"]


def api_map(extraction: dict, prior_art_number: str, chunks: list) -> dict:
    response = requests.post(
        f"{API_BASE_URL}/map",
        json={
            "extraction": extraction,
            "prior_art_number": prior_art_number,
            "prior_art_chunks": chunks
        },
        headers={"X-API-Key": APP_API_KEY},
        timeout=120
    )
    response.raise_for_status()
    return response.json()["mapping"]

# ── Page config ───────────────────────────────────────────────
st.set_page_config(
    page_title="Patent Prior Art Search",
    page_icon="⚖️",
    layout="wide"
)

# ── Styles ────────────────────────────────────────────────────
st.markdown("""
<style>
    .risk-high    { color: #ff4444; font-weight: bold; font-size: 1.2em; }
    .risk-medium  { color: #ffaa00; font-weight: bold; font-size: 1.2em; }
    .risk-low     { color: #00cc44; font-weight: bold; font-size: 1.2em; }
    .status-prior_art  { background: #ff444433; padding: 2px 8px; border-radius: 4px; }
    .status-ambiguous  { background: #ffaa0033; padding: 2px 8px; border-radius: 4px; }
    .status-novel      { background: #00cc4433; padding: 2px 8px; border-radius: 4px; }
    .section-header { font-size: 1.1em; font-weight: bold; margin-top: 1em; }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────
st.title("⚖️ Patent Prior Art Search")
st.caption("Invention Extraction · Prior Art Retrieval · Claim Mapping")
st.divider()

# ── Session state ─────────────────────────────────────────────
if "extraction" not in st.session_state:
    st.session_state.extraction = None
if "retrieval_results" not in st.session_state:
    st.session_state.retrieval_results = None
if "mappings" not in st.session_state:
    st.session_state.mappings = {}

# ══════════════════════════════════════════════════════════════
# PANEL 1 — INPUT & EXTRACTION
# ══════════════════════════════════════════════════════════════
st.subheader("📄 Patent Specification")

input_method = st.radio(
    "Select an input method",
    "Upload your patent specification",
    horizontal=True,
    label_visibility="collapsed"
)

patent_text_input = ""

if input_method == "Enter patent number":
    patent_number = st.text_input(
        "Patent number",
        placeholder="e.g. EP1000000 or GB2296214",
        help="Enter an EP or GB patent number"
    )
    if patent_number:
        if st.button("Fetch patent", type="secondary"):
            with st.spinner(f"Fetching {patent_number} from EPO..."):
                try:
                    raw = fetch_patent(patent_number.strip())
                    parsed = parse_patent(raw)
                    patent_text_input = f"""ABSTRACT:
{parsed.abstract}

CLAIMS:
{chr(10).join(parsed.claims)}"""
                    st.session_state.fetched_text = patent_text_input
                    st.success(f"✅ Fetched {patent_number} — {len(parsed.claims)} claims found")
                except Exception as e:
                    st.error(f"Could not fetch patent: {e}")

    if "fetched_text" in st.session_state and input_method == "Enter patent number":
        with st.expander("Preview fetched patent text"):
            st.text(st.session_state.fetched_text[:2000])
        patent_text_input = st.session_state.fetched_text

elif input_method == "Upload your patent specification":
    uploaded_file = st.file_uploader(
        "Allowed formats: PDF",
        type=["pdf"],
        help="Upload a PDF of the patent application or invention disclosure"
    )
    if uploaded_file:
        with st.spinner("Extracting text from PDF..."):
            try:
                pdf_text = extract_text_from_pdf(uploaded_file.read())
                st.session_state.fetched_text = pdf_text
                st.success(f"✅ PDF extracted — {len(pdf_text)} characters")
                with st.expander("Preview extracted text"):
                    st.text(pdf_text[:2000])
            except ValueError as e:
                st.error(str(e))

    if "fetched_text" in st.session_state and input_method == "Upload your patent specification":
        patent_text_input = st.session_state.fetched_text

else:
    patent_text_input = st.text_area(
        "Paste your patent application or invention disclosure",
        height=200,
        placeholder="Paste abstract and claims here..."
    )

# Extract button
if patent_text_input and st.button("🔬 Extract Inventive Concept", type="primary"):
    with st.spinner("Extracting inventive concept with Nova Pro..."):
        try:
            st.session_state.extraction = api_extract(patent_text_input)
            st.session_state.retrieval_results = None
            st.session_state.mappings = {}
        except Exception as e:
            st.error(f"Extraction failed: {e}")

# Show extraction results
if st.session_state.extraction:
    ext = st.session_state.extraction
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**💡 Inventive Concept**")
        st.info(ext.get("concept", ""))

        st.markdown("**🔧 Key Elements**")
        for i, el in enumerate(ext.get("elements", []), 1):
            st.markdown(f"{i}. {el}")

    with col2:
        st.markdown("**🎯 Problem Solved**")
        st.info(ext.get("problem", ""))

    st.divider()

    # ══════════════════════════════════════════════════════════
    # PANEL 2 — RETRIEVAL
    # ══════════════════════════════════════════════════════════
    st.subheader("🔍 Prior Art Results")

    num_results = st.slider("Number of prior art patents to retrieve", 1, 5, 3)

    if st.button("🔍 Search Prior Art", type="primary"):
        with st.spinner("Searching EPO database and ingesting candidates..."):
            try:
                st.session_state.retrieval_results = api_retrieve(
                    st.session_state.extraction,
                    max_results=num_results
                )
                st.session_state.mappings = {}
            except Exception as e:
                st.error(f"Retrieval failed: {e}")

    if st.session_state.retrieval_results:
        results = st.session_state.retrieval_results

        # Group by patent number
        patents_found = list(dict.fromkeys([r["patent_number"] for r in results]))
        st.success(f"Found {len(patents_found)} relevant prior art patents")

        for patent_num in patents_found:
            patent_chunks = [r for r in results if r["patent_number"] == patent_num]
            top_score = max(r["score"] for r in patent_chunks)

            with st.expander(f"📋 {patent_num}  —  Similarity: {top_score:.1%}"):
                st.markdown(f"**Chunks retrieved:** {len(patent_chunks)}")
                for chunk in patent_chunks:
                    section = chunk.get("section", "")
                    claim_num = chunk.get("claim_number", "")
                    label = f"Claim {int(claim_num)}" if section == "claim" and claim_num else section.capitalize()
                    st.markdown(f"- {label} (score: {chunk['score']})")

        st.divider()

        # ══════════════════════════════════════════════════════
        # PANEL 3 — CLAIM MAPPING
        # ══════════════════════════════════════════════════════
        st.subheader("🗺️ Claim Mapping")

        if st.button("🗺️ Run Claim Mapping", type="primary"):
            results_by_patent = {}
            for r in st.session_state.retrieval_results:
                pn = r["patent_number"]
                if pn not in results_by_patent:
                    results_by_patent[pn] = []
                results_by_patent[pn].append(r)

            for patent_num, chunks in results_by_patent.items():
                with st.spinner(f"Mapping claims against {patent_num}..."):
                    try:
                        mapping = api_map(
                            st.session_state.extraction,
                            patent_num,
                            chunks
                        )
                        st.session_state.mappings[patent_num] = mapping
                    except Exception as e:
                        st.error(f"Mapping failed for {patent_num}: {e}")

        # Display mappings
        if st.session_state.mappings:
            for patent_num, mapping in st.session_state.mappings.items():
                risk = mapping.get("risk_level", "unknown")
                risk_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(risk, "⚪")
                risk_class = f"risk-{risk}"

                st.markdown(f"### {risk_emoji} {patent_num}")
                st.markdown(
                    f'<p class="{risk_class}">Risk Level: {risk.upper()}</p>',
                    unsafe_allow_html=True
                )
                st.markdown(f"**Overall Assessment:**")
                st.warning(mapping.get("overall_assessment", ""))

                st.markdown("**Element by Element Mapping:**")
                for em in mapping.get("element_mapping", []):
                    status = em.get("status", "unknown")
                    status_emoji = {
                        "prior_art": "🔴",
                        "ambiguous": "🟡",
                        "novel": "🟢"
                    }.get(status, "⚪")

                    with st.expander(
                        f"{status_emoji} {em.get('element', '')} — {status.replace('_', ' ').title()}"
                    ):
                        st.markdown(f"**Status:** {status.replace('_', ' ').title()}")
                        st.markdown(f"**Evidence:** _{em.get('evidence', 'None')}_")
                        st.markdown(f"**Explanation:** {em.get('explanation', '')}")

                st.divider()