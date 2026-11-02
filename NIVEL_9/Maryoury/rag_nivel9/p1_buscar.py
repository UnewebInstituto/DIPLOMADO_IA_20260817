import json, numpy as np
from sentence_transformers import SentenceTransformer
chunks = json.load(open("chunks.json", encoding="utf-8"))
vectores = np.load("embeddings.npy")
modelo = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
def buscar(pregunta, k=3):
    q = modelo.encode([pregunta], normalize_embeddings=True)[0]
    similitudes = vectores @ q  # producto punto = coseno (vectores normalizados)
    top = np.argsort(-similitudes)[:k]
    return [(float(similitudes[i]), chunks[i]) for i in top]
while True:
    p = input("\nPregunta (vacío para salir): ").strip()
    if not p:
        break
    for sim, c in buscar(p):
        print(f"[{sim:.3f}] {c['fuente']} p.{c['pagina']}\n{c['texto']
[:300]}...\n")
