from __future__ import annotations

import argparse
import os
import re
from pathlib import Path
from typing import Any

import chromadb
from dotenv import load_dotenv
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer

try:
    from google import genai
except ImportError:  # pragma: no cover
    genai = None

ROOT_DIR = Path(__file__).resolve().parent
load_dotenv(ROOT_DIR / ".env")

DB_PATH = ROOT_DIR / "chroma_db"
EMBEDDING_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
COLLECTION_NAME = "manuales"
CHUNK_SIZE = 400
CHUNK_OVERLAP = 80
_EMBEDDING_MODEL: SentenceTransformer | None = None


def get_embedding_model(model_name: str = EMBEDDING_MODEL_NAME) -> SentenceTransformer:
    global _EMBEDDING_MODEL
    if _EMBEDDING_MODEL is None:
        _EMBEDDING_MODEL = SentenceTransformer(model_name)
    return _EMBEDDING_MODEL


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
        print("No se encontraron resultados relevantes.")
        return

    print("\nResultados relevantes:\n")
    for idx, (doc, dist, meta) in enumerate(zip(documents, distances, metadatas), start=1):
        print(f"[{idx}] Distancia: {dist:.4f}")
        print(f"Fuente: {meta.get('fuente')} | Página: {meta.get('pagina')}")
        print(doc)
        print("-" * 80)


def build_rag_prompt(question: str, result: dict[str, Any]) -> str:
    documents = result.get("documents", [[]])[0]
    metadatas = result.get("metadatas", [[]])[0]

    if not documents:
        return (
            "No hay contexto suficiente para responder la pregunta. "
            "Indica que la información no aparece en los documentos indexados."
        )

    context_parts: list[str] = []
    for idx, (doc, meta) in enumerate(zip(documents, metadatas), start=1):
        fuente = meta.get("fuente", "desconocida")
        pagina = meta.get("pagina", "?")
        context_parts.append(f"[{idx}] Fuente: {fuente} | Página: {pagina}\n{doc}")

    context = "\n\n".join(context_parts)

    return (
        "Responde la pregunta usando únicamente el contexto proporcionado. "
        "Si la respuesta no está en el texto, di claramente que no se encuentra en los documentos.\n\n"
        f"Pregunta: {question}\n\n"
        f"Contexto:\n{context}\n\n"
        "Respuesta breve, útil y basada estrictamente en el contexto."
    )


def fallback_answer_from_context(question: str, result: dict[str, Any]) -> str:
    documents = result.get("documents", [[]])[0]
    metadatas = result.get("metadatas", [[]])[0]

    if not documents:
        return (
            "No hay contexto suficiente para responder la pregunta. "
            "No aparece información relevante en los documentos indexados."
        )

    best_doc = str(documents[0]).strip()
    best_meta = metadatas[0] if metadatas else {}
    fuente = best_meta.get("fuente", "documento")
    pagina = best_meta.get("pagina", "?")

    if len(best_doc) > 500:
        preview = best_doc[:500].rsplit(" ", 1)[0]
        best_doc = f"{preview}..."

    return (
        f"Respuesta basada en el contexto recuperado (fuente: {fuente}, página: {pagina}).\n\n"
        f"{best_doc}\n\n"
        "La clave GEMINI_API_KEY no está configurada, por lo que la respuesta se genera con el contenido recuperado del documento."
    )


def answer_with_gemini(question: str, result: dict[str, Any]) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError(
            "Falta la variable de entorno GEMINI_API_KEY. "
            "Configúrela antes de consultar con Gemini."
        )

    if genai is None:
        raise RuntimeError(
            "La librería google-genai no está instalada. "
            "Instálala con: pip install google-genai"
        )

    client = genai.Client(api_key=api_key)
    model_name = os.getenv("GEMINI_MODEL", GEMINI_MODEL_NAME)
    prompt = build_rag_prompt(question, result)
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )

    return getattr(response, "text", str(response))


def rag_answer(question: str, source: str | None = None, top_k: int = 5, model: SentenceTransformer | None = None) -> dict[str, Any]:
    if model is None:
        model = get_embedding_model(EMBEDDING_MODEL_NAME)

    result = query_collection(question, model, source=source, top_k=top_k)
    documents = result.get("documents", [[]])[0]
    metadatas = result.get("metadatas", [[]])[0]
    citations: list[dict[str, Any]] = []

    for doc, meta in zip(documents, metadatas):
        citations.append({
            "fuente": meta.get("fuente", "desconocida"),
            "pagina": meta.get("pagina", "?"),
            "texto": doc,
        })

    answer = ""
    try:
        answer = answer_with_gemini(question, result)
    except (ValueError, RuntimeError):
        answer = fallback_answer_from_context(question, result)

    return {
        "question": question,
        "answer": answer,
        "citations": citations,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Motor de búsqueda semántica para manuales PDF con soporte RAG en Gemini.")
    parser.add_argument("--query", type=str, help="Pregunta a buscar sobre los documentos.")
    parser.add_argument("--source", type=str, help="Filtro opcional por nombre de archivo PDF, por ejemplo: manual_ti.pdf")
    parser.add_argument("--top-k", type=int, default=3, help="Número de resultados a devolver.")
    parser.add_argument("--reindex", action="store_true", help="Reindexa todos los PDFs disponibles antes de consultar.")
    parser.add_argument("--model", type=str, default=os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite"), help="Modelo de Gemini a usar.")
    args = parser.parse_args()

    if args.model:
        os.environ["GEMINI_MODEL"] = args.model

    model = get_embedding_model(EMBEDDING_MODEL_NAME)

    if args.reindex or not DB_PATH.exists():
        collection, count = build_index(ROOT_DIR, model)
        print(f"Se indexaron {count} fragmentos en la colección '{collection.name}'.")

    if args.query:
        result = query_collection(args.query, model, source=args.source, top_k=args.top_k)
        print_results(result)

        try:
            answer = answer_with_gemini(args.query, result)
            print("\nRespuesta generada por Gemini:\n")
            print(answer)
        except (ValueError, RuntimeError) as exc:
            print(f"\nNo se pudo generar la respuesta con Gemini: {exc}")
            print("\nUsando respuesta local basada en el contexto recuperado:\n")
            print(fallback_answer_from_context(args.query, result))
        return

    print("Sistema listo. Usa --query 'tu pregunta' para consultar los PDFs.")


if __name__ == "__main__":
    main()
