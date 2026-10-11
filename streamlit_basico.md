# Streamlit: guía básica

Streamlit convierte un script de Python en una aplicación web. Cada vez que el usuario interactúa con un widget, **el script se vuelve a ejecutar entero de arriba abajo**. Esa idea es la clave para entender la caché y el estado.

---

## 1. Instalación y ejecución

```bash
pip install streamlit
streamlit run app.py
```

La app se abre en `http://localhost:8501`.

Estructura mínima:

```python
import streamlit as st

st.title("Mi primera app")
st.write("Hola, mundo")
```

---

## 2. Mostrar contenido

```python
st.title("Título")
st.header("Encabezado")
st.subheader("Subencabezado")
st.markdown("Texto con **negrita**, *cursiva* y `código`")
st.caption("Texto pequeño y gris")
st.code("print('hola')", language="python")
st.latex(r"E = mc^2")

st.write(...)          # "navaja suiza": texto, DataFrames, gráficos, dicts...
st.dataframe(df)       # tabla interactiva (ver sección 7)
st.table(df)           # tabla estática
st.metric("Temperatura", "24 °C", "+1.2 °C")
st.json({"a": 1, "b": [1, 2]})

# Mensajes
st.success("Todo bien")
st.info("Información")
st.warning("Cuidado")
st.error("Error")
```

Gráficos:

```python
st.line_chart(df)
st.bar_chart(df)
st.pyplot(fig)          # matplotlib
st.plotly_chart(fig)    # plotly
```

---

## 3. Widgets básicos

Todos los widgets **devuelven su valor actual**, que se guarda en una variable normal.

### Botón

```python
if st.button("Saludar"):
    st.write("¡Hola!")
```

`st.button` devuelve `True` **solo en la ejecución inmediatamente posterior al clic**. Si necesitas que el efecto se mantenga, usa `st.session_state` (ver sección 5).

### Entrada de texto y números

```python
nombre = st.text_input("Tu nombre", value="Ana")
comentario = st.text_area("Comentario", height=150)
edad = st.number_input("Edad", min_value=0, max_value=120, value=30, step=1)
password = st.text_input("Contraseña", type="password")
```

### Casilla y conmutador

```python
acepto = st.checkbox("Acepto las condiciones")
modo_oscuro = st.toggle("Modo oscuro")
```

### Deslizadores

Sintaxis completa:

```python
st.slider(
    label,               # texto que se muestra encima
    min_value=None,      # mínimo (por defecto 0 / 0.0)
    max_value=None,      # máximo (por defecto 100 / 1.0)
    value=None,          # valor inicial; si es una tupla, el slider es de rango
    step=None,           # paso (por defecto 1 para int, 0.01 para float)
    format=None,         # formato del número mostrado, p. ej. "%.1f"
    key=None,            # nombre en st.session_state
    help=None,           # tooltip con un icono "?"
    on_change=None,      # función que se ejecuta al cambiar el valor
    disabled=False,      # deshabilitado (solo lectura)
    label_visibility="visible",  # "visible", "hidden" o "collapsed"
)
```

Los argumentos posicionales siguen este orden: `label, min_value, max_value, value, step`.

```python
# Equivalentes
st.slider("Nota", 0.0, 10.0, 5.0, 0.5)
st.slider("Nota", min_value=0.0, max_value=10.0, value=5.0, step=0.5)
```

> **Los tipos deben coincidir**: si `min_value` es float, `max_value`, `value` y `step` también deben serlo.
> `st.slider("Nota", 0, 10.0, 5)` da error; `st.slider("Nota", 0.0, 10.0, 5.0)` funciona.

Ejemplos:

