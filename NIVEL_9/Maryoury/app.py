import os

import streamlit as st

from main import DB_PATH, answer_question

st.set_page_config(page_title="Asistente documental", page_icon="📘", layout="wide")

st.title("Asistente documental con evidencia")
st.caption("Consulta los manuales indexados y obtén respuestas con citas y referencias a la fuente.")

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.header("Configuración")
    api_key = st.text_input("API Key Gemini", type="password", value=os.getenv("GEMINI_API_KEY", ""))
    model_name = st.text_input("Modelo Gemini", value=os.getenv("GEMINI_MODEL", "gemini-3.8-flash"))
    st.caption("La clave puede dejarse como variable de entorno en el sistema; usa un modelo válido de Gemini como gemini-3.8-flash.")
    if api_key:
        os.environ["GEMINI_API_KEY"] = api_key
    if model_name:
        os.environ["GEMINI_MODEL"] = model_name

    if not os.getenv("GEMINI_API_KEY"):
        st.warning("Aún no hay clave de Gemini configurada. La app seguirá funcionando, pero la generación final necesitará la API key.")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("evidence"):
            st.markdown("**Evidencia**")
            for item in msg["evidence"]:
                st.markdown(f"- {item['citation']}")

prompt = st.chat_input("Haz una pregunta sobre los manuales...")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    if not os.getenv("GEMINI_API_KEY"):
        answer = "Necesito la API key de Gemini en la configuración para generar la respuesta final con evidencia."
        evidence = []
    else:
        with st.spinner("Buscando evidencia en los documentos..."):
            try:
                answer, evidence = answer_question(
                    prompt,
                    db_path=DB_PATH,
                    top_k=3,
                    api_key=os.getenv("GEMINI_API_KEY"),
                    model_name=os.getenv("GEMINI_MODEL", "gemini-3.8-flash"),
                )
            except Exception as exc:
                answer = (
                    "No se pudo generar la respuesta con el modelo. "
                    f"Verifica la clave y el nombre del modelo. Error: {exc}"
                )
                evidence = []

    with st.chat_message("assistant"):
        st.markdown(answer)
        if evidence:
            st.markdown("**Evidencia documental**")
            for item in evidence:
                st.markdown(f"- {item['citation']}")

    st.session_state.messages.append({"role": "assistant", "content": answer, "evidence": evidence})
