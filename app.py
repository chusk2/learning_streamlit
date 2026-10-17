import pandas as pd
import streamlit as st
from datetime import date
import time

st.set_page_config(page_title="Mi app", page_icon="🧪", layout="wide")

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


@st.cache_data
def load_inventory():
    df = pd.read_csv("reactivos.csv")

    # Procesar columnas dentro de la función cacheada para que solo se ejecute una vez
    df["fecha_caducidad"] = pd.to_datetime(df["fecha_caducidad"]).dt.date
    df["valor"] = round(df["cantidad"] / 100 * df["precio_100"], 2)
    df["bajo_stock"] = df["cantidad"] < df["stock_minimo"]
    df["caducado"] = df["fecha_caducidad"] < date.today()

    df = df.rename(columns={"ficha_pdf": "ficha_url", "pictograma": "picto_url"})

    # Usar la ruta /app/static/ para que ImageColumn y LinkColumn funcionen
    df["ficha_url"] = "/app/static/" + df["ficha_url"].astype(str)
    df["picto_url"] = "/app/static/" + df["picto_url"].astype(str)

    return df


# Cargamos una copia limpia en cada ejecución
df = load_inventory().copy()

tab_names = ["Inventario", "Editar stock", "Detalle", "Gráficos", "Nuevo reactivo"]
tabs = {k: v for k, v in zip(tab_names, st.tabs(tab_names))}

with tabs["Inventario"]:
    filtered_df = df.copy()

    st.title("Inventario de Productos Químicos")
    st.subheader("Productos químicos disponibles")

    # creación de máscara de filtrado
    mask = pd.Series(True, index=df.index)

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

with tabs["Editar stock"]:
    pass
