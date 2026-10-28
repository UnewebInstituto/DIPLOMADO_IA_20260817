from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import List, Dict, Any

from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
import chromadb

try:
    from google import genai
except ImportError:
    genai = None


PDF_DIR = Path(r"C:\.Profesores\HENRY_DUQUE\DIPLOMADO_IA_20260817\NIVEL_9\Keyla")
DB_PATH = PDF_DIR / "chroma_db_gemini"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
GEMINI_MODEL = "gemini-2.5-flash"

_model = None
_collection = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        print("Cargando modelo de embeddings...")
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def get_collection():
    global _collection
    if _collection is None:
        client = chromadb.PersistentClient(path=str(DB_PATH))
        _collection = client.get_or_create_collection(
            name="manuales_gemini",
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def extraer_texto_pdf(archivo_pdf: Path) -> str:
    lector = PdfReader(str(archivo_pdf))
    paginas = []
    for pagina_num, pagina in enumerate(lector.pages, start=1):
        texto = pagina.extract_text() or ""
        texto = " ".join(texto.split())
        if texto:
            paginas.append(f"[Página {pagina_num}] {texto}")
    return "\n".join(paginas)


def dividir_texto(texto: str, chunk_size: int = 500, overlap: int = 80) -> List[str]:
    if not texto:
        return []

    chunks: List[str] = []
    inicio = 0
    longitud = len(texto)

    while inicio < longitud:
        fin = min(inicio + chunk_size, longitud)
        chunk = texto[inicio:fin].strip()
        if chunk:
            chunks.append(chunk)
        if fin == longitud:
            break
        inicio += chunk_size - overlap

    return chunks


def indexar_documentos(force: bool = False):
    col = get_collection()

    if not force:
        try:
            if col.get()["ids"]:
                return col
        except Exception:
            pass

    ids = []
    documentos = []
    metadatos = []

    for pdf_path in sorted(PDF_DIR.glob("*.pdf")):
        texto = extraer_texto_pdf(pdf_path)
        chunks = dividir_texto(texto)

        for idx, chunk in enumerate(chunks):
            ids.append(f"{pdf_path.stem}_{idx:03d}")
            documentos.append(chunk)
            metadatos.append({
                "fuente": pdf_path.name,
                "archivo": pdf_path.stem,
                "chunk": idx,
            })

    if documentos:
        embeddings = get_model().encode(documentos, normalize_embeddings=True).tolist()
        col.upsert(
            ids=ids,
            documents=documentos,
            metadatas=metadatos,
            embeddings=embeddings,
        )

    return col


def buscar_contexto(pregunta: str, n_results: int = 4):
    col = indexar_documentos()
    embedding = get_model().encode([pregunta], normalize_embeddings=True).tolist()
    resultado = col.query(query_embeddings=embedding, n_results=n_results)

    items = []
    for doc, meta, dist in zip(
        resultado["documents"][0],
        resultado["metadatas"][0],
        resultado["distances"][0],
    ):
        items.append({
            "texto": doc,
            "fuente": meta.get("fuente", "Desconocida"),
            "chunk": meta.get("chunk", 0),
            "distancia": float(dist),
        })

    return items


def crear_prompt(pregunta: str, contexto: List[Dict[str, Any]]) -> str:
    contexto_texto = "\n\n---\n\n".join(
        f"Fuente: {item['fuente']}\nChunk: {item['chunk']}\n\n{item['texto']}"
        for item in contexto
    )

    return f"""
Eres un asistente experto que responde preguntas usando únicamente el contexto proporcionado.

INSTRUCCIONES:
- Responde solo con base en el contexto.
- Si la información no aparece en el contexto, dilo claramente.
- Cita la fuente del documento cuando sea posible.
- No inventes datos.
- Sé breve, claro y útil.

PREGUNTA DEL USUARIO:
{pregunta}

CONTEXTO:
{contexto_texto}

RESPUESTA:
""".strip()


def llamar_gemini(prompt: str, api_key: str | None = None):
    key = api_key or os.getenv("GOOGLE_API_KEY")
    if not key:
        raise RuntimeError(
            "No hay clave de API de Google. Define la variable GOOGLE_API_KEY o pasa --api-key."
        )

    if genai is not None:
        try:
            client = genai.Client(api_key=key)
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
            )
            return response.text
        except Exception:
            pass

    try:
        import google.generativeai as ggenai

        ggenai.configure(api_key=key)
        model = ggenai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(prompt)
        return response.text
    except Exception as exc:
        raise RuntimeError(f"No se pudo llamar a Gemini: {exc}") from exc


def responder_rag(pregunta: str, n_results: int = 4, api_key: str | None = None):
    contexto = buscar_contexto(pregunta, n_results=n_results)
    prompt = crear_prompt(pregunta, contexto)
    respuesta = llamar_gemini(prompt, api_key=api_key)

    return {
        "pregunta": pregunta,
        "respuesta": respuesta,
        "contexto": contexto,
    }


def main():
    parser = argparse.ArgumentParser(description="RAG sobre PDFs con ChromaDB + Google Gemini")
    parser.add_argument("--query", type=str, required=True, help="Pregunta del usuario")
    parser.add_argument("--n-results", type=int, default=4, help="Número de fragmentos a recuperar")
    parser.add_argument("--api-key", type=str, default=None, help="Clave API de Google Gemini")
    args = parser.parse_args()

    resultado = responder_rag(args.query, n_results=args.n_results, api_key=args.api_key)

    print("\nPREGUNTA:")
    print(resultado["pregunta"])
    print("\nRESPUESTA:")
    print(resultado["respuesta"])
    print("\nFUENTES:")
    for item in resultado["contexto"]:
        print(f"- {item['fuente']} | distancia={item['distancia']:.4f}")


if __name__ == "__main__":
    main()
