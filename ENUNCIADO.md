# Ejercicio Streamlit: inventario del laboratorio de Química

Vas a construir una app para gestionar el inventario de reactivos del laboratorio. La app tiene que permitir filtrar, consultar, editar, añadir y pedir reactivos, y debe abrir sus fichas en PDF y sus pictogramas de peligro.

En el ejercicio se practican todos los apartados de los apuntes: widgets, desplegables, organización de la página, caché, `st.session_state`, persistencia en disco, `st.dataframe`, `st.data_editor`, imágenes, enlaces y descargas.

> Los datos y las fichas son **ficticios y con fines didácticos**. No son fichas de datos de seguridad oficiales.

---

## Material

```
ejercicio_streamlit/
├── ENUNCIADO.md          ← este archivo
├── reactivos.csv         ← datos (34 reactivos)
├── solucion.py           ← solución de referencia (¡no la mires antes de intentarlo!)
├── .streamlit/
│   └── config.toml       ← activa enableStaticServing
└── static/
    ├── fichas/           ← una ficha PDF por reactivo
    └── pictogramas/      ← 7 imágenes PNG, una por tipo de peligro
```

Crea tu `app.py` en la carpeta raíz, junto a `reactivos.csv`. La carpeta `static/` tiene que estar al lado del script que ejecutas, y el comando se lanza desde esa misma carpeta:

```bash
cd ejercicio_streamlit
streamlit run app.py
```

Requisitos: `streamlit >= 1.40` y `pandas`.

### Columnas de `reactivos.csv`

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | texto | Código único (`R001`, `R002`…) |
| `reactivo` | texto | Nombre |
| `formula` | texto | Fórmula química |
| `categoria` | texto | Ácido, Base, Sal, Óxido, Disolvente, Indicador, Metal, Otros |
| `estado` | texto | Sólido o Líquido |
| `masa_molar` | decimal | g/mol |
| `pureza_pct` | decimal | Pureza en % (95–100) |
| `cantidad` | entero | Cantidad disponible |
| `unidad` | texto | `g` (sólidos) o `mL` (líquidos) |
| `stock_minimo` | entero | Por debajo de este valor hay que reponer |
| `precio_100` | decimal | Precio en € por 100 g o 100 mL |
| `ubicacion` | texto | Armario o estantería |
| `peligro` | texto | Corrosivo, Inflamable, Comburente, Tóxico, Nocivo, Irritante, Ninguno |
| `fecha_caducidad` | fecha | `AAAA-MM-DD` |
| `ficha_pdf` | texto | Ruta del PDF **relativa a `static/`** (p. ej. `fichas/acetona.pdf`) |
| `pictograma` | texto | Ruta del PNG **relativa a `static/`** (p. ej. `pictogramas/inflamable.png`) |

---

## Tareas

Hazlas en orden. Cada una se apoya en la anterior.

### 1. Configuración y carga de datos

- Configura la página con `st.set_page_config` (título, icono y `layout="wide"`).
- Escribe una función `cargar(ruta)` decorada con `@st.cache_data` que lea el CSV y convierta `fecha_caducidad` en fecha.
- Guarda el DataFrame en `st.session_state.inventario` **solo la primera vez** que se ejecute el script. A partir de ahí, la app trabajará sobre esa copia, que es la que se podrá modificar.

### 2. Columnas calculadas

Añade al DataFrame (sin guardarlas en el CSV):

- `valor` = `cantidad / 100 * precio_100`, redondeado a 2 decimales.
- `bajo_stock`: `True` si `cantidad < stock_minimo`.
- `caducado`: `True` si la fecha de caducidad es anterior a hoy.
- `ficha_url` y `picto_url`: las rutas anteriores precedidas de `app/static/`.

### 3. Filtros en la barra lateral

En `st.sidebar`, crea:

