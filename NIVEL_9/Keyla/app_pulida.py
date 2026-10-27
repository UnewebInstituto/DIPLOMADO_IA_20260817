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
    try:
        ids_actuales = col.get()["ids"]
        if ids_actuales:
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
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Buscador de manuales</title>
  <style>
    :root {
      --bg: #f4f7fb;
      --card: #ffffff;
      --text: #1f2937;
      --muted: #6b7280;
      --primary: #2563eb;
      --primary-dark: #1d4ed8;
      --border: #e5e7eb;
      --shadow: 0 10px 25px rgba(15, 23, 42, 0.08);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: linear-gradient(135deg, #eef5ff, var(--bg));
      font-family: Arial, sans-serif;
      color: var(--text);
    }
    .container {
      max-width: 1100px;
      margin: 40px auto;
      padding: 20px;
    }
    .card {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 18px;
      box-shadow: var(--shadow);
      padding: 28px;
    }
    h1 {
      margin-top: 0;
      font-size: 2rem;
    }
    form {
      display: flex;
      gap: 12px;
      margin-bottom: 18px;
      flex-wrap: wrap;
    }
    input {
      flex: 1 1 500px;
      min-width: 240px;
      padding: 14px 16px;
      border: 1px solid var(--border);
      border-radius: 10px;
      font-size: 1rem;
    }
    button {
      border: none;
      background: var(--primary);
      color: white;
      padding: 14px 20px;
      font-size: 1rem;
      border-radius: 10px;
      cursor: pointer;
      transition: background 0.2s ease;
    }
    button:hover { background: var(--primary-dark); }
    .status {
      color: var(--muted);
      font-size: 0.9rem;
      margin-bottom: 14px;
    }
    .result {
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 16px;
      margin-top: 16px;
      background: #fafcff;
    }
    .meta {
      font-size: 0.8rem;
      color: var(--muted);
      margin-bottom: 8px;
    }
    .texto {
      line-height: 1.6;
      white-space: pre-wrap;
      margin: 0;
    }
    .empty {
      color: var(--muted);
      margin-top: 20px;
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="card">
      <h1>Buscador de manuales</h1>
      <form id="searchForm">
        <input id="pregunta" type="text" placeholder="Ejemplo: ¿Cómo recupero mi contraseña?" />
        <button type="submit">Buscar</button>
      </form>
      <div class="status" id="status">Listo para consultar.</div>
      <div id="resultado"></div>
    </div>
  </div>

  <script>
    const form = document.getElementById('searchForm');
    const preguntaInput = document.getElementById('pregunta');
    const status = document.getElementById('status');
    const resultado = document.getElementById('resultado');

    form.addEventListener('submit', async function (event) {
      event.preventDefault();
      const pregunta = preguntaInput.value.trim();

      if (!pregunta) {
        resultado.innerHTML = '<div class="empty">Escribe una pregunta para buscar.</div>';
        return;
      }

      status.textContent = 'Consultando...';
      resultado.innerHTML = '';

      try {
        const res = await fetch('/buscar', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ pregunta })
        });

        if (!res.ok) {
          throw new Error('Error en la búsqueda');
        }

        const data = await res.json();

        if (!data.resultados || data.resultados.length === 0) {
          resultado.innerHTML = '<div class="empty">No se encontraron coincidencias.</div>';
          status.textContent = 'Consulta finalizada.';
          return;
        }

        data.resultados.forEach((item, idx) => {
          const div = document.createElement('div');
          div.className = 'result';
          div.innerHTML = `
            <div class="meta">Resultado ${idx + 1} · ${item.fuente} · Distancia: ${item.distancia.toFixed(4)}</div>
            <p class="texto">${item.texto}</p>
          `;
          resultado.appendChild(div);
        });

        status.textContent = 'Consulta finalizada.';
      } catch (error) {
        status.textContent = 'Hubo un error al consultar.';
        resultado.innerHTML = '<div class="empty">Verifica que el backend esté ejecutándose.</div>';
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

    if not pregunta:
        return jsonify({"resultados": []})

    model = get_model()
    col = indexar_si_hace_falta()

    embedding = model.encode([pregunta], normalize_embeddings=True).tolist()
    resultado = col.query(query_embeddings=embedding, n_results=3)

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
