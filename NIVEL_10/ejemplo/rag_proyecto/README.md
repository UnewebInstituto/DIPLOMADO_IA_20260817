# Asistente RAG sobre base de conocimiento propia (Nivel 9 — UNEWEB)

Pipeline completo: **ingesta → limpieza → chunking → embeddings → Chroma → búsqueda híbrida (BM25 + vectorial, RRF) →
re-ranking → generación con citas (Llama 3 en Ollama o Gemini) → interfaz Streamlit**, con actualización
incremental, registro de consultas y evaluación (dataset dorado, métricas y LLM como juez).

## Arquitectura

```
documentos/ ─► ingesta.py (PDF/TXT/MD, limpieza, quita encabezados/pies repetidos)
            ─► chunking.py (recursivo, 800 car., solape 120, sección vigente)
            ─► embedder.py (sentence-transformers; prefijos E5 automáticos)
            ─► almacen.py  (Chroma persistente, coseno) ◄─ sincronizacion.py (hash SHA-256, upsert, huérfanos)

Pregunta ─► [reescritura según historial] ─► recuperacion.py:
              vectorial ┐
              BM25      ┴─► RRF ─► re-ranking (cross-encoder) ─► top-k
          ─► generacion.py (prompt con <documentos>, citas [n], "No encontré esa información…")
          ─► app.py (Streamlit) / cli.py        registro.py ─► logs/registro.jsonl
```

| Archivo | Rol |
|---|---|
| `config.py` | Parámetros (variables de entorno o `.env`) |
| `motor.py` | Clase `RAG`: `sincronizar()`, `reindexar()`, `responder()` |
| `cli.py` | `sincronizar`, `reindexar`, `estado`, `preguntar`, `chat` |
| `app.py` | Interfaz Streamlit |
| `evaluacion/` | `construir_dataset.py`, `eval_recuperacion.py`, `eval_generacion.py` |
| `tests/` | 17 pruebas automáticas (no requieren modelos ni API) |

## Instalación

```bash
cd rag_proyecto
python -m venv venv
source venv/bin/activate              # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                  # opcional: ajuste modelos y parámetros
```

### Generación local con Ollama (Llama 3)

```bash
ollama pull llama3                    # ~4,7 GB
curl http://localhost:11434/api/tags  # verifica que el servidor responde
```

### Alternativa: Gemini

En `.env`: `LLM_PROVEEDOR=gemini` y `GEMINI_API_KEY=su_clave` (verifique el ID de modelo vigente en `GEMINI_MODELO`).

## Uso

```bash
python cli.py sincronizar             # indexa documentos/ (primera vez descarga el modelo de embeddings)
python cli.py estado
python cli.py preguntar "¿Cuál es la longitud mínima de la contraseña?"
streamlit run app.py                  # http://localhost:8501
```

Los documentos se pueden agregar, modificar y eliminar desde la barra lateral de la app (o copiando archivos a
`documentos/` y ejecutando `python cli.py sincronizar`). Solo se reprocesa lo que cambió.

## Evaluación (Práctica 4)

```bash
python evaluacion/construir_dataset.py       # (re)genera dataset.json con IDs de chunks reales
python evaluacion/eval_recuperacion.py --configs vectorial,hibrida,hibrida_rerank
python evaluacion/eval_generacion.py         # LLM como juez; genera resultados.json y diagnóstico
```

**Experimentos de la tabla (chunk 400/1200, otro modelo):** edite `.env` (`CHUNK_TAMANO=400`, `CHUNK_SOLAPE=60`;
o `EMB_MODELO=...`), ejecute `python cli.py reindexar` y luego `python evaluacion/construir_dataset.py` (los IDs
dependen del chunking) antes de evaluar. Para volver al modelo del curso: `EMB_MODELO=paraphrase-multilingual-MiniLM-L12-v2`.

Valide el juez a mano (mínimo 5 evaluaciones): es una herramienta de apoyo, no una verdad absoluta.

## Pruebas

```bash
python -m pytest tests -q
```

## Despliegue

- **Local / red interna:** `streamlit run app.py --server.address 0.0.0.0` y comparta `http://IP_DEL_EQUIPO:8501`.
- **Streamlit Community Cloud:** no puede ejecutar Ollama; use `LLM_PROVEEDOR=gemini` y guarde la clave en *Secrets*.
  Su disco es efímero: el índice se reconstruye al reiniciar.
- **Docker:** hay un `Dockerfile` de partida (sin probar). Con Ollama en el anfitrión use `OLLAMA_HOST=http://host.docker.internal:11434`.
- Datos de misión crítica: mantenga embeddings y LLM locales (Ollama) y no use el proveedor Gemini.

## Limitaciones conocidas

- El re-ranker por defecto (`BAAI/bge-reranker-v2-m3`, ~2 GB) es lento en CPU; desactívelo con `USAR_RERANKER=0`
  o use uno más liviano (`RERANK_MODELO`). Si no puede cargarse, la app sigue sin él y avisa.
- Llama 3 8B sigue peor que un modelo comercial las reglas de citas `[n]` y de abstención exacta.
- PDF escaneados (sin texto) requieren OCR: se omiten y se registra una advertencia.
- Sin control de acceso por usuario: todos ven todos los documentos.
- La reescritura de consulta añade una llamada al LLM por turno.
