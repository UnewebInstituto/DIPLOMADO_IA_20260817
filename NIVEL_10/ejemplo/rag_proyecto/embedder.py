"""Fase 3 — Embeddings con sentence-transformers (maneja los prefijos de los modelos E5)."""
import logging
import config

log = logging.getLogger(__name__)


class Embedder:
    def __init__(self, modelo=None):
        from sentence_transformers import SentenceTransformer   # import tardío: pesado
        self.modelo = modelo or config.EMB_MODELO
        self.m = SentenceTransformer(self.modelo)
        es_e5 = "e5" in self.modelo.lower()
        self.pref_consulta = "query: " if es_e5 else ""
        self.pref_doc = "passage: " if es_e5 else ""
        largo = getattr(self.m, "max_seq_length", None)
        if largo and config.CHUNK_TAMANO / 3.5 > largo:
            log.warning("El modelo trunca a %s tokens pero los chunks pueden tener ~%d. "
                        "Reduzca CHUNK_TAMANO o use otro modelo.", largo, int(config.CHUNK_TAMANO / 3.5))

    def documentos(self, textos, lote=32):
        if not textos:
            return []
        v = self.m.encode([self.pref_doc + t for t in textos], normalize_embeddings=True,
                          batch_size=lote, show_progress_bar=len(textos) > 50)
        return v.tolist()

    def consulta(self, texto):
        return self.m.encode([self.pref_consulta + texto], normalize_embeddings=True)[0].tolist()