| Widget | Filtra por |
|---|---|
| `st.text_input` | Texto contenido en el nombre **o** en la fórmula, sin distinguir mayúsculas |
| `st.multiselect` | Categoría (vacío = todas) |
| `st.selectbox` | Ubicación, con una primera opción `"Todas"` |
| `st.radio` horizontal | Estado: Todos / Sólido / Líquido |
| `st.slider` de rango | Masa molar (mínimo y máximo sacados de los datos) |
| `st.checkbox` | Solo reactivos bajo stock |
| `st.toggle` | Ocultar caducados |

Combina todos los filtros en una única máscara booleana y obtén el DataFrame `filtrado`.

### 4. Indicadores

Debajo del título, muestra cuatro `st.metric` en columnas: reactivos mostrados (sobre el total), valor del inventario filtrado en €, número de reactivos bajo stock y número de caducados.

### 5. Pestaña «Inventario»: tabla con formato

Organiza el resto de la app en cinco pestañas (`st.tabs`): **Inventario, Editar stock, Detalle, Gráficos, Nuevo reactivo**.

En «Inventario», muestra `filtrado` con `st.dataframe` y:

- Oculta el índice y elige qué columnas aparecen y en qué orden (`column_order`).
- Usa `column_config` para:
  - mostrar el pictograma como imagen (`ImageColumn`);
  - mostrar la pureza como barra de progreso entre 90 y 100 (`ProgressColumn`);
  - formatear `precio_100` y `valor` con el símbolo €;
  - mostrar la caducidad como `DD/MM/YYYY`;
  - convertir `ficha_url` en un enlace con el texto «📄 Abrir» (`LinkColumn`).
- Añade un `st.download_button` que descargue la tabla filtrada en CSV.

### 6. Selección de filas y pedido (`session_state`)

- Haz la tabla anterior seleccionable (`on_select="rerun"`, `selection_mode="multi-row"`).
- Si hay filas seleccionadas, muestra sus nombres y un botón «🛒 Añadir al pedido» que guarde sus `id` en `st.session_state.pedido` sin duplicados.
- Añade en la barra lateral un `st.expander` con el pedido:
  - Para cada reactivo, la cantidad que hay que pedir es `2 · stock_minimo − cantidad` (mínimo 0).
  - Calcula el coste estimado total.
  - Incluye un botón para descargar el pedido en CSV y otro para vaciarlo (con `on_click`).

Comprueba que el pedido se conserva aunque cambies los filtros o de pestaña.

### 7. Pestaña «Editar stock»: `st.data_editor` y persistencia

- Muestra `id`, `reactivo`, `unidad`, `cantidad` y `stock_minimo` en un `st.data_editor`.
- Solo deben poder editarse `cantidad` y `stock_minimo`, que no admitirán valores negativos.
- Muestra cuántas filas se han modificado. Puedes consultarlo en `st.session_state[clave_del_editor]["edited_rows"]`.
- Al pulsar «💾 Guardar cambios»:
  1. traslada los cambios a `st.session_state.inventario` (empareja las filas por `id`, no por posición);
  2. guarda el CSV **solo con las columnas originales**;
  3. vacía la caché de `cargar` para que una recarga lea el archivo nuevo.

Comprueba que, tras guardar y reiniciar la app, los cambios siguen ahí.

### 8. Pestaña «Detalle»: imágenes, enlaces y descargas

- Crea un `st.selectbox` con los `id` del DataFrame filtrado que muestre `"R001 · Ácido clorhídrico 37%"` (usa `format_func`).
- Para el reactivo elegido:
  - muestra su pictograma con `st.image`, leyendo el archivo de disco;
  - muestra masa molar, cantidad y pureza con `st.metric`. En la cantidad, añade como `delta` la diferencia con el stock mínimo;
  - muestra un aviso (`st.error` o `st.warning`) si está caducado o por debajo del mínimo;
  - añade un `st.link_button` que abra la ficha PDF en otra pestaña y un `st.download_button` que la descargue.
- Si el filtro deja la tabla vacía, muestra un `st.info` en lugar de producir un error.

