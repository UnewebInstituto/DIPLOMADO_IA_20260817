from __future__ import annotations

import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from main import get_embedding_model, rag_answer

ROOT_DIR = Path(__file__).resolve().parent
load_dotenv(ROOT_DIR / ".env")
os.environ.setdefault("GEMINI_MODEL", "gemini-3.5-flash-lite")

st.set_page_config(
    page_title="Asistente documental RAG",
    page_icon="📚",
    layout="wide",
)

st.title("Asistente documental RAG")
st.caption("Responde con base en los PDFs indexados y cita la evidencia documental.")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Hola. Puedes hacerme preguntas sobre los manuales o documentos indexados y te responderé con evidencia.",
        }
    ]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("Escribe tu pregunta sobre los documentos...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        model = get_embedding_model()
        response = rag_answer(prompt, top_k=5, model=model)
        answer = response.get("answer", "No se pudo generar una respuesta.")
        citations = response.get("citations", [])

        with st.chat_message("assistant"):
            st.markdown(answer)

        if citations:
            with st.expander("Ver evidencia documental"):
                for i, citation in enumerate(citations, start=1):
                    fuente = citation.get("fuente", "Fuente")
                    pagina = citation.get("pagina", "?")
                    texto = citation.get("texto", "")
                    st.markdown(f"**{i}. {fuente}** | Página: {pagina}")
                    st.write(texto)

        st.session_state.messages.append({"role": "assistant", "content": answer})
    except Exception as exc:
        error_message = f"Ocurrió un error al consultar el asistente: {exc}"
        with st.chat_message("assistant"):
            st.error(error_message)
        st.session_state.messages.append({"role": "assistant", "content": error_message})
