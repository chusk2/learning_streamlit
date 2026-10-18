import pandas as pd
import streamlit as st
from datetime import date
import time

st.set_page_config(page_title="Mi app", page_icon="🧪", layout="wide")

# CSS
st.markdown(
    """
    <style>
    /* Contenedor principal y tipografía */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2.5rem;
        max-width: 1400px;
    }

    h1 {
        font-weight: 800 !important;
        letter-spacing: -0.02em;
        background: linear-gradient(90deg, #0f172a 0%, #0d9488 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.25rem !important;
    }

    h3 {
        color: #475569 !important;
        font-weight: 500 !important;
        margin-top: 0 !important;
        margin-bottom: 1.25rem !important;
    }

    /* Barra lateral */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f1f5f9 0%, #e2e8f0 100%);
        border-right: 1px solid #cbd5e1;
    }

    [data-testid="stSidebar"] h1 {
        font-size: 1.5rem !important;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #0d9488;
        margin-bottom: 1rem !important;
    }

    [data-testid="stSidebar"] .stButton > button {
        width: 100%;
        font-size: 0.85rem;
        padding: 0.35rem 0.75rem;
        margin-bottom: 0.5rem;
    }

    /* Pestañas (Tabs) */
    [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #e2e8f0;
        padding: 6px;
        border-radius: 12px;
        margin-bottom: 1rem;
    }

    [data-baseweb="tab"] {
        height: 40px;
        border-radius: 8px !important;
        padding: 0 18px !important;
        font-weight: 600 !important;
        color: #475569 !important;
        background-color: transparent !important;
        border: none !important;
        transition: all 0.2s ease;
    }

    [data-baseweb="tab"]:hover {
        color: #0f172a !important;
        background-color: rgba(255, 255, 255, 0.6) !important;
    }

    [aria-selected="true"][data-baseweb="tab"] {
        background-color: #ffffff !important;
        color: #0d9488 !important;
        box-shadow: 0 2px 6px rgba(15, 23, 42, 0.08);
    }

    [data-baseweb="tab-highlight"] {
        display: none;
    }

    /* Tarjetas de métricas (st.metric) */
    [data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-left: 4px solid #0d9488;
        border-radius: 12px;
        padding: 1rem 1.25rem;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }

    [data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(15, 23, 42, 0.08);
    }

    [data-testid="stMetricLabel"] {
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        color: #64748b !important;
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }

    [data-testid="stMetricValue"] {
        font-size: 1.65rem !important;
        font-weight: 700 !important;
        color: #0f172a !important;
    }

    /* Tabla de datos (st.dataframe) */
    [data-testid="stDataFrame"] {
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 2px 10px rgba(15, 23, 42, 0.04);
        background: #ffffff;
    }

    /* Botones y botón de descarga */
    .stButton > button,
    .stDownloadButton > button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        border: 1px solid #cbd5e1 !important;
        background-color: #ffffff !important;
        color: #0f172a !important;
        padding: 0.45rem 1rem !important;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.05);
        transition: all 0.18s ease !important;
    }

    .stButton > button:hover,
    .stDownloadButton > button:hover {
        border-color: #0d9488 !important;
        color: #0d9488 !important;
        background-color: #f0fdfa !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 10px rgba(13, 148, 136, 0.12);
    }

    .stButton > button:active,
    .stDownloadButton > button:active {
        transform: translateY(0);
    }

    /* Inputs y desplegables en la barra lateral */
    [data-testid="stSidebar"] [data-baseweb="input"],
    [data-testid="stSidebar"] [data-baseweb="select"] > div {
        border-radius: 8px !important;
        background-color: #ffffff !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if "inventory" not in st.session_state:
    st.session_state["inventory"] = None

# fuerzo a que sea conjunto
if "order" not in st.session_state or not isinstance(st.session_state.order, set):
    st.session_state.order = set()

if "table_counter" not in st.session_state:
    st.session_state.table_counter = 0


def limpiar_texto_reactivo():
    st.session_state.texto_reactivo = ""


def limpiar_texto_formula():
    st.session_state.texto_formula = ""


# carga del dataframe y
# creación de columnas calculadas
@st.cache_data
def load_inventory():
    df = pd.read_csv("reactivos.csv")

    # Procesar columnas dentro de la función cacheada para que solo se ejecute una vez
    df["fecha_caducidad"] = pd.to_datetime(df["fecha_caducidad"]).dt.date
    df["valor"] = round(df["cantidad"] / 100 * df["precio_100"], 2)
    df["bajo_stock"] = df["cantidad"] < df["stock_minimo"]
    df["caducado"] = df["fecha_caducidad"] < date.today()

    df = df.rename(
        columns={
            "ficha_pdf": "ficha_url",
            "pictograma": "picto_url",
            "cantidad": "unidades_stock",
        }
    )

    # Usar la ruta /app/static/ para que ImageColumn y LinkColumn funcionen
    df["ficha_url"] = "/app/static/" + df["ficha_url"].astype(str)
    df["picto_url"] = "/app/static/" + df["picto_url"].astype(str)

    return df


# Cargamos una copia limpia en cada ejecución
df = load_inventory().copy()

tab_names = [
    "Inventario",
    "Pedido",
    "Editar stock",
    "Detalle",
    "Gráficos",
    "Nuevo reactivo",
]
tabs = {k: v for k, v in zip(tab_names, st.tabs(tab_names))}

with tabs["Inventario"]:
    filtered_df = df.copy()

    st.title("Inventario de Productos Químicos")
    st.subheader("Productos químicos disponibles")

    # creación de máscara de filtrado
    mask = pd.Series(True, index=df.index)

    # filtros
    with st.sidebar:
        st.title("Filtrar reactivos")

        search_text_reactivo = st.text_input(
            "Buscar en nombre del reactivo...", key="texto_reactivo"
        )
        st.button("Limpiar búsqueda nombre producto", on_click=limpiar_texto_reactivo)

        search_text_formula = st.text_input("Buscar en fórmula del reactivo...")
        st.button("Limpiar búsqueda fórmula", on_click=limpiar_texto_formula)

        if search_text_reactivo:
            mask &= filtered_df["reactivo"].str.contains(
                search_text_reactivo, case=False, regex=False
            )

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
        if masa_molar != (0, 0):
            mask &= filtered_df["masa_molar"].between(*masa_molar)

        # reactivos con stock
        productos_bajo_stock = st.checkbox("Productos con bajo stock")
        if productos_bajo_stock:
            mask &= filtered_df["bajo_stock"]

        # productos no caducados
        if st.toggle(label="Productos no cadudados"):
            mask &= ~filtered_df.caducado

    # Oculta el índice y elige qué columnas aparecen y en qué orden (column_order).
    # Usa column_config para:
    # mostrar el pictograma como imagen (ImageColumn);
    # mostrar la pureza como barra de progreso entre 90 y 100 (ProgressColumn);
    # formatear precio_100 y valor con el símbolo €;
    # mostrar la caducidad como DD/MM/YYYY;
    # convertir ficha_url en un enlace con el texto «📄 Abrir» (LinkColumn).
    # Añade un st.download_button que descargue la tabla filtrada en CSV.

    # dataframe inventario
    filtered_df = st.dataframe(
        df[mask],
        hide_index=True,
        column_order=[
            "reactivo",
            "pureza_pct",
            "precio_100",
            "valor",
            "fecha_caducidad",
            "ficha_url",
            "picto_url",
        ],
        column_config={
            "pureza_pct": st.column_config.ProgressColumn(
                "Pureza", min_value=90, max_value=100, format="%d %%"
            ),
            "precio_100": st.column_config.NumberColumn(
                "Precio 100 ud", format="%.2f €"
            ),
            "valor": st.column_config.NumberColumn("Valor total", format="%.2f €"),
            "fecha_caducidad": st.column_config.DatetimeColumn(format="DD-MM-YYYY"),
            "ficha_url": st.column_config.LinkColumn(
                "Ficha seguridad", display_text="📄 Abrir"
            ),
            "picto_url": st.column_config.ImageColumn("pictograma"),
        },
        on_select="rerun",
        selection_mode="multi-row",
        key=f"table_key_{st.session_state.table_counter}",
    )

    # add to cart
    with st.container(horizontal=True):
        st.download_button(
            label="Descargar listado en csv",
            data=df[mask].to_csv(encoding="utf-8", index=False),
            file_name="inventario_filtrado.csv",
            mime="text/csv",
        )

        selected_rows = filtered_df.selection.rows
        if selected_rows and st.button("🛒 Añadir al pedido"):
            new_items = set(selected_rows) - st.session_state.order
            st.session_state.order.update(new_items)

            temp_container = st.empty()

            if len(new_items) > 0:
                temp_container.success(
                    f"Added {len(new_items)} new reagents to shopping cart."
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
    col1, col2, col3, col4 = st.columns([1 for _ in range(4)])

    # reactivos mostrados (sobre el total)
    with col1:
        st.metric(label="Reactivos mostrados:", value=f"{len(df[mask])} / {len(df)}")

    # valor del inventario filtrado en €
    with col2:
        st.metric(
            label="Valor total del inventario (€):",
            value=f"{sum(df[mask].valor):.2f} €",
        )

    #  número de reactivos bajo stock
    with col3:
        st.metric(
            label="Reactivos con bajo stock:",
            value=f"{len(df[df.bajo_stock])} / {len(df)}",
        )

    # número de productos caducados
    with col4:
        st.metric(
            label="Reactivos caducados:", value=f"{len(df[df.caducado])} / {len(df)}"
        )

with tabs["Pedido"]:
    # columnas a mostrar en el pedido
    # id, reactivo, fórmula, unidades_stock,
    #
    if st.session_state.order:
        df_order = df.iloc[list(st.session_state.order), :].copy()
        st.write(df_order.columns)
        df_order["unidades_pedido"] = 1
        df_order["coste_total"] = (
            df_order["unidades_stock"]
            / 100
            * df_order.precio_100
            * df_order.unidades_pedido
        )

        st.data_editor(
            df_order,
            hide_index=True,
            column_order=[
                "reactivo",
                "formula",
                "unidades_stock",
                "unidades_pedido",
                "coste_total",
            ],
            # Solo 'unidades_pedido' será editable)
            disabled=["reactivo", "formula", "unidades_stock"],
            column_config={
                "coste_total": st.column_config.NumberColumn(
                    label="Coste total", format="%.2f €"
                ),
                "unidades_pedido": st.column_config.SelectboxColumn(
                    label="Unidades pedido",
                    help="Haz doble clic en la celda para abrir el desplegable y seleccionar las unidades",
                    options=list(range(21)),
                    required=True,
                ),
            },
        )
