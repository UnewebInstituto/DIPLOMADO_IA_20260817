import json, os, pathlib, time
import streamlit as st

# Raíz del proyecto: permite lanzar la app desde cualquier carpeta
RAIZ = pathlib.Path(__file__).resolve().parent
os.chdir(RAIZ)

from rag import RAG

st.set_page_config(page_title="Asistente de conocimiento", page_icon="📚")
st.title("📚 Asistente de conocimiento")

if not (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")):
    st.error("Falta la variable de entorno GEMINI_API_KEY. Defínala y reinicie la app.")
    st.stop()


@st.cache_resource(show_spinner="Cargando modelo de embeddings...")
def cargar():
    rag = RAG()
    if rag.col.count() == 0:
        rag.indexar("documentos")   # primera ejecución: indexa si la base está vacía
    return rag


try:
    rag = cargar()
except Exception as e:
    st.error(f"No se pudo iniciar el asistente: {e}")
    st.stop()


def md(texto):
    """Escapa $ para que Streamlit no lo interprete como fórmula LaTeX."""
    return texto.replace("$", "\\$")


def registrar(pregunta, salida, segundos, ruta="registro.jsonl"):
    with open(ruta, "a", encoding="utf-8") as f:
        f.write(json.dumps({
            "fecha": time.strftime("%Y-%m-%d %H:%M:%S"),
            "pregunta": pregunta,
            "fuentes": [f"{x['fuente']}:p{x['pagina']}" for x in salida["fragmentos"]],
            "respuesta": salida["respuesta"],
            "segundos": round(segundos, 2),
        }, ensure_ascii=False) + "\n")


def mostrar_fuentes(fragmentos, abstencion=False):
    titulo = ("Fragmentos más cercanos (no respaldan una respuesta)"
              if abstencion else "Fuentes consultadas")
    with st.expander(titulo):
        for n, f in enumerate(fragmentos, 1):
            st.markdown(f"**[{n}] {f['fuente']} — p. {f['pagina']}** "
                        f"· distancia {f['distancia']:.3f}")
            corto = f["texto"][:300] + ("..." if len(f["texto"]) > 300 else "")
            st.caption(md(corto))


# --- Barra lateral ---
with st.sidebar:
    st.header("Configuración")
    k = st.slider("Fragmentos a recuperar (k)", 1, 8, 4)
    st.caption(f"Chunks indexados: {rag.col.count()}")
    if st.button("Reindexar documentos"):
        with st.spinner("Indexando..."):
            n = rag.indexar("documentos")
        st.success(f"{n} chunks procesados")
    if st.button("Limpiar conversación"):
        st.session_state.historial = []
        st.rerun()

# --- Historial (cada mensaje conserva sus fuentes) ---
if "historial" not in st.session_state:
    st.session_state.historial = []

for m in st.session_state.historial:
    with st.chat_message(m["rol"]):
        st.markdown(md(m["texto"]))
        if m.get("fuentes"):
            mostrar_fuentes(m["fuentes"], m.get("abstencion", False))

# --- Nueva pregunta ---
pregunta = st.chat_input("Escriba su pregunta sobre los documentos...")
if pregunta:
    st.session_state.historial.append({"rol": "user", "texto": pregunta})
    with st.chat_message("user"):
        st.markdown(md(pregunta))

    with st.chat_message("assistant"):
        try:
            with st.spinner("Buscando en la base de conocimiento..."):
                inicio = time.time()
                salida = rag.responder(pregunta, k=k)
                segundos = time.time() - inicio
        except Exception as e:
            st.error(f"No se pudo generar la respuesta: {e}")
            st.stop()

        abst = salida["respuesta"].strip().lower().startswith("no encontré esa información")
        st.markdown(md(salida["respuesta"]))
        mostrar_fuentes(salida["fragmentos"], abst)

    registrar(pregunta, salida, segundos)
    st.session_state.historial.append({
        "rol": "assistant", "texto": salida["respuesta"],
        "fuentes": salida["fragmentos"], "abstencion": abst,
    })