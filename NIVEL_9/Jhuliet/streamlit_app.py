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
    .assistant-box {
        background: #ffffff;
        border: 1px solid #dbeafe;
        border-radius: 0.9rem;
        padding: 1rem 1.1rem;
        margin: 0.5rem 0;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
    }
    .citation-box {
        background: #f8fafc;
        border-left: 4px solid #3b82f6;
        border-radius: 0.5rem;
        padding: 0.85rem 1rem;
        margin-top: 0.7rem;
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

    if "messages" not in st.session_state:
        st.session_state.messages = []


load_app_state()

st.title("Asistente documental de manuales")
st.caption("Consulta los PDFs indexados y obtén respuestas con evidencia y fuente documentada.")

pdf_files = get_pdf_files(Path("."))
source_options = ["Todos"] + [pdf.name for pdf in pdf_files]

with st.sidebar:
    st.subheader("Configuración")
    if not pdf_files:
        st.warning("No se encontraron PDFs en el directorio actual.")
        st.stop()

    if st.session_state.collection is None:
        if st.button("Cargar índice de PDFs", use_container_width=True):
            try:
                with st.spinner("Cargando documentos y creando el índice..."):
                    st.session_state.collection = build_index(Path("."), reindex=False)
                st.success("Índice cargado correctamente.")
            except Exception as exc:
                st.session_state.index_error = str(exc)
                st.error(f"No se pudo cargar el índice: {exc}")

    selected_source = st.selectbox("Filtrar por archivo PDF", source_options)
    if st.button("Reindexar PDFs", use_container_width=True):
        try:
            with st.spinner("Reindexando documentos..."):
                st.session_state.collection = build_index(Path("."), reindex=True)
            st.success("Índice actualizado correctamente.")
        except Exception as exc:
            st.error(f"No se pudo reindexar: {exc}")

    if pdf_files:
        st.subheader("Documentos")
        for pdf in pdf_files:
            st.write(f"- {pdf.name}")

if "index_error" in st.session_state and st.session_state.index_error and st.session_state.collection is None:
    st.error(f"No se pudo inicializar el índice: {st.session_state.index_error}")
    st.stop()

if st.session_state.collection is None:
    st.info("La base documental aún no está cargada. Pulsa “Cargar índice de PDFs” para inicializarla.")
    st.stop()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("Pregunta sobre los manuales o políticas documentadas...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    source_filter = None if selected_source == "Todos" else selected_source
    with st.spinner("Buscando evidencia en los documentos..."):
        results = search_documents(
            query=prompt,
            collection=st.session_state.collection,
            model=st.session_state.model,
            top_k=5,
            source_filter=source_filter,
        )

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    if not documents:
        response = "No encontré evidencia suficiente en los documentos indexados para responder con seguridad."
        with st.chat_message("assistant"):
            st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
    else:
        retrieved = [
            {"source": metadata.get("fuente", "desconocida"), "content": document}
            for document, metadata in zip(documents, metadatas)
        ]
        grounded = build_grounded_response(prompt, retrieved)

        with st.chat_message("assistant"):
            st.markdown(f"<div class='assistant-box'>{grounded['answer']}</div>", unsafe_allow_html=True)
            for citation in grounded["citations"]:
                source = citation.get("source", "Documento")
                quote = citation.get("quote", "")
                st.markdown(
                    f"<div class='citation-box'><strong>Fuente:</strong> {source}<br><em>\"{quote}\"</em></div>",
                    unsafe_allow_html=True,
                )

        assistant_message = "\n\n".join(
            [grounded["answer"]] + [f"**Fuente:** {c['source']}\n> \"{c['quote']}\"" for c in grounded["citations"]]
        )
        st.session_state.messages.append({"role": "assistant", "content": assistant_message})

if not st.session_state.messages:
    welcome = "Hola. Hazme una pregunta sobre los PDFs cargados y te responderé con evidencia de las fuentes indexadas."
    st.info(welcome)

