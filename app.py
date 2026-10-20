import pandas as pd
import streamlit as st
from datetime import date
import time
import unicodedata

st.set_page_config(page_title="Mi app", page_icon="🧪", layout="wide")

st.markdown(
    """
    <style>
    .block-container { max-width: 1200px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# CSS
# st.markdown(
#     """
#     <style>
#     /* Contenedor principal y tipografía */
#     .block-container {
#         padding-top: 2rem;
#         padding-bottom: 2.5rem;
#         max-width: 1400px;
#     }

#     h1 {
#         font-weight: 800 !important;
#         letter-spacing: -0.02em;
#         background: linear-gradient(90deg, #0f172a 0%, #0d9488 100%);
#         -webkit-background-clip: text;
#         -webkit-text-fill-color: transparent;
#         margin-bottom: 0.25rem !important;
#     }

#     h3 {
#         color: #475569 !important;
#         font-weight: 500 !important;
#         margin-top: 0 !important;
#         margin-bottom: 1.25rem !important;
#     }

#     /* Barra lateral */
#     [data-testid="stSidebar"] {
#         background: linear-gradient(180deg, #f1f5f9 0%, #e2e8f0 100%);
#         border-right: 1px solid #cbd5e1;
#     }

#     [data-testid="stSidebar"] h1 {
#         font-size: 1.5rem !important;
#         padding-bottom: 0.5rem;
#         border-bottom: 2px solid #0d9488;
#         margin-bottom: 1rem !important;
#     }

#     [data-testid="stSidebar"] .stButton > button {
#         width: 100%;
#         font-size: 0.85rem;
#         padding: 0.35rem 0.75rem;
#         margin-bottom: 0.5rem;
#     }

#     /* Pestañas (Tabs) */
#     [data-baseweb="tab-list"] {
#         gap: 8px;
#         background-color: #e2e8f0;
#         padding: 6px;
#         border-radius: 12px;
#         margin-bottom: 1rem;
#     }

#     [data-baseweb="tab"] {
#         height: 40px;
#         border-radius: 8px !important;
#         padding: 0 18px !important;
#         font-weight: 600 !important;
#         color: #475569 !important;
#         background-color: transparent !important;
#         border: none !important;
#         transition: all 0.2s ease;
#     }

#     [data-baseweb="tab"]:hover {
#         color: #0f172a !important;
#         background-color: rgba(255, 255, 255, 0.6) !important;
#     }

#     [aria-selected="true"][data-baseweb="tab"] {
#         background-color: #ffffff !important;
#         color: #0d9488 !important;
#         box-shadow: 0 2px 6px rgba(15, 23, 42, 0.08);
#     }

#     [data-baseweb="tab-highlight"] {
#         display: none;
#     }

#     /* Tarjetas de métricas (st.metric) */
#     [data-testid="stMetric"] {
#         background: #ffffff;
#         border: 1px solid #e2e8f0;
#         border-left: 4px solid #0d9488;
#         border-radius: 12px;
#         padding: 1rem 1.25rem;
#         box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
#         transition: transform 0.15s ease, box-shadow 0.15s ease;
#     }

#     [data-testid="stMetric"]:hover {
#         transform: translateY(-2px);
#         box-shadow: 0 6px 16px rgba(15, 23, 42, 0.08);
#     }

#     [data-testid="stMetricLabel"] {
#         font-size: 0.85rem !important;
#         font-weight: 600 !important;
#         color: #64748b !important;
#         text-transform: uppercase;
#         letter-spacing: 0.03em;
#     }

#     [data-testid="stMetricValue"] {
#         font-size: 1.65rem !important;
#         font-weight: 700 !important;
#         color: #0f172a !important;
#     }

#     /* Tabla de datos (st.dataframe) */
#     [data-testid="stDataFrame"] {
#         border: 1px solid #e2e8f0;
#         border-radius: 12px;
#         overflow: hidden;
#         box-shadow: 0 2px 10px rgba(15, 23, 42, 0.04);
#         background: #ffffff;
#     }

#     /* Botones y botón de descarga */
#     .stButton > button,
#     .stDownloadButton > button {
#         border-radius: 8px !important;
#         font-weight: 600 !important;
#         border: 1px solid #cbd5e1 !important;
#         background-color: #ffffff !important;
#         color: #0f172a !important;
#         padding: 0.45rem 1rem !important;
#         box-shadow: 0 1px 3px rgba(15, 23, 42, 0.05);
#         transition: all 0.18s ease !important;
#     }

#     .stButton > button:hover,
#     .stDownloadButton > button:hover {
#         border-color: #0d9488 !important;
#         color: #0d9488 !important;
#         background-color: #f0fdfa !important;
#         transform: translateY(-1px);
#         box-shadow: 0 4px 10px rgba(13, 148, 136, 0.12);
#     }

#     .stButton > button:active,
#     .stDownloadButton > button:active {
#         transform: translateY(0);
#     }

#     /* Inputs y desplegables en la barra lateral */
#     [data-testid="stSidebar"] [data-baseweb="input"],
#     [data-testid="stSidebar"] [data-baseweb="select"] > div {
#         border-radius: 8px !important;
#         background-color: #ffffff !important;
#     }
#     </style>
#     """,
#     unsafe_allow_html=True,
# )

# CSS para línea separadora
st.markdown(
    """
            <style>
            hr {
            margin: 0.5rem 0 !important; 
            border: 1px solid #4FC3F7 !important}
            </style>
            """,
    unsafe_allow_html=True,
)

# order_dict: {"R034" : 3 ud}
if "order_dict" not in st.session_state:
    st.session_state.order_dict = {}

if "table_counter" not in st.session_state:
    st.session_state.table_counter = 0


def limpiar_texto_reactivo():
    st.session_state.texto_reactivo = ""


def limpiar_texto_formula():
    st.session_state.texto_formula = ""

def strip_accents(text):
    """Devuelve `text` (str) en minúsculas y sin tildes ni diéresis: "Ácido" -> "acido"."""
    # NFD separa cada letra de su tilde ("Á" -> "A" + "´"); luego se descartan
    # las tildes, que son caracteres de categoría "Mn" (marca diacrítica)
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(c for c in decomposed if unicodedata.category(c) != "Mn").lower()

def add_units(row):
    cantidad = row.iloc[0]
    estado = row.iloc[1]
    if estado == "Sólido":
        return f"{cantidad} g"
    elif estado == "Líquido":
        return f"{cantidad} mL"
    else:
        return cantidad


#######################
### CARGA DATAFRAME ###
#######################
@st.cache_data
def load_inventory():
    df = pd.read_csv("reactivos_comercial.csv")

    # Procesar columnas dentro de la función cacheada para que solo se ejecute una vez
    df["fecha_caducidad"] = pd.to_datetime(df["fecha_caducidad"]).dt.date
    df["bajo_stock"] = df["cantidad"] < df["stock_minimo"]
    df["caducado"] = df["fecha_caducidad"] < date.today()
    df["stock_ud"] = df.loc[:, ["cantidad", "estado"]].apply(add_units, axis = 1)
    df["cantidad_comercial_ud"] = df.loc[:, ["cantidad_comercial", "estado"]].apply(add_units, axis = 1)
    df = df.rename(
        columns={
            "ficha_pdf": "ficha_url",
            "pictograma": "picto_url",
        }
    )

    # Usar la ruta /app/static/ para que ImageColumn y LinkColumn funcionen
    df["ficha_url"] = "/app/static/" + df["ficha_url"].astype(str)
    df["picto_url"] = "/app/static/" + df["picto_url"].astype(str)

    return df


# Cargamos una copia limpia en cada ejecución
df = load_inventory().copy()

#######################
######## FILTROS ######
#######################

# filtros
with st.sidebar:
    st.title("Filtrar reactivos")

    filtered_df = df.copy()
    # creación de máscara de filtrado
    mask = pd.Series(True, index=df.index)

    search_text_reactivo = st.text_input(
        "Buscar en nombre del reactivo...", key="texto_reactivo"
    )
    st.button("Limpiar", on_click=limpiar_texto_reactivo, key="limpiar_reactivo")

    search_text_formula = st.text_input("Buscar fórmula...", key="texto_formula")
    st.button("Limpiar", on_click=limpiar_texto_formula, key="limpiar_formula")

    if search_text_reactivo:
        mask &= filtered_df["reactivo"].str.contains(search_text_reactivo,
                                                     case=False, regex=False)

    if search_text_formula:
        mask &= filtered_df["formula"].str.contains(
            search_text_formula, case=False, regex=False
        )

    categorias = st.multiselect(
        "Elige categoría",
        filtered_df.categoria.unique(),
        default=None,
        placeholder="Elige categoría(s) de reactivo...",
    )
    if categorias:
        mask &= filtered_df["categoria"].isin(categorias)

    ubicacion = st.selectbox(
        "Ubicación",
        ["Todas"] + list(filtered_df["ubicacion"].unique()),
        index=0,
        placeholder="Elige ubicación del reactivo...",
    )
    if ubicacion != "Todas":
        mask &= filtered_df.ubicacion == ubicacion

    estado = st.radio(
        "Estado de agregación", ["Todos", "Líquido", "Sólido"], horizontal=True
    )
    if estado != "Todos":
        mask &= filtered_df.estado == estado

    # masa molar
    masa_min = float(df["masa_molar"].min())
    masa_max = float(df["masa_molar"].max())

    masa_molar = st.slider(
        label="Masa molar",
        min_value=masa_min,
        max_value=masa_max,
        value=(masa_min, masa_max),
        step=0.1,
    )

    # filtrar la masa molar
    mask &= filtered_df["masa_molar"].between(*masa_molar)

    # reactivos con stock
    productos_bajo_stock = st.checkbox("Productos con bajo stock")
    if productos_bajo_stock:
        mask &= filtered_df["bajo_stock"]

    # productos caducados
    if st.toggle(label="Productos cadudados"):
        mask &= filtered_df.caducado

    

#######################
######## TABS ######
#######################

tab_names = [
    "Inventario",
    "Pedido",
    "Editar stock",
    "Detalle",
    "Gráficos",
    "Nuevo reactivo",
]
tabs = {
    k: v
    for k, v in zip(tab_names, st.tabs(tab_names, key="active_tab", on_change="rerun"))
}

#######################
##### INVENTARIO ######
#######################

with tabs["Inventario"]:

    # dataframe filtrado
    filtered_df = (df[mask]
                   .sort_values("reactivo", key=lambda names: names.map(strip_accents))
                   .reset_index()
                   )
    
    if len(filtered_df) == 0:
        st.markdown("### No existen productos que cumplan el filtro actual.")
    else:
        cart = st.container(horizontal=True, horizontal_alignment="left", 
                            vertical_alignment="center")

        with cart:
            st.title("Inventario de Productos Químicos")

        # dataframe inventario
        event = st.dataframe(
            filtered_df,
            hide_index=True,
            column_order=[
                "reactivo",
                "pureza_pct",
                "stock_ud",
                "fecha_caducidad",
                "ficha_url",
                "picto_url",
            ],
            column_config={
                "reactivo" : "Reactivo",
                "stock_ud": "Cantidad actual",
                "pureza_pct": st.column_config.ProgressColumn(
                    "Pureza", min_value=90, max_value=100, format="%d %%"
                ),
                "fecha_caducidad": st.column_config.DatetimeColumn("Fecha caducidad", format="DD-MM-YYYY"),
                "ficha_url": st.column_config.LinkColumn(
                    "Ficha seguridad", display_text="📄 Abrir"
                ),
                "picto_url": st.column_config.ImageColumn("Pictograma seguridad"),
            },
            on_select="rerun",
            selection_mode="multi-row",
            key=f"table_key_{st.session_state.table_counter}",
        )

        with cart:
            st.download_button(
                label="Descargar listado en csv",
                data=df[mask].to_csv(encoding="utf-8", index=False),
                file_name="inventario_filtrado.csv",
                mime="text/csv",
            )

            if "order_round" not in st.session_state:
                st.session_state.order_round = 0

            # guarda los valores de ID de reactivo de las filas seleccionadas
            selected_ids = filtered_df.loc[event.selection.rows, "id"]
            if len(selected_ids) > 0 and st.button(
                "🛒 Añadir al pedido"):
                new_order_ids = [
                    id_ for id_ in selected_ids if id_ not in st.session_state.order_dict
                ]
                # inicializar las cantidades de los reactivos
                # añadidos al pedido a 1
                new_order_dict = {id_: 1 for id_ in new_order_ids}
                st.session_state.order_dict.update(new_order_dict)

                # container para mensajes
                temp_container = st.empty()

                if len(new_order_ids) > 0:
                    temp_container.success(
                        f"Added {len(new_order_ids)} new reagents to shopping cart."
                    )
                    time.sleep(1)
                    temp_container.empty()
                else:
                    temp_container.warning("Items already in shopping cart!")
                    time.sleep(1)
                    temp_container.empty()

                # limpio la selección
                st.session_state.table_counter += 1
                st.rerun()

            # KPI's
            with st.container(horizontal=True):
                KPI_WIDTH = "content"  # o 250, o "stretch"

                kpi_values = {
                    "Reactivos mostrados:": f"{len(df[mask])} / {len(df)}",
                    "Reactivos con bajo stock:": f"{len(df[df.bajo_stock])} / {len(df)}",
                    "Reactivos caducados:": f"{len(df[df.caducado])} / {len(df)}",
                }

                cols = st.columns(len(kpi_values))
                for col, (label, value) in zip(cols, kpi_values.items()):
                    col.metric(label, value, width=KPI_WIDTH)

with tabs["Pedido"]:

    if len(st.session_state.order_dict) == 0:
        st.markdown("### Sin artículos añadidos al pedido.")

    else:

        # cabecera: "Pedido de reactivos"
        st.markdown("## Pedido de reactivos")

        # inicializar order_df
        order_df = (df.set_index("id")
                    .loc[list(st.session_state.order_dict)]
                    .reset_index())
        
        order_df["unidades_pedido"] = order_df["id"].map(st.session_state.order_dict)
        order_df["coste_subtotal"] = order_df["unidades_pedido"] * order_df["precio_unitario"]

        # rellena order_df.unidades_pedido a partir del dict order_dict {id_reactivo : qty}
        # recupera value del order_dict cuya clave coincida con order_df.id
        order_df["unidades_pedido"] = order_df["id"].map(st.session_state.order_dict)

        # cálculo de los subtotales
        order_df["coste_subtotal"] = order_df.unidades_pedido * order_df.precio_unitario

        # resetea el índice
        order_df.reset_index(drop=True, inplace=True)

        # st.dataframe con reactivos del pedido
        cols_to_show = [
            "reactivo",
            "stock_ud",
            "cantidad_comercial_ud",
            "unidades_pedido",
            "precio_unitario",            
        ]

        st.dataframe(
            order_df,
            hide_index=True,
            column_order=cols_to_show,
            column_config={
                "reactivo": "Reactivo",
                "stock_ud": "Stock actual",
                "cantidad_comercial_ud": "Cantidad comercial",
                "precio_unitario": st.column_config.NumberColumn(
                    "Precio unitario", format="%.2f €"
                ),
                "unidades_pedido": "Unidades pedido",
            },
            key="order_table",
        )

        # headers
        PROPORCIONES = [0.5, 0.6, 1, 1, 0.6]
        h1, h2, h3, h4, h5 = st.columns(PROPORCIONES)
        h1.markdown("**Eliminar**")
        h2.markdown("**Reactivo**")
        h3.markdown("**Unidades**")
        h4.markdown("**Precio unitario**")
        h5.markdown("**Subtotal**")
        
        st.divider()

        def update_quantities(id_):
            # order -> {id_reactivo : cantidad}
            st.session_state.order_dict[id_] = st.session_state[f"qty_{id_}"]

        def remove_item(id_):
            del st.session_state.order_dict[id_]

        def remove_order():
            st.session_state["order_dict"] = {}
            # mover a Inventario
            st.session_state.active_tab = "Inventario"
            st.toast("Pedido eliminado", icon="🗑️")

        # listado de productos en el pedido
        for index, row in order_df.iterrows():
            col1, col2, col3, col4, col5 = st.columns(
                PROPORCIONES, vertical_alignment="center"
            )

            # eliminar artículo del pedido
            col1.button(
                            label="🗑️", on_click=remove_item, args=(row.id,), key=f"borrar_{row.id}"
                        )
            
            # reactivo
            col2.write(row.reactivo)

            # unidades
            col3.number_input(
                label="",
                min_value=1,
                value=row.unidades_pedido,
                step=1,
                on_change=update_quantities,
                # IMPORTANTE: args recibe tuplas! (value1, )
                args=(row.id,),
                key=f"qty_{row.id}",
            )

            # coste_unitario
            col4.write(f"{row.precio_unitario:.2f} €")

            # coste_total
            col5.write(
                f"{row.precio_unitario * row.unidades_pedido:.2f} €"
            )  

            # borrar artículo del pedido
            
            st.divider()

        # total del pedido
        with st.container(
            horizontal=True, horizontal_alignment="right", vertical_alignment="center"
        ):
            # botón de limpieza del pedido
            st.button("Borrar pedido 🗑️", on_click=remove_order)
            
            # KPI con total pedido
            st.metric(
                label="Coste total del pedido",
                value=f"{order_df.coste_subtotal.sum():.2f} €",
                width="content",
            )

with tabs["Editar stock"] :

    # separar unidades de la cantidad
    # para poder editar la cantidad
    df_stock = df[mask].copy()
    if len(df_stock) == 0:
        st.markdown("### No existen productos que cumplan el filtro actual.")
    else:
        parts = df_stock.stock_ud.str.split(expand=True)
        df_stock["unidades_reactivo"] = parts[1]

        with st.container(horizontal=False, horizontal_alignment="center", width = "stretch"):
            st.markdown("## Edita los artículos del inventario")
            edited_stock_df = st.data_editor(
                df_stock,
                width=600,
                hide_index=True,
                column_order= ["id", "reactivo", "cantidad", "stock_minimo", "unidades_reactivo"],
                column_config={
                    "id" : "ID",
                    "reactivo" : "Reactivo",
                    "cantidad" : "Stock actual",
                    "stock_minimo" : "Stock mínimo necesario",
                    "unidades_reactivo" : "Unidad medida"
                },
                disabled = ["id", "reactivo", "unidades_reactivo"],
                key ="stock_editor"
            )
        with st.container(horizontal=True, vertical_alignment="center"):

                edited_reagents = len(st.session_state.stock_editor["edited_rows"])
                if edited_reagents > 0:
                    if edited_reagents == 1:
                        st.write(f"Se ha editado 1 reactivo.")
                    else:
                        st.write(f"Se han editado {edited_reagents} reactivos.")

                updated_stock_df = edited_stock_df.iloc[:,:-5]  # excluir columnas calculadas
                # eliminar "/app/static/" de las rutas
                updated_stock_df["ficha_url"] = updated_stock_df.ficha_url.str.replace("/app/static/", "")
                updated_stock_df["picto_url"] = updated_stock_df.picto_url.str.replace("/app/static/", "")

                if st.download_button(label = "Guardar stock actualizado",
                                data = updated_stock_df.to_csv(index = False),
                                file_name = "reactivos_comercial.csv",
                                mime="text/csv"):
                    load_inventory.clear()

