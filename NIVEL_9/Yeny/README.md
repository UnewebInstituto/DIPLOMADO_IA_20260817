# Búsqueda semántica de manuales PDF con RAG en Gemini

Este proyecto extrae texto de archivos PDF, divide el contenido en fragmentos, genera embeddings con SentenceTransformers y almacena los resultados en ChromaDB para consultas semánticas. Además, puede integrar el contexto recuperado con Gemini para responder preguntas de negocio usando un LLM.

## Requisitos

```bash
pip install -r requirements.txt
```

## Configuración de Gemini

Antes de consultar con Gemini, define la clave API y el modelo a usar:

### PowerShell

```powershell
$env:GEMINI_API_KEY="tu_api_key_aqui"
$env:GEMINI_MODEL="gemini-3.5-flash"
```

### Bash / zsh

```bash
export GEMINI_API_KEY="tu_api_key_aqui"
export GEMINI_MODEL="gemini-3.5-flash"
```

## Uso

### Indexar PDFs

```bash
python main.py --reindex
```

### Consultar con recuperación semántica

```bash
python main.py --query "¿Cómo recupero mi contraseña?" --source manual_ti.pdf --top-k 3
```

### Consultar con respuesta generada por Gemini

```bash
python main.py --query "¿Cómo recupero mi contraseña?" --source manual_ti.pdf --top-k 5
```

### Interfaz web tipo asistente

```bash
python web_app.py
```

Luego abre tu navegador en:

```text
http://localhost:5000
```

La interfaz permite consultar los documentos indexados y muestra la respuesta junto con citas y referencias a la fuente documental.

Si `GEMINI_API_KEY` está configurada, la app mostrará también la respuesta generada por el modelo Gemini usando los fragmentos recuperados como contexto.

## Estructura

- `main.py`: lógica principal del RAG
- `web_app.py`: interfaz web estilo asistente
- `chroma_db/`: base de datos persistente de ChromaDB
- `manual_rrhh.pdf`: archivo de ejemplo
- `manual_ti.pdf`: archivo de ejemplo
