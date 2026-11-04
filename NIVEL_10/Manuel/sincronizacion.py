"""Fase 5 — Indexado y actualización incremental.

Agrega, actualiza y elimina documentos según el estado de la carpeta, sin reindexar todo:
 - hash SHA-256 del archivo: si no cambió (y el chunking tampoco), se omite;
 - IDs deterministas (archivo::pPPP::NNN) + upsert;
 - al modificar un archivo se borran sus chunks viejos (evita huérfanos);
 - al eliminar un archivo se borran todos sus chunks.
"""
import datetime, logging
import config
from chunking import cfg_chunking, preparar_chunks, texto_para_embedding
from ingesta import cargar_documento, hash_archivo, listar_documentos

log = logging.getLogger(__name__)


def sincronizar(almacen, embedder, carpeta=None, tamano=None, solape=None):
    carpeta = carpeta or config.DIR_DOCS
    cfg = cfg_chunking(tamano, solape)
    previos = almacen.estado_fuentes()
    archivos = listar_documentos(carpeta)
    rep = {"agregados": [], "actualizados": [], "eliminados": [], "sin_cambios": [], "sin_texto": [], "chunks": 0}

    for fuente in sorted(set(previos) - set(archivos)):
        almacen.borrar_fuente(fuente)
        rep["eliminados"].append(fuente)

    for nombre, ruta in archivos.items():
        h = hash_archivo(ruta)
        if previos.get(nombre) == {(h, cfg)}:
            rep["sin_cambios"].append(nombre)
            continue
        chunks = preparar_chunks(cargar_documento(ruta), tamano, solape)
        if not chunks:
            if nombre in previos:
                almacen.borrar_fuente(nombre)
            rep["sin_texto"].append(nombre)
            continue
        # 1) calcular vectores primero: si falla, el índice anterior queda intacto
        vectores = embedder.documentos([texto_para_embedding(c["texto"], c["seccion"]) for c in chunks])
        fecha = datetime.date.fromtimestamp(ruta.stat().st_mtime).isoformat()
        metas = [{"fuente": c["fuente"], "pagina": c["pagina"], "chunk": c["chunk"],
                  "seccion": c["seccion"], "hash_doc": h, "version": h[:8],
                  "chunk_cfg": cfg, "fecha": fecha} for c in chunks]
        # 2) limpiar chunks viejos y escribir los nuevos
        if nombre in previos:
            almacen.borrar_fuente(nombre)
        almacen.upsert([c["id"] for c in chunks], [c["texto"] for c in chunks], vectores, metas)
        rep["actualizados" if nombre in previos else "agregados"].append(nombre)
        rep["chunks"] += len(chunks)
        log.info("Indexado %s (%d chunks)", nombre, len(chunks))
    return rep
