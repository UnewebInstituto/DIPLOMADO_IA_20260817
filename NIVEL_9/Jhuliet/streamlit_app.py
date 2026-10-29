from __future__ import annotations

from pathlib import Path

import streamlit as st
from sentence_transformers import SentenceTransformer

from gemini_rag import build_grounded_response
from pdf_search_app import MODEL_NAME, build_index, get_pdf_files, search_documents


st.set_page_config(page_title="Asistente documental PDF", layout="wide")

st.markdown(
    """
    <style>
    .main {
        background: linear-gradient(180deg, #07131f 0%, #0b1725 100%);
    }
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    div[data-testid="stSidebar"] {
        background: #0f172a;
        border-right: 1px solid rgba(148, 163, 184, 0.2);
    }
    .sidebar-button > button {
        width: 100%;
    }
    .prompt-panel {
        background: rgba(15, 23, 42, 0.92);
        border: 1px solid rgba(96, 165, 250, 0.35);
        border-radius: 18px;
        padding: 1rem 1.1rem;
        box-shadow: 0 12px 24px rgba(0,0,0,0.12);
    }
    .answer-panel {
        background: rgba(255,255,255,0.96);
        color: #0f172a;
        border-radius: 18px;
        padding: 1.1rem 1.2rem;
        border: 1px solid rgba(148, 163, 184, 0.45);
        box-shadow: 0 12px 24px rgba(15, 23, 42, 0.08);
    }
    .citation-box {
        background: #f8fafc;
        border-left: 4px solid #3b82f6;
        border-radius: 10px;
        padding: 0.75rem 0.9rem;
        margin-top: 0.8rem;
        color: #0f172a;
    }
    .page-title {
        color: #f8fafc;
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }
    .page-subtitle {
        color: #cbd5e1;
        font-size: 1.05rem;
        margin-bottom: 1.2rem;
    }
    .stTextArea textarea {
        background: rgba(15, 23, 42, 0.5);
        color: #e2e8f0;
        border: 1px solid rgba(96, 165, 250, 0.35);
        border-radius: 12px;
    }
    .stButton > button {
        background: linear-gradient(90deg, #2563eb, #3b82f6);
        color: white;
        border: none;
        border-radius: 0.7rem;
        font-weight: 700;
        padding: 0.6rem 1rem;
    }
    .stButton > button:hover {
        filter: brightness(1.08);
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def load_app_state() -> None:
    if "model" not in st.session_state:
        st.session_state.model = SentenceTransformer(MODEL_NAME)

    if "collection" not in st.session_state:
        st.session_state.collection = None
        st.session_state.index_error = None

    if "last_query" not in st.session_state:
        st.session_state.last_query = ""

    if "last_answer" not in st.session_state:
        st.session_state.last_answer = ""

    if "last_citations" not in st.session_state:
        st.session_state.last_citations = []


load_app_state()

pdf_files = get_pdf_files(Path("."))
source_options = ["Todos"] + [pdf.name for pdf in pdf_files]

with st.sidebar:
    st.markdown("## Configuración")
    if not pdf_files:
        st.warning("No se encontraron PDFs en el directorio actual.")
        st.stop()

    if st.session_state.collection is None:
        if st.button("Cargar índice de PDFs", use_container_width=True, key="load_index"):
            try:
                with st.spinner("Cargando documentos y creando el índice..."):
                    st.session_state.collection = build_index(Path("."), reindex=False)
                st.success("Índice cargado correctamente.")
            except Exception as exc:
                st.session_state.index_error = str(exc)
                st.error(f"No se pudo cargar el índice: {exc}")

    selected_source = st.selectbox("Filtrar por archivo PDF", source_options, key="selected_source")

    if st.button("Reindexar PDFs", use_container_width=True, key="reindex_btn"):
        try:
            with st.spinner("Reindexando documentos..."):
                st.session_state.collection = build_index(Path("."), reindex=True)
            st.success("Índice actualizado correctamente.")
        except Exception as exc:
            st.error(f"No se pudo reindexar: {exc}")

    if pdf_files:
        st.markdown("### Documentos")
        for pdf in pdf_files:
            st.write(f"• {pdf.name}")

if "index_error" in st.session_state and st.session_state.index_error and st.session_state.collection is None:
    st.error(f"No se pudo inicializar el índice: {st.session_state.index_error}")
    st.stop()

if st.session_state.collection is None:
    st.markdown('<div class="page-title">Asistente documental de manuales</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Consulta los PDFs indexados y obtén respuestas con evidencia y fuente documentada.</div>', unsafe_allow_html=True)
    st.info("La base documental aún no está cargada. Usa el botón de la izquierda para cargar el índice.")
    st.stop()

st.markdown('<div class="page-title">Asistente documental de manuales</div>', unsafe_allow_html=True)
st.markdown('<div class="page-subtitle">Consulta los PDFs indexados y obtén respuestas con evidencia y fuente documentada.</div>', unsafe_allow_html=True)

left_col, right_col = st.columns([1.1, 1.3])

with left_col:
    st.markdown('<div class="prompt-panel">', unsafe_allow_html=True)
    st.markdown("### Plaza tu consulta")
    with st.form("query_form", clear_on_submit=True):
        user_query = st.text_area(
            "",
            value=st.session_state.last_query,
            height=150,
            label_visibility="collapsed",
            placeholder="Escribe tu pregunta sobre los manuales o políticas...",
        )
        submitted = st.form_submit_button("Generar respuesta", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with right_col:
    st.markdown('<div class="answer-panel">', unsafe_allow_html=True)
    st.markdown("### Respuesta")

    if submitted and user_query.strip():
        st.session_state.last_query = user_query.strip()
        source_filter = None if st.session_state.selected_source == "Todos" else st.session_state.selected_source

        with st.spinner("Buscando evidencia en los documentos..."):
            results = search_documents(
                query=st.session_state.last_query,
                collection=st.session_state.collection,
                model=st.session_state.model,
                top_k=5,
                source_filter=source_filter,
            )

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]

        if not documents:
            st.session_state.last_answer = "No encontré evidencia suficiente en los documentos indexados para responder con seguridad."
            st.session_state.last_citations = []
        else:
            retrieved = [
                {"source": metadata.get("fuente", "desconocida"), "content": document}
                for document, metadata in zip(documents, metadatas)
            ]
            grounded = build_grounded_response(st.session_state.last_query, retrieved)
            st.session_state.last_answer = grounded["answer"]
            st.session_state.last_citations = grounded["citations"]

        st.markdown(st.session_state.last_answer)

        if st.session_state.last_citations:
            for citation in st.session_state.last_citations:
                source = citation.get("source", "Documento")
                quote = citation.get("quote", "")
                st.markdown(
                    f"<div class='citation-box'><strong>Fuente:</strong> {source}<br><em>\"{quote}\"</em></div>",
                    unsafe_allow_html=True,
                )
        else:
            st.info("No se encontraron citas relevantes en el contexto consultado.")
    elif st.session_state.last_answer:
        st.markdown(st.session_state.last_answer)
        for citation in st.session_state.last_citations:
            source = citation.get("source", "Documento")
            quote = citation.get("quote", "")
            st.markdown(
                f"<div class='citation-box'><strong>Fuente:</strong> {source}<br><em>\"{quote}\"</em></div>",
                unsafe_allow_html=True,
            )
    else:
        st.info("La respuesta aparecerá aquí una vez que escribas tu consulta.")

    st.markdown("</div>", unsafe_allow_html=True)