```python
# Entero
edad = st.slider("Edad", 0, 100, 18)

# Decimal con formato
nota = st.slider("Nota", 0.0, 10.0, 5.0, step=0.25, format="%.2f")

# Rango: value es una tupla y devuelve una tupla
minimo, maximo = st.slider("Rango de notas", 0.0, 10.0, (5.0, 8.0))

# Porcentaje mostrado con símbolo
pct = st.slider("Porcentaje", 0, 100, 50, format="%d %%")

# Fechas
from datetime import date, timedelta
inicio = st.slider(
    "Fecha",
    min_value=date(2026, 1, 1),
    max_value=date(2026, 12, 31),
    value=date(2026, 6, 1),
    step=timedelta(days=7),
    format="DD/MM/YYYY",
)

# Horas
from datetime import time
hora = st.slider("Hora", value=(time(9, 0), time(14, 0)))

# Con key y callback
def aviso():
    st.toast(f"Nueva temperatura: {st.session_state.temp} °C")

st.slider("Temperatura (°C)", -10, 40, 20, key="temp", on_change=aviso,
          help="Arrastra para cambiar la temperatura")
```

`st.select_slider` funciona igual, pero con opciones no numéricas o con valores discretos concretos:

```python
talla = st.select_slider("Talla", options=["XS", "S", "M", "L", "XL"], value="M")
desde, hasta = st.select_slider("Nivel", options=["Bajo", "Medio", "Alto"], value=("Bajo", "Medio"))
```

### Botones de opción (radio)

```python
nivel = st.radio("Nivel", ["Básico", "Intermedio", "Avanzado"], horizontal=True)
```

### Menús desplegables (dropdown)

**Selección única → `st.selectbox`**

```python
asignatura = st.selectbox(
    "Elige asignatura",
    ["Matemáticas", "Física", "Química"],
    index=0,                      # opción seleccionada al inicio
    # index=None, placeholder="Selecciona...",  # para empezar vacío
)
st.write("Has elegido:", asignatura)
```

**Selección múltiple → `st.multiselect`**

```python
temas = st.multiselect(
    "Temas",
    ["Estequiometría", "Termoquímica", "Cinética", "Equilibrio"],
    default=["Cinética"],
)
st.write(temas)   # lista
```

Mostrar un texto distinto del valor interno con `format_func`:

```python
codigos = {"QUI": "Química", "FIS": "Física", "MAT": "Matemáticas"}
codigo = st.selectbox("Asignatura", options=list(codigos), format_func=lambda c: codigos[c])
st.write(codigo)  # devuelve "QUI", "FIS"...
```

Desplegables dependientes (el segundo depende del primero):

```python
datos = {
    "Química": ["Ácido-base", "Redox", "Equilibrio"],
    "Física": ["Ondas", "Campo eléctrico", "Óptica"],
}
asig = st.selectbox("Asignatura", list(datos))
tema = st.selectbox("Tema", datos[asig])
```

### Fechas, horas, colores

```python
fecha = st.date_input("Fecha")
hora = st.time_input("Hora")
color = st.color_picker("Color", "#FF4B4B")
```

### Subida de archivos

```python
archivo = st.file_uploader("Sube un CSV", type=["csv"])
if archivo is not None:
    import pandas as pd
    df = pd.read_csv(archivo)
    st.dataframe(df)

# Varios a la vez
archivos = st.file_uploader("Imágenes", type=["png", "jpg"], accept_multiple_files=True)
```

### Formularios (agrupar widgets y enviar de una vez)

Sin formulario, cada cambio en un widget relanza el script. Dentro de un `st.form`, el script solo se relanza al pulsar el botón de envío.

```python
with st.form("alta"):
    nombre = st.text_input("Nombre")
    curso = st.selectbox("Curso", ["1º Bach", "2º Bach"])
    enviado = st.form_submit_button("Guardar")

if enviado:
    st.success(f"Guardado: {nombre} ({curso})")
```

---

## 4. Organizar la página

```python
# Barra lateral
with st.sidebar:
    filtro = st.selectbox("Filtro", ["Todos", "Activos"])

# Columnas
col1, col2 = st.columns(2)          # o st.columns([2, 1]) para anchos distintos
col1.metric("Alumnos", 25)
col2.metric("Aprobados", 21)

# Pestañas
tab1, tab2 = st.tabs(["Datos", "Gráfico"])
with tab1:
    st.dataframe(df)
with tab2:
    st.line_chart(df)

# Sección plegable
with st.expander("Ver detalles"):
    st.write("Contenido oculto por defecto")

# Contenedor vacío que se rellena después
hueco = st.empty()
hueco.write("Cargando...")
hueco.write("¡Listo!")   # reemplaza el contenido
```

