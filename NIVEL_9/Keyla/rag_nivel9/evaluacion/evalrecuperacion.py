import json, os, sys, pathlib

# Raíz del proyecto (rag_nivel9/): permite ejecutar desde cualquier carpeta
RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
os.chdir(RAIZ)  # para que ./chroma_db y evaluacion/ se resuelvan bien

from rag import RAG

KS = (1, 3, 5, 8)
K_MAX = max(KS)

rag = RAG()

with open("evaluacion/dataset.json", encoding="utf-8") as f:
    todos = json.load(f)
# Las preguntas no respondibles (relevantes vacío) se evalúan en generación
casos = [c for c in todos if c["relevantes"]]

# --- Verificaciones previas ---
if rag.col.count() == 0:
    sys.exit("La colección está vacía. Indexe primero: RAG().indexar('documentos')")

existentes = set(rag.col.get(include=[])["ids"])
faltantes = sorted({i for c in casos for i in c["relevantes"]} - existentes)
if faltantes:
    sys.exit("IDs del dataset que no existen en la colección "
             "(¿otro chunking o chroma_db desactualizada?):\n  " + "\n  ".join(faltantes))

# --- Una sola consulta por pregunta, con el k máximo ---
recuperados = {}
for c in casos:
    q = rag.emb.encode([c["pregunta"]], normalize_embeddings=True).tolist()
    recuperados[c["pregunta"]] = rag.col.query(
        query_embeddings=q, n_results=K_MAX)["ids"][0]


def evaluar(k):
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
    total = len(casos)
    return {"k": k,
            "precision": round(sum(precs) / total, 3),
            "recall": round(sum(recs) / total, 3),
            "hit_rate": round(sum(hits) / total, 3),
            "MRR": round(sum(rrs) / total, 3)}


resultados = [evaluar(k) for k in KS]
for r in resultados:
    print(r)

# --- Preguntas que fallan con k=5 (insumo para el análisis de errores) ---
print("\nPreguntas sin ningún relevante en el top-5:")
for c in casos:
    if not set(c["relevantes"]) & set(recuperados[c["pregunta"]][:5]):
        print(" -", c["pregunta"])

with open("evaluacion/resultados_recuperacion.json", "w", encoding="utf-8") as f:
    json.dump(resultados, f, ensure_ascii=False, indent=2)