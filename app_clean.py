"""Inventario de reactivos de laboratorio (Streamlit).

Estructura del script (Streamlit lo ejecuta entero de arriba abajo en cada rerun):
    1. Configuración de página
    2. Estilos CSS
    3. Constantes
    4. Estado de sesión
    5. Callbacks
    6. Carga de datos
    7. Barra lateral: filtros
    8. Pestañas
    9. Pestaña «Inventario»
   10. Pestaña «Pedido»
"""

import time
import unicodedata
from datetime import date

import pandas as pd
import streamlit as st


# =============================================================================
# 1. CONFIGURACIÓN DE PÁGINA
# =============================================================================
st.set_page_config(page_title="Mi app", page_icon="🧪", layout="wide")


# =============================================================================
# 2. ESTILOS CSS
# =============================================================================

# estilo de página
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

# estilo para línea separadora
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


# =============================================================================
# 3. CONSTANTES
# =============================================================================
# str: CSV con el inventario y los datos comerciales de cada reactivo
DATA_PATH = "reactivos_comercial.csv"

# str: prefijo para servir los archivos de static/ (necesario en LinkColumn e ImageColumn)
STATIC_URL = "/app/static/"

# list[str]: nombres de las pestañas, en el orden en que se muestran
TAB_NAMES = [
    "Inventario",
    "Pedido",
    "Editar stock",
    "Detalle",
    "Gráficos",
    "Nuevo reactivo",
]

# str | int: ancho de las tarjetas de KPI ("content", "stretch" o píxeles)
KPI_WIDTH = "content"

# list[str]: columnas visibles en la tabla del pedido
ORDER_COLUMNS = [
    "reactivo",
    "formula",
    "stock_con_unidad",
    "precio_unitario",
    "cantidad_comercial_con_unidad",
    "unidades_pedido",
]


# =============================================================================
# 4. ESTADO DE SESIÓN
# =============================================================================
# Lo único que sobrevive entre reruns. Todo lo demás se recalcula cada vez.

# set[str]: ids de los reactivos que están en el pedido, p. ej. {"R003", "R017"}
if "order_ids" not in st.session_state:
    st.session_state.order_ids = set()

# dict[str, int]: unidades pedidas de cada reactivo, p. ej. {"R003": 2, "R017": 1}
if "order" not in st.session_state:
    st.session_state.order = {}

# int: versión de la tabla de inventario; al incrementarlo cambia su key y se
# limpia la selección de filas
if "inventory_table_version" not in st.session_state:
    st.session_state.inventory_table_version = 0


# =============================================================================
# 5. CALLBACKS
# =============================================================================
# Se ejecutan ANTES del rerun, así que el script ya se pinta con el estado nuevo.


def clear_name_search():
    """Vacía el buscador por nombre de reactivo."""
    st.session_state.name_query = ""


def clear_formula_search():
    """Vacía el buscador por fórmula."""
    st.session_state.formula_query = ""


def update_quantity(item_id):
    """Copia al pedido el valor del number_input del reactivo `item_id`."""
    st.session_state.order[item_id] = st.session_state[f"qty_{item_id}"]


def remove_item(item_id):
    """Quita un reactivo del pedido."""
    st.session_state.order_ids.discard(item_id)
    st.session_state.order.pop(item_id, None)


def clear_order():
    """Vacía el pedido completo y vuelve a la pestaña Inventario."""
    st.session_state.order_ids.clear()
    st.session_state.order.clear()
    st.session_state.active_tab = "Inventario"
    st.toast("Pedido eliminado", icon="🗑️")


# =============================================================================
# 6. CARGA DE DATOS
# =============================================================================


def with_unit(values, states):
    """Devuelve list[str] con cada valor seguido de "g" (sólidos) o "mL" (líquidos)."""
    return [
        f"{value} g" if state == "Sólido" else f"{value} mL"
        for value, state in zip(values, states)
    ]