Configuración de la página (debe ser la primera llamada a Streamlit):

```python
st.set_page_config(page_title="Mi app", page_icon="🧪", layout="wide")
```

---

## 5. Persistencia de datos

Como el script se re-ejecuta en cada interacción, todas las variables normales se pierden y las operaciones costosas se repetirían. Hay tres mecanismos distintos:

| Mecanismo | Qué guarda | Ámbito | Uso típico |
|---|---|---|---|
| `@st.cache_data` | Resultado de una función (datos serializables) | Todos los usuarios, hasta reiniciar el servidor | Leer CSV, consultas SQL, cálculos |
| `@st.cache_resource` | Objetos "vivos" no copiables | Todos los usuarios | Conexión a BD, modelo de ML |
| `st.session_state` | Variables arbitrarias | Una pestaña / sesión de usuario | Contadores, carrito, login, pasos |

> **Nota sobre `st.cache`**: el antiguo decorador `@st.cache` está **obsoleto** y se ha eliminado en las versiones recientes. Se sustituye por `@st.cache_data` y `@st.cache_resource`. Si ves `@st.cache` en tutoriales antiguos, cámbialo por `@st.cache_data` (casi siempre es el adecuado).

### 5.1 `@st.cache_data`

La función solo se ejecuta la primera vez para unos argumentos dados; las siguientes devuelve el resultado guardado (una copia).

```python
import pandas as pd

@st.cache_data
def cargar_datos(ruta):
    return pd.read_csv(ruta)   # solo se lee una vez por ruta

df = cargar_datos("datos.csv")
```

Opciones útiles:

```python
@st.cache_data(ttl=600)              # caduca a los 600 s (útil para datos que cambian)
@st.cache_data(max_entries=20)       # limita cuántos resultados guarda
@st.cache_data(show_spinner="Cargando datos...")
```

Vaciar la caché:

```python
cargar_datos.clear()       # solo esta función
st.cache_data.clear()      # toda la caché de datos
```

Si un argumento no se puede "hashear" (p. ej. una conexión), pon un guion bajo delante para que se ignore: `def consulta(_conn, sql): ...`

### 5.2 `@st.cache_resource`

Para objetos que deben crearse una sola vez y compartirse (no se copian):

```python
import sqlite3

@st.cache_resource
def get_conexion():
    return sqlite3.connect("base.db", check_same_thread=False)

conn = get_conexion()
```

### 5.3 `st.session_state`

Diccionario que sobrevive a las re-ejecuciones dentro de la misma sesión del navegador.

```python
# Inicializar solo si no existe
if "contador" not in st.session_state:
    st.session_state.contador = 0

if st.button("Sumar 1"):
    st.session_state.contador += 1

st.write("Contador:", st.session_state.contador)
```

Vincular un widget al estado con `key`:

```python
st.text_input("Nombre", key="nombre")
st.write("Hola,", st.session_state.nombre)
```

Callbacks (`on_click`, `on_change`), que se ejecutan **antes** de relanzar el script:

```python
def reiniciar():
    st.session_state.contador = 0

st.button("Reiniciar", on_click=reiniciar)
```

Guardar una lista que crece:

```python
if "tareas" not in st.session_state:
    st.session_state.tareas = []

nueva = st.text_input("Nueva tarea")
if st.button("Añadir") and nueva:
    st.session_state.tareas.append(nueva)

for t in st.session_state.tareas:
    st.write("•", t)
```

### 5.4 Persistencia permanente

Ni la caché ni `session_state` sobreviven a un reinicio del servidor (y `session_state` se pierde al recargar la página). Para guardar datos de verdad hay que escribirlos fuera: un CSV/JSON, SQLite, MySQL, etc.

