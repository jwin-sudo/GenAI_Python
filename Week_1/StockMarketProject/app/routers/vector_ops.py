from fastapi import APIRouter, HTTPException, status, Body, Request
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import asyncio
import json

from app.services.vectordb_service import (
    ingest_text_for_year,
    ingest_items_for_year,
    search_year,
)
from app.services.chain_service import get_general_chain

router = APIRouter(prefix="/vectors", tags=["vectors"])

class IngestTextRequest(BaseModel):
    text: str
    id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class IngestItem(BaseModel):
    id: Optional[str] = None
    text: str
    metadata: Optional[Dict[str, Any]] = None

class IngestItemsRequest(BaseModel):
    items: List[IngestItem]

@router.post(
    "/{year}/text",
    status_code=status.HTTP_201_CREATED,
    response_model=Dict[str, str],
)
async def ingest_text(year: int, request: Request):
    """
    Accept raw text for a given year. Supports:
      - text/plain raw body (recommended for large files)
      - application/json with {"text": "..."}
      - fallback: raw decoded body when JSON parsing fails
    """
    try:
        raw_bytes = await request.body()
        raw_str = raw_bytes.decode("utf-8", errors="replace")
        content_type = (request.headers.get("content-type") or "").lower()

        if "application/json" in content_type or raw_str.lstrip().startswith(("{", "[")):
            try:
                payload = json.loads(raw_str)
                text_value = payload.get("text") if isinstance(payload, dict) else raw_str
            except Exception:
                # invalid JSON -> use raw string
                text_value = raw_str
        else:
            # plain text or other -> use raw string
            text_value = raw_str

        if not text_value or not text_value.strip():
            raise HTTPException(status_code=400, detail="No text provided in request body")

        preview = (text_value[:200] + "...") if len(text_value) > 200 else text_value
        print(f"[INGEST DEBUG] year={year} len={len(text_value)} preview={preview!r}")

        loop = asyncio.get_running_loop()
        doc_id = await loop.run_in_executor(None, ingest_text_for_year, year, text_value, None, None)
    except HTTPException:
        raise
    except Exception as e:
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"ingest failed: {e}")

    return {"id": doc_id}

@router.post(
    "/{year}/items",
    status_code=status.HTTP_201_CREATED,
    response_model=Dict[str, List[str]],
)
async def ingest_items(year: int, req: IngestItemsRequest):
    loop = asyncio.get_running_loop()
    items = [item.dict() for item in req.items]
    try:
        ids = await loop.run_in_executor(None, ingest_items_for_year, year, items)
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print("[INGEST ERROR]", tb)
        # include traceback in detail for local debugging (remove in production)
        raise HTTPException(status_code=500, detail=f"batch ingest failed: {e}\n{tb}")
    return {"ids": ids}

general_chain = get_general_chain()

@router.get("/{year}/search", response_model=Dict[str, Any])
async def search_year_endpoint(year: int, q: str, k: int = 3):
    """
    Search the year collection for query `q` (top-k) and use the LLM to produce a concise
    answer/summary based on the retrieved excerpts. Returns both the raw search hits and
    the LLM's answer.
    """
    loop = asyncio.get_running_loop()
    try:
        results = await loop.run_in_executor(None, search_year, year, q, k)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"search failed: {e}")

    # Build a short context from the top results to feed the LLM
    def build_excerpts(docs: List[Dict[str, Any]]) -> str:
        parts: List[str] = []
        for i, d in enumerate(docs[:k], start=1):
            text = d.get("text") or d.get("page_content") or ""
            meta = d.get("metadata") or {}
            parts.append(f"Excerpt {i} (source={meta.get('source') or meta.get('source_name') or 'unknown'}):\n{text.strip()[:800]}")
        return "\n\n".join(parts) if parts else "No excerpts available."

    excerpts = build_excerpts(results)

    prompt = (
        f"You are an expert on macro reports. A user asked: {q}\n\n"
        f"Use the following excerpts from the {year} macro report collection to answer concisely:\n\n"
        f"{excerpts}\n\n"
        "Provide a short, actionable answer (2-4 sentences). If the excerpts do not contain enough information, say so."
    )

    try:
        llm_result = await general_chain.ainvoke({"input": prompt})
    except Exception as e:
        # still return search results if LLM fails
        return {"search_results": results, "llm_answer": None, "llm_error": str(e)}

    # normalize LLM result
    if isinstance(llm_result, dict):
        llm_answer = llm_result.get("answer") or llm_result.get("text") or str(llm_result)
    else:
        llm_answer = getattr(llm_result, "content", None) or getattr(llm_result, "text", None) or str(llm_result)

    return {"search_results": results, "llm_answer": llm_answer}


@router.get("/{year_a}/compare/{year_b}", response_model=Dict[str, Any])
async def compare_years(
    year_a: int,
    year_b: int,
    q: Optional[str] = "macro report",
    k: int = 3,
):
    """
    Compare two years' macro reports.
    - q: optional focus/query string used to retrieve the most relevant excerpts for each year.
    - k: number of top documents to retrieve per year.
    Returns a short comparison produced by the LLM plus the source excerpts.
    """
    loop = asyncio.get_running_loop()

    try:
        docs_a = await loop.run_in_executor(None, search_year, year_a, q, k)
        docs_b = await loop.run_in_executor(None, search_year, year_b, q, k)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"vector search failed: {e}")

    # prepare excerpts (keep them short to avoid context overflow)
    def excerpt_text(docs: List[Dict[str, Any]]) -> str:
        snippets = []
        for idx, d in enumerate(docs[:k], start=1):
            text = d.get("text") or d.get("page_content") or ""
            meta = d.get("metadata") or {}
            snippets.append(f"Excerpt {idx}: {text[:800]}")  # truncate to 800 chars each
        return "\n\n".join(snippets) if snippets else "No excerpts available."

    a_text = excerpt_text(docs_a)
    b_text = excerpt_text(docs_b)

    prompt = (
        f"Compare the macroeconomic reports for {year_a} and {year_b}.\n\n"
        f"=== {year_a} Excerpts ===\n{a_text}\n\n"
        f"=== {year_b} Excerpts ===\n{b_text}\n\n"
        "Task:\n"
        "- Identify the top 3 differences in macro themes between the two years.\n"
        "- Provide investor implications (2-3 short bullets).\n"
        "- Give a concise recommendation (Buy/Hold/Avoid) and brief rationale.\n"
        "Keep the response short and actionable."
    )

    try:
        llm_result = await general_chain.ainvoke({"input": prompt})
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"LLM invocation failed: {e}")

    # normalize LLM result
    if isinstance(llm_result, dict):
        comparison = llm_result.get("answer") or llm_result.get("text") or str(llm_result)
    else:
        comparison = getattr(llm_result, "content", None) or getattr(llm_result, "text", None) or str(llm_result)

    return {
        "year_a": year_a,
        "year_b": year_b,
        "query": q,
        "comparison": comparison,
        "year_a_sources": docs_a,
        "year_b_sources": docs_b,
    }