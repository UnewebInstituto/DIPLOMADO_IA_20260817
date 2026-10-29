from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template_string, request

from main import get_embedding_model, rag_answer

app = Flask(__name__)
ROOT_DIR = Path(__file__).resolve().parent
load_dotenv(ROOT_DIR / ".env")
os.environ.setdefault("GEMINI_MODEL", "gemini-3.5-flash-lite")

HTML_PAGE = """
<!doctype html>
<html lang="es">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Asistente RAG</title>
    <style>
      :root {
        --bg: #111827;
        --panel: #1f2937;
        --panel-alt: #0f172a;
        --text: #e5e7eb;
        --muted: #9ca3af;
        --accent: #60a5fa;
        --success: #34d399;
        --border: rgba(148, 163, 184, 0.2);
      }
      * { box-sizing: border-box; }
      body {
        margin: 0;
        font-family: Arial, sans-serif;
        background: linear-gradient(135deg, #0f172a, #111827 40%, #1e293b);
        color: var(--text);
      }
      .container {
        max-width: 1100px;
        margin: 40px auto;
        padding: 24px;
      }
      .header {
        margin-bottom: 22px;
      }
      .title {
        font-size: 2rem;
        margin: 0 0 8px;
      }
      .subtitle {
        color: var(--muted);
        margin: 0;
      }
      .chat {
        background: rgba(15, 23, 42, 0.9);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 18px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.25);
      }
      .messages {
        min-height: 240px;
        max-height: 420px;
        overflow-y: auto;
        margin-bottom: 18px;
        padding-right: 10px;
      }
      .msg {
        margin-bottom: 16px;
        padding: 14px 16px;
        border-radius: 12px;
        line-height: 1.5;
      }
      .user {
        background: rgba(96, 165, 250, 0.12);
        border-left: 3px solid var(--accent);
        margin-left: 30px;
      }
      .assistant {
        background: rgba(52, 211, 153, 0.08);
        border-left: 3px solid var(--success);
        margin-right: 30px;
      }
      .citations {
        margin-top: 14px;
        padding-top: 12px;
        border-top: 1px solid var(--border);
      }
      .citation {
        background: rgba(148, 163, 184, 0.08);
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 10px 12px;
        margin-top: 8px;
      }
      form {
        display: grid;
        grid-template-columns: 1fr auto;
        gap: 12px;
      }
      input, button {
        font: inherit;
        border-radius: 10px;
      }
      input {
        width: 100%;
        padding: 14px 16px;
        border: 1px solid var(--border);
        background: rgba(15, 23, 42, 0.95);
        color: var(--text);
      }
      button {
        padding: 14px 20px;
        background: var(--accent);
        border: none;
        color: #0f172a;
        font-weight: bold;
        cursor: pointer;
      }
      .status {
        color: var(--muted);
        font-size: 0.95rem;
        margin-top: 12px;
      }
      .evidence-title {
        font-weight: bold;
        margin-bottom: 6px;
      }
      @media (max-width: 700px) {
        form { grid-template-columns: 1fr; }
      }
    </style>
  </head>
  <body>
    <div class="container">
      <div class="header">
        <h1 class="title">Asistente documental RAG</h1>
        <p class="subtitle">Responde con base en los PDFs indexados y cita la evidencia documental.</p>
      </div>

      <div class="chat">
        <div class="messages" id="messages">
          <div class="msg assistant">
            Hola. Puedes hacerme preguntas sobre los manuales o documentos indexados y te responderé con evidencia.
          </div>
        </div>

        <form id="chat-form">
          <input id="question" type="text" placeholder="Ejemplo: ¿Cómo recupero mi contraseña?" required>
          <button type="submit">Enviar</button>
        </form>
        <div class="status" id="status">Listo para consultar.</div>
      </div>
    </div>

    <script>
      const form = document.getElementById('chat-form');
      const input = document.getElementById('question');
      const messages = document.getElementById('messages');
      const status = document.getElementById('status');
      const submitButton = form.querySelector('button[type="submit"]');

      function setLoading(isLoading) {
        submitButton.disabled = isLoading;
        submitButton.textContent = isLoading ? 'Consultando...' : 'Enviar';
        input.disabled = isLoading;
      }

      function addMessage(role, text, citations = []) {
        const item = document.createElement('div');
        item.className = 'msg ' + role;
        let html = '<div>' + text.replace(/\n/g, '<br>') + '</div>';
        if (citations && citations.length) {
          html += '<div class="citations">';
          html += '<div class="evidence-title">Evidencia documental:</div>';
          citations.forEach((c) => {
            html += '<div class="citation">';
            html += '<strong>' + (c.fuente || 'Fuente') + '</strong> | Página ' + (c.pagina || '?') + '<br>';
            html += '<small>' + (c.texto || '').replace(/\n/g, '<br>') + '</small>';
            html += '</div>';
          });
          html += '</div>';
        }
        item.innerHTML = html;
        messages.appendChild(item);
        messages.scrollTop = messages.scrollHeight;
      }

      form.addEventListener('submit', async (event) => {
        event.preventDefault();
        const question = input.value.trim();
        if (!question) {
          status.textContent = 'Escribe una pregunta antes de enviar.';
          input.focus();
          return;
        }

        addMessage('user', question);
        input.value = '';
        status.textContent = 'Buscando en los documentos...';
        setLoading(true);

        try {
          const response = await fetch('/ask', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question })
          });
          const data = await response.json();

          if (!response.ok) {
            throw new Error(data.error || 'Error en la consulta');
          }

          addMessage('assistant', data.answer || 'No se pudo generar una respuesta.', data.citations || []);
          status.textContent = 'Respuesta generada con evidencia.';
        } catch (error) {
          addMessage('assistant', 'Ocurrió un error: ' + error.message);
          status.textContent = 'Hubo un problema al consultar el asistente.';
        } finally {
          setLoading(false);
          input.focus();
        }
      });
    </script>
  </body>
</html>
"""


@app.get("/")
def index():
    return render_template_string(HTML_PAGE)


@app.post("/ask")
def ask():
    data = request.get_json(silent=True) or {}
    question = (data.get("question") or "").strip()

    if not question:
        return jsonify({"error": "Debes enviar una pregunta."}), 400

    model = None
    try:
        model = get_embedding_model()
    except Exception:
        model = None

    os.environ.setdefault("GEMINI_MODEL", "gemini-3.5-flash-lite")
    result = rag_answer(question, top_k=5, model=model)
    return jsonify({
        "answer": result.get("answer", ""),
        "citations": result.get("citations", [])
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=False, threaded=True)
