from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException

from gemini_rag import build_grounded_response
from pdf_search_app import MODEL_NAME, build_index, get_pdf_files, search_documents
from sentence_transformers import SentenceTransformer

app = FastAPI(title="Buscador semántico de PDFs", version="1.0.0")


@app.on_event("startup")
def startup_event() -> None:
    app.state.model = SentenceTransformer(MODEL_NAME)
    try:
        app.state.collection = build_index(Path("."), reindex=False)
        app.state.index_error = None
    except Exception as exc:  # pragma: no cover - runtime dependency issue
        app.state.collection = None
        app.state.index_error = str(exc)


@app.get("/health")
def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "pdf_count": len(get_pdf_files(Path("."))),
        "index_ready": app.state.collection is not None,
        "error": app.state.index_error,
    }


@app.post("/reindex")
def reindex() -> Dict[str, Any]:
    try:
        app.state.collection = build_index(Path("."), reindex=True)
        app.state.index_error = None
        return {"status": "ok", "message": "Índice reconstruido correctamente."}
    except Exception as exc:  # pragma: no cover - runtime dependency issue
        app.state.index_error = str(exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/search")
def search(query: str, top_k: int = 5, source: Optional[str] = None) -> Dict[str, Any]:
    if not query or not query.strip():
        raise HTTPException(status_code=400, detail="Debe indicar una consulta válida.")

    if app.state.collection is None:
        raise HTTPException(status_code=500, detail=f"Índice no disponible: {app.state.index_error}")

    results = search_documents(
        query=query,
        collection=app.state.collection,
        model=app.state.model,
        top_k=top_k,
        source_filter=source,
    )

    documents = results.get("documents", [[]])[0]
    distances = results.get("distances", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    formatted: List[Dict[str, Any]] = []
    for doc, distance, metadata in zip(documents, distances, metadatas):
        formatted.append({
            "source": metadata.get("fuente", "desconocida"),
            "distance": float(distance),
            "content": doc,
        })

    grounded = build_grounded_response(
        query=query,
        retrieved_documents=[
            {"source": metadata.get("fuente", "desconocida"), "content": document}
            for document, metadata in zip(documents, metadatas)
        ],
    )

    return {
        "query": query,
        "results": formatted,
        "answer": grounded["answer"],
        "citations": grounded["citations"],
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api_app:app", host="127.0.0.1", port=8000, reload=False)
