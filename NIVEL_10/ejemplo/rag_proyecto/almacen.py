"""Fase 4 — Base de datos vectorial (Chroma persistente, distancia coseno)."""
import chromadb


class Almacen:
    def __init__(self, ruta_db, coleccion):
        self.nombre = coleccion
        self.cliente = chromadb.PersistentClient(path=str(ruta_db))
        self.col = self._abrir()

    def _abrir(self):
        return self.cliente.get_or_create_collection(self.nombre, metadata={"hnsw:space": "cosine"})

    def contar(self):
        return self.col.count()

    def upsert(self, ids, documentos, embeddings, metadatas, lote=500):
        for i in range(0, len(ids), lote):
            s = slice(i, i + lote)
            self.col.upsert(ids=ids[s], documents=documentos[s],
                            embeddings=embeddings[s], metadatas=metadatas[s])

    def borrar_fuente(self, fuente):
        self.col.delete(where={"fuente": fuente})

    def estado_fuentes(self):
        """{fuente: {(hash_doc, chunk_cfg), ...}} — más de un par indica una indexación incompleta."""
        estado = {}
        for m in self.col.get(include=["metadatas"])["metadatas"]:
            estado.setdefault(m["fuente"], set()).add((m.get("hash_doc"), m.get("chunk_cfg")))
        return estado

    def todos(self):
        return self.col.get(include=["documents", "metadatas"])

    def consultar(self, vector, n):
        n = min(n, self.contar())
        if n <= 0:
            return []
        r = self.col.query(query_embeddings=[vector], n_results=n)
        return [{"id": i, "texto": d, "meta": m, "distancia": s}
                for i, d, m, s in zip(r["ids"][0], r["documents"][0], r["metadatas"][0], r["distances"][0])]

    def reiniciar(self):
        try:
            self.cliente.delete_collection(self.nombre)
        except Exception:
            pass
        self.col = self._abrir()