```python
import json, pathlib

RUTA = pathlib.Path("datos.json")

def guardar(datos):
    RUTA.write_text(json.dumps(datos, ensure_ascii=False, indent=2))

def cargar():
    return json.loads(RUTA.read_text()) if RUTA.exists() else []
```

---

## 6. Enlaces, archivos e imágenes

### 6.1 Enlaces a páginas web

```python
st.markdown("[Documentación de Streamlit](https://docs.streamlit.io)")
st.link_button("Ir a la documentación", "https://docs.streamlit.io")
```

Los enlaces externos se abren en una pestaña nueva.

### 6.2 Mostrar imágenes

```python
st.image("img/logo.png", caption="Logo", width=300)
st.image("https://ejemplo.com/foto.jpg")           # también por URL
st.image(["a.png", "b.png"], width=150)            # varias
st.image(archivo_subido)                            # desde file_uploader
```

### 6.3 Descargar archivos (`st.download_button`)

Es la forma más fiable de que el usuario obtenga un archivo local del servidor (PDF, CSV, imagen...).

```python
with open("apuntes/tema1.pdf", "rb") as f:
    st.download_button(
        label="Descargar tema 1 (PDF)",
        data=f,
        file_name="tema1.pdf",
        mime="application/pdf",
    )

# Un DataFrame como CSV
st.download_button("Descargar CSV", df.to_csv(index=False), "datos.csv", "text/csv")
```

MIME habituales: `application/pdf`, `image/png`, `image/jpeg`, `text/csv`, `application/zip`.

### 6.4 Enlaces que abren archivos en el navegador (servicio estático)

Un `st.markdown("[ver](archivos/tema1.pdf)")` **no funciona** con rutas locales: el navegador no tiene acceso al disco del servidor. Para que un enlace abra un PDF o una imagen en otra pestaña hay que activar el servicio de archivos estáticos.

1. Crea `.streamlit/config.toml` junto a tu app:

   ```toml
   [server]
   enableStaticServing = true
   ```

2. Coloca los archivos en una carpeta llamada `static/` junto al script:

   ```
   mi_app/
   ├── app.py
   ├── .streamlit/
   │   └── config.toml
   └── static/
       ├── tema1.pdf
       └── esquema.png
   ```

3. Enlázalos con la ruta `app/static/...`:

   ```python
   st.markdown("[Abrir tema 1 (PDF)](app/static/tema1.pdf)")
   st.markdown("[Ver esquema](app/static/esquema.png)")
   st.link_button("Abrir PDF", "app/static/tema1.pdf")

   # Imagen en miniatura que al pulsarla se abre a tamaño completo
   st.markdown(
       '<a href="app/static/esquema.png" target="_blank">'
       '<img src="app/static/esquema.png" width="200"></a>',
       unsafe_allow_html=True,
   )
   ```

Limitaciones: solo sirve archivos de la carpeta `static/`; los tipos que no son imagen/PDF/texto se pueden servir como `text/plain` (para esos, usa `st.download_button`).

Generar enlaces para todos los archivos de la carpeta:

```python
from pathlib import Path

for p in sorted(Path("static").glob("*.pdf")):
    st.markdown(f"- [{p.stem}](app/static/{p.name})")
```

### 6.5 Mostrar un PDF incrustado

```python
st.pdf("static/tema1.pdf", height=600)   # versiones recientes (requiere: pip install streamlit[pdf])
```

En versiones antiguas, con un iframe a un archivo estático:

```python
st.markdown(
    '<iframe src="app/static/tema1.pdf" width="100%" height="600"></iframe>',
    unsafe_allow_html=True,
)
```

### 6.6 Ver una imagen ampliada en ventana emergente

```python
@st.dialog("Vista ampliada", width="large")
def ampliar(ruta):
    st.image(ruta, use_container_width=True)

st.image("static/esquema.png", width=200)
if st.button("Ampliar"):
    ampliar("static/esquema.png")
```

---

## 7. DataFrames: mostrar, filtrar y editar

Streamlit tiene tres formas de mostrar una tabla:

| Función | Interactiva | Editable | Uso |
|---|---|---|---|
| `st.table(df)` | No | No | Tablas pequeñas y estáticas |
| `st.dataframe(df)` | Sí: ordenar, buscar, redimensionar, descargar, seleccionar filas | No | Lo habitual |
| `st.data_editor(df)` | Sí | Sí | Que el usuario modifique datos |

### 7.1 `st.dataframe`

```python
st.dataframe(
    df,
    height=400,               # alto en píxeles (por defecto muestra unas 10 filas)
    hide_index=True,          # oculta el índice de pandas
    column_order=["nombre", "nota", "curso"],   # qué columnas y en qué orden
    column_config={...},      # formato de cada columna (ver 7.2)
)
```

- Para que la tabla ocupe todo el ancho, en versiones recientes se usa `width="stretch"`. En versiones antiguas se usaba `use_container_width=True`, que ahora está obsoleto.
- La tabla ya trae de serie ordenación al pulsar la cabecera, búsqueda (icono 🔍), descarga a CSV y pantalla completa.
- Para tablas grandes (más de ~10 000 filas), filtra antes con pandas: es más rápido que pasar todo el DataFrame al navegador.

### 7.2 Formato de columnas con `column_config`

`column_config` es un diccionario `{nombre_columna: configuración}`. El valor puede ser un texto (cambia solo el título), `None` (oculta la columna) o un objeto `st.column_config.*`:

```python
st.dataframe(
    df,
    hide_index=True,
    column_config={
        "id": None,                                   # ocultar
        "nombre": "Alumno",                           # solo renombrar
        "nota": st.column_config.NumberColumn(
            "Nota", format="%.1f", help="Nota final sobre 10"
        ),
        "precio": st.column_config.NumberColumn("Precio", format="%.2f €"),
        "progreso": st.column_config.ProgressColumn(
            "Progreso", min_value=0, max_value=100, format="%d %%"
        ),
        "fecha": st.column_config.DateColumn("Fecha", format="DD/MM/YYYY"),
        "aprobado": st.column_config.CheckboxColumn("¿Aprobado?"),
        "web": st.column_config.LinkColumn("Enlace", display_text="Abrir"),
        "foto": st.column_config.ImageColumn("Foto", width="small"),
        "historial": st.column_config.LineChartColumn("Evolución", y_min=0, y_max=10),
    },
)
```

Tipos más útiles:

| Tipo | Muestra | Notas |
|---|---|---|
| `TextColumn` | Texto | `max_chars`, `validate` (regex) al editar |
| `NumberColumn` | Número | `format` estilo printf (`"%.2f"`, `"%d %%"`, `"%.2f €"`), `min_value`, `max_value`, `step` |
| `ProgressColumn` | Barra de progreso | `min_value`, `max_value` |
| `CheckboxColumn` | Casilla | Para columnas booleanas |
| `SelectboxColumn` | Desplegable al editar | `options=[...]` |
| `DateColumn` / `DatetimeColumn` / `TimeColumn` | Fechas y horas | `format` con `DD`, `MM`, `YYYY`, `HH:mm` |
| `LinkColumn` | Enlace clicable | `display_text` fijo o regex para extraer el texto de la URL |
| `ImageColumn` | Miniatura | La celda debe contener una URL o un *data URI* |
| `LineChartColumn` / `BarChartColumn` / `AreaChartColumn` | Minigráfico | La celda debe contener una lista de números |

Parámetros comunes a todos: `label`, `width` (`"small"`, `"medium"`, `"large"` o píxeles), `help`, `disabled` y `required` (estos dos últimos, en el editor).

**Enlaces e imágenes de archivos locales en la tabla**: con el servicio estático activado (sección 6.4), basta con crear una columna con la URL:

