import re, pathlib
from pypdf import PdfReader

def cargar_documentos(carpeta):
    """Devuelve una lista de dicts {fuente, pagina, texto} para PDF, TXT y 
MD."""
    docs = []
    for ruta in sorted(pathlib.Path(carpeta).glob("*")):
        if ruta.suffix.lower() == ".pdf":
            lector = PdfReader(str(ruta))
            for n, pag in enumerate(lector.pages, start=1):
                texto = limpiar(pag.extract_text() or "")
                if texto:
                    docs.append({"fuente": ruta.name, "pagina": n, "texto": 
texto})
        elif ruta.suffix.lower() in (".txt", ".md"):
            texto = limpiar(ruta.read_text(encoding="utf-8"))
            docs.append({"fuente": ruta.name, "pagina": 1, "texto": texto})
    return docs

def limpiar(texto):
    texto = re.sub(r"-\n(\w)", r"\1", texto)       # une palabras cortadas 
    texto = re.sub(r"[ \t]+", " ", texto)
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip()

def dividir_en_chunks(texto, tamano=800, solape=120):
    parrafos = [p.strip() for p in re.split(r"\n\s*\n", texto) if p.strip()]
    chunks, actual = [], ""
    for p in parrafos:
        if len(actual) + len(p) + 1 <= tamano:
            actual = f"{actual}\n{p}".strip()
        else:
            if actual:
                chunks.append(actual)
            cola = actual[-solape:] if actual else ""
            actual = f"{cola}\n{p}".strip()
    if actual:
        chunks.append(actual)
    return chunks

def preparar_chunks(carpeta, tamano=800, solape=120):
    """Devuelve una lista de dicts {id, texto, fuente, pagina, chunk}."""
    resultado = []
    for d in cargar_documentos(carpeta):
        for i, c in enumerate(dividir_en_chunks(d["texto"], tamano, solape)):
            resultado.append({
                "id": f"{d['fuente']}::p{d['pagina']:03d}::{i:03d}",
                "texto": c, "fuente": d["fuente"],
                "pagina": d["pagina"], "chunk": i,
            })
    return resultado