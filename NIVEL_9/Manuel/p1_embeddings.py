import json, numpy as np
from sentence_transformers import SentenceTransformer
from utils import preparar_chunks
chunks = preparar_chunks("documentos")
print(f"Total de chunks: {len(chunks)}")
modelo = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
vectores = modelo.encode([c["texto"] for c in chunks],
                         normalize_embeddings=True, show_progress_bar=True)
print("Forma de la matriz:", vectores.shape)   # (n_chunks, 384)
np.save("embeddings.npy", vectores)
json.dump(chunks, open("chunks.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)

