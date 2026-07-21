"""Interfaz web del agente BimBam Buy (Streamlit).

Ejecutar localmente:
    streamlit run app.py

En OCI se ejecuta igual, exponiendo el puerto 8501 (ver docs/deploy_oci.md).
"""

import streamlit as st
from src.agente import construir_agente

st.set_page_config(page_title="Agente BimBam Buy", page_icon="🛍️")

st.title("🛍️ Agente BimBam Buy")
st.caption(
    "Pregúntame sobre la Política de Reembolsos y Devoluciones. "
    "Respondo en base al documento oficial, sin que tengas que abrirlo."
)


@st.cache_resource(show_spinner="Cargando el documento y construyendo el índice...")
def obtener_agente():
    return construir_agente()


try:
    agente = obtener_agente()
except EnvironmentError as e:
    st.error(str(e))
    st.stop()

if "historial" not in st.session_state:
    st.session_state.historial = []

# Mostrar historial
for rol, texto in st.session_state.historial:
    with st.chat_message(rol):
        st.markdown(texto)

# Sugerencias iniciales
if not st.session_state.historial:
    st.markdown("**Prueba con:**")
    st.markdown(
        "- ¿Cuántos días tengo para devolver un producto que no me gustó?\n"
        "- ¿Quién paga el envío si el producto llegó defectuoso?\n"
        "- ¿En cuánto tiempo me devuelven el dinero a la tarjeta de crédito?"
    )

pregunta = st.chat_input("Escribe tu pregunta...")
if pregunta:
    st.session_state.historial.append(("user", pregunta))
    with st.chat_message("user"):
        st.markdown(pregunta)
    with st.chat_message("assistant"):
        with st.spinner("Buscando en la política..."):
            respuesta = agente.invoke(pregunta)
        st.markdown(respuesta)
    st.session_state.historial.append(("assistant", respuesta))
