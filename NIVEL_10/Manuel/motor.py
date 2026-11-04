"""Orquestador del pipeline RAG: sincronización -> recuperación -> generación."""
import time
import config
import sincronizacion
from almacen import Almacen
from generacion import LLM, FRASE_ABSTENCION, es_abstencion, generar_respuesta, reescribir_consulta
from recuperacion import Recuperador


class RAG:
    def __init__(self, embedder=None, llm=None, reranker=None, almacen=None):
        if embedder is None:
            from embedder import Embedder
            embedder = Embedder(config.EMB_MODELO)
        self.embedder = embedder
        modelo = getattr(embedder, "modelo", config.EMB_MODELO)
        self.almacen = almacen or Almacen(config.DIR_DB, config.nombre_coleccion(modelo))
        self.recuperador = Recuperador(self.almacen, self.embedder, reranker=reranker)
        self._llm = llm

    @property
    def llm(self):
        if self._llm is None:
            self._llm = LLM()
        return self._llm

    # --- Indexado ---
    def sincronizar(self, carpeta=None):
        rep = sincronizacion.sincronizar(self.almacen, self.embedder, carpeta)
        self.recuperador.invalidar()
        return rep

    def reindexar(self, carpeta=None):
        """Reconstruye todo desde cero (necesario al cambiar de modelo de embeddings)."""
        self.almacen.reiniciar()
        self.recuperador.invalidar()
        return self.sincronizar(carpeta)

    def estado(self):
        metas = self.almacen.todos()["metadatas"] if self.almacen.contar() else []
        fuentes = {}
        for m in metas:
            fuentes[m["fuente"]] = fuentes.get(m["fuente"], 0) + 1
        return {"chunks": len(metas), "fuentes": fuentes, "coleccion": self.almacen.nombre,
                "modelo_emb": getattr(self.embedder, "modelo", "?")}

    # --- Consulta ---
    def recuperar(self, pregunta, k=None, modo=None, rerank=None):
        return self.recuperador.buscar(pregunta, k, modo, rerank, config.CANDIDATOS)

    def responder(self, pregunta, k=None, modo=None, rerank=None, historial=None, reescribir=False):
        t0 = time.time()
        consulta = reescribir_consulta(self.llm, pregunta, historial) if (reescribir and historial) else pregunta
        frags, info = self.recuperar(consulta, k, modo, rerank)
        t1 = time.time()
        respuesta = generar_respuesta(self.llm, consulta, frags) if frags else FRASE_ABSTENCION
        t2 = time.time()
        return {"respuesta": respuesta, "fragmentos": frags, "consulta": consulta,
                "abstencion": es_abstencion(respuesta), "modo": info["modo"],
                "rerank": info["rerank"], "aviso": info["aviso"],
                "tiempos": {"recuperacion": round(t1 - t0, 2), "generacion": round(t2 - t1, 2)}}
