import streamlit as st

st.title("Form")

with st.form("Datos personales"):
    name = st.text_input(label = "Nombre", placeholder="Introduce tu nombre")
    email = st.text_input(label = "Email", placeholder="email@dominio.com")
    submit = st.form_submit_button("Enviar datos")

if submit:
    st.success(f"Información enviada con éxito: {name}, {email}")