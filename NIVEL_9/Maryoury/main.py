import os
from typing import Any, Dict, List, Sequence, Tuple

import chromadb
import pymupdf as fitz
import requests
from sentence_transformers import SentenceTransformer

MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
DB_PATH = os.path.join(os.getcwd(), "chroma_db")
COLLECTION_NAME = "manuales"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash-lite")


def chunk_text(text: str, chunk_size: int = 400, overlap: int = 80) -> List[str]:
    cleaned = text.strip()
    if not cleaned:
        return []

    chunks: List[str] = []
    start = 0
    while start < len(cleaned):
        end = min(len(cleaned), start + chunk_size)
        chunk = cleaned[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(cleaned):
            break
        start += chunk_size - overlap

    return chunks


def extract_text_from_pdf(pdf_path: str) -> List[Tuple[int, str]]:
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"No se encontró el archivo PDF: {pdf_path}")

    doc = fitz.open(pdf_path)
    pages: List[Tuple[int, str]] = []
    try:
        for page_number, page in enumerate(doc, start=1):
            text = page.get_text("text", sort=True)
            cleaned = " ".join(text.split())
            if cleaned:
                pages.append((page_number, cleaned))
    finally:
        doc.close()

    return pages


def index_manuals(pdf_paths: Sequence[str], db_path: str = DB_PATH, collection_name: str = COLLECTION_NAME):
    model = SentenceTransformer(MODEL_NAME)
    client = chromadb.PersistentClient(path=db_path)
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )

    all_ids: List[str] = []
    all_docs: List[str] = []
    all_metadatas: List[Dict[str, Any]] = []
    all_embeddings: List[List[float]] = []

    for pdf_path in pdf_paths:
        source_name = os.path.basename(pdf_path)
        pages = extract_text_from_pdf(pdf_path)
        for page_number, page_text in pages:
            chunks = chunk_text(page_text)
            if not chunks:
                continue

            embeddings = model.encode(chunks, normalize_embeddings=True).tolist()
            for chunk_index, chunk in enumerate(chunks):
                chunk_id = f"{source_name}_p{page_number}_c{chunk_index}"
                all_ids.append(chunk_id)
                all_docs.append(chunk)
                all_metadatas.append({
                    "fuente": source_name,
                    "pagina": page_number,
                    "tipo": "manual",
                })
                all_embeddings.append(embeddings[chunk_index])

    if all_docs:
        collection.upsert(
            ids=all_ids,
            documents=all_docs,
            metadatas=all_metadatas,
            embeddings=all_embeddings,
        )

    return model, collection


def search_manuals(question: str, db_path: str = DB_PATH, collection_name: str = COLLECTION_NAME, source: str | None = None, top_k: int = 3):
    model = SentenceTransformer(MODEL_NAME)
    client = chromadb.PersistentClient(path=db_path)
    collection = client.get_collection(name=collection_name)

    query_vector = model.encode([question], normalize_embeddings=True).tolist()
    where_clause = {"fuente": source} if source else None

    result = collection.query(
        query_embeddings=query_vector,
        n_results=top_k,
        where=where_clause,
    )
    return result


def build_rag_prompt(question: str, context_chunks: Sequence[str]) -> str:
    if not context_chunks:
        return (
            "No hay contexto suficiente para responder. "
            f"Pregunta original: {question}"
        )

    context = "\n\n---\n\n".join(
        f"Fragmento {index + 1}:\n{chunk}"
        for index, chunk in enumerate(context_chunks)
    )
    return (
        "Responde la pregunta usando únicamente el contexto proporcionado. "
        "Si la información no aparece en el contexto, di que no la encuentras en los documentos. "
        "Incluye una respuesta en formato de cita con referencia a la fuente documental y a la página cuando sea posible.\n\n"
        f"Contexto:\n{context}\n\nPregunta: {question}\n\nRespuesta:"
    )


def format_citation(source_name: str, page_number: int | None, snippet: str) -> str:
    page_text = f"página {page_number}" if page_number is not None else "página desconocida"
    excerpt = snippet.strip().replace("\n", " ")
    if len(excerpt) > 220:
        excerpt = excerpt[:217].rstrip() + "..."
    return f"[{source_name} · {page_text}] “{excerpt}”"


def answer_question(question: str, db_path: str = DB_PATH, collection_name: str = COLLECTION_NAME, source: str | None = None, top_k: int = 3, api_key: str | None = None, model_name: str = GEMINI_MODEL):
    result = search_manuals(question, db_path=db_path, collection_name=collection_name, source=source, top_k=top_k)
    documents = result.get("documents", [[]])[0]
    metadatas = result.get("metadatas", [[]])[0]

    if not documents:
        return "No se encontraron documentos relevantes para su consulta.", []

    answer = ask_gemini(question, documents, api_key=api_key, model_name=model_name)
    evidence = []
    for document, metadata in zip(documents, metadatas):
        metadata_dict = metadata if isinstance(metadata, dict) else {}
        source_name = metadata_dict.get("fuente", "documento")
        page_number = metadata_dict.get("pagina")
        evidence.append({
            "source": source_name,
            "page": page_number,
            "citation": format_citation(source_name, page_number, document),
            "text": document,
        })

    return answer, evidence


def ask_gemini(question: str, context_chunks: Sequence[str], api_key: str | None = None, model_name: str = "gemini-3.8-flash-lite") -> str:
    key = api_key or GEMINI_API_KEY
    if not key:
        raise ValueError("Falta la variable de entorno GEMINI_API_KEY")

    selected_model = model_name or GEMINI_MODEL or "gemini-3.8-flash-lite"
    prompt = build_rag_prompt(question, context_chunks)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{selected_model}:generateContent?key={key}"
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }

    response = requests.post(url, json=payload, timeout=60)
    response.raise_for_status()
    data = response.json()

    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError):
        raise ValueError(f"No se pudo interpretar la respuesta de Gemini: {data}")


if __name__ == "__main__":
    pdf_files = [
        os.path.join(os.getcwd(), "manual_ti.pdf"),
        os.path.join(os.getcwd(), "manual_rrhh.pdf"),
    ]

    print("Indexando documentos...")
    _, collection = index_manuals(pdf_files)
    print(f"Base vectorial lista. Registros: {collection.count()}")
    print("Recuerda configurar la variable de entorno GEMINI_API_KEY antes de usar Gemini.")

    while True:
        pregunta = input("\nPregunta (o 'salir'): ").strip()
        if pregunta.lower() in {"salir", "exit", "quit"}:
            break

        resultado = search_manuals(pregunta, top_k=3)
        documentos = resultado.get("documents", [[]])[0]
        distancias = resultado.get("distances", [[]])[0]
        metadatos = resultado.get("metadatas", [[]])[0]

        if not documentos:
            print("No se encontraron resultados relevantes.")
            continue

        for i, texto in enumerate(documentos):
            print(f"\nResultado {i + 1} | distancia: {distancias[i]}")
            print(texto[:600])
            if i < len(metadatos):
                print("Metadatos:", metadatos[i])

        try:
            respuesta = ask_gemini(pregunta, documentos)
            print("\nRespuesta generada por Gemini:\n")
            print(respuesta)
        except ValueError as exc:
            print(f"No se pudo generar respuesta con Gemini: {exc}")
