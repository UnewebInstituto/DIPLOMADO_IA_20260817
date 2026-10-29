from __future__ import annotations

import argparse
from pathlib import Path

from sentence_transformers import SentenceTransformer

from gemini_rag import build_grounded_response
from pdf_search_app import MODEL_NAME, build_index, get_pdf_files, search_documents


def run_rag(query: str, directory: str = ".", top_k: int = 5, source: str | None = None, reindex: bool = False) -> dict:
    directory_path = Path(directory).resolve()
    pdf_files = get_pdf_files(directory_path)
    if not pdf_files:
        raise FileNotFoundError(f"No se encontraron PDFs en: {directory_path}")

    collection = build_index(directory_path, reindex=reindex)
    model = SentenceTransformer(MODEL_NAME)
    results = search_documents(
        query=query,
        collection=collection,
        model=model,
        top_k=top_k,
        source_filter=source,
    )

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    if not documents:
        return {
            "query": query,
            "answer": "No encontré evidencia suficiente en los documentos indexados para responder con seguridad.",
            "citations": [],
            "results": [],
        }

    retrieved = [
        {"source": metadata.get("fuente", "desconocida"), "content": document}
        for document, metadata in zip(documents, metadatas)
    ]
    grounded = build_grounded_response(query, retrieved)

    return {
        "query": query,
        "answer": grounded["answer"],
        "citations": grounded["citations"],
        "results": [
            {"source": item.get("source", "desconocida"), "content": item.get("content", "")}
            for item in retrieved
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Lanzador RAG con PDFs locales.")
    parser.add_argument("--query", required=True, help="Pregunta a responder usando los PDFs.")
    parser.add_argument("--directory", default=".", help="Directorio que contiene los PDFs.")
    parser.add_argument("--top-k", type=int, default=5, help="Número de documentos relevantes a recuperar.")
    parser.add_argument("--source", help="Filtrar por nombre del PDF.")
    parser.add_argument("--reindex", action="store_true", help="Recrea el índice vectorial completo.")
    args = parser.parse_args()

    print(f"\nConsulta: {args.query}\n")
    result = run_rag(
        query=args.query,
        directory=args.directory,
        top_k=args.top_k,
        source=args.source,
        reindex=args.reindex,
    )

    print("RESPUESTA:")
    print(result["answer"])

    if result["citations"]:
        print("\nCitas:")
        for i, citation in enumerate(result["citations"], start=1):
            source = citation.get("source", "documento")
            quote = citation.get("quote", "")
            print(f"{i}. {source}: {quote[:220]}{'...' if len(quote) > 220 else ''}")


if __name__ == "__main__":
    main()
