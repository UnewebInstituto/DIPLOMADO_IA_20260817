"""Métricas de recuperación: precisión@k, recall@k, hit rate@k y MRR."""


def metricas_recuperacion(casos, recuperados, k):
    """casos: [{pregunta, relevantes}]; recuperados: {pregunta: [ids ordenados]}."""
    precs, recs, hits, rrs = [], [], [], []
    for c in casos:
        ids = recuperados[c["pregunta"]][:k]
        rel = set(c["relevantes"])
        aciertos = [i for i in ids if i in rel]
        precs.append(len(aciertos) / k)
        recs.append(len(aciertos) / len(rel))
        hits.append(1 if aciertos else 0)
        pos = next((p for p, i in enumerate(ids, 1) if i in rel), None)
        rrs.append(1 / pos if pos else 0)
    n = len(casos)
    return {"k": k, "precision": round(sum(precs) / n, 3), "recall": round(sum(recs) / n, 3),
            "hit_rate": round(sum(hits) / n, 3), "MRR": round(sum(rrs) / n, 3)}