def strip_accents(text):
    """Devuelve `text` (str) en minúsculas y sin tildes ni diéresis: "Ácido" -> "acido"."""
    # NFD separa cada letra de su tilde ("Á" -> "A" + "´"); luego se descartan
    # las tildes, que son caracteres de categoría "Mn" (marca diacrítica)
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(c for c in decomposed if unicodedata.category(c) != "Mn").lower()


@st.cache_data
def load_inventory():
    """Lee el CSV y añade las columnas calculadas (se ejecuta una sola vez)."""
    df = pd.read_csv(DATA_PATH)

    df["fecha_caducidad"] = pd.to_datetime(df["fecha_caducidad"]).dt.date

    # columnas calculadas
    df["bajo_stock"] = df["cantidad"] < df["stock_minimo"]  # bool
    df["caducado"] = df["fecha_caducidad"] < date.today()  # bool
    df["stock_con_unidad"] = with_unit(df["cantidad"], df["estado"])  # str: "817 mL"
    df["cantidad_comercial_con_unidad"] = with_unit(
        df["cantidad_comercial"], df["estado"]
    )  # str: "1000 mL"

    # rutas a los archivos de static/
    df = df.rename(columns={"ficha_pdf": "ficha_url", "pictograma": "picto_url"})
    df["ficha_url"] = STATIC_URL + df["ficha_url"].astype(str)
    df["picto_url"] = STATIC_URL + df["picto_url"].astype(str)

    return df


# pd.DataFrame: inventario completo (copia para no modificar el resultado cacheado)
inventory_df = load_inventory().copy()


# =============================================================================
# 7. BARRA LATERAL: FILTROS
# =============================================================================
# pd.Series[bool]: True en las filas del inventario que cumplen todos los filtros
filter_mask = pd.Series(True, index=inventory_df.index)

with st.sidebar:
    st.title("Filtrar reactivos")

    # --- búsqueda por texto -------------------------------------------------
    # str: texto buscado en el nombre del reactivo
    name_query = st.text_input("Buscar en nombre del reactivo...", key="name_query")
    st.button("Limpiar búsqueda nombre producto", on_click=clear_name_search)

    # str: texto buscado en la fórmula
    formula_query = st.text_input("Buscar en fórmula del reactivo...", key="formula_query")
    st.button("Limpiar búsqueda fórmula", on_click=clear_formula_search)

    if name_query:
        filter_mask &= inventory_df["reactivo"].str.contains(
            name_query, case=False, regex=False
        )
    if formula_query:
        filter_mask &= inventory_df["formula"].str.contains(
            formula_query, case=False, regex=False
        )

    # --- categoría ----------------------------------------------------------
    # list[str]: categorías elegidas (vacía = todas)
    selected_categories = st.multiselect(
        "Elige categoría",
        inventory_df["categoria"].unique(),
        default=None,
        placeholder="Elige categoría(s) de reactivo...",
    )
    if selected_categories:
        filter_mask &= inventory_df["categoria"].isin(selected_categories)

    # --- ubicación ----------------------------------------------------------
    # str: ubicación elegida, o "Todas"
    selected_location = st.selectbox(
        "Ubicación",
        ["Todas"] + list(inventory_df["ubicacion"].unique()),
        index=0,
        placeholder="Elige ubicación del reactivo...",
    )
    if selected_location != "Todas":
        filter_mask &= inventory_df["ubicacion"] == selected_location

    # --- estado de agregación -----------------------------------------------
    # str: "Todos", "Líquido" o "Sólido"
    selected_state = st.radio(
        "Estado de agregación", ["Todos", "Líquido", "Sólido"], horizontal=True
    )
    if selected_state != "Todos":
        filter_mask &= inventory_df["estado"] == selected_state

    # --- masa molar ---------------------------------------------------------
    molar_mass_min = float(inventory_df["masa_molar"].min())  # float
    molar_mass_max = float(inventory_df["masa_molar"].max())  # float

    # tuple[float, float]: rango (mínimo, máximo) elegido en el slider
    molar_mass_range = st.slider(
        label="Masa molar",
        min_value=molar_mass_min,
        max_value=molar_mass_max,
        value=(molar_mass_min, molar_mass_max),
        step=0.1,
    )
    filter_mask &= inventory_df["masa_molar"].between(*molar_mass_range)

    # --- stock y caducidad --------------------------------------------------
    # bool: mostrar solo reactivos por debajo del stock mínimo
    only_low_stock = st.checkbox("Productos con bajo stock")
    if only_low_stock:
        filter_mask &= inventory_df["bajo_stock"]

    # bool: ocultar los reactivos caducados
    only_not_expired = st.toggle("Productos no caducados")
    if only_not_expired:
        filter_mask &= ~inventory_df["caducado"]

