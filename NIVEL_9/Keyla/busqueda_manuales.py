from pathlib import Path
import argparse

import chromadb
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer

MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"


def extraer_texto_pdf(archivo_pdf: Path) -> str:
    """Extrae todo el texto de un archivo PDF."""
    lector = PdfReader(str(archivo_pdf))
    textos = []
    for pagina_num, pagina in enumerate(lector.pages, start=1):
        texto = pagina.extract_text() or ""
        texto = " ".join(texto.split())
        if texto:
            textos.append(f"[Página {pagina_num}] {texto}")
    return "\n".join(textos)


def dividir_texto(texto: str, chunk_size: int = 500, overlap: int = 80):
    """Divide el texto en fragmentos con solapamiento."""
    if not texto:
        return []

    chunks = []
    inicio = 0
    longitud = len(texto)

    while inicio < longitud:
        fin = min(inicio + chunk_size, longitud)
        chunk = texto[inicio:fin]
        chunks.append(chunk.strip())
        if fin == longitud:
            break
        inicio += chunk_size - overlap

    return [c for c in chunks if c]


def crear_coleccion(pdf_dir: Path, db_path: Path, modelo: SentenceTransformer):
    """Indexa todos los PDFs de una carpeta en ChromaDB."""
    cliente = chromadb.PersistentClient(path=str(db_path))
    coleccion = cliente.get_or_create_collection(
        name="manuales",
        metadata={"hnsw:space": "cosine"},
    )

    ids = []
    documentos = []
    metadatos = []

    for pdf_path in sorted(pdf_dir.glob("*.pdf")):
        texto_completo = extraer_texto_pdf(pdf_path)
        chunks = dividir_texto(texto_completo)

        for idx, chunk in enumerate(chunks):
            chunk_id = f"{pdf_path.stem}_{idx:03d}"
            ids.append(chunk_id)
            documentos.append(chunk)
            metadatos.append({
                "fuente": pdf_path.name,
                "archivo": pdf_path.stem,
                "chunk": idx,
            })

    if not documentos:
        raise ValueError(f"No se encontraron PDFs en: {pdf_dir}")

    embeddings = modelo.encode(documentos, normalize_embeddings=True).tolist()
    coleccion.upsert(
        ids=ids,
        documents=documentos,
        metadatas=metadatos,
        embeddings=embeddings,
    )

    return coleccion


def consultar(coleccion, modelo: SentenceTransformer, pregunta: str, n_results: int = 3, fuente: str | None = None):
    """Consulta semántica sobre la colección."""
    pregunta_embedding = modelo.encode([pregunta], normalize_embeddings=True).tolist()
    filtros = {"fuente": fuente} if fuente else None

    resultado = coleccion.query(
        query_embeddings=pregunta_embedding,
        n_results=n_results,
        where=filtros,
    )
    return resultado


def main():
    parser = argparse.ArgumentParser(description="Búsqueda semántica sobre PDFs con ChromaDB")
    parser.add_argument(
        "--pdf-dir",
        default=r"C:\.Profesores\HENRY_DUQUE\DIPLOMADO_IA_20260817\NIVEL_9\Keyla",
        help="Carpeta con archivos PDF",
    )
    parser.add_argument(
        "--query",
        default="¿Cómo recupero mi contraseña?",
        help="Pregunta a buscar",
    )
    parser.add_argument(
        "--fuente",
        default=None,
        help="Opcional: filtrar por nombre de archivo, por ejemplo manual_ti.pdf",
    )
    parser.add_argument(
        "--n-results",
        type=int,
        default=3,
        help="Número de resultados a devolver",
    )

    args = parser.parse_args()

    pdf_dir = Path(args.pdf_dir)
    db_path = pdf_dir / "chroma_db"

    modelo = SentenceTransformer(MODEL_NAME)
    coleccion = crear_coleccion(pdf_dir, db_path, modelo)

    resultado = consultar(coleccion, modelo, args.query, args.n_results, args.fuente)

    print(f"Pregunta: {args.query}")
    print("\nResultados:")
    for i, (doc, distancia) in enumerate(zip(resultado["documents"][0], resultado["distances"][0]), start=1):
        fuente = resultado["metadatas"][0][i - 1].get("fuente", "desconocida")
        print(f"\n[{i}] Fuente: {fuente}")
        print(f"Texto: {doc}")
        print(f"Distancia coseno: {distancia:.4f}")


if __name__ == "__main__":
    main()
