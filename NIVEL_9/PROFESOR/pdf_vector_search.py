import argparse
from pathlib import Path

import chromadb
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer

MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
DEFAULT_PERSIST_DIR = "./chroma_db"
DEFAULT_COLLECTION = "manuales"


def extract_pdf_pages(pdf_path: Path):
    """Extrae texto de un PDF y devuelve una lista de diccionarios con página y texto."""
    reader = PdfReader(str(pdf_path))
    pages = []
    for page_num, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if text and text.strip():
            pages.append({"page": page_num, "text": text.strip()})
    return pages


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 80):
    """Divide un texto largo en fragmentos con overlap."""
    words = text.split()
    if not words:
        return []

    chunks = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end])
        if chunk.strip():
            chunks.append(chunk.strip())
        if end == len(words):
            break
        start = max(start + chunk_size - overlap, end - overlap)
    return chunks


def build_index(pdf_dir: str = ".", persist_dir: str = DEFAULT_PERSIST_DIR, collection_name: str = DEFAULT_COLLECTION):
    """Lee los PDFs del directorio, genera embeddings y guarda la colección en ChromaDB."""
    pdf_dir_path = Path(pdf_dir)
    pdf_files = sorted(pdf_dir_path.glob("*.pdf"))
    if not pdf_files:
        raise FileNotFoundError(f"No se encontraron archivos PDF en: {pdf_dir_path}")

    model = SentenceTransformer(MODEL_NAME)
    client = chromadb.PersistentClient(path=str(persist_dir))
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )

    ids = []
    documents = []
    metadatas = []

    for pdf_file in pdf_files:
        pages = extract_pdf_pages(pdf_file)
        for page_info in pages:
            chunks = chunk_text(page_info["text"])
            for chunk_idx, chunk in enumerate(chunks):
                chunk_id = f"{pdf_file.name}__p{page_info['page']}__c{chunk_idx}"
                ids.append(chunk_id)
                documents.append(chunk)
                metadatas.append({
                    "fuente": pdf_file.name,
                    "pagina": page_info["page"],
                    "chunk": chunk_idx,
                })

    if not documents:
        raise ValueError(f"No se pudo extraer texto útil de ningún PDF en {pdf_dir_path}")

    embeddings = model.encode(documents, normalize_embeddings=True).tolist()
    collection.upsert(
        ids=ids,
        documents=documents,
        metadatas=metadatas,
        embeddings=embeddings,
    )

    print(f"Se indexaron {len(documents)} fragmentos desde {len(pdf_files)} PDF(s).")
    print(f"Colección persistida en: {persist_dir}")
    return collection


def query_collection(question: str, persist_dir: str = DEFAULT_PERSIST_DIR, collection_name: str = DEFAULT_COLLECTION, n_results: int = 3, source_filter: str = None):
    """Consulta una pregunta en la colección vectorial."""
    model = SentenceTransformer(MODEL_NAME)
    client = chromadb.PersistentClient(path=str(persist_dir))
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )

    query_vector = model.encode([question], normalize_embeddings=True).tolist()
    where = {"fuente": source_filter} if source_filter else None

    result = collection.query(
        query_embeddings=query_vector,
        n_results=n_results,
        where=where,
    )

    return result


def main():
    parser = argparse.ArgumentParser(description="Sistema de búsqueda semántica sobre PDFs con ChromaDB y SentenceTransformers")
    parser.add_argument("action", choices=["index", "query"], help="Acción a ejecutar: indexar documentos o consultar")
    parser.add_argument("--pdf-dir", default=".", help="Directorio que contiene los PDFs a indexar")
    parser.add_argument("--persist-dir", default=DEFAULT_PERSIST_DIR, help="Ruta de persistencia para ChromaDB")
    parser.add_argument("--collection", default=DEFAULT_COLLECTION, help="Nombre de la colección vectorial")
    parser.add_argument("--question", default=None, help="Pregunta a consultar cuando se usa action=query")
    parser.add_argument("--source", default=None, help="Filtro opcional por nombre de archivo PDF")
    parser.add_argument("--n-results", type=int, default=3, help="Número máximo de resultados a devolver")
    args = parser.parse_args()

    if args.action == "index":
        build_index(args.pdf_dir, args.persist_dir, args.collection)
        return

    if not args.question:
        raise SystemExit("Debe indicar --question cuando uses la acción query")

    results = query_collection(
        question=args.question,
        persist_dir=args.persist_dir,
        collection_name=args.collection,
        n_results=args.n_results,
        source_filter=args.source,
    )

    print("\nRESULTADOS:")
    for idx, doc in enumerate(results["documents"][0], start=1):
        meta = results["metadatas"][0][idx - 1]
        distance = results["distances"][0][idx - 1]
        print(f"\n[{idx}] Archivo: {meta.get('fuente')} | Página: {meta.get('pagina')} | Distancia: {distance:.4f}")
        print(doc)


if __name__ == "__main__":
    main()
