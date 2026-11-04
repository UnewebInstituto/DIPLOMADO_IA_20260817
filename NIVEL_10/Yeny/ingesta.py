"""Fase 1 — Ingesta: listar, leer y limpiar documentos (PDF, TXT, MD)."""
import collections, hashlib, logging, pathlib, re, unicodedata
from pypdf import PdfReader

log = logging.getLogger(__name__)
EXTENSIONES = {".pdf", ".txt", ".md"}


def listar_documentos(carpeta):
    """Devuelve {nombre_archivo: Path} de los documentos soportados."""
    carpeta = pathlib.Path(carpeta)
    if not carpeta.exists():
        return {}
    return {p.name: p for p in sorted(carpeta.iterdir())
            if p.is_file() and p.suffix.lower() in EXTENSIONES}


def hash_archivo(ruta):
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def limpiar(texto):
    texto = unicodedata.normalize("NFKC", texto)          # ligaduras: ﬁ -> fi
    texto = texto.replace("\r\n", "\n").replace("\r", "\n").replace("\x00", "")
    texto = re.sub(r"-\n(\w)", r"\1", texto)              # une palabras cortadas por guion
    texto = re.sub(r"[ \t]+", " ", texto)
    texto = re.sub(r" ?\n ?", "\n", texto)
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip()


def _clave_linea(linea):
    return re.sub(r"\d+", "#", linea.strip().lower())


def quitar_repetidos(paginas, minimo_paginas=3, proporcion=0.5):
    """Elimina encabezados y pies que se repiten en la mayoría de las páginas
    (ej.: 'Manual de TI — M-TI-2026-V4 Página 3 de 15')."""
    if len(paginas) < minimo_paginas:
        return paginas
    cuenta = collections.Counter()
    for p in paginas:
        cuenta.update({_clave_linea(l) for l in p.split("\n") if l.strip()})
    umbral = max(minimo_paginas, int(proporcion * len(paginas)))
    repetidas = {k for k, c in cuenta.items() if c >= umbral}
    return ["\n".join(l for l in p.split("\n") if _clave_linea(l) not in repetidas)
            for p in paginas]


def cargar_documento(ruta):
    """Devuelve [{fuente, pagina, texto}] de un archivo."""
    ruta = pathlib.Path(ruta)
    ext = ruta.suffix.lower()
    if ext == ".pdf":
        lector = PdfReader(str(ruta))
        crudas = [limpiar(p.extract_text() or "") for p in lector.pages]
        paginas = quitar_repetidos(crudas)
        docs = []
        vacias = 0
        for n, t in enumerate(paginas, start=1):
            t = limpiar(t)
            if t:
                docs.append({"fuente": ruta.name, "pagina": n, "texto": t})
            else:
                vacias += 1
        if vacias:
            log.warning("%s: %d página(s) sin texto (¿PDF escaneado? requiere OCR)", ruta.name, vacias)
        return docs
    if ext in (".txt", ".md"):
        try:
            bruto = ruta.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            bruto = ruta.read_text(encoding="latin-1")
        texto = limpiar(bruto)
        return [{"fuente": ruta.name, "pagina": 1, "texto": texto}] if texto else []
    return []


def cargar_carpeta(carpeta):
    docs = []
    for ruta in listar_documentos(carpeta).values():
        docs.extend(cargar_documento(ruta))
    return docs
