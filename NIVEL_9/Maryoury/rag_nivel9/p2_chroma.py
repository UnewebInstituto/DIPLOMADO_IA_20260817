import chromadb
from sentence_transformers import SentenceTransformer
from utils import preparar_chunks
modelo = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
cliente = chromadb.PersistentClient(path="./chroma_db")
# Recrear la colección desde cero para la práctica
try:
    cliente.delete_collection("conocimiento")
except Exception:
    pass
col = cliente.create_collection("conocimiento", metadata={"hnsw:space": 
"cosine"})

chunks = preparar_chunks("documentos")
vectores = modelo.encode([c["texto"] for c in chunks],
                         normalize_embeddings=True).tolist()
col.add(
    ids=[c["id"] for c in chunks],
    documents=[c["texto"] for c in chunks],
    embeddings=vectores,
    metadatas=[{"fuente": c["fuente"], "pagina": c["pagina"]} for c in 
chunks],
)
print("Chunks indexados:", col.count())

# Continúa en la misma sesión del Paso 1: usa las variables modelo y col
def consultar(pregunta, k=3, fuente=None):
    q = modelo.encode([pregunta], normalize_embeddings=True).tolist()
    filtro = {"fuente": fuente} if fuente else None
    r = col.query(query_embeddings=q, n_results=k, where=filtro)
    for doc, meta, dist in zip(r["documents"][0], r["metadatas"][0], 
r["distances"][0]):
        print(f"[distancia {dist:.3f}] {meta['fuente']} p.{meta['pagina']}")
        print(doc[:250].replace("\n", " "), "...\n")
consultar("¿Cómo se solicita una devolución?")
consultar("¿Cómo se solicita una devolución?", fuente="politicas.pdf")

# Continúa en la misma sesión: usa col, modelo y chunks del Paso 1
# Actualizar el texto de un chunk (hay que recalcular su vector)
nuevo = "Texto corregido del fragmento..."
col.update(ids=[chunks[0]["id"]], documents=[nuevo],
           embeddings=modelo.encode([nuevo], 
normalize_embeddings=True).tolist())
# Obtener por ID
print(col.get(ids=[chunks[0]["id"]]))
# Eliminar todos los chunks de un documento (use el nombre de uno de sus archivos;
# si no hay chunks con ese nombre, no ocurre nada)
col.delete(where={"fuente": "documento_obsoleto.pdf"})
print("Quedan:", col.count())