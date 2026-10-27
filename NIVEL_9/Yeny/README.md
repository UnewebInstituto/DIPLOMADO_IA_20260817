# Búsqueda semántica de manuales PDF

Este proyecto extrae texto de archivos PDF, divide el contenido en fragmentos, genera embeddings con SentenceTransformers y almacena los resultados en ChromaDB para consultas semánticas.

## Requisitos

```bash
pip install -r requirements.txt
```

## Uso

### Indexar PDFs

```bash
python main.py --reindex
```

### Consultar

```bash
python main.py --query "¿Cómo recupero mi contraseña?" --source manual_ti.pdf --top-k 3
```

## Estructura

- `main.py`: lógica principal
- `chroma_db/`: base de datos persistente de ChromaDB
- `manual_rrhh.pdf`: archivo de ejemplo
- `manual_ti.pdf`: archivo de ejemplo
