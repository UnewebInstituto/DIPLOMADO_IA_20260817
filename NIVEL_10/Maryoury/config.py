"""Configuración central del proyecto.

Todo se puede sobrescribir con variables de entorno o con un archivo .env
(ver .env.example). No requiere librerías extra para leer el .env.
"""
import os, pathlib, re

RAIZ = pathlib.Path(__file__).resolve().parent


def _cargar_env():
    ruta = RAIZ / ".env"
    if not ruta.exists():
        return
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        clave, valor = linea.split("=", 1)
        os.environ.setdefault(clave.strip(), valor.strip().strip('"').strip("'"))


_cargar_env()


def _e(nombre, defecto):
    return os.environ.get(nombre, defecto)


# --- Rutas ---
DIR_DOCS = RAIZ / _e("DIR_DOCS", "documentos")
DIR_DB = RAIZ / _e("DIR_DB", "chroma_db")
RUTA_REGISTRO = RAIZ / _e("RUTA_REGISTRO", "logs/registro.jsonl")

# --- Fragmentación (chunking) ---
CHUNK_TAMANO = int(_e("CHUNK_TAMANO", "800"))     # caracteres
CHUNK_SOLAPE = int(_e("CHUNK_SOLAPE", "120"))     # caracteres
CHUNK_VERSION = "v2"                              # cambie si modifica el algoritmo

# --- Embeddings ---
# e5-small admite 512 tokens (el MiniLM del curso trunca en 128). Para volver al
# modelo del curso: EMB_MODELO=paraphrase-multilingual-MiniLM-L12-v2
EMB_MODELO = _e("EMB_MODELO", "intfloat/multilingual-e5-small")

# --- Recuperación ---
K = int(_e("K", "4"))
MODO = _e("MODO", "hibrida")                      # "hibrida" | "vectorial"
CANDIDATOS = int(_e("CANDIDATOS", "20"))          # candidatos por método antes de fusionar/re-rankear
RRF_K = int(_e("RRF_K", "60"))
USAR_RERANKER = _e("USAR_RERANKER", "1") == "1"
RERANK_MODELO = _e("RERANK_MODELO", "BAAI/bge-reranker-v2-m3")   # ~2 GB; más liviano: cross-encoder/mmarco-mMiniLMv2-L12-H384-v1

# --- Generación ---
LLM_PROVEEDOR = _e("LLM_PROVEEDOR", "ollama")     # "ollama" | "gemini"
OLLAMA_MODELO = _e("OLLAMA_MODELO", "llama3")
OLLAMA_HOST = _e("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_NUM_CTX = int(_e("OLLAMA_NUM_CTX", "8192"))
GEMINI_MODELO = _e("GEMINI_MODELO", "gemini-3.5-flash-lite")   # verificar ID vigente
TEMPERATURA = float(_e("TEMPERATURA", "0.2"))
MAX_TOKENS = int(_e("MAX_TOKENS", "1000"))


def nombre_coleccion(modelo):
    """Una colección por modelo de embeddings (los vectores de modelos distintos no se mezclan)."""
    slug = re.sub(r"[^a-z0-9]+", "_", modelo.lower()).strip("_")
    return ("conocimiento_" + slug)[:63].strip("_-.")
