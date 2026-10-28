from __future__ import annotations

import os
import re
from typing import Any, Dict, List

from dotenv import load_dotenv
from google import genai

from pdf_search_app import generate_answer_from_context

load_dotenv()


def get_gemini_client():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return None

    try:
        return genai.Client(api_key=api_key)
    except Exception:
        return None


def normalize_tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-zA-ZáéíóúüñÁÉÍÓÚÜÑ]+", text.lower()))


def extract_source_quote(query: str, document: str) -> str:
    if not document:
        return ""

    sentences = re.split(r"(?<=[.!?])\s+", document)
    query_tokens = normalize_tokens(query)
    scored: list[tuple[int, str]] = []

    for sentence in sentences:
        cleaned = sentence.strip()
        if len(cleaned) < 30:
            continue
        sentence_tokens = normalize_tokens(cleaned)
        score = len(sentence_tokens & query_tokens)
        if score > 0:
            scored.append((score, cleaned))

    if scored:
        return max(scored, key=lambda item: item[0])[1]

    snippet = document.strip()
    return snippet[:250] if len(snippet) > 250 else snippet


def build_context_for_rag(documents: List[str]) -> str:
    cleaned = [doc.strip() for doc in documents if doc and doc.strip()]
    if not cleaned:
        return ""
    return "\n\n---\n\n".join(cleaned[:5])


def build_citations(query: str, retrieved_documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    citations: List[Dict[str, Any]] = []
    for item in retrieved_documents:
        source = item.get("source") or item.get("fuente") or "documento"
        content = item.get("content") or item.get("document") or ""
        quote = extract_source_quote(query, content)
        citations.append({
            "source": source,
            "quote": quote,
        })
    return citations[:5]


def generate_answer_with_gemini(query: str, documents: List[str], model_name: str = "gemini-3.5-flash-lite") -> str:
    fallback_answer = generate_answer_from_context(query, documents)
    client = get_gemini_client()

    if client is None:
        return fallback_answer

    context = build_context_for_rag(documents)
    if not context:
        return fallback_answer

    prompt = (
        "Eres un asistente documental. Responde usando exclusivamente la evidencia del contexto. "
        "Si la información no aparece en el contexto, responde que no hay evidencia suficiente. "
        "No inventes ni generalices. Responde con una respuesta clara, directa y basada en citas del contexto.\n\n"
        f"Contexto:\n{context}\n\n"
        f"Pregunta del usuario:\n{query}\n\n"
        "Respuesta:"
    )

    try:
        response = client.models.generate_content(model=model_name, contents=prompt)
        answer = getattr(response, "text", None) or ""
        if answer.strip():
            return answer.strip()
    except Exception:
        pass

    return fallback_answer


def build_grounded_response(query: str, retrieved_documents: List[Dict[str, Any]], model_name: str = "gemini-3.5-flash-lite") -> Dict[str, Any]:
    citations = build_citations(query, retrieved_documents)
    documents = [item.get("content") or item.get("document") or "" for item in retrieved_documents]
    answer = generate_answer_with_gemini(query, documents, model_name=model_name)
    return {
        "answer": answer,
        "citations": citations,
    }
