"""Observabilidad básica: un registro JSONL con cada consulta."""
import json, time
import config


def registrar(pregunta, salida, ruta=None):
    ruta = ruta or config.RUTA_REGISTRO
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta, "a", encoding="utf-8") as f:
        f.write(json.dumps({
            "fecha": time.strftime("%Y-%m-%d %H:%M:%S"),
            "pregunta": pregunta,
            "consulta_usada": salida.get("consulta"),
            "modo": salida.get("modo"), "rerank": salida.get("rerank"),
            "fuentes": [f"{x['fuente']}:p{x['pagina']}" for x in salida["fragmentos"]],
            "abstencion": salida.get("abstencion"),
            "respuesta": salida["respuesta"],
            "tiempos": salida.get("tiempos"),
        }, ensure_ascii=False) + "\n")
