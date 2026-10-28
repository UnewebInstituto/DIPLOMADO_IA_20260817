import os

import chromadb
import streamlit as st
from google import genai
from google.genai import types
from sentence_transformers import SentenceTransformer

MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
PERSIST_DIR = "./chroma_db"
COLLECTION_NAME = "manuales"
DEFAULT_GEMINI_MODEL = "gemini-3.5-flash-lite"


@st.cache_resource
def load_embedding_model():
    return SentenceTransformer(MODEL_NAME)


@st.cache_resource
def load_collection():
    client = chromadb.PersistentClient(path=PERSIST_DIR)
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


@st.cache_data
def query_documents(question: str, n_results: int = 5):
    model = load_embedding_model()
    collection = load_collection()
    query_vector = model.encode([question], normalize_embeddings=True).tolist()
    result = collection.query(
        query_embeddings=query_vector,
        n_results=n_results,
    )

    documents = result.get("documents", [[]])[0]
    metadatas = result.get("metadatas", [[]])[0]
    distances = result.get("distances", [[]])[0]

    evidence = []
    for doc, meta, distance in zip(documents, metadatas, distances):
        metadata = meta if isinstance(meta, dict) else {}
        evidence.append(
            {
                "fuente": metadata.get("fuente", "Desconocida"),
                "pagina": metadata.get("pagina", "?"),
                "chunk": metadata.get("chunk", "?"),
                "documento": doc,
                "distancia": float(distance),
            }
        )

    return evidence


def build_prompt(question: str, evidence: list[dict]):
    context = "\n\n".join(
        f"[Fuente: {item['fuente']} | Página: {item['pagina']}]\n{item['documento']}"
        for item in evidence
    )

    return f"""
Eres un asistente que responde únicamente con base en el contexto proporcionado.
No inventes información. Si no se encuentra evidencia suficiente, dilo con honestidad.
Incluye una respuesta breve, clara y con citas de fuente y página.

CONTEXTO:
{context}

PREGUNTA:
{question}

RESPUESTA:
""".strip()


def answer_question(question: str, evidence: list[dict], model_name: str):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Falta la variable GEMINI_API_KEY. Defínela antes de usar la aplicación.")

    client = genai.Client(api_key=api_key)
    prompt = build_prompt(question, evidence)
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.2,
            top_p=0.95,
            max_output_tokens=700,
        ),
    )
    return getattr(response, "text", str(response))


def main():
    st.set_page_config(page_title="Asistente RAG", page_icon="🧠", layout="wide")
    st.title("Asistente documental con RAG")
    st.caption("Consulta tus PDFs indexados con ChromaDB y responde con evidencia de fuente")

    with st.sidebar:
        st.header("Configuración")
        model_name = st.selectbox(
            "Modelo Gemini",
            ["gemini-3.5-flash-lite"],
            index=0,
        )
        n_results = st.slider("Resultados a recuperar", min_value=1, max_value=8, value=3)
        st.info(
            "Para usar esta app define la variable de entorno GEMINI_API_KEY antes de arrancar Streamlit."
        )

    question = st.text_area(
        "Escribe tu consulta",
        value="¿Cómo se solicita una constancia laboral?",
        height=120,
    )

    if st.button("Consultar", type="primary"):
        if not question.strip():
            st.warning("Escribe una pregunta antes de continuar.")
            return

        try:
            with st.spinner("Recuperando evidencia y generando respuesta..."):
                evidence = query_documents(question, n_results=n_results)
                if not evidence:
                    st.warning("No se encontró evidencia relevante en la base vectorial.")
                    return

                answer = answer_question(question, evidence, model_name)

            st.success("Respuesta generada")
            st.markdown("### Respuesta")
            st.write(answer)

            st.markdown("### Evidencia recuperada")
            for idx, item in enumerate(evidence, start=1):
                st.markdown(f"**{idx}. {item['fuente']} | Página {item['pagina']}**")
                st.write(item["documento"])
                st.caption(f"Distancia: {item['distancia']:.4f}")

        except Exception as exc:
            st.error(f"No se pudo completar la consulta: {exc}")


if __name__ == "__main__":
    main()