### 9. Pestaña «Gráficos»

- `st.bar_chart` con el valor total por categoría.
- `st.bar_chart` que compare `cantidad` y `stock_minimo` de los reactivos bajo stock, con las barras agrupadas y no apiladas.
- Una tabla de caducidades ordenada por fecha, con las filas caducadas **coloreadas** mediante un `Styler` de pandas.

### 10. Pestaña «Nuevo reactivo»: formulario

Crea un `st.form` (con `clear_on_submit=True`) para dar de alta un reactivo. Debe usar, como mínimo, `text_input`, `selectbox`, `radio`, `number_input`, `slider` y `date_input`.

- Nombre y fórmula son obligatorios. Si faltan, muestra un error.
- El `id` nuevo es el siguiente número libre (`R035`, `R036`…).
- La unidad se deduce del estado (sólido → `g`, líquido → `mL`).
- El pictograma se elige según el peligro.
- El nuevo reactivo no tiene ficha. La app debe funcionar igual, mostrando «Este reactivo no tiene ficha» en la pestaña Detalle.
- Guarda el CSV igual que en la tarea 7.

---

## Comprobaciones

Con el CSV original y fecha de referencia **11/10/2026**:

- Total: **34 reactivos**, valor del inventario **5 231,53 €**.
- Bajo stock: **8** (entre ellos Ácido sulfúrico 96%, Hexano y Sodio metálico).
- Caducados: **5** (entre ellos Ácido nítrico 65% e Hidróxido de sodio).
- Buscar `"ácido"` con todo lo demás sin filtrar devuelve 5 reactivos. Si además pones la masa molar en 20–100 g/mol, devuelve 4 (queda fuera el ácido cítrico).
- La categoría con más reactivos es **Sal** (9).

Si cambia la fecha del sistema, el número de caducados puede variar.

---

## Pistas

- **Máscara combinada**: empieza con `mascara = df["masa_molar"].between(minimo, maximo)` y ve añadiendo condiciones con `&=`. Las condiciones opcionales solo se añaden si el widget tiene un valor.
- **Búsqueda**: `df["col"].str.contains(texto, case=False, regex=False)`. Con `regex=False` se evita que caracteres como `(` den error.
- **Selección de filas**: `evento = st.dataframe(..., on_select="rerun", selection_mode="multi-row", key="tabla")`. `evento.selection.rows` devuelve **posiciones** en el DataFrame mostrado. Usa `filtrado.reset_index(drop=True)` para que posición e índice coincidan.
- **Volcar las ediciones**: con `inv = inventario.set_index("id")` y `e = editado.set_index("id")`, hacer `inv.loc[e.index, cols] = e[cols]`.
- **Reiniciar el editor tras guardar**: `del st.session_state["clave_del_editor"]` y después `st.rerun()`.
- **Imágenes en la tabla**: si los pictogramas no aparecen en el `ImageColumn`, prueba con la ruta absoluta `/app/static/...` y comprueba que `enableStaticServing` está activo.
- **Guardar fechas**: `df.to_csv(..., date_format="%Y-%m-%d")` mantiene el mismo formato que el CSV original.

---

## Retos opcionales

1. Pide una confirmación con `@st.dialog` antes de guardar los cambios del editor.
2. Usa `st.data_editor(num_rows="dynamic")` para permitir borrar reactivos. Los borrados aparecen en `st.session_state[clave]["deleted_rows"]`.
3. Al seleccionar **una** fila en «Inventario», salta automáticamente a su detalle. Para ello, guarda el `id` en `session_state` y úsalo como valor inicial del selectbox de «Detalle».
4. Incrusta la ficha PDF en «Detalle» con `st.pdf` o con un `<iframe>`.
5. Divide la app en varias páginas con `st.navigation` y `st.Page`.
6. Sustituye el CSV por una base de datos SQLite usando `@st.cache_resource` para la conexión.