```python
df["ficha_url"] = "app/static/fichas/" + df["archivo_pdf"]
df["imagen_url"] = "app/static/img/" + df["archivo_png"]

st.dataframe(
    df,
    column_config={
        "ficha_url": st.column_config.LinkColumn("Ficha", display_text="📄 Abrir"),
        "imagen_url": st.column_config.ImageColumn("Imagen"),
    },
)
```

### 7.3 Colorear celdas con `Styler` de pandas

`st.dataframe` acepta un `Styler` de pandas, lo que permite dar formato condicional:

```python
# Resaltar máximo y mínimo de las columnas numéricas
st.dataframe(df.style.highlight_max(color="#c8e6c9").highlight_min(color="#ffcdd2"))

# Colorear filas según una condición
def color_fila(fila):
    color = "background-color: #ffcdd2" if fila["nota"] < 5 else ""
    return [color] * len(fila)

st.dataframe(df.style.apply(color_fila, axis=1))

# Colorear celdas sueltas de una columna
st.dataframe(df.style.map(lambda v: "color: red" if v < 5 else "", subset=["nota"]))

# Formato de números y fechas (si no usas column_config)
st.dataframe(df.style.format({"precio": "{:.2f} €", "fecha": "{:%d/%m/%Y}"}))

# Degradado de color (requiere matplotlib)
st.dataframe(df.style.background_gradient(subset=["nota"], cmap="RdYlGn"))
```

En versiones antiguas de pandas, `Styler.map` se llamaba `applymap`.

### 7.4 Filtrar un DataFrame con widgets

Streamlit no filtra por sí mismo: los widgets dan valores y **pandas** hace el filtrado. El patrón recomendado es construir una máscara booleana y añadir condiciones solo cuando el widget tiene valor:

```python
with st.sidebar:
    texto = st.text_input("Buscar nombre")
    cursos = st.multiselect("Curso", sorted(df["curso"].unique()))
    grupo = st.selectbox("Grupo", ["Todos"] + sorted(df["grupo"].unique()))
    nota_min, nota_max = st.slider("Nota", 0.0, 10.0, (0.0, 10.0), step=0.5)
    solo_aprobados = st.checkbox("Solo aprobados")
    desde, hasta = st.date_input("Fechas", value=(df["fecha"].min(), df["fecha"].max()))

mascara = df["nota"].between(nota_min, nota_max)          # condición siempre presente

if texto:                                                  # texto contenido, sin mayúsculas
    mascara &= df["nombre"].str.contains(texto, case=False, regex=False, na=False)
if cursos:                                                 # multiselect vacío = todos
    mascara &= df["curso"].isin(cursos)
if grupo != "Todos":                                       # opción comodín
    mascara &= df["grupo"] == grupo
if solo_aprobados:
    mascara &= df["nota"] >= 5
mascara &= df["fecha"].between(pd.Timestamp(desde), pd.Timestamp(hasta))

filtrado = df[mascara]
st.caption(f"{len(filtrado)} de {len(df)} filas")
st.dataframe(filtrado, hide_index=True)
```

Recordatorio de operaciones de pandas:

| Condición | Expresión |
|---|---|
| Igual / distinto | `df["c"] == v`, `df["c"] != v` |
| Rango (incluye extremos) | `df["c"].between(a, b)` |
| Pertenece a una lista | `df["c"].isin(lista)` |
| Contiene texto | `df["c"].str.contains(t, case=False, regex=False, na=False)` |
| Empieza por | `df["c"].str.startswith(t)` |
| Nulo / no nulo | `df["c"].isna()`, `df["c"].notna()` |
| Y / O / NO | `&`, `\|`, `~` (con paréntesis en cada condición) |
| Alternativa en texto | `df.query("nota >= @minimo and curso in @cursos")` |

Detalles a tener en cuenta:

- Usa `regex=False` en `str.contains` para que caracteres como `(` o `+` que escriba el usuario no rompan la búsqueda.
- `st.date_input` con un rango devuelve una tupla **de uno o dos elementos** mientras el usuario está eligiendo. Comprueba que tenga longitud 2 antes de desempaquetarla.
- Las opciones de los desplegables deben salir de los datos (`sorted(df["col"].unique())`), no escribirse a mano.
- Para filtros **dependientes**, calcula las opciones del segundo widget a partir del DataFrame ya filtrado por el primero.

