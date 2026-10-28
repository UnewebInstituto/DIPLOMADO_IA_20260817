from flask import Flask, request, jsonify, render_template_string
from pathlib import Path
import os

from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
import chromadb
from google import genai

app = Flask(__name__)

PDF_DIR = Path(r"C:\.Profesores\HENRY_DUQUE\DIPLOMADO_IA_20260817\NIVEL_9\Keyla")
DB_PATH = PDF_DIR / "chroma_db_gemini_assistant"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
GEMINI_MODEL = "gemini-3.5-flash-lite"
API_KEY = os.getenv("GOOGLE_API_KEY")

_model = None
_collection = None


def get_model():
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
            name="manuales_gemini_assistant",
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


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


def indexar_si_hace_falta(force: bool = False):
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
        embs = get_model().encode(documentos, normalize_embeddings=True).tolist()
        col.upsert(ids=ids, documents=documentos, metadatas=metadatos, embeddings=embs)

    return col


def buscar_contexto(pregunta: str, n_results: int = 5):
    col = indexar_si_hace_falta()
    embedding = get_model().encode([pregunta], normalize_embeddings=True).tolist()
    resultado = col.query(query_embeddings=embedding, n_results=n_results)

    items = []
    for doc, meta, dist in zip(resultado["documents"][0], resultado["metadatas"][0], resultado["distances"][0]):
        items.append({
            "texto": doc,
            "fuente": meta.get("fuente", "Desconocida"),
            "chunk": meta.get("chunk", 0),
            "distancia": float(dist),
        })
    return items


def construir_prompt(pregunta: str, contexto: list) -> str:
    contexto_formateado = "\n\n---\n\n".join(
        f"Fuente: {item['fuente']}\nChunk: {item['chunk']}\n\n{item['texto']}"
        for item in contexto
    )

    return f"""
Eres un asistente experto que responde únicamente con base en el contexto proporcionado.

Instrucciones:
- Responde con un tono claro y profesional.
- Usa evidencia del contexto y cita la fuente de cada afirmación.
- Si el contexto no contiene la respuesta, dilo sin inventar.
- No menciones que estás usando una IA ni un modelo.
- Si hay varios documentos, menciona los que respaldan la respuesta.

Pregunta del usuario:
{pregunta}

Contexto recuperado:
{contexto_formateado}

Respuesta:
""".strip()


def llamar_gemini(prompt: str):
    if not API_KEY:
        return "No hay clave de API de Gemini configurada. Define la variable GOOGLE_API_KEY y reinicia la app."

    try:
        client = genai.Client(api_key=API_KEY)
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
        )
        return response.text
    except Exception as exc:
        return f"Error al consultar Gemini: {exc}"


HTML = """
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Asistente RAG con Gemini</title>
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
      flex-wrap: wrap;
      margin-bottom: 18px;
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
    }
    button:hover { background: var(--primary-dark); }
    .resumen {
      color: var(--muted);
      font-size: 0.9rem;
      margin-bottom: 14px;
    }
    .respuesta {
      background: #f8fbff;
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 18px;
      margin-top: 18px;
      white-space: pre-wrap;
      line-height: 1.6;
    }
    .evidencias {
      margin-top: 22px;
    }
    .evidencia {
      background: white;
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 14px;
      margin-top: 12px;
    }
    .meta {
      color: var(--muted);
      font-size: 0.8rem;
      margin-bottom: 8px;
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="card">
      <h1>Asistente RAG con Gemini</h1>
      <form id="formPregunta">
        <input id="pregunta" type="text" placeholder="Ejemplo: ¿Cómo recupero mi contraseña?" />
        <button type="submit">Consultar</button>
      </form>
      <div class="resumen" id="status">Listo para consultar.</div>
      <div id="resultado"></div>
    </div>
  </div>

  <script>
    const form = document.getElementById('formPregunta');
    const preguntaInput = document.getElementById('pregunta');
    const status = document.getElementById('status');
    const resultado = document.getElementById('resultado');

    form.addEventListener('submit', async function (event) {
      event.preventDefault();
      const pregunta = preguntaInput.value.trim();

      if (!pregunta) {
        resultado.innerHTML = '<div class="respuesta">Escribe una pregunta para consultar.</div>';
        return;
      }

      status.textContent = 'Consultando evidencia y generando respuesta...';
      resultado.innerHTML = '';

      try {
        const res = await fetch('/buscar', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ pregunta })
        });

        const data = await res.json();

        if (!data.respuesta) {
          resultado.innerHTML = '<div class="respuesta">No se pudo generar la respuesta.</div>';
          status.textContent = 'Consulta finalizada.';
          return;
        }

        const respuestaDiv = document.createElement('div');
        respuestaDiv.className = 'respuesta';
        respuestaDiv.textContent = data.respuesta;
        resultado.appendChild(respuestaDiv);

        const evidenceTitle = document.createElement('div');
        evidenceTitle.className = 'resumen';
        evidenceTitle.textContent = 'Evidencia recuperada';
        resultado.appendChild(evidenceTitle);

        if (data.contexto && data.contexto.length) {
          data.contexto.forEach((item, idx) => {
            const div = document.createElement('div');
            div.className = 'evidencia';
            div.innerHTML = `
              <div class="meta">Evidencia ${idx + 1} · ${item.fuente} · Distancia: ${item.distancia.toFixed(4)}</div>
              <div>${item.texto}</div>
            `;
            resultado.appendChild(div);
          });
        }

        status.textContent = 'Consulta finalizada.';
      } catch (error) {
        status.textContent = 'Error al consultar.';
        resultado.innerHTML = '<div class="respuesta">Verifica la API key y el servicio de Gemini.</div>';
      }
    });
  </script>
</body>
</html>
"""


@app.route('/')
def index():
    return render_template_string(HTML)


@app.route('/health')
def health():
    return jsonify({"status": "ok"})


@app.route('/buscar', methods=['POST'])
def buscar():
    data = request.get_json(force=True) or {}
    pregunta = (data.get('pregunta') or '').strip()
    if not pregunta:
        return jsonify({"respuesta": "", "contexto": []})

    contexto = buscar_contexto(pregunta, n_results=5)
    prompt = construir_prompt(pregunta, contexto)
    respuesta = llamar_gemini(prompt)

    return jsonify({
        "pregunta": pregunta,
        "respuesta": respuesta,
        "contexto": contexto,
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
