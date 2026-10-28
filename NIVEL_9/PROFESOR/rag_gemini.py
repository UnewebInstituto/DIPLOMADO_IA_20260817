import argparse
import os

import chromadb
from google import genai
from google.genai import types
from sentence_transformers import SentenceTransformer

MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
DEFAULT_PERSIST_DIR = "./chroma_db"
DEFAULT_COLLECTION = "manuales"
DEFAULT_GEMINI_MODEL = "gemini-3.5-flash-lite"


def get_retrieved_context(question: str, persist_dir: str = DEFAULT_PERSIST_DIR, collection_name: str = DEFAULT_COLLECTION, n_results: int = 3):
    """Recupera los top-k fragmentos relevantes de ChromaDB para una pregunta."""
    model = SentenceTransformer(MODEL_NAME)
    client = chromadb.PersistentClient(path=str(persist_dir))
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )

    query_vector = model.encode([question], normalize_embeddings=True).tolist()
    result = collection.query(
        query_embeddings=query_vector,
        n_results=n_results,
    )

    documents = result.get("documents", [[]])[0]
    metadatas = result.get("metadatas", [[]])[0]

    if not documents:
        raise ValueError("No se encontraron documentos relevantes para la consulta realizada.")

    context_blocks = []
    for idx, (doc, meta) in enumerate(zip(documents, metadatas), start=1):
        fuente = meta.get("fuente", "desconocida") if isinstance(meta, dict) else "desconocida"
        pagina = meta.get("pagina", "?") if isinstance(meta, dict) else "?"
        context_blocks.append(f"[{idx}] Documento: {fuente} | Página: {pagina}\n{doc}")

    return "\n\n".join(context_blocks), result


def build_rag_prompt(question: str, context: str):
    """Construye el prompt del modelo generativo con el contexto recuperado."""
    return f"""
Eres un asistente que responde únicamente con base en el contexto proporcionado.
No inventes información ni respondas fuera del contexto.
Si no encuentras una respuesta clara, dilo de manera honesta.
Incluye la fuente y la página cuando sea posible.

CONTEXTO:
{context}

PREGUNTA:
{question}

RESPUESTA:
""".strip()


def answer_with_gemini(question: str, persist_dir: str = DEFAULT_PERSIST_DIR, collection_name: str = DEFAULT_COLLECTION, n_results: int = 3, model_name: str = DEFAULT_GEMINI_MODEL):
    """Recupera contexto desde ChromaDB y genera la respuesta final usando Gemini."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Define la variable de entorno GEMINI_API_KEY antes de ejecutar esta solución.")

    client = genai.Client(api_key=api_key)

    context, result = get_retrieved_context(
        question=question,
        persist_dir=persist_dir,
        collection_name=collection_name,
        n_results=n_results,
    )

    prompt = build_rag_prompt(question, context)
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.2,
            top_p=0.95,
            max_output_tokens=500,
        ),
    )

    answer_text = getattr(response, "text", str(response))
    return {
        "answer": answer_text,
        "context": context,
        "raw_result": result,
    }


def main():
    parser = argparse.ArgumentParser(description="RAG con ChromaDB + Gemini para responder preguntas sobre PDFs.")
    parser.add_argument("--question", required=True, help="Pregunta a responder")
    parser.add_argument("--persist-dir", default=DEFAULT_PERSIST_DIR, help="Ruta de persistencia de ChromaDB")
    parser.add_argument("--collection", default=DEFAULT_COLLECTION, help="Nombre de la colección en ChromaDB")
    parser.add_argument("--n-results", type=int, default=3, help="Número de fragmentos a recuperar")
    parser.add_argument("--model", default=DEFAULT_GEMINI_MODEL, help="Modelo de Gemini a usar")
    args = parser.parse_args()

    result = answer_with_gemini(
        question=args.question,
        persist_dir=args.persist_dir,
        collection_name=args.collection,
        n_results=args.n_results,
        model_name=args.model,
    )

    print("\nRESPUESTA:")
    print(result["answer"])

    print("\nFUENTES RECUPERADAS:")
    for idx, doc in enumerate(result["raw_result"]["documents"][0], start=1):
        meta = result["raw_result"]["metadatas"][0][idx - 1]
        print(f"[{idx}] {meta.get('fuente')} | Página: {meta.get('pagina')}")


if __name__ == "__main__":
    main()
