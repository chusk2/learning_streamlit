import pandas as pd
import streamlit as st
from datetime import date
import time
import unicodedata

st.set_page_config(page_title="Mi app", page_icon="🧪", layout="wide")

# definir ancho de la página
st.markdown(
    """
    <style>
    .block-container { max-width: 1200px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# tema personalizado CSS
# st.html("styles.css")

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


def reset_filters():
        ss = st.session_state
        ss["texto_reactivo"] = ""
        ss["texto_formula"] = ""
        ss["categorias_multiselect"] = []
        ss["ubicacion_selectbox"] = "Todas"
        ss["estado.radio"] = "Todos"
        ss["masa_molar_slider"] = (df.masa_molar.min(), df.masa_molar.max())   # rango del df completo
        ss["bajo_stock_checkbox"] = False
        ss["caducados_toggle"] = False

        
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


# Colorear filas de reactivo caducado
    
# colores
dark_theme_enabled = st.context.theme.type == "dark"
colour_pink = "background-color: #ffcdd2"

if dark_theme_enabled:
    red_colour = "background-color: rgba(255, 75, 75, 1)"
    amber_colour = "background-color: rgba(230, 126, 0, 1)"
else:
    red_colour = "background-color: rgba(255, 75, 75, 1); color : #ffffff"
    amber_colour = "background-color: rgba(230, 126, 0, 1); color: #ffffff"

def expiration_color(dias_para_caducar):
    """Estilo CSS según los días que faltan para caducar (número)."""
    if dias_para_caducar < 0:
        return red_colour
    elif dias_para_caducar < 30:
        return amber_colour
    else:
        return ""          # sin estilo


def color_fecha_caducidad(df_):
    """Colorea solo la celda fecha_caducidad, decidiendo con dias_para_caducar."""
    def _estilos(col_fecha):
        # col_fecha es la columna fecha_caducidad; el color sale de
        # dias_para_caducar de las mismas filas (mismo índice)
        return df_.loc[col_fecha.index, "dias_para_caducar"].map(expiration_color)
    return df_.style.apply(_estilos, subset=["fecha_caducidad"])


def color_fila_caducidad(row):
    """Colorea la fila entera según dias_para_caducar."""
    return [expiration_color(row["dias_para_caducar"])] * len(row)


#######################
### CARGA DATAFRAME ###
#######################
@st.cache_data
def load_inventory():
    df = pd.read_csv("reactivos_comercial.csv")

    # Procesar columnas dentro de la función cacheada para que solo se ejecute una vez
    
    # cálculos con caducidad
    today_ = pd.Timestamp.today().normalize()
    fecha_cad = pd.to_datetime(df["fecha_caducidad"])

    df["dias_para_caducar"] = (fecha_cad - today_).dt.days
    df["fecha_caducidad"] = fecha_cad.dt.date
    
    df["bajo_stock"] = df["cantidad"] < df["stock_minimo"]
    df["caducado"] = df["fecha_caducidad"] < date.today()
    df["stock_ud"] = df.loc[:, ["cantidad", "estado"]].apply(add_units, axis = 1)
    df["stock_minimo_ud"] = df.loc[:, ["stock_minimo", "estado"]].apply(add_units, axis = 1)
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
        key="categorias_multiselect"
    )
    if categorias:
        mask &= filtered_df["categoria"].isin(categorias)

    ubicacion = st.selectbox(
        "Ubicación",
        ["Todas"] + list(filtered_df["ubicacion"].unique()),
        index=0,
        placeholder="Elige ubicación del reactivo...",
        key= "ubicacion_selectbox"
    )

    if ubicacion != "Todas":
        mask &= filtered_df.ubicacion == ubicacion

    estado = st.radio("Estado de agregación",
                      index = 0,
                      options = ["Todos", "Líquido", "Sólido"],
                      horizontal=True,
                      key="estado.radio")

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
        key="masa_molar_slider")

    # filtrar la masa molar
    mask &= filtered_df["masa_molar"].between(*masa_molar)

    # reactivos con stock
    productos_bajo_stock = st.checkbox("Productos con bajo stock", key="bajo_stock_checkbox")
    if productos_bajo_stock:
        mask &= filtered_df["bajo_stock"]

    # productos caducados
    if st.toggle(label="Productos cadudados", key="caducados_toggle"):
        mask &= filtered_df.caducado

    # reactivos filtrados
    st.metric(label = "Reactivos filtrados",
              value = df[mask].shape[0])

    # LIMPIEZA DE FILTROS

    # key="texto_reactivo"
    # key="texto_formula"
    # key="categorias_multiselect"
    # key= "ubicacion_selectbox"
    # key="estado.radio"
    # key="masa_molar_slider"
    # key="bajo_stock_checkbox"
    # key="caducados_toggle"

    FILTER_KEYS = [
    "texto_reactivo", "texto_formula", "categorias_multiselect",
    "ubicacion_selectbox", "estado.radio", "masa_molar_slider",
    "bajo_stock_checkbox", "caducados_toggle",]

    st.button(label = "Limpiar filtros", on_click=reset_filters)
    
#######################
######## TABS ######
#######################

tab_names = [
    "Inventario",
    "Pedido",
    "Editar stock",
    "Detalle",
    "Estadísticas",
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

    st.title("Inventario de Productos Químicos")
    st.write("Marca reactivos para añadir a un pedido.")

    # dataframe filtrado
    filtered_df = (df[mask]
                   .sort_values("reactivo", key=lambda names: names.map(strip_accents))
                   .reset_index() )
    
    if len(filtered_df) == 0:
        st.info("No existen productos que cumplan el filtro actual.")
    else:
        
        cart = st.container(horizontal=True, horizontal_alignment="right", 
                            vertical_alignment="center")

        
        
        # dataframe inventario
        event = st.dataframe(
            color_fecha_caducidad(filtered_df),
            hide_index=True,
            column_order=[
                "id",
                "reactivo",
                "pureza_pct",
                "stock_ud",
                "stock_minimo",
                "fecha_caducidad",
                "ficha_url",
                "picto_url",
            ],
            column_config={
                "id" : "ID",
                "reactivo" : "Reactivo",
                "stock_ud": "Cantidad actual",
                "stock_minimo" : "Stock mínimo",
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

    st.title("Gestión del pedido de reactivos")

    if len(st.session_state.order_dict) == 0:
        st.info("Sin artículos añadidos al pedido.")

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

    st.title("Edita los artículos del inventario")

    # separar unidades de la cantidad
    # para poder editar la cantidad
    df_stock = df[mask].copy()
    if len(df_stock) == 0:
        st.info("No existen productos que cumplan el filtro actual.")
    else:
        parts = df_stock.stock_ud.str.split(expand=True)
        df_stock["unidades_reactivo"] = parts[1]

        with st.container(horizontal=False, horizontal_alignment="center", width = "stretch"):
            
            edited_stock_df = st.data_editor(
                df_stock,
                width=700,
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
        with st.container(horizontal=True, horizontal_alignment="center"):

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

with tabs["Detalle"]:
    st.title("Detalles de reactivo")

    option_strings = df[mask].apply(lambda row: f"{row.id} - {row.reactivo}", axis=1)
    if len(option_strings) == 0:
        st.info("No existen reactivos que cumplan con el filtro actual.")
    else:
        selected_id = st.selectbox(label = "ID reactivo",
                                options = option_strings,
                                placeholder="ID de reactivo",
                                index = None)

        if selected_id:

            selected_id = selected_id.split()[0]
            id_info = df.loc[df.id == selected_id].squeeze().to_dict()

            fecha_cad = pd.to_datetime(id_info["fecha_caducidad"], format="%d-%m-%Y").date()

            # si está caducado
            if id_info["caducado"]:
                days_expired = ( date.today() - fecha_cad).days
            
            with st.container(horizontal=True, vertical_alignment="center"):
            
                st.image(image = id_info["picto_url"])
                st.metric(label = "Masa molar, g/mol", value = id_info["masa_molar"])
                st.metric(label = "Stock", value = id_info["stock_ud"],
                        delta = id_info["cantidad"] - id_info["stock_minimo"], delta_color="normal")
                st.metric(label = "Pureza, % masa", value = id_info["pureza_pct"])
                if id_info["caducado"]:
                    st.warning(f"El reactivo está caducado. Fecha caducidad: {fecha_cad:%d-%m-%Y}. {days_expired} días caducado.")

with tabs["Estadísticas"]:

    st.title("Estadísticas del inventario")

    # valor del inventario
    st.markdown("### Valor económico por categoría de reactivo")
    data_plots = df[mask].copy()
    data_plots["valor"] = data_plots.cantidad / 100 * data_plots.precio_100
    value_by_category = (data_plots.groupby("categoria").valor
                         .sum()
                         .to_frame()
                         .reset_index() )

    st.bar_chart(data = value_by_category,
                 x = "categoria", y = "valor",
                 x_label = "Categoría reactivo",
                 y_label = "Valor (€)",
                 horizontal=True, sort="valor")

    st.metric(label="Valor total del inventario", value=f"{data_plots.valor.sum():.2f} €")

    st.markdown("### Comparativa para productos con bajo stock")

    # comparación stock sólidos
    st.markdown("#### Reactivos sólidos")
    data_low_stock = (df[(df.bajo_stock) & (df.estado == "Sólido")]
                      .rename(columns = {
                          "cantidad" : "stock actual",
                          "stock_minimo" : "stock mínimo"}))
    st.bar_chart(data = data_low_stock,
                 x = "reactivo",
                 y = ["stock actual", "stock mínimo"],
                 x_label = "Reactivo",
                 y_label = "Cantidad",
                 stack = False
                 )

    # comparación stock líquidos
    st.markdown("#### Reactivos líquidos")
    data_low_stock = (df[(df.bajo_stock) & (df.estado == "Líquido")]
                          .rename(columns = {
                              "cantidad" : "stock actual",
                              "stock_minimo" : "stock mínimo"}))
    st.bar_chart(data = data_low_stock,
                     x = "reactivo",
                     y = ["stock actual", "stock mínimo"],
                     x_label = "Reactivo",
                     y_label = "Cantidad",
                     stack = False
                     )

    st.markdown("### Fechas de caducidad")
       
    def etiqueta(texto, estilo):
        return f'<span style="{estilo}; padding: 2px 8px; border-radius: 4px;">{texto}</span>'

    st.html(etiqueta("Caducado", red_colour) + " · " + etiqueta("Caduca pronto (menos de 1 mes)", amber_colour))

    cols = ["id", "reactivo", "fecha_caducidad", "caducado", "dias_para_caducar"]
    data_expiration_dates = df[cols].sort_values("fecha_caducidad").reset_index()

    st.dataframe(color_fecha_caducidad(data_expiration_dates),
                 hide_index=True,
                 column_order= cols,
                 column_config={
                     "caducado" : None,
                     "dias_para_caducar" : "Días hasta caducidad",
                     "fecha_caducidad" : "Fecha de caducidad",
                     "id" : "ID",
                     "reactivo" : "Reactivo"
                 })

with tabs["Nuevo reactivo"]:
    # ['id', 'reactivo', 'formula', 'categoria', 'estado', 'masa_molar',
    #    'pureza_pct', 'cantidad', 'unidad', 'stock_minimo', 'precio_100',
    #    'cantidad_comercial', 'precio_unitario', 'ubicacion', 'peligro',
    #    'fecha_caducidad', 'ficha_url', 'picto_url']

    # keys de los widgets del formulario de nuevo reactivo
    NEW_REAGENT_KEYS = [
        "nuevo_nombre", "nuevo_formula", "nuevo_categoria", "nuevo_estado",
        "nuevo_masa_molar", "nuevo_pureza", "nuevo_cantidad", "nuevo_stock_minimo",
        "nuevo_cantidad_comercial", "nuevo_precio_unitario", "nuevo_ubicacion",
        "nuevo_peligro", "nuevo_caducidad",
    ]
 
    # Resetear el formulario ANTES de crear los widgets (tras guardar un reactivo).
    # Borrar la key hace que el widget vuelva a su valor por defecto.
    if st.session_state.pop("reset_nuevo_reactivo", False):
        for k in NEW_REAGENT_KEYS:
            st.session_state.pop(k, None)
        st.toast("¡Datos del nuevo reactivo incorporados con éxito!", icon="✅")
 
    with st.form("new_reagent", border=True, enter_to_submit=False):  # deshabilita envío de formulario al pulsar Enter
 
        # calculo nuevo id para el nuevo reactivo
        id_ = f"R{str(max(df["id"].apply(lambda x: int(x[1:]) + 1))).zfill(3)}" # x[1:] excluye la "R"
        st.markdown(f"### 🧪 Nuevo reactivo &nbsp; `{id_}`")
         
        # ── 1. Identificación ────────────────────────────────────────────────────
        with st.container(border=True):
            st.markdown("**🏷️ Identificación**")
            c1, c2 = st.columns([3, 1])
            name = c1.text_input("Reactivo", placeholder="p. ej. Ácido clorhídrico 37%", key="nuevo_nombre")
            formula = c2.text_input("Fórmula", placeholder="HCl", key="nuevo_formula")
    
            c1, c2 = st.columns(2)
            categoria = c1.selectbox(
                "Categoría",
                options=sorted(df["categoria"].dropna().unique(), key=strip_accents),
                index=None,
                placeholder="Selecciona categoría",
                key="nuevo_categoria",
            )
            estado = c2.selectbox(
                "Estado",
                options=["Líquido", "Sólido", "Gas"],
                index=None,
                placeholder="Estado de agregación",
                key="nuevo_estado",
            )
    
        # ── 2. Propiedades químicas ──────────────────────────────────────────────
        with st.container(border=True):
            st.markdown("**⚗️ Propiedades**")
            c1, c2 = st.columns(2)
            masa_molar = c1.number_input(
                "Masa molar (g/mol)",
                value=2.0, min_value=2.0, max_value=500.0, step=0.1, format="%.2f",
                key="nuevo_masa_molar",
            )
            pureza_pct = c2.number_input(
                "Pureza (%)",
                value=90.0, min_value=0.1, max_value=100.0, step=0.1, format="%.1f",
                key="nuevo_pureza",
            )
    
        # ── 3. Stock y compra ────────────────────────────────────────────────────
        with st.container(border=True):
            st.markdown("**📦 Stock y compra**")
            st.caption("Cantidades en **mL** para líquidos y en **g** para sólidos y gases.")

            c1, c2 = st.columns(2)
            cantidad = c1.number_input("Cantidad en stock", value=1, min_value=1, max_value=5000,
                                      key="nuevo_cantidad")
            stock_minimo = c2.number_input("Stock mínimo", value=1, min_value=1, max_value=5000,
                                          key="nuevo_stock_minimo")
    
            c1, c2 = st.columns(2)
            cantidad_comercial = c1.number_input("Formato comercial", value=1, min_value=1, max_value=5000,
                help="Cantidad que trae cada envase del proveedor",
                key="nuevo_cantidad_comercial",
            )
            precio_unitario = c2.number_input(
                "Precio por envase (€)",
                value=0.1, min_value=0.1, max_value=500.0, step=0.1, format="%.2f",
                key="nuevo_precio_unitario",
            )
    
        # ── 4. Almacenamiento y seguridad ────────────────────────────────────────
        with st.container(border=True):
            st.markdown("**🛡️ Almacenamiento y seguridad**")
            c1, c2, c3 = st.columns(3)
            ubicacion = c1.selectbox(
                "Ubicación",
                options=sorted(df["ubicacion"].dropna().unique(), key=strip_accents),
                index=None,
                placeholder="Armario / estante",
                key="nuevo_ubicacion",
            )
            peligro = c2.selectbox(
                "Peligro",
                options=sorted(df["peligro"].dropna().unique(), key=strip_accents),
                index=None,
                placeholder="Categoría de peligro",
                key="nuevo_peligro",
            )
            fecha_caducidad = c3.date_input(
                "Caducidad",
                value=None,
                # no añadir un reactivo ya caducado
                min_value=date.today(),
                format="DD/MM/YYYY",
                key="nuevo_caducidad",
            )

        submit = st.form_submit_button("💾 Guardar reactivo", type="primary", use_container_width=True)

    if submit:
        # campos obligatorios
        obligatorios = {
            "Reactivo": name,
            "Fórmula": formula,
            "Categoría": categoria,
            "Estado": estado,
            "Ubicación": ubicacion,
            "Peligro": peligro,
            "Caducidad": fecha_caducidad,
        }

        # campos no rellenos
        faltan = [campo for campo, valor in obligatorios.items() if not valor]

        if faltan:
            st.error(f"Faltan campos obligatorios por rellenar: {', '.join(faltan)}")
            st.stop()

        unidad = "mL" if estado == "Líquido" else "g"
        precio_100 = round(precio_unitario / cantidad_comercial * 100, 2)
        pictograms_dict = df[["peligro", "picto_url"]].drop_duplicates().set_index("peligro").to_dict()["picto_url"]
        picto_url = pictograms_dict.get(peligro, "")
        ficha_url = ""
    
        # Ajusta las claves a los nombres reales de tus columnas
        new_reagent = {
            "id": id_,
            "reactivo": name.strip(),
            "formula": formula.strip(),
            "categoria": categoria,
            "estado": estado,
            "masa_molar": masa_molar,
            "pureza_pct": pureza_pct,
            "cantidad": cantidad,
            "unidad": unidad,
            "stock_minimo": stock_minimo,
            "cantidad_comercial": cantidad_comercial,
            "precio_unitario": precio_unitario,
            "precio_100": precio_100,
            "ubicacion": ubicacion,
            "peligro": peligro,
            "picto_url": picto_url,
            "fecha_caducidad": fecha_caducidad,
            "ficha_url": ficha_url,
        }

        reagent_data = pd.Series(new_reagent)

        # añadir al archivo csv
        source_df = pd.read_csv("reactivos_comercial.csv")

        # ajustar al formato del CSV: rutas sin prefijo, fecha como en el original
        new_reagent["fecha_caducidad"] = new_reagent["fecha_caducidad"].strftime("%Y-%m-%d")  # usa el formato de tu CSV
        new_reagent["picto_url"] = new_reagent["picto_url"].removeprefix("/app/static/")  # elimina el prefijo /app/static

        try:
            combined_df = pd.concat([source_df, pd.DataFrame(new_reagent, index=[0])], axis=0, ignore_index=True)
            combined_df.to_csv("reactivos_comercial.csv", index=False)
        
            load_inventory.clear()  # limpiar caché
            # marcar el formulario para resetearlo en la próxima ejecución
            st.session_state["reset_nuevo_reactivo"] = True
            st.rerun()

        except Exception as e:
            st.error(f"Error: {e}")
        

        
        
        
