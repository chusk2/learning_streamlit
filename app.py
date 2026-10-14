import pandas as pd
import streamlit as st
from datetime import date

st.set_page_config(page_title="Mi app", page_icon="🧪", layout="wide")

if "inventory" not in st.session_state:
    st.session_state["inventory"] = None

@st.cache_data
def load_inventory():
    st.session_state.inventory = pd.read_csv("reactivos.csv")

load_inventory()
df = st.session_state.inventory

def limpiar_texto_reactivo():
     st.session_state.texto_reactivo = ""

def limpiar_texto_formula():
     st.session_state.texto_formula = ""

# set as datatime column fecha_caducidad
df.fecha_caducidad = pd.to_datetime(df.fecha_caducidad).dt.date

# add columns
df["valor"] = round(df.cantidad / 100 * df.precio_100, 2)
df["bajo_stock"] = df.cantidad < df.stock_minimo
df["caducado"] = df.fecha_caducidad < date.today()
df = df.rename(columns = {"ficha_pdf" : "ficha_url",
                          "pictograma" : "picto_url"})
df.ficha_url = "static/" + df.ficha_url
df.picto_url = "static/" + df.picto_url

filtered_df = df.copy()

st.title("Inventario de Productos Químicos")
st.subheader("Productos químicos disponibles")

# creación de máscara de filtrado
mask = pd.Series(True, index = df.index)

with st.sidebar:

    st.title("Filtrar reactivos")
    
    search_text_reactivo = st.text_input("Buscar en nombre del reactivo...",
                                         key = "texto_reactivo").lower()
    st.button("Limpiar búsqueda nombre producto", on_click=limpiar_texto_reactivo)

    search_text_formula = st.text_input("Buscar en fórmula del reactivo...").lower()
    st.button("Limpiar búsqueda fórmula", on_click=limpiar_texto_formula)

    if search_text_reactivo:
        mask &= filtered_df.reactivo.str.lower().str.contains(search_text_reactivo)

    if search_text_formula:
        mask &= filtered_df.formula.str.lower().str.contains(search_text_formula)
        
    categorias = st.multiselect("Elige categoría", filtered_df.categoria.unique(),
                             default = None, placeholder="Elige categoría(s) de reactivo...")
    if len(categorias) > 0:
            mask &= filtered_df.categoria.isin(categorias)

    ubicacion = st.selectbox("Ubicación", filtered_df.ubicacion.unique(), index=None,
                             placeholder="Elige ubicación del reactivo...")
    if ubicacion:
         mask &= filtered_df.ubicacion == ubicacion

    estado = st.radio("Estado de agregación", ["Todos", "Líquido", "Sólido"], horizontal=True)
    if estado != "Todos":
         mask &= filtered_df.estado == estado

    # masa molar
    # masa_min = float(df["masa_molar"].min())
    # masa_max = float(df["masa_molar"].max())

    # masa_molar = st.slider(label = "Masa molar",
    #                        min_value=masa_min,
    #                        max_value= masa_max,
    #                        value = (masa_min, masa_max),
    #                        step = 0.1)
    # if masa_molar != (0,0):
    #      filtered_df = filtered_df[filtered_df.masa_molar.between(*masa_molar)]

    # reactivos con stock
    productos_bajo_stock = st.checkbox("Productos con bajo stock")
    mask &= filtered_df.bajo_stock == productos_bajo_stock

    # productos no caducados
    if st.toggle(label="Productos no cadudados"):
         mask &= ~filtered_df.caducado

st.dataframe(df[mask],
             column_config={
                 "ficha_url": st.column_config.LinkColumn("Ficha seguridad", display_text="Abrir"),
                 "picto_url" : st.column_config.LinkColumn("Pictograma", display_text="Abrir")
    },
    hide_index = True)


col1, col2, col3, col4 = st.columns([1 for _ in range(4)])

# reactivos mostrados (sobre el total)
with col1:
    st.metric(label = "Reactivos mostrados:",
              value = f"{len(df[mask])} / {len(df)}")

# valor del inventario filtrado en €
with col2:
     st.metric(label = "Valor total del inventario (€):",
                   value = f"{sum(df[mask].valor):.2f} €")

#  número de reactivos bajo stock
with col3:
     st.metric(label = "Reactivos con bajo stock:",
              value = f"{len(df[df.bajo_stock])} / {len(df)}")

# número de productos caducados
with col4:
     st.metric(label = "Reactivos caducados:",
              value = f"{len(df[df.caducado])} / {len(df)}")


