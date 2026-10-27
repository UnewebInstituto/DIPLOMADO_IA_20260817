from __future__ import annotations

from pathlib import Path

import streamlit as st
from sentence_transformers import SentenceTransformer

from pdf_search_app import MODEL_NAME, build_index, generate_answer_from_context, get_pdf_files, search_documents


st.set_page_config(page_title="Buscador de manuales PDF", layout="wide")

st.markdown(
    """
    <style>
    .main { background: linear-gradient(180deg, #f4f8ff 0%, #eef3ff 100%); }
    .block-container { padding-top: 2rem; }
    div[data-testid="stSidebar"] { background: #0f172a; }
    h1 { color: #0f172a; }
    .stButton > button {
        background: linear-gradient(90deg, #2563eb, #3b82f6);
        color: white;
        border: none;
        border-radius: 0.6rem;
        font-weight: 600;
    }
    .stButton > button:hover { filter: brightness(1.05); }
    .result-box {
        background: rgba(255,255,255,0.8);
        border: 1px solid #dbeafe;
        border-radius: 0.8rem;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def load_app_state() -> None:
    if "model" not in st.session_state:
        st.session_state.model = SentenceTransformer(MODEL_NAME)

    if "collection" not in st.session_state:
        try:
            st.session_state.collection = build_index(Path("."), reindex=False)
        except Exception as exc:  # pragma: no cover - UI error display
            st.session_state.index_error = str(exc)
            st.session_state.collection = None


load_app_state()

st.title("Buscador semántico de manuales PDF")
st.caption("Consulta documentos en lenguaje natural sobre los PDFs del directorio actual.")

if "index_error" in st.session_state and st.session_state.collection is None:
    st.error(f"No se pudo inicializar el índice: {st.session_state.index_error}")
    st.stop()

pdf_files = get_pdf_files(Path("."))
source_options = ["Todos"] + [pdf.name for pdf in pdf_files]

with st.container():
    left_col, right_col = st.columns([2, 1])

    with left_col:
        selected_source = st.selectbox("Filtrar por archivo PDF", source_options)

    with right_col:
        if st.button("Reindexar PDFs", use_container_width=True):
            try:
                st.session_state.collection = build_index(Path("."), reindex=True)
                st.success("Índice actualizado correctamente.")
            except Exception as exc:
                st.error(f"No se pudo reindexar: {exc}")

query = st.text_area(
    "Escribe tu pregunta",
    value="",
    placeholder="Ejemplo: ¿Cómo recupero mi contraseña?",
    height=120,
)

if st.button("Buscar", type="primary"):
    if not query.strip():
        st.warning("Debes escribir una pregunta antes de buscar.")
    else:
        source_filter = None if selected_source == "Todos" else selected_source
        results = search_documents(
            query=query,
            collection=st.session_state.collection,
            model=st.session_state.model,
            top_k=5,
            source_filter=source_filter,
        )
        documents = results.get("documents", [[]])[0]
        distances = results.get("distances", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]

        if not documents:
            st.info("No se encontraron resultados relevantes para tu consulta.")
        else:
            answer = generate_answer_from_context(query, documents)
            st.subheader("Respuesta sugerida")
            st.markdown(
                f"<div class='result-box'><strong>Resumen:</strong><br>{answer}</div>",
                unsafe_allow_html=True,
            )
            st.markdown("---")

            for i, (document, distance, metadata) in enumerate(zip(documents, distances, metadatas), start=1):
                with st.container():
                    st.markdown(
                        f"""
                        <div class='result-box'>
                            <h4>Resultado {i}</h4>
                            <p><strong>Fuente:</strong> {metadata.get('fuente', 'desconocida')}</p>
                            <p><strong>Distancia:</strong> {distance:.4f}</p>
                            <p>{document[:1200]}</p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

if pdf_files:
    st.subheader("Archivos PDF disponibles")
    for pdf in pdf_files:
        st.write(f"- {pdf.name}")
else:
    st.warning("No se encontraron PDFs en el directorio actual.")
