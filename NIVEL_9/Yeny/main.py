from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any

import chromadb
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer

ROOT_DIR = Path(__file__).resolve().parent
DB_PATH = ROOT_DIR / "chroma_db"
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
COLLECTION_NAME = "manuales"
CHUNK_SIZE = 400
CHUNK_OVERLAP = 80


def clean_text(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    cleaned = clean_text(text)
    if not cleaned:
        return []

    words = cleaned.split()
    if len(words) <= chunk_size:
        return [cleaned]

    chunks: list[str] = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk:
            chunks.append(chunk)
        if i + chunk_size >= len(words):
            break
    return chunks


def extract_pdf_text(pdf_path: Path) -> list[dict[str, Any]]:
    reader = PdfReader(str(pdf_path))
    pages: list[dict[str, Any]] = []

    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        cleaned = clean_text(text)
        if cleaned:
            pages.append({
                "fuente": pdf_path.name,
                "pagina": page_number,
                "texto": cleaned,
            })

    return pages


def build_index(pdf_dir: Path, model: SentenceTransformer, collection_name: str = COLLECTION_NAME) -> tuple[chromadb.Collection, int]:
    client = chromadb.PersistentClient(path=str(DB_PATH))
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )

    ids: list[str] = []
    documents: list[str] = []
    metadatas: list[dict[str, Any]] = []

    for pdf_path in sorted(pdf_dir.glob("*.pdf")):
        pages = extract_pdf_text(pdf_path)
        for page in pages:
            chunks = chunk_text(page["texto"])
            for idx, chunk in enumerate(chunks):
                chunk_id = f"{pdf_path.stem}_{page['pagina']}_{idx}"
                ids.append(chunk_id)
                documents.append(chunk)
                metadatas.append({
                    "fuente": page["fuente"],
                    "pagina": page["pagina"],
                    "chunk_index": idx,
                })

    if not documents:
        return collection, 0

    embeddings = model.encode(documents, normalize_embeddings=True).tolist()
    collection.upsert(
        ids=ids,
        documents=documents,
        metadatas=metadatas,
        embeddings=embeddings,
    )

    return collection, len(documents)


def query_collection(question: str, model: SentenceTransformer, source: str | None = None, top_k: int = 3) -> dict[str, Any]:
    client = chromadb.PersistentClient(path=str(DB_PATH))
    collection = client.get_collection(name=COLLECTION_NAME)

    vector = model.encode([question], normalize_embeddings=True).tolist()
    where = {"fuente": source} if source else None

    result = collection.query(
        query_embeddings=vector,
        n_results=top_k,
        where=where,
    )

    return result


def print_results(result: dict[str, Any]) -> None:
    documents = result.get("documents", [[]])[0]
    distances = result.get("distances", [[]])[0]
    metadatas = result.get("metadatas", [[]])[0]

    if not documents:
        print("No se encontraron resultados relevants.")
        return

    print("\nResultados relevantes:\n")
    for idx, (doc, dist, meta) in enumerate(zip(documents, distances, metadatas), start=1):
        print(f"[{idx}] Distancia: {dist:.4f}")
        print(f"Fuente: {meta.get('fuente')} | Página: {meta.get('pagina')}")
        print(doc)
        print("-" * 80)


def main() -> None:
    parser = argparse.ArgumentParser(description="Motor de búsqueda semántica para manuales PDF.")
    parser.add_argument("--query", type=str, help="Pregunta a buscar sobre los documentos.")
    parser.add_argument("--source", type=str, help="Filtro opcional por nombre de archivo PDF, por ejemplo: manual_ti.pdf")
    parser.add_argument("--top-k", type=int, default=3, help="Número de resultados a devolver.")
    parser.add_argument("--reindex", action="store_true", help="Reindexa todos los PDFs disponibles antes de consultar.")
    args = parser.parse_args()

    model = SentenceTransformer(MODEL_NAME)

    if args.reindex or not DB_PATH.exists():
        collection, count = build_index(ROOT_DIR, model)
        print(f"Se indexaron {count} fragmentos en la colección '{collection.name}'.")

    if args.query:
        result = query_collection(args.query, model, source=args.source, top_k=args.top_k)
        print_results(result)
        return

    print("Sistema listo. Usa --query 'tu pregunta' para consultar los PDFs.")


if __name__ == "__main__":
    main()