# pd.DataFrame: inventario filtrado y ordenado. El índice se resetea para que
# las posiciones de selection.rows coincidan con las etiquetas de .loc.
# Se ordena sin tildes para que "Ácido" vaya con la A y no detrás de la Z.
filtered_df = (
    inventory_df[filter_mask]
    .sort_values("reactivo", key=lambda names: names.map(strip_accents))
    .reset_index(drop=True)
)


# =============================================================================
# 8. PESTAÑAS
# =============================================================================
# dict[str, DeltaGenerator]: contenedor de cada pestaña, por nombre
tabs = dict(
    zip(TAB_NAMES, st.tabs(TAB_NAMES, key="active_tab", on_change="rerun"))
)


# =============================================================================
# 9. PESTAÑA «INVENTARIO»
# =============================================================================
with tabs["Inventario"]:
    # --- 9.1 cabecera: título + botones -------------------------------------
    # se rellena en dos tiempos: el título ahora y los botones tras la tabla,
    # porque el botón de añadir necesita conocer la selección
    header_bar = st.container(
        horizontal=True, horizontal_alignment="left", vertical_alignment="center"
    )
    with header_bar:
        st.title("Inventario de Productos Químicos")

    # --- 9.2 tabla del inventario -------------------------------------------
    # objeto de selección de st.dataframe (no es un DataFrame):
    # inventory_event.selection.rows -> list[int] con las posiciones marcadas
    inventory_event = st.dataframe(
        filtered_df,
        hide_index=True,
        column_order=[
            "reactivo",
            "pureza_pct",
            "stock_con_unidad",
            "fecha_caducidad",
            "ficha_url",
            "picto_url",
        ],
        column_config={
            "reactivo": "Reactivo",
            "stock_con_unidad": "Cantidad disponible",
            "pureza_pct": st.column_config.ProgressColumn(
                "Pureza", min_value=90, max_value=100, format="%d %%"
            ),
            "fecha_caducidad": st.column_config.DatetimeColumn(
                "Fecha de caducidad", format="DD-MM-YYYY"
            ),
            "ficha_url": st.column_config.LinkColumn(
                "Ficha seguridad", display_text="📄 Abrir"
            ),
            "picto_url": st.column_config.ImageColumn("Pictograma"),
        },
        on_select="rerun",
        selection_mode="multi-row",
        key=f"inventory_table_{st.session_state.inventory_table_version}",
    )

    # --- 9.3 descargar CSV y añadir al pedido -------------------------------
    with header_bar:
        st.download_button(
            label="Descargar listado en csv",
            data=filtered_df.to_csv(encoding="utf-8", index=False),
            file_name="inventario_filtrado.csv",
            mime="text/csv",
        )

        # list[str]: ids de las filas seleccionadas en la tabla
        selected_ids = filtered_df.loc[inventory_event.selection.rows, "id"].tolist()

        if selected_ids and st.button("🛒 Añadir al pedido"):
            # set[str]: ids seleccionados que aún no estaban en el pedido
            new_ids = set(selected_ids) - st.session_state.order_ids

            st.session_state.order_ids.update(new_ids)
            for item_id in new_ids:
                st.session_state.order.setdefault(item_id, 1)  # 1 unidad por defecto

            # mensaje temporal de confirmación
            feedback = st.empty()
            if new_ids:
                feedback.success(f"Añadidos {len(new_ids)} reactivos al pedido.")
            else:
                feedback.warning("Esos reactivos ya están en el pedido.")
            time.sleep(1)
            feedback.empty()

            # limpiar la selección cambiando la key de la tabla
            st.session_state.inventory_table_version += 1
            st.rerun()

    # --- 9.4 KPIs -----------------------------------------------------------
    total_count = len(inventory_df)  # int

    # dict[str, str]: etiqueta -> valor de cada tarjeta
    kpi_values = {
        "Reactivos mostrados:": f"{len(filtered_df)} / {total_count}",
        "Reactivos con bajo stock:": f"{inventory_df['bajo_stock'].sum()} / {total_count}",
        "Reactivos caducados:": f"{inventory_df['caducado'].sum()} / {total_count}",
    }

    with st.container(horizontal=True):
        kpi_cols = st.columns(len(kpi_values))
        for kpi_col, (label, value) in zip(kpi_cols, kpi_values.items()):
            kpi_col.metric(label, value, width=KPI_WIDTH)


