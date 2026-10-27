from flask import Flask, request, jsonify
from pathlib import Path
from sentence_transformers import SentenceTransformer
import chromadb
from pypdf import PdfReader

app = Flask(__name__)

MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
PDF_DIR = Path(r"C:\.Profesores\HENRY_DUQUE\DIPLOMADO_IA_20260817\NIVEL_9\Keyla")
DB_PATH = PDF_DIR / "chroma_db"

modelo = SentenceTransformer(MODEL_NAME)


def extraer_texto_pdf(archivo_pdf: Path) -> str:
    lector = PdfReader(str(archivo_pdf))
    textos = []
    for pagina_num, pagina in enumerate(lector.pages, start=1):
        texto = pagina.extract_text() or ""
        texto = " ".join(texto.split())
        if texto:
            textos.append(f"[Página {pagina_num}] {texto}")
    return "\n".join(textos)


def dividir_texto(texto: str, chunk_size: int = 500, overlap: int = 80):
    if not texto:
        return []
    chunks = []
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


def construir_coleccion():
    cliente = chromadb.PersistentClient(path=str(DB_PATH))
    coleccion = cliente.get_or_create_collection(
        name="manuales",
        metadata={"hnsw:space": "cosine"}
    )

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
                "chunk": idx
            })

    if documentos:
        embeddings = modelo.encode(documentos, normalize_embeddings=True).tolist()
        coleccion.upsert(
            ids=ids,
            documents=documentos,
            metadatas=metadatos,
            embeddings=embeddings
        )

    return coleccion


coleccion = construir_coleccion()


@app.route("/buscar", methods=["POST"])
def buscar():
    data = request.get_json()
    pregunta = data.get("pregunta", "")
    fuente = data.get("fuente")

    embedding = modelo.encode([pregunta], normalize_embeddings=True).tolist()

    if fuente:
        resultado = coleccion.query(
            query_embeddings=embedding,
            n_results=3,
            where={"fuente": fuente}
        )
    else:
        resultado = coleccion.query(
            query_embeddings=embedding,
            n_results=3
        )

    items = []
    for doc, dist, meta in zip(resultado["documents"][0], resultado["distances"][0], resultado["metadatas"][0]):
        items.append({
            "fuente": meta.get("fuente", "desconocida"),
            "texto": doc,
            "distancia": float(dist)
        })

    return jsonify({
        "pregunta": pregunta,
        "resultados": items
    })


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
