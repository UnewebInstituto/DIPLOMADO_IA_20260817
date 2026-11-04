"""Fase 2 — Fragmentación (chunking) recursiva con solapamiento y contexto de sección.

Jerarquía de corte: párrafos -> líneas -> oraciones -> palabras. Cada fragmento
respeta `tamano` caracteres y arranca con el final del anterior (solape).
A cada fragmento se le asocia el encabezado de sección vigente ("3. Licencias...")
que luego se antepone al texto SOLO al vectorizar (mejora la recuperación).
"""
import re
import config
from ingesta import cargar_carpeta

_TITULO = re.compile(
    r"^(?:\d{1,2}(?:\.\d{1,2})*\.\s+|\d{1,2}\.\d{1,2}(?:\.\d{1,2})*\s+|#{1,4}\s+)[A-ZÁÉÍÓÚÑ¿¡0-9]")


def _titulo(linea):
    linea = linea.strip()
    return linea if len(linea) <= 120 and _TITULO.match(linea) else None


def _cortar_palabras(texto, maximo):
    partes, actual = [], ""
    for palabra in texto.split():
        while len(palabra) > maximo:                       # palabra gigante: corte duro
            if actual:
                partes.append(actual)
                actual = ""
            partes.append(palabra[:maximo])
            palabra = palabra[maximo:]
        if actual and len(actual) + 1 + len(palabra) > maximo:
            partes.append(actual)
            actual = palabra
        else:
            actual = f"{actual} {palabra}".strip()
    if actual:
        partes.append(actual)
    return partes


def _partir(texto, maximo):
    """Unidades de a lo sumo `maximo` caracteres, respetando la estructura natural."""
    unidades = []
    for parrafo in re.split(r"\n\s*\n", texto):
        parrafo = parrafo.strip()
        if not parrafo:
            continue
        if len(parrafo) <= maximo:
            unidades.append(parrafo)
            continue
        for linea in parrafo.split("\n"):
            linea = linea.strip()
            if not linea:
                continue
            if len(linea) <= maximo:
                unidades.append(linea)
                continue
            for oracion in re.split(r"(?<=[.!?;:])\s+", linea):
                if len(oracion) <= maximo:
                    unidades.append(oracion)
                else:
                    unidades.extend(_cortar_palabras(oracion, maximo))
    return unidades


def _cola(texto, n):
    """Últimos ~n caracteres, empezando en un límite de palabra."""
    if n <= 0:
        return ""
    if len(texto) <= n:
        return texto
    c = texto[-n:]
    m = re.search(r"\s", c)
    return c[m.end():] if m else c


def _ultimo_titulo(texto):
    ultimo = None
    for linea in texto.split("\n"):
        t = _titulo(linea)
        if t:
            ultimo = t
    return ultimo


def dividir_en_chunks(texto, tamano=800, solape=120):
    """Devuelve [{texto, seccion}]. `seccion` es el encabezado vigente del fragmento."""
    if tamano <= 2 * solape:
        raise ValueError("tamano debe ser mayor que el doble del solape")
    maximo = tamano - solape - 1          # garantiza len(chunk) <= tamano
    chunks, actual, sec_inicio, vigente = [], "", "", ""
    for u in _partir(texto, maximo):
        if actual and len(actual) + 1 + len(u) > tamano:
            chunks.append((actual, sec_inicio))
            cola = _cola(actual, solape)
            actual = f"{cola}\n{u}" if cola else u
            sec_inicio = vigente
        else:
            actual = f"{actual}\n{u}" if actual else u
        t = _titulo(u.split("\n")[0])
        if t:
            vigente = t
        for linea in u.split("\n")[1:]:                    # títulos dentro de un párrafo agrupado
            t2 = _titulo(linea)
            if t2:
                vigente = t2
    if actual:
        chunks.append((actual, sec_inicio))
    return [{"texto": c, "seccion": _ultimo_titulo(c) or s} for c, s in chunks]


def texto_para_embedding(chunk_texto, seccion):
    """Antepone la sección si el fragmento no la contiene (solo para vectorizar)."""
    if seccion and seccion not in chunk_texto:
        return f"{seccion}\n{chunk_texto}"
    return chunk_texto


def cfg_chunking(tamano=None, solape=None):
    return f"{tamano or config.CHUNK_TAMANO}-{solape if solape is not None else config.CHUNK_SOLAPE}-{config.CHUNK_VERSION}"


def preparar_chunks(docs, tamano=None, solape=None):
    """docs: [{fuente, pagina, texto}] -> [{id, texto, seccion, fuente, pagina, chunk}]"""
    tamano = tamano or config.CHUNK_TAMANO
    solape = config.CHUNK_SOLAPE if solape is None else solape
    resultado = []
    for d in docs:
        for i, c in enumerate(dividir_en_chunks(d["texto"], tamano, solape)):
            resultado.append({
                "id": f"{d['fuente']}::p{d['pagina']:03d}::{i:03d}",
                "texto": c["texto"], "seccion": c["seccion"] or "",
                "fuente": d["fuente"], "pagina": d["pagina"], "chunk": i,
            })
    return resultado


def chunks_de_carpeta(carpeta=None, tamano=None, solape=None):
    return preparar_chunks(cargar_carpeta(carpeta or config.DIR_DOCS), tamano, solape)
