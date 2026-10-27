from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List

import chromadb
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer

WORKSPACE_DIR = Path(__file__).resolve().parent
PDF_DIR = WORKSPACE_DIR
DB_DIR = WORKSPACE_DIR / "chroma_db"
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
COLLECTION_NAME = "manuales"


def get_pdf_files(directory: Path) -> List[Path]:
    pdfs = sorted(directory.glob("*.pdf"))
    if not pdfs:
        raise FileNotFoundError(f"No se encontraron archivos PDF en: {directory}")
    return pdfs


def clean_text(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_pdf_pages(pdf_path: Path) -> List[Dict[str, Any]]:
    reader = PdfReader(str(pdf_path))
    pages: List[Dict[str, Any]] = []

    for page_number, page in enumerate(reader.pages, start=1):
        raw_text = page.extract_text() or ""
        cleaned = clean_text(raw_text)
        if cleaned:
            pages.append(
                {
                    "fuente": pdf_path.name,
                    "pagina": page_number,
                    "texto": cleaned,
                }
            )

    return pages


def chunk_text(text: str, chunk_size: int = 350, overlap: int = 60) -> List[str]:
    words = text.split()
    if not words:
        return []

    chunks: List[str] = []
    start = 0

    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end])
        chunks.append(chunk)

        if end == len(words):
            break

        start += max(1, chunk_size - overlap)

    return chunks


def build_documents() -> List[Dict[str, Any]]:
    documents: List[Dict[str, Any]] = []

    for pdf_path in get_pdf_files(PDF_DIR):
        for page in extract_pdf_pages(pdf_path):
            for index, chunk in enumerate(chunk_text(page["texto"])):
                documents.append(
                    {
                        "id": f"{pdf_path.stem}_{page['pagina']}_{index}",
                        "fuente": page["fuente"],
                        "pagina": page["pagina"],
                        "texto": chunk,
                    }
                )

    return documents


def get_or_create_collection() -> chromadb.Collection:
    client = chromadb.PersistentClient(path=str(DB_DIR))
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )
    return collection


def index_documents(model: SentenceTransformer, documents: Iterable[Dict[str, Any]]) -> chromadb.Collection:
    docs = list(documents)
    if not docs:
        raise ValueError("No hay documentos para indexar.")

    collection = get_or_create_collection()

    ids = [item["id"] for item in docs]
    texts = [item["texto"] for item in docs]
    metadatas = [
        {"fuente": item["fuente"], "pagina": item["pagina"]}
        for item in docs
    ]
    embeddings = model.encode(texts, normalize_embeddings=True).tolist()

    collection.upsert(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas,
    )

    return collection


def search_documents(
    model: SentenceTransformer,
    collection: chromadb.Collection,
    question: str,
    source: str | None = None,
    top_k: int = 3,
) -> Dict[str, Any]:
    query_embedding = model.encode([question], normalize_embeddings=True).tolist()
    where = {"fuente": source} if source else None

    return collection.query(
        query_embeddings=query_embedding,
        n_results=top_k,
        where=where,
    )


def print_results(results: Dict[str, Any]) -> None:
    documents = results.get("documents", [[]])[0]
    distances = results.get("distances", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    if not documents:
        print("No se encontraron resultados relevantes.")
        return

    for index, document in enumerate(documents, start=1):
        metadata = metadatas[index - 1] if index - 1 < len(metadatas) else {}
        distance = distances[index - 1] if index - 1 < len(distances) else None
        print(f"\nResultado {index}")
        print(f"- Fuente: {metadata.get('fuente', 'N/A')}")
        print(f"- Página: {metadata.get('pagina', 'N/A')}")
        print(f"- Distancia: {distance}")
        print(f"- Texto: {document}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Búsqueda semántica sobre manuales PDF.")
    parser.add_argument("--reindex", action="store_true", help="Reindexa los PDFs desde cero.")
    parser.add_argument("--query", type=str, help="Pregunta a consultar en la colección.")
    parser.add_argument("--source", type=str, help="Filtra resultados por fuente (nombre del PDF).")
    parser.add_argument("--top-k", type=int, default=3, help="Número máximo de resultados a devolver.")
    args = parser.parse_args()

    model = SentenceTransformer(MODEL_NAME)

    if args.reindex:
        docs = build_documents()
        collection = index_documents(model, docs)
        print(f"Se indexaron {len(docs)} fragmentos en la colección '{COLLECTION_NAME}'.")
    else:
        collection = get_or_create_collection()

    if args.query:
        print(f"\nConsulta: {args.query}\n")
        results = search_documents(model, collection, args.query, source=args.source, top_k=args.top_k)
        print_results(results)
    else:
        sample_queries = [
            "¿Cómo recupero mi contraseña?",
            "¿Cuándo se solicita vacaciones?",
            "¿Qué se debe hacer para restablecer la clave?",
        ]

        print("Ejemplos de consultas:")
        for question in sample_queries:
            print(f"\nConsulta: {question}")
            results = search_documents(model, collection, question, top_k=2)
            print_results(results)


if __name__ == "__main__":
    main()
