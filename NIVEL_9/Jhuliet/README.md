# Buscador semántico de PDFs

Este proyecto busca documentos PDF usando embeddings semánticos y ChromaDB. Está pensado para consultar manuales, políticas o documentación técnica en lenguaje natural.

## Funcionalidades

- Lectura de PDFs desde el directorio actual
- Extracción de texto con `pypdf`
- Segmentación de texto en chunks
- Generación de embeddings con `SentenceTransformer`
- Búsqueda semántica con `ChromaDB`
- Resumen de respuesta basado en los fragmentos más relevantes
- Interfaz web con Streamlit
- API REST con FastAPI

## Estructura

- `pdf_search_app.py`: lógica principal de extracción, indexación y búsqueda
- `streamlit_app.py`: interfaz web
- `api_app.py`: servicio REST
- `requirements.txt`: dependencias del proyecto

## Requisitos

Python 3.11+ recomendado.

## Instalación

```powershell
cd "C:\.Profesores\HENRY_DUQUE\DIPLOMADO_IA_20260817\NIVEL_9\Jhuliet"
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Ejecutar la interfaz web

```powershell
cd "C:\.Profesores\HENRY_DUQUE\DIPLOMADO_IA_20260817\NIVEL_9\Jhuliet"
.venv\Scripts\python.exe -m streamlit run streamlit_app.py
```

## Ejecutar la API

```powershell
cd "C:\.Profesores\HENRY_DUQUE\DIPLOMADO_IA_20260817\NIVEL_9\Jhuliet"
.venv\Scripts\python.exe api_app.py
```

## Consulta de ejemplo

```powershell
cd "C:\.Profesores\HENRY_DUQUE\DIPLOMADO_IA_20260817\NIVEL_9\Jhuliet"
.venv\Scripts\python.exe pdf_search_app.py --directory . --query "¿Cómo recupero mi contraseña?" --top-k 3
```

## Endpoints de la API

- `GET /health`
- `POST /reindex`
- `GET /search?query=...&top_k=5&source=manual_ti.pdf`

## Nota

El sistema usa un modelo multilingüe para búsquedas semánticas en español. El comportamiento mejora cuando el contenido de los PDFs está bien estructurado.
