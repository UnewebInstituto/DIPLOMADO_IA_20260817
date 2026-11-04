"""Evalúa la recuperación (P4). Ejemplos:

    python evaluacion/eval_recuperacion.py                          # vectorial e híbrida
    python evaluacion/eval_recuperacion.py --configs vectorial,hibrida,hibrida_rerank
"""
import argparse, json, pathlib, sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import config
from metricas import metricas_recuperacion
from motor import RAG

CONFIGS = {"vectorial": ("vectorial", False), "hibrida": ("hibrida", False),
           "vectorial_rerank": ("vectorial", True), "hibrida_rerank": ("hibrida", True)}
KS = (1, 3, 5, 8)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--configs", default="vectorial,hibrida")
    a = ap.parse_args()

    rag = RAG()
    if rag.almacen.contar() == 0:
        sys.exit("Índice vacío. Ejecute: python cli.py sincronizar")
    with open(RAIZ / "evaluacion" / "dataset.json", encoding="utf-8") as f:
        casos = [c for c in json.load(f) if c["relevantes"]]      # las no respondibles se evalúan en generación

    existentes = set(rag.almacen.col.get(include=[])["ids"])
    faltan = sorted({i for c in casos for i in c["relevantes"]} - existentes)
    if faltan:
        sys.exit("IDs del dataset que no existen en el índice (¿cambió el chunking?). "
                 "Ejecute python evaluacion/construir_dataset.py y luego python cli.py reindexar.\n  "
                 + "\n  ".join(faltan))

    salida = {}
    for nombre in a.configs.split(","):
        modo, rerank = CONFIGS[nombre.strip()]
        recuperados = {c["pregunta"]: [f["id"] for f in rag.recuperar(c["pregunta"], k=max(KS), modo=modo, rerank=rerank)[0]]
                       for c in casos}
        salida[nombre] = [metricas_recuperacion(casos, recuperados, k) for k in KS]
        fallan = [c["pregunta"] for c in casos if not set(c["relevantes"]) & set(recuperados[c["pregunta"]][:5])]
        salida[nombre + "_fallan_top5"] = fallan

    print(f"Preguntas evaluadas: {len(casos)} | chunk={config.CHUNK_TAMANO}/{config.CHUNK_SOLAPE} | modelo={config.EMB_MODELO}\n")
    print(f"{'configuración':<18}{'Precisión@5':>12}{'Recall@5':>10}{'Hit@5':>8}{'MRR':>8}")
    for nombre in a.configs.split(","):
        m = next(x for x in salida[nombre.strip()] if x["k"] == 5)
        print(f"{nombre.strip():<18}{m['precision']:>12}{m['recall']:>10}{m['hit_rate']:>8}{m['MRR']:>8}")
    for nombre in a.configs.split(","):
        print(f"\n[{nombre.strip()}] sin relevante en el top-5:")
        for q in salida[nombre.strip() + "_fallan_top5"] or ["(ninguna)"]:
            print(" -", q)
    with open(RAIZ / "evaluacion" / "resultados_recuperacion.json", "w", encoding="utf-8") as f:
        json.dump(salida, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