### 7.5 Seleccionar filas de la tabla

Desde la versión 1.35, `st.dataframe` permite que el usuario seleccione filas o columnas y devuelve la selección:

```python
evento = st.dataframe(
    filtrado.reset_index(drop=True),
    hide_index=True,
    on_select="rerun",              # relanza el script al seleccionar
    selection_mode="multi-row",     # "single-row", "multi-row", "single-column", "multi-column"
    key="tabla",
)

filas = evento.selection.rows       # lista de POSICIONES, p. ej. [0, 3]
if filas:
    seleccion = filtrado.reset_index(drop=True).iloc[filas]
    st.write("Has seleccionado:", seleccion["nombre"].tolist())
```

Las posiciones son relativas al DataFrame **mostrado**. Por eso conviene hacer `reset_index(drop=True)` antes y usar `.iloc`. La selección también queda en `st.session_state.tabla.selection`.

### 7.6 Editar con `st.data_editor`

`st.data_editor` se parece a `st.dataframe` pero permite editar celdas, y **devuelve un DataFrame nuevo con los cambios**. El original no se modifica.

```python
editado = st.data_editor(
    df,
    hide_index=True,
    num_rows="fixed",                   # "fixed" o "dynamic" (permite añadir/borrar filas)
    disabled=["id", "nombre"],          # columnas de solo lectura (o True para toda la tabla)
    column_order=["id", "nombre", "nota", "curso", "aprobado"],
    column_config={
        "nota": st.column_config.NumberColumn("Nota", min_value=0, max_value=10, step=0.1, required=True),
        "curso": st.column_config.SelectboxColumn("Curso", options=["1º Bach", "2º Bach"], required=True),
        "aprobado": st.column_config.CheckboxColumn("Aprobado"),
    },
    key="editor",
)

st.write("Nota media tras editar:", editado["nota"].mean())
```

- Con `num_rows="dynamic"` aparece una fila vacía al final para añadir, y se pueden borrar filas seleccionándolas.
- Las columnas booleanas se editan con casilla y las de fecha con calendario automáticamente.
- `SelectboxColumn` convierte la celda en un desplegable.
- Columnas calculadas: no las metas en el editor. Calcúlalas después a partir de `editado`.

**Saber qué ha cambiado**: si el editor tiene `key`, en `st.session_state[key]` se guarda un diccionario con los cambios respecto al DataFrame de entrada:

```python
cambios = st.session_state["editor"]
cambios["edited_rows"]    # {0: {"nota": 7.5}, 4: {"curso": "2º Bach"}}  posición → cambios
cambios["added_rows"]     # [{"nombre": "Nuevo", "nota": 6}]
cambios["deleted_rows"]   # [2, 7]  posiciones borradas

hay_cambios = any(cambios[k] for k in ("edited_rows", "added_rows", "deleted_rows"))
```

### 7.7 Guardar las ediciones (patrón completo)

El editor solo recuerda las ediciones mientras su entrada no cambie. Para que los cambios se conserven, hay que guardarlos en `session_state` y, si se quiere persistencia permanente, en disco:

```python
RUTA = "alumnos.csv"

@st.cache_data
def cargar(ruta):
    return pd.read_csv(ruta)

# 1. Copia de trabajo en la sesión (se carga una sola vez)
if "datos" not in st.session_state:
    st.session_state.datos = cargar(RUTA)

# 2. Editor sobre la copia de trabajo
editado = st.data_editor(st.session_state.datos, num_rows="dynamic", key="editor")

# 3. Guardar al pulsar el botón
if st.button("💾 Guardar"):
    st.session_state.datos = editado            # actualiza la copia de la sesión
    editado.to_csv(RUTA, index=False)           # persistencia en disco
    cargar.clear()                              # la caché ya no es válida
    del st.session_state["editor"]              # limpia las ediciones pendientes
    st.success("Guardado")
    st.rerun()
```

