from __future__ import annotations

import os
from typing import Any, Dict

import streamlit as st
from sentence_transformers import SentenceTransformer

from main import (
    GEMINI_MODEL,
    MODEL_NAME,
    ask_gemini,
    build_documents,
    get_or_create_collection,
    index_documents,
    search_documents,
)


st.set_page_config(page_title="Asistente documental RAG", page_icon="📚", layout="wide")


@st.cache_resource
def load_embedder() -> SentenceTransformer:
    return SentenceTransformer(MODEL_NAME)


@st.cache_resource
def load_collection():
    return get_or_create_collection()


def render_evidence(results: Dict[str, Any]) -> None:
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    if not documents:
        st.warning("No se encontraron evidencias relevantes para la consulta.")
        return

    st.markdown("### Evidencia documental")
    for index, document in enumerate(documents, start=1):
        metadata = metadatas[index - 1] if index - 1 < len(metadatas) else {}
        distance = distances[index - 1] if index - 1 < len(distances) else None
        source = metadata.get("fuente", "Desconocida")
        page = metadata.get("pagina", "N/A")

        st.markdown(f"#### Cita {index}")
        st.markdown(f'> "{document}"')
        st.caption(f"Fuente: {source} | Página: {page} | Distancia: {distance}")


def main() -> None:
    st.title("Asistente documental con RAG")
    st.caption("Consulta los PDFs indexados y responde con citas y evidencia documental.")

    with st.sidebar:
        st.header("Configuración")
        api_key = st.text_input("Google Gemini API Key", type="password", value=os.getenv("GEMINI_API_KEY", ""))
        model_name = st.text_input("Modelo Gemini", value=os.getenv("GEMINI_MODEL", "gemini-3.8-flash"), help="Usa un modelo disponible para tu cuenta Gemini.")
        top_k = st.slider("Número de citas", min_value=1, max_value=6, value=3)

        if st.button("Reindexar PDFs"):
            try:
                model = load_embedder()
                docs = build_documents()
                index_documents(model, docs)
                st.success(f"Se indexaron {len(docs)} fragmentos.")
            except Exception as exc:  # pragma: no cover - UI feedback only
                st.error(f"No se pudo reindexar: {exc}")

    question = st.text_area(
        "¿Qué desea consultar en los manuales?",
        placeholder="Ejemplo: ¿Cómo recupero mi contraseña?",
        height=120,
    )

    if st.button("Consultar") and question.strip():
        try:
            model = load_embedder()
            collection = load_collection()
            results = search_documents(model, collection, question, top_k=top_k)
            documents = results.get("documents", [[]])[0]

            if not documents:
                st.warning("No se encontraron resultados relevantes en los documentos cargados.")
                return

            if not api_key:
                st.warning("Ingrese la GEMINI_API_KEY para generar la respuesta con Gemini.")
                render_evidence(results)
                return

            answer = ask_gemini(question, results, api_key=api_key, model_name=model_name)

            st.markdown("### Respuesta del asistente")
            st.write(answer)
            render_evidence(results)

        except Exception as exc:  # pragma: no cover - UI feedback only
            st.error(f"Ocurrió un error al procesar la consulta: {exc}")


if __name__ == "__main__":
    main()
