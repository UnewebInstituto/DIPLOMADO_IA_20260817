"""Fase 6 — Recuperación: vectorial, léxica (BM25), híbrida (RRF) y re-ranking."""
import logging, re, unicodedata
from rank_bm25 import BM25Plus   # IDF siempre positivo (BM25Okapi da 0 a términos en la mitad del corpus)
import config

log = logging.getLogger(__name__)

STOP = set("""a al algo ante con contra cual cuales cuando cuanto cuantos cuanta cuantas como de del desde donde el
ella ellos en entre es esta este esto estos fue ha hay la las le les lo los mas me mi mis muy ni no nos o para pero
por que se si sin sobre su sus te tiene tienen todo tu tus un una unos unas y ya debo debe deben puedo puede son ser
cada hay""".split())


def normalizar(texto):
    t = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in t if not unicodedata.combining(c)).lower()


def tokenizar(texto):
    return [w for w in re.findall(r"\w+", normalizar(texto)) if w not in STOP]


def rrf(listas_de_ids, k=60):
    """Reciprocal Rank Fusion: puntaje(d) = Σ 1 / (k + posición)."""
    puntajes = {}
    for lista in listas_de_ids:
        for pos, i in enumerate(lista, start=1):
            puntajes[i] = puntajes.get(i, 0.0) + 1.0 / (k + pos)
    return puntajes


def _frag(i, texto, meta, **extra):
    f = {"id": i, "texto": texto, "fuente": meta["fuente"], "pagina": meta["pagina"],
         "seccion": meta.get("seccion", ""), "distancia": None, "score_bm25": None,
         "score_rrf": None, "score_rerank": None}
    f.update(extra)
    return f


class Reranker:
    """Cross-encoder cargado de forma tardía (la primera vez descarga el modelo)."""
    def __init__(self, modelo=None):
        self.modelo = modelo or config.RERANK_MODELO
        self._m = None

    def reordenar(self, pregunta, frags):
        if self._m is None:
            from sentence_transformers import CrossEncoder
            self._m = CrossEncoder(self.modelo)
        puntajes = self._m.predict([(pregunta, f["texto"]) for f in frags])
        for f, p in zip(frags, puntajes):
            f["score_rerank"] = float(p)
        return sorted(frags, key=lambda f: f["score_rerank"], reverse=True)


class Recuperador:
    def __init__(self, almacen, embedder, reranker=None, rrf_k=None):
        self.almacen, self.embedder = almacen, embedder
        self.reranker = reranker
        self.rrf_k = rrf_k or config.RRF_K
        self._bm25 = None

    def invalidar(self):
        """Llamar tras sincronizar: el índice BM25 se reconstruye en la próxima búsqueda."""
        self._bm25 = None

    def _preparar_bm25(self):
        if self._bm25 is None:
            d = self.almacen.todos()
            self._ids, self._docs, self._metas = d["ids"], d["documents"], d["metadatas"]
            corpus = [tokenizar(m.get("seccion", "") + " " + t) for t, m in zip(self._docs, self._metas)]
            self._bm25 = BM25Plus(corpus) if corpus else False
        return self._bm25

    def vectorial(self, pregunta, n):
        if self.almacen.contar() == 0:
            return []
        res = self.almacen.consultar(self.embedder.consulta(pregunta), n)
        return [_frag(r["id"], r["texto"], r["meta"], distancia=r["distancia"]) for r in res]

    def lexica(self, pregunta, n):
        bm25 = self._preparar_bm25()
        tokens = tokenizar(pregunta)
        if not bm25 or not tokens:
            return []
        puntajes = bm25.get_scores(tokens)
        orden = sorted(range(len(puntajes)), key=lambda i: puntajes[i], reverse=True)[:n]
        return [_frag(self._ids[i], self._docs[i], self._metas[i], score_bm25=float(puntajes[i]))
                for i in orden if puntajes[i] > 0]          # sin coincidencia léxica no se aporta ruido

    def hibrida(self, pregunta, n):
        lv, ll = self.vectorial(pregunta, n), self.lexica(pregunta, n)
        pun = rrf([[f["id"] for f in lv], [f["id"] for f in ll]], self.rrf_k)
        fusion = {}
        for f in lv + ll:
            if f["id"] not in fusion:
                fusion[f["id"]] = f
            else:                                               # combina datos de ambos métodos
                for campo in ("distancia", "score_bm25"):
                    if fusion[f["id"]][campo] is None:
                        fusion[f["id"]][campo] = f[campo]
        for i, f in fusion.items():
            f["score_rrf"] = pun[i]
        return sorted(fusion.values(), key=lambda f: f["score_rrf"], reverse=True)

    def buscar(self, pregunta, k=None, modo=None, rerank=None, candidatos=None):
        """Devuelve (fragmentos, info). Si el re-ranking falla, degrada sin él y lo informa."""
        k = k or config.K
        modo = modo or config.MODO
        rerank = config.USAR_RERANKER if rerank is None else rerank
        candidatos = max(candidatos or config.CANDIDATOS, k)
        if modo == "vectorial":
            lista = self.vectorial(pregunta, candidatos if rerank else k)
        else:
            lista = self.hibrida(pregunta, candidatos)
        info = {"modo": modo, "rerank": False, "aviso": None}
        if rerank and len(lista) > 1:
            try:
                if self.reranker is None:
                    self.reranker = Reranker()
                lista = self.reranker.reordenar(pregunta, lista)
                info["rerank"] = True
            except Exception as e:                              # sin red / sin memoria / modelo inexistente
                log.warning("Re-ranking no disponible: %s", e)
                info["aviso"] = f"Re-ranking no disponible ({e.__class__.__name__}); se usó el orden original."
        return lista[:k], info