**Editar una tabla filtrada**: si el editor muestra solo una parte de los datos, hay que llevar los cambios a la tabla completa emparejando por una columna identificadora, **nunca por posición**:

```python
filtrado = st.session_state.datos[mascara]
editado = st.data_editor(filtrado[["id", "nombre", "nota"]], disabled=["id", "nombre"], key="editor")

if st.button("Guardar"):
    completo = st.session_state.datos.set_index("id")
    cambios = editado.set_index("id")
    completo.loc[cambios.index, ["nota"]] = cambios[["nota"]]
    st.session_state.datos = completo.reset_index()
```

Errores frecuentes:

- **Las ediciones «desaparecen»**: ocurre cuando el DataFrame que recibe el editor cambia entre ejecuciones (por un filtro, un `sort_values` o columnas recalculadas). El editor se reinicia con los datos nuevos. Guarda antes de cambiar los filtros, o desactiva los filtros mientras se edita.
- **Asignar `st.session_state.datos = editado` en cada ejecución** (fuera del botón) provoca que el editor reciba datos distintos cada vez y pierda las ediciones. Actualiza el estado solo en un callback o tras pulsar un botón.
- **Tipos de datos**: una columna entera con algún valor vacío se convierte en `float`. Usa `required=True` en el `column_config` para impedir celdas vacías.

---

## 8. Ejemplo completo

```python
import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(page_title="Ejercicios", layout="wide")

@st.cache_data
def cargar():
    return pd.read_csv("ejercicios.csv")   # columnas: asignatura, tema, titulo, pdf

df = cargar()

if "favoritos" not in st.session_state:
    st.session_state.favoritos = []

with st.sidebar:
    asig = st.selectbox("Asignatura", sorted(df["asignatura"].unique()))
    temas = st.multiselect("Temas", sorted(df.loc[df.asignatura == asig, "tema"].unique()))

filtrado = df[df.asignatura == asig]
if temas:
    filtrado = filtrado[filtrado.tema.isin(temas)]

st.title(f"Ejercicios de {asig}")
st.caption(f"{len(filtrado)} ejercicios")

for i, fila in filtrado.iterrows():
    c1, c2, c3 = st.columns([4, 1, 1])
    c1.markdown(f"**{fila.titulo}** · [abrir PDF](app/static/{fila.pdf})")
    with open(Path("static") / fila.pdf, "rb") as f:
        c2.download_button("Descargar", f, fila.pdf, "application/pdf", key=f"d{i}")
    if c3.button("⭐", key=f"f{i}"):
        st.session_state.favoritos.append(fila.titulo)

with st.expander("Favoritos"):
    st.write(st.session_state.favoritos)
```

---

## 9. Resumen rápido

| Necesito... | Uso |
|---|---|
| Lista desplegable | `st.selectbox` / `st.multiselect` |
| Que una carga lenta no se repita | `@st.cache_data` |
| Una conexión o modelo compartido | `@st.cache_resource` |
| Recordar algo entre clics | `st.session_state` |
| Guardar datos para siempre | Archivo o base de datos |
| Mostrar una imagen | `st.image` |
| Que el usuario baje un archivo | `st.download_button` |
| Enlace que abre un archivo local | `enableStaticServing` + `static/` + `app/static/...` |
| Enlace a una web | `st.markdown("[texto](url)")` o `st.link_button` |
| Tabla interactiva | `st.dataframe` |
| Dar formato a columnas (€, fechas, barras, enlaces, imágenes) | `column_config` + `st.column_config.*` |
| Colorear celdas o filas | `df.style.apply(...)` / `df.style.map(...)` |
| Filtrar una tabla con widgets | Máscara booleana de pandas combinada con `&=` |
| Saber qué filas ha seleccionado el usuario | `st.dataframe(..., on_select="rerun")` → `.selection.rows` |
| Que el usuario edite una tabla | `st.data_editor` |
| Saber qué celdas se han editado | `st.session_state[key]["edited_rows"]` |
