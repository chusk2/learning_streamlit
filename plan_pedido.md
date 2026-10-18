# Plan: rediseño de la pestaña «Pedido» (inventario de reactivos)

## Contexto

App de Streamlit (interfaz en español) para gestionar el inventario de reactivos de un laboratorio de química. Los datos están en `reactivos.csv` y se cargan en un DataFrame `df`.

Columnas relevantes: `id` (R001, R002…), `reactivo`, `formula`, `unidades_stock`, `precio_unitario`, `cantidad_comercial`, `bajo_stock`, `caducado`.

En la pestaña **Pedido** el usuario revisa el carrito y ajusta cuántas unidades pide de cada reactivo. Hasta ahora se hacía con un `st.data_editor` (`SelectboxColumn` para `unidades_pedido` + `Index.map()` desde un diccionario). **Ese enfoque se sustituye** por el diseño de abajo.

## Diseño elegido

1. Una tabla de **solo lectura** (`st.dataframe`) con el pedido y **selección de filas múltiple**.
2. Para cada fila seleccionada aparece debajo una línea de edición: nombre | `st.number_input` (con flechas) | subtotal | botón 🗑.
3. Total del pedido en un `st.metric`.

## Modelo de estado (regla principal)

- **Única fuente de verdad:** `st.session_state.order`, un diccionario `{id: unidades}`, p. ej. `{"R003": 2, "R017": 1}`.
- Tabla, subtotales y total se **calculan** a partir de ese diccionario en cada rerun. No se guarda nada más.
- **Eliminar `st.session_state.order_id`** (lista duplicada). Todo lo que la use debe pasar a usar las claves de `order`.
- Al añadir un reactivo desde la pestaña Inventario: `st.session_state.order.setdefault(id_, 1)`.

## Pasos

### 1. Inicializar el estado
```python
if "order" not in st.session_state:
    st.session_state.order = {}
```
Si `order` está vacío, mostrar un mensaje («Aún no hay artículos en el pedido») y no pintar nada más.

### 2. Construir `df_order`
```python
df_order = df.loc[df["id"].isin(st.session_state.order.keys())].reset_index(drop=True)
df_order["unidades_pedido"] = df_order["id"].map(st.session_state.order)
df_order["subtotal"] = df_order["unidades_pedido"] * df_order["precio_unitario"]
```
- Usar `.isin()`, **no** `in` (con `in` da `ValueError: truth value of a Series is ambiguous`).
- `reset_index(drop=True)` es obligatorio: `selection.rows` devuelve **posiciones**, y con el índice reseteado posición = etiqueta para usar `.loc`.

### 3. Tabla con selección
```python
evento = st.dataframe(
    df_order, on_select="rerun", selection_mode="multi-row",
    key="tabla_pedido", hide_index=True,
)
```
`evento` no es un DataFrame: es el objeto de selección que devuelve `st.dataframe`.

### 4. Ids seleccionados
```python
ids_sel = df_order.loc[evento.selection.rows, "id"].tolist()
```

### 5. Callbacks
```python
def actualizar(id_):
    st.session_state.order[id_] = st.session_state[f"cant_{id_}"]

def eliminar(id_):
    del st.session_state.order[id_]
    st.session_state.pop("tabla_pedido", None)   # limpiar selección: las posiciones cambian
```
Los callbacks se ejecutan **antes** del rerun, así que la tabla de arriba ya sale actualizada en el mismo clic.

### 6. Líneas de edición (solo filas seleccionadas)
```python
for id_ in ids_sel:
    fila = df_order.loc[df_order["id"] == id_].iloc[0]
    c1, c2, c3, c4 = st.columns([3, 2, 2, 1], vertical_alignment="center")
    c1.write(fila["reactivo"])
    c2.number_input(
        "Unidades", min_value=1, step=1,
        value=st.session_state.order[id_],
        key=f"cant_{id_}", on_change=actualizar, args=(id_,),
        label_visibility="collapsed",
    )
    c3.write(f"{st.session_state.order[id_] * fila['precio_unitario']:.2f} €")
    c4.button("🗑", key=f"del_{id_}", on_click=eliminar, args=(id_,))
```
- Una `key` distinta por widget (`cant_R003`, `del_R003`…) para evitar claves duplicadas.
- `value=` solo se usa la primera vez que aparece el widget; después Streamlit usa su propio estado.

### 7. Total
`st.metric("Total del pedido", f"{df_order['subtotal'].sum():.2f} €")`

### 8. Limpieza
Quitar el `st.data_editor` antiguo de la pestaña Pedido, el `Index.map()` asociado y todas las referencias a `order_id`.

## Comprobaciones
- Cambiar una cantidad actualiza a la vez tabla, subtotal y total.
- La selección se mantiene tras editar una cantidad. **Si se pierde**, mostrar en la tabla solo columnas fijas (`reactivo`, `formula`, `precio_unitario`) y dejar unidades/subtotal en las líneas de edición.
- Desmarcar y volver a marcar una fila conserva la cantidad.
- Eliminar un reactivo lo quita de la tabla sin dejar filas mal seleccionadas.
- Depuración temporal: `st.write(st.session_state)` al final del script.

## Cómo trabajar conmigo
- Estoy aprendiendo y quiero entender cada cambio: **explica qué haces y por qué**, paso a paso.
- Implementa **un paso cada vez** y espera a que lo pruebe antes del siguiente.
- No reescribas el script entero: modifica solo lo necesario y respeta el estilo, el CSS (tema oscuro) y la fila de KPIs existentes.
