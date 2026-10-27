from flask import Flask, request, jsonify, render_template_string
from pathlib import Path
import chromadb
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer

app = Flask(__name__)

PDF_DIR = Path(r"C:\.Profesores\HENRY_DUQUE\DIPLOMADO_IA_20260817\NIVEL_9\Keyla")
DB_PATH = PDF_DIR / "chroma_db"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

modelo = None
coleccion = None


def get_model():
    global modelo
    if modelo is None:
        print("Cargando modelo...")
        modelo = SentenceTransformer(MODEL_NAME)
    return modelo


def get_collection():
    global coleccion
    if coleccion is None:
        cliente = chromadb.PersistentClient(path=str(DB_PATH))
        coleccion = cliente.get_or_create_collection(
            name="manuales",
            metadata={"hnsw:space": "cosine"}
        )
    return coleccion


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


def indexar_si_hace_falta():
    col = get_collection()
    ids_actuales = col.get()["ids"]
    if ids_actuales:
        return col

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
        embeddings = get_model().encode(documentos, normalize_embeddings=True).tolist()
        col.upsert(
            ids=ids,
            documents=documentos,
            metadatas=metadatos,
            embeddings=embeddings
        )

    return col


HTML = """
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <title>Buscador de manuales</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 40px; background: #f5f7fb; }
    .card { max-width: 900px; margin: 0 auto; background: white; padding: 24px; border-radius: 14px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
    form { display: flex; gap: 10px; margin-bottom: 16px; flex-wrap: wrap; }
    input { flex: 1 1 420px; padding: 10px 14px; font-size: 16px; }
    button { background: #2563eb; color: white; border: none; border-radius: 8px; cursor: pointer; padding: 10px 14px; font-size: 16px; }
    .result { margin-top: 20px; border-top: 1px solid #ddd; padding-top: 16px; }
    .meta { color: #4b5563; font-size: 13px; }
    .status { color: #4b5563; margin-bottom: 12px; }
  </style>
</head>
<body>
  <div class="card">
    <h2>Buscador de manuales</h2>
    <form id="searchForm">
      <input id="pregunta" type="text" placeholder="Ejemplo: ¿Cómo recupero mi contraseña?" />
      <button type="submit">Buscar</button>
    </form>
    <div class="status" id="status">Listo para consultar.</div>
    <div id="resultado"></div>
  </div>

  <script>
    const form = document.getElementById('searchForm');
    const preguntaInput = document.getElementById('pregunta');
    const status = document.getElementById('status');
    const cont = document.getElementById('resultado');

    form.addEventListener('submit', async function (event) {
      event.preventDefault();
      const pregunta = preguntaInput.value.trim();
      if (!pregunta) {
        cont.innerHTML = '<p>Escribe una pregunta para buscar.</p>';
        return;
      }

      status.textContent = 'Consultando...';
      cont.innerHTML = '';

      try {
        const res = await fetch('/buscar', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ pregunta })
        });

        if (!res.ok) {
          throw new Error('Respuesta no válida');
        }

        const data = await res.json();

        if (!data.resultados || data.resultados.length === 0) {
          cont.innerHTML = '<p>No se encontraron coincidencias.</p>';
          status.textContent = 'Consulta finalizada.';
          return;
        }

        data.resultados.forEach((item, idx) => {
          const div = document.createElement('div');
          div.className = 'result';
          div.innerHTML = `
            <div class="meta">Resultado ${idx + 1} · ${item.fuente} · Distancia: ${item.distancia.toFixed(4)}</div>
            <p>${item.texto}</p>
          `;
          cont.appendChild(div);
        });

        status.textContent = 'Consulta finalizada.';
      } catch (error) {
        status.textContent = 'Hubo un error al consultar.';
        cont.innerHTML = '<p>Verifica que el backend esté ejecutándose.</p>';
      }
    });
  </script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/buscar", methods=["POST"])
def buscar():
    data = request.get_json(force=True) or {}
    pregunta = data.get("pregunta", "")

    model = get_model()
    col = indexar_si_hace_falta()

    embedding = model.encode([pregunta], normalize_embeddings=True).tolist()
    resultado = col.query(
        query_embeddings=embedding,
        n_results=3
    )

    items = []
    for doc, dist, meta in zip(resultado["documents"][0], resultado["distances"][0], resultado["metadatas"][0]):
        items.append({
            "fuente": meta.get("fuente", "Desconocida"),
            "texto": doc,
            "distancia": float(dist)
        })

    return jsonify({"pregunta": pregunta, "resultados": items})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
