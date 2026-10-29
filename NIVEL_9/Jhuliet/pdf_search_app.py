from __future__ import annotations

import argparse
import os
import re
from pathlib import Path
from typing import Any, Dict, List

from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
import chromadb

MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
COLLECTION_NAME = "manuales"
DB_PATH = Path("./.chroma_db")


def clean_text(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_text_from_pdf(pdf_path: Path) -> str:
    reader = PdfReader(str(pdf_path))
    pages: List[str] = []

    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        cleaned = clean_text(text)
        if cleaned:
            pages.append(f"[Página {page_number}] {cleaned}")

    return "\n".join(pages)


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 80) -> List[str]:
    if not text:
        return []

    words = text.split()
    if len(words) <= chunk_size:
        return [" ".join(words)]

    chunks: List[str] = []
    start = 0

    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end])
        chunks.append(chunk.strip())
        start += max(1, chunk_size - overlap)

    return chunks


def get_pdf_files(directory: Path) -> List[Path]:
    return sorted(directory.glob("*.pdf"))


def _should_rebuild_index(collection: chromadb.Collection, pdf_files: List[Path]) -> bool:
    if not pdf_files:
        return False

    source_mtimes: Dict[str, int] = {}
    stored = collection.get(include=["metadatas"]).get("metadatas", [])
    for metadata in stored:
        if not isinstance(metadata, dict):
            continue
        source = metadata.get("fuente")
        mtime = metadata.get("mtime")
        if not source:
            continue
        if isinstance(mtime, (int, float)):
            source_mtimes[source] = max(source_mtimes.get(source, -1), int(mtime))

    current_sources = {pdf.name for pdf in pdf_files}
    if set(source_mtimes) != current_sources:
        return True

    for pdf_path in pdf_files:
        expected_mtime = int(pdf_path.stat().st_mtime)
        if source_mtimes.get(pdf_path.name) != expected_mtime:
            return True

    return False


def build_index(directory: Path, collection_name: str = COLLECTION_NAME, reindex: bool = False) -> chromadb.Collection:
    model = SentenceTransformer(MODEL_NAME)
    client = chromadb.PersistentClient(path=str(DB_PATH))
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )

    pdf_files = get_pdf_files(directory)
    if not pdf_files:
        raise FileNotFoundError(f"No se encontraron archivos PDF en: {directory}")

    if reindex or _should_rebuild_index(collection, pdf_files):
        existing_ids = collection.get(include=[]).get("ids", [])
        if existing_ids:
            collection.delete(ids=existing_ids)

    pdf_files = get_pdf_files(directory)
    if not pdf_files:
        raise FileNotFoundError(f"No se encontraron archivos PDF en: {directory}")

    all_ids: List[str] = []
    all_documents: List[str] = []
    all_metadatas: List[Dict[str, Any]] = []

    for pdf_path in pdf_files:
        full_text = extract_text_from_pdf(pdf_path)
        chunks = chunk_text(full_text)
        pdf_mtime = int(pdf_path.stat().st_mtime)

        for index, chunk in enumerate(chunks):
            doc_id = f"{pdf_path.stem}_{index}"
            all_ids.append(doc_id)
            all_documents.append(chunk)
            all_metadatas.append({
                "fuente": pdf_path.name,
                "categoria": "manual",
                "pagina": index + 1,
                "mtime": pdf_mtime,
            })

    if not all_documents:
        raise ValueError("No se pudo extraer contenido útil de los PDFs.")

    embeddings = model.encode(all_documents, normalize_embeddings=True).tolist()
    collection.upsert(
        ids=all_ids,
        documents=all_documents,
        metadatas=all_metadatas,
        embeddings=embeddings,
    )

    return collection


def search_documents(
    query: str,
    collection: chromadb.Collection,
    model: SentenceTransformer,
    top_k: int = 5,
    source_filter: str | None = None,
) -> Dict[str, Any]:
    vector_query = model.encode([query], normalize_embeddings=True).tolist()
    query_kwargs: Dict[str, Any] = {
        "query_embeddings": vector_query,
        "n_results": top_k,
    }

    if source_filter:
        query_kwargs["where"] = {"fuente": source_filter}

    return collection.query(**query_kwargs)


def generate_answer_from_context(query: str, documents: List[str]) -> str:
    if not documents:
        return "No encontré información suficiente para responder con seguridad."

    query_tokens = set(re.findall(r"[a-zA-Záéíóúüñ]+", query.lower()))
    selected_sentences: List[str] = []

    for document in documents:
        sentences = re.split(r"(?<=[.!?])\s+", document)
        for sentence in sentences:
            cleaned = sentence.strip()
            if len(cleaned) < 40:
                continue
            sentence_tokens = set(re.findall(r"[a-zA-Záéíóúüñ]+", cleaned.lower()))
            if not query_tokens or sentence_tokens.intersection(query_tokens):
                selected_sentences.append(cleaned)

    if not selected_sentences:
        selected_sentences = [document.strip() for document in documents[:3] if document.strip()]

    answer = " ".join(selected_sentences[:3])
    return answer[:1800]


def print_results(results: Dict[str, Any]) -> None:
    documents = results.get("documents", [[]])[0]
    distances = results.get("distances", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    if not documents:
        print("No se encontraron resultados relevantes.")
        return

    print("\nResultados más relevantes:\n")
    for idx, (document, distance, metadata) in enumerate(zip(documents, distances, metadatas), start=1):
        print(f"{idx}. Distancia: {distance:.4f}")
        print(f"   Fuente: {metadata.get('fuente', 'desconocida')}")
        print(f"   Documento: {document[:500]}...")
        print("-" * 80)

    answer = generate_answer_from_context(" ", documents)
    print("\nRespuesta resumida:\n")
    print(answer)


def interactive_mode(directory: Path, top_k: int = 5) -> None:
    model = SentenceTransformer(MODEL_NAME)
    collection = build_index(directory, reindex=False)

    print(f"\nSistema listo. Documentos cargados desde: {directory}")
    print("Escribe una consulta o 'salir' para terminar.\n")

    while True:
        query = input("Pregunta > ").strip()
        if query.lower() in {"salir", "exit", "quit"}:
            print("Saliendo del sistema...")
            break

        if not query:
            continue

        results = search_documents(query, collection, model, top_k=top_k)
        print_results(results)


def main() -> None:
    parser = argparse.ArgumentParser(description="Buscador semántico para documentos PDF.")
    parser.add_argument("--directory", type=str, default=".", help="Directorio que contiene los PDFs.")
    parser.add_argument("--query", type=str, help="Consulta semántica para buscar en los PDFs.")
    parser.add_argument("--top-k", type=int, default=5, help="Número de resultados a devolver.")
    parser.add_argument("--source", type=str, help="Filtrar resultados por el nombre del archivo PDF.")
    parser.add_argument("--reindex", action="store_true", help="Reindexa todos los PDFs aunque ya existan en ChromaDB.")
    parser.add_argument("--interactive", action="store_true", help="Activa modo interactivo.")
    args = parser.parse_args()

    directory = Path(args.directory).resolve()

    collection = build_index(directory, reindex=args.reindex)
    model = SentenceTransformer(MODEL_NAME)

    if args.interactive:
        interactive_mode(directory, top_k=args.top_k)
        return

    if not args.query:
        print("No se ingresó una consulta. Usa --query o --interactive.")
        return

    results = search_documents(args.query, collection, model, top_k=args.top_k, source_filter=args.source)
    print_results(results)


if __name__ == "__main__":
    main()
