"""Interfaz Streamlit del asistente RAG.  Ejecutar:  streamlit run app.py"""
import os, pathlib, time
import streamlit as st

RAIZ = pathlib.Path(__file__).resolve().parent
os.chdir(RAIZ)

import config
from ingesta import EXTENSIONES, listar_documentos
from motor import RAG
from registro import registrar

st.set_page_config(page_title="Asistente de conocimiento", page_icon="📚", layout="wide")
st.title("📚 Asistente de conocimiento")


@st.cache_resource(show_spinner="Cargando modelos e índice (la primera vez puede tardar)...")
def cargar():
    rag = RAG()
    if rag.almacen.contar() == 0:
        rag.sincronizar()                       # primera ejecución: indexa la carpeta documentos/
    return rag


try:
    rag = cargar()
except Exception as e:
    st.error(f"No se pudo iniciar el asistente: {e}")
    st.stop()


def md(texto):
    """Escapa $ para que Streamlit no lo interprete como fórmula LaTeX (ej.: '$60 USD')."""
    return texto.replace("$", "\\$")


def mostrar_fuentes(fragmentos, abstencion=False):
    titulo = ("Fragmentos más cercanos (no respaldan una respuesta)" if abstencion
              else "Fuentes consultadas")
    with st.expander(titulo):
        for n, f in enumerate(fragmentos, 1):
            datos = []
            if f.get("distancia") is not None:
                datos.append(f"distancia {f['distancia']:.3f}")
            if f.get("score_bm25") is not None:
                datos.append(f"BM25 {f['score_bm25']:.2f}")
            if f.get("score_rerank") is not None:
                datos.append(f"re-rank {f['score_rerank']:.2f}")
            st.markdown(f"**[{n}] {f['fuente']} — p. {f['pagina']}**"
                        + (f" · {' · '.join(datos)}" if datos else ""))
            if f.get("seccion"):
                st.caption(f"Sección: {md(f['seccion'])}")
            st.caption(md(f["texto"][:400] + ("..." if len(f["texto"]) > 400 else "")))


def reporte(rep):
    partes = [f"{len(rep[k])} {k}" for k in ("agregados", "actualizados", "eliminados", "sin_texto") if rep[k]]
    return ", ".join(partes) or f"sin cambios ({len(rep['sin_cambios'])} documentos al día)"


# ---------------- Barra lateral ----------------
st.session_state.setdefault("historial", [])
st.session_state.setdefault("uploader_key", 0)

with st.sidebar:
    st.header("Configuración")
    k = st.slider("Fragmentos a recuperar (k)", 1, 8, config.K)
    modo = st.selectbox("Búsqueda", ["hibrida", "vectorial"],
                        index=0 if config.MODO == "hibrida" else 1,
                        format_func=lambda m: "Híbrida (BM25 + vectorial)" if m == "hibrida" else "Solo vectorial")
    rerank = st.checkbox("Re-ranking (cross-encoder)", value=config.USAR_RERANKER,
                         help="Más preciso pero más lento; la primera vez descarga el modelo.")
    reescribir = st.checkbox("Reescribir pregunta según el historial", value=True,
                             help="Convierte '¿y para administradores?' en una pregunta autónoma.")
    if st.button("Limpiar conversación"):
        st.session_state.historial = []
        st.rerun()

    st.divider()
    st.header("Documentos")
    estado = rag.estado()
    st.caption(f"{len(estado['fuentes'])} documentos · {estado['chunks']} fragmentos")
    for fuente, n in sorted(estado["fuentes"].items()):
        st.caption(f"• {fuente} ({n})")

    subidos = st.file_uploader("Agregar o actualizar documentos", type=[e.strip('.') for e in EXTENSIONES],
                               accept_multiple_files=True, key=f"up_{st.session_state.uploader_key}")
    if subidos and st.button("Guardar y sincronizar"):
        config.DIR_DOCS.mkdir(parents=True, exist_ok=True)
        for s in subidos:
            (config.DIR_DOCS / pathlib.Path(s.name).name).write_bytes(s.getbuffer())
        with st.spinner("Sincronizando..."):
            rep = rag.sincronizar()
        st.session_state.uploader_key += 1
        st.session_state.mensaje = reporte(rep)
        st.rerun()

    docs = sorted(listar_documentos(config.DIR_DOCS))
    if docs:
        elegido = st.selectbox("Eliminar documento", ["—"] + docs)
        if elegido != "—" and st.button("Eliminar y sincronizar"):
            (config.DIR_DOCS / elegido).unlink(missing_ok=True)
            rep = rag.sincronizar()
            st.session_state.mensaje = reporte(rep)
            st.rerun()
    if st.button("Sincronizar carpeta"):
        with st.spinner("Sincronizando..."):
            rep = rag.sincronizar()
        st.session_state.mensaje = reporte(rep)
        st.rerun()
    if "mensaje" in st.session_state:
        st.success(st.session_state.pop("mensaje"))

    st.divider()
    st.caption(f"Embeddings: {estado['modelo_emb']}")
    st.caption(f"LLM: {config.LLM_PROVEEDOR} · {config.OLLAMA_MODELO if config.LLM_PROVEEDOR == 'ollama' else config.GEMINI_MODELO}")

# ---------------- Conversación ----------------
for m in st.session_state.historial:
    with st.chat_message(m["rol"]):
        st.markdown(md(m["texto"]))
        if m.get("fuentes"):
            mostrar_fuentes(m["fuentes"], m.get("abstencion", False))

pregunta = st.chat_input("Escriba su pregunta sobre los documentos...")
if pregunta:
    historial_previo = [(m["rol"], m["texto"]) for m in st.session_state.historial]
    st.session_state.historial.append({"rol": "user", "texto": pregunta})
    with st.chat_message("user"):
        st.markdown(md(pregunta))

    with st.chat_message("assistant"):
        try:
            with st.spinner("Buscando en la base de conocimiento..."):
                salida = rag.responder(pregunta, k=k, modo=modo, rerank=rerank,
                                       historial=historial_previo, reescribir=reescribir)
        except Exception as e:
            st.error(f"No se pudo generar la respuesta: {e}")
            st.session_state.historial.pop()
            st.stop()
        if salida.get("aviso"):
            st.warning(salida["aviso"])
        st.markdown(md(salida["respuesta"]))
        mostrar_fuentes(salida["fragmentos"], salida["abstencion"])
        if salida["consulta"] != pregunta:
            st.caption(f"Consulta reescrita: {md(salida['consulta'])}")
        t = salida["tiempos"]
        st.caption(f"⏱ búsqueda {t['recuperacion']} s · generación {t['generacion']} s")

    registrar(pregunta, salida)
    st.session_state.historial.append({"rol": "assistant", "texto": salida["respuesta"],
                                       "fuentes": salida["fragmentos"], "abstencion": salida["abstencion"]})
