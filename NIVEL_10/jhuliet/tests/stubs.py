"""Sustitutos livianos para probar el pipeline sin descargar modelos ni usar un LLM."""
import re, zlib


class StubEmbedder:
    modelo = "stub"

    def _vec(self, texto, dim=256):
        v = [0.0] * dim
        for w in re.findall(r"\w+", texto.lower()):
            v[zlib.crc32(w.encode()) % dim] += 1.0
        n = sum(x * x for x in v) ** 0.5 or 1.0
        return [x / n for x in v]

    def documentos(self, textos):
        return [self._vec(t) for t in textos]

    def consulta(self, texto):
        return self._vec(texto)


class StubLLM:
    def __init__(self, respuesta="Respuesta de prueba [1]."):
        self.respuesta, self.llamadas = respuesta, []

    def generar(self, sistema, usuario, **kw):
        self.llamadas.append((sistema, usuario, kw))
        return self.respuesta


class StubReranker:
    """Invierte el orden: permite comprobar que el re-ranking se aplica."""
    def reordenar(self, pregunta, frags):
        for i, f in enumerate(reversed(frags)):
            f["score_rerank"] = float(i)
        return list(reversed(frags))