# =============================================================================
# 10. PESTAÑA «PEDIDO»
# =============================================================================
with tabs["Pedido"]:
    if not st.session_state.order_ids:
        st.markdown("### Aún no se han añadido artículos al carrito de compra.")

    else:
        # --- 10.1 construir el pedido a partir del estado -------------------
        # pd.DataFrame: una fila por reactivo del pedido, con unidades y subtotal.
        # Se reconstruye en cada rerun desde order_ids y order: no se guarda.
        order_df = inventory_df[
            inventory_df["id"].isin(st.session_state.order_ids)
        ].reset_index(drop=True)
        order_df["unidades_pedido"] = order_df["id"].map(st.session_state.order)  # int
        order_df["coste_subtotal"] = (
            order_df["unidades_pedido"] * order_df["precio_unitario"]
        )  # float, €

        # --- 10.2 tabla resumen (solo lectura) ------------------------------
        st.dataframe(
            order_df,
            hide_index=True,
            column_order=ORDER_COLUMNS,
            column_config={
                "reactivo": "Reactivo",
                "formula": "Fórmula",
                "stock_con_unidad": "Cantidad existente",
                "cantidad_comercial_con_unidad": "Capacidad producto comercial",
                "precio_unitario": st.column_config.NumberColumn(
                    "Precio unitario", format="%.2f €"
                ),
                "unidades_pedido": "Unidades pedido",
            },
            key="order_table",
        )

        # --- 10.3 líneas de edición: cabecera -------------------------------
        header_cols = st.columns(5)
        for header_col, title in zip(
            header_cols,
            ["Reactivo", "Unidades", "Precio unitario", "Subtotal", "Eliminar"],
        ):
            header_col.markdown(f"**{title}**")
        st.divider()

        # --- 10.4 líneas de edición: una por reactivo -----------------------
        # Las keys usan el id (no la posición) para que cada widget siga
        # ligado a su reactivo aunque se añadan o borren filas.
        for row in order_df.itertuples():
            name_col, qty_col, price_col, subtotal_col, delete_col = st.columns(
                5, vertical_alignment="center"
            )

            name_col.write(row.reactivo)
            qty_col.number_input(
                label="Unidades pedido",
                label_visibility="collapsed",
                min_value=1,
                value=row.unidades_pedido,
                step=1,
                on_change=update_quantity,
                args=(row.id,),
                key=f"qty_{row.id}",
            )
            price_col.write(f"{row.precio_unitario:.2f} €")
            subtotal_col.write(f"{row.coste_subtotal:.2f} €")
            delete_col.button(
                "🗑️", on_click=remove_item, args=(row.id,), key=f"delete_{row.id}"
            )
            st.divider()

        # --- 10.5 total y vaciar pedido -------------------------------------
        with st.container(
            horizontal=True, horizontal_alignment="left", vertical_alignment="center"
        ):
            st.metric(
                label="Coste total del pedido",
                value=f"{order_df['coste_subtotal'].sum():.2f} €",
                width="content",
            )
            st.button("Borrar pedido 🗑️", on_click=clear_order)
