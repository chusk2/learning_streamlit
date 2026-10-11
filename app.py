import pandas as pd
import streamlit as st
from datetime import date

st.set_page_config(page_title="Mi app", page_icon="🧪", layout="wide")

if "inventory" not in st.session_state:
    st.session_state["inventory"] = None
df = st.session_state.inventory
@st.cache_data
def load_inventory():
    st.session_state.inventory = pd.read_csv("reactivos.csv")

load_inventory()

# set as datatime column fecha_caducidad
df.fecha_caducidad = pd.to_datetime(df.fecha_caducidad).dt.date

# add columns
df["valor"] = round(df.cantidad / 100 * df.precio_100, 2)
df["bajo_stock"] = df.cantidad < df.stock_minimo
df["caducado"] = df.fecha_caducidad > date.today()
df = df.rename(columns = {"ficha_pdf" : "ficha_url",
                          "pictograma" : "picto_url"})
df.ficha_url = "static/" + df.ficha_url
df.picto_url = "static/" + df.picto_url


st.title("Inventario de Productos Químicos")
st.subheader("Productos químicos disponibles")

st.dataframe(df,
             column_config={
                 "ficha_url": st.column_config.LinkColumn("Ficha seguridad", display_text="Abrir"),
                 "picto_url" : st.column_config.LinkColumn("Pictograma", display_text="Abrir")
    })
