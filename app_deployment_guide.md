# Deploy de Streamlit con Nginx en un VPS Debian

Oct 24, 2026 · @Dani

## Visión general

Streamlit escucha solo en `127.0.0.1:8501`, systemd lo mantiene vivo y Nginx es la única puerta al exterior: recibe HTTPS en el puerto 443 y reenvía las peticiones (incluido el WebSocket) a Streamlit. Así el proceso de Python nunca queda expuesto directamente a Internet.

&#91;embedded content: arquitectura del despliegue · navegador, Nginx y Streamlit\]

El navegador solo habla con Nginx; Nginx reenvía por la red interna del propio VPS a Streamlit, que systemd mantiene en marcha.

Por qué un proxy inverso delante:

- **HTTPS**: Nginx gestiona los certificados; Streamlit no tiene que saber nada de TLS.
- **Dominio y puertos limpios**: el usuario entra en `https://app.midominio.es`, sin `:8501`.
- **Varias apps en un VPS**: cada dominio o subruta apunta a un puerto interno distinto.
- **Seguridad y control**: cabeceras, límites de subida, autenticación básica o bloqueo de IPs, sin tocar la app.

Requisitos previos:

- Un VPS con Debian 12 (bookworm) o 13 (trixie) y acceso SSH.
- Un dominio o subdominio con un registro **A** apuntando a la IP pública del VPS (y **AAAA** si usas IPv6). Sin esto no se puede emitir el certificado.
- Tu app en un repositorio Git o en una carpeta local con `app.py` y `requirements.txt`.

Nombres usados en toda la guía (cámbialos por los tuyos): usuario `deploy`, carpeta `/home/deploy/miapp`, fichero principal `app.py`, dominio `app.midominio.es`.

## Paso 1: preparar el servidor

El objetivo es un sistema actualizado, un usuario sin privilegios que ejecute la app y un firewall que solo deje pasar SSH, HTTP y HTTPS.

### 1.1 Actualizar e instalar paquetes

Conectado como root (o con un usuario con `sudo`):

```bash
# Descarga la lista actualizada de paquetes disponibles
apt update

# Instala las actualizaciones pendientes; -y responde "sí" a todo
apt upgrade -y

# Instala lo necesario:
#   python3        intérprete de Python del sistema
#   python3-venv   módulo para crear entornos virtuales (en Debian va aparte)
#   python3-pip    gestor de paquetes de Python
#   git            para clonar y actualizar tu repositorio
#   nginx          el servidor web que hará de proxy inverso
#   ufw            firewall sencillo (front-end de nftables/iptables)
#   sudo           por si la imagen del VPS no lo trae
apt install -y python3 python3-venv python3-pip git nginx ufw sudo
```

### 1.2 Crear un usuario para la app

No conviene ejecutar Streamlit como root: si la app tuviera un fallo explotable, el atacante tendría el sistema entero.

```bash
# Crea el usuario 'deploy' con su /home/deploy y pide contraseña
adduser deploy

# (Opcional) lo añade al grupo sudo para administrar con él
usermod -aG sudo deploy
```

Si entras por clave SSH, copia tu clave al nuevo usuario desde tu ordenador con `ssh-copy-id deploy@IP_DEL_VPS`.

### 1.3 Firewall con ufw

```bash
# Por defecto, rechaza todo lo que entra
ufw default deny incoming

# Por defecto, permite todo lo que sale (apt, pip, git...)
ufw default allow outgoing

# Abre el 22/tcp (SSH). HAZLO ANTES de activar el firewall o te quedas fuera
ufw allow OpenSSH

# Abre 80/tcp (HTTP) y 443/tcp (HTTPS); es un perfil que instala nginx
ufw allow 'Nginx Full'

# Activa el firewall y lo deja activo tras reiniciar
ufw enable

# Comprueba las reglas activas
ufw status verbose
```

Fíjate en que **no** se abre el 8501: Streamlit solo será accesible a través de Nginx. Si tu SSH usa otro puerto, cambia `OpenSSH` por `ufw allow 2222/tcp` (con tu puerto). Si tu proveedor tiene un firewall propio en el panel, abre allí también el 80 y el 443.

## Paso 2: subir la app y crear el entorno virtual

Cada app necesita un entorno virtual con sus dependencias, separado del Python del sistema (Debian 12 y 13 bloquean `pip install` global por la PEP 668). Hay dos formas de organizarlo: un entorno por app o uno compartido por varias apps (2.3).

### 2.1 Subir el código

```bash
# Pasa a ser el usuario deploy (con su entorno y su $HOME)
su - deploy

# Descarga el repo en /home/deploy/miapp
git clone https://github.com/tuusuario/miapp.git ~/miapp

# Entra en la carpeta del proyecto
cd ~/miapp
```

Si el repositorio es privado, usa una *deploy key* SSH o un token de acceso. Si no usas Git, sube la carpeta con `scp -r miapp deploy@IP_DEL_VPS:~/` o `rsync`. No subas nunca la carpeta del venv desde tu ordenador: se crea en el servidor.

### 2.2 requirements.txt

Un `requirements.txt` mínimo, con versiones fijadas para que el servidor instale lo mismo que probaste en local:

```text
streamlit==1.50.0
pandas==2.3.3
```

Las versiones son de ejemplo: sácalas de tu entorno local con `pip freeze > requirements.txt`.

### 2.3 Crear el entorno: elige una opción

Regla para las dos: un venv **no se puede mover ni renombrar** después de crearlo, porque sus scripts guardan rutas absolutas. Créalo directamente en su ruta definitiva; si hay que cambiarlo de sitio, se borra y se recrea.

#### Opción A: un entorno por app, con uv

[uv](https://docs.astral.sh/uv/) sustituye a `venv` y `pip`. Guarda cada paquete una sola vez en una caché global (`~/.cache/uv`) y en cada venv crea *hardlinks* a esa caché en vez de copias.

```bash
# Instala uv para el usuario actual (una sola vez); queda en ~/.local/bin
curl -LsSf https://astral.sh/uv/install.sh | sh

# Recarga el PATH para que esta terminal encuentre el comando uv
source ~/.local/bin/env

# Crea el entorno en .venv, dentro de la carpeta de la app
uv venv .venv

# Instala las dependencias de la app en ese entorno
uv pip install -r requirements.txt --python .venv/bin/python
```

Ventajas:

- Aislamiento total: cada app tiene sus versiones y actualizar una no afecta a las demás.
- Poco disco: el mismo Streamlit en cinco apps ocupa casi lo mismo que en una.
- Instala en segundos en vez de minutos.
- El `.service` del Paso 4 no cambia: sigue usando `.venv/bin/streamlit`.

Inconvenientes:

- Es una herramienta más que instalar y aprender.
- El ahorro de espacio solo funciona si la caché y los venvs están en el mismo disco (en un VPS normal, siempre).
- Para cada app nueva hay que crear su entorno e instalar sus dependencias.

Sin uv se hace igual con las herramientas estándar, pero entonces cada venv es una copia completa (400 a 600 MB con Streamlit y pandas):

```bash
# Crea el entorno en .venv
python3 -m venv .venv

# Actualiza pip dentro del entorno
.venv/bin/pip install --upgrade pip

# Instala las dependencias de la app
.venv/bin/pip install -r requirements.txt
```

#### Opción B: un entorno compartido por varias apps

El venv vive fuera de las carpetas de las apps y todas usan el mismo. Cada app sigue teniendo su propio puerto y su `baseUrlPath`, porque Streamlit lee `.streamlit/config.toml` de la carpeta de trabajo, no de la del venv.

```bash
# Crea el entorno común fuera de las carpetas de las apps
python3 -m venv /home/deploy/venvs/streamlit

# Actualiza pip dentro del entorno común
/home/deploy/venvs/streamlit/bin/pip install --upgrade pip

# Instala las dependencias de esta app; repítelo con el requirements.txt de cada app nueva
/home/deploy/venvs/streamlit/bin/pip install -r requirements.txt
```

Ventajas:

- Sin herramientas extra: solo `venv` y `pip`.
- Una app nueva con las mismas dependencias no instala nada.
- Un solo sitio que actualizar.

Inconvenientes:

- Todas las apps comparten versiones: si una necesita pandas 2.2 y otra 2.3, una de las dos se queda sin la suya.
- Actualizar un paquete para una app puede romper otra.
- Desinstalar paquetes es arriesgado, porque no sabes qué app los usa.
- En el `.service` cambia `ExecStart` (ver Paso 4).

**Cuál elegir**: la opción B para apps de prueba o prácticas; la opción A para apps que vas a mantener en el tiempo.

### 2.4 Prueba rápida

Antes de seguir, comprueba que la app arranca con el Streamlit del entorno:

```bash
# Opción A (entorno propio)
.venv/bin/streamlit run app.py --server.address 127.0.0.1 --server.port 8501

# Opción B (entorno compartido)
/home/deploy/venvs/streamlit/bin/streamlit run app.py --server.address 127.0.0.1 --server.port 8501

# En otra sesión SSH: debería responder HTTP/1.1 200 OK
curl -I http://127.0.0.1:8501
```

Detén la prueba con Ctrl+C: a partir de ahora la arrancará systemd.

## Paso 3: configurar Streamlit

Streamlit lee `.streamlit/config.toml` de la carpeta desde la que se lanza. Ahí fijamos la dirección, el puerto y el modo producción, en vez de pasarlos como flags.

Crea `/home/deploy/miapp/.streamlit/config.toml`:

```toml
[server]
# Escucha solo en local: inaccesible desde fuera aunque falle el firewall
address = "127.0.0.1"

# Puerto interno; Nginx reenviará aquí
port = 8501

# No intenta abrir navegador ni pide email al arrancar (servidor sin pantalla)
headless = true

# No recarga la app al detectar cambios en el código
runOnSave = false

# Desactiva la vigilancia de ficheros: menos CPU y sin recargas inesperadas
fileWatcherType = "none"

# Tamaño máximo de st.file_uploader, en MB (200 es el valor por defecto)
maxUploadSize = 200

# Protección CORS activada (por defecto); con proxy en el mismo dominio no molesta
enableCORS = true

# Protección XSRF activada (por defecto); déjala así
enableXsrfProtection = true

[browser]
# No envía estadísticas de uso anónimas a Streamlit
gatherUsageStats = false

[theme]
# Opcional: fuerza tema claro (o "dark")
base = "light"
```

Notas:

- `address = "127.0.0.1"` es la línea clave de seguridad: con `0.0.0.0` la app escucharía en todas las interfaces y, si el firewall tuviera un hueco, se podría entrar por `IP:8501` saltándose Nginx y HTTPS.
- Nginx limita por defecto cada petición a 1 MB, así que para subir archivos grandes con `maxUploadSize` hay que ajustar también `client_max_body_size` en Nginx (Paso 5), o Nginx cortará las subidas antes de que lleguen a Streamlit.
- Los secretos (contraseñas de BD, API keys) van en `.streamlit/secrets.toml`, que **no** se sube a Git: cópialo a mano al servidor y protégelo con `chmod 600 .streamlit/secrets.toml`.

## Paso 4: servicio systemd

systemd arranca Streamlit al encender el VPS, lo reinicia si se cae y guarda sus logs. Sustituye a dejar un `streamlit run` abierto en `screen` o `nohup`.

Crea `/etc/systemd/system/miapp.service` (como root o con `sudo nano`):

```ini
[Unit]
# Nombre legible que sale en systemctl status y en los logs
Description=Streamlit - miapp
# Arranca después de que la red esté levantada
After=network-online.target
# Pide que ese objetivo de red se active
Wants=network-online.target

[Service]
# El proceso lanzado ES el servicio (no se demoniza solo)
Type=simple
# Se ejecuta como el usuario sin privilegios...
User=deploy
# ...y con su grupo
Group=deploy
# Carpeta de trabajo: aquí busca .streamlit/config.toml y las rutas relativas
WorkingDirectory=/home/deploy/miapp
# Los print() salen al log al momento, sin buffer
Environment=PYTHONUNBUFFERED=1
# Comando de arranque con el streamlit del venv (ruta absoluta)
ExecStart=/home/deploy/miapp/.venv/bin/streamlit run app.py
# Si el proceso muere con error, lo vuelve a lanzar
Restart=on-failure
# Espera 5 s antes de reintentar
RestartSec=5

# Endurecimiento (opcional pero recomendable)
# El proceso no puede ganar privilegios (p. ej. vía setuid)
NoNewPrivileges=true
# /tmp propio y aislado para el servicio
PrivateTmp=true
# /usr, /boot y /etc quedan de solo lectura para la app
ProtectSystem=full

[Install]
# Se activa en el arranque normal del sistema (al hacer enable)
WantedBy=multi-user.target
```

En los ficheros de systemd un comentario solo es válido si la línea **empieza** por `#` o `;`. Un comentario al final de una línea con valor se toma como parte del valor y rompe el servicio.

No hace falta activar el venv: al llamar al binario `.venv/bin/streamlit` por ruta absoluta, ya usa el Python y los paquetes de ese entorno.

Si usas el **entorno compartido** (opción B del Paso 2), solo cambia `ExecStart`; `WorkingDirectory` sigue apuntando a la carpeta de cada app, que es de donde Streamlit lee su `config.toml`:

```ini
WorkingDirectory=/home/deploy/miapp
ExecStart=/home/deploy/venvs/streamlit/bin/streamlit run app.py
```

Actívalo:

```bash
# Relee los ficheros .service (necesario tras crear o editar uno)
sudo systemctl daemon-reload

# enable: arranca en cada inicio; --now: arráncalo también ya
sudo systemctl enable --now miapp

# Debe decir "active (running)"
sudo systemctl status miapp

# Comprobación desde el propio VPS
curl -I http://127.0.0.1:8501
```

Si tu app necesita variables de entorno, añade `EnvironmentFile=/home/deploy/miapp/.env` en `[Service]` con un fichero `CLAVE=valor` por línea.

## Paso 5: Nginx como proxy inverso

La clave con Streamlit es el **WebSocket**: la página carga por HTTP normal, pero toda la interacción (widgets, reruns) va por una conexión persistente en `/_stcore/stream`. Si Nginx no reenvía las cabeceras de *upgrade*, la app se queda en «Please wait...» o se reconecta sin parar.

En Debian, cada sitio va en `/etc/nginx/sites-available/` y se activa con un enlace en `sites-enabled/`. Crea `/etc/nginx/sites-available/miapp`:

```nginx
# Traduce la cabecera Upgrade del cliente en el valor correcto de Connection
map $http_upgrade $connection_upgrade {
    # Si el cliente pide Upgrade (WebSocket), Connection: upgrade
    default upgrade;
    # Si no la pide (HTTP normal), Connection: close
    ''      close;
}

server {
    # Escucha HTTP en IPv4, puerto 80
    listen 80;
    # Lo mismo en IPv6
    listen [::]:80;
    # Este bloque solo atiende a este dominio
    server_name app.midominio.es;

    # Tamaño máximo de petición; igual o mayor que maxUploadSize de Streamlit
    client_max_body_size 200M;

    # Todo lo que llegue (cualquier ruta) se gestiona aquí
    location / {
        # Reenvía a Streamlit
        proxy_pass http://127.0.0.1:8501;
        # HTTP/1.1: obligatorio para WebSocket y keep-alive
        proxy_http_version 1.1;

        # Pasa el dominio original, no "127.0.0.1"
        proxy_set_header Host $host;
        # IP real del visitante
        proxy_set_header X-Real-IP $remote_addr;
        # Cadena de IPs por las que pasó la petición
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        # Indica si el cliente usó http o https
        proxy_set_header X-Forwarded-Proto $scheme;

        # Reenvía la petición de cambio a WebSocket...
        proxy_set_header Upgrade $http_upgrade;
        # ...con el valor calculado en el map de arriba
        proxy_set_header Connection $connection_upgrade;

        # 24 h sin datos antes de cerrar; el defecto (60 s) corta sesiones inactivas
        proxy_read_timeout 86400;
        # Lo mismo en sentido servidor a cliente
        proxy_send_timeout 86400;
        # Entrega las respuestas al momento, sin acumularlas en Nginx
        proxy_buffering off;
    }
}
```

Por qué el `map` va fuera del `server`: la directiva `map` solo es válida en el contexto `http`, y Debian incluye los ficheros de `sites-enabled/` justo dentro de ese contexto en `/etc/nginx/nginx.conf`. Si sirves varias apps, defínelo **una sola vez** (por ejemplo, en `/etc/nginx/conf.d/websocket.conf`); repetido en dos ficheros, `nginx -t` da error.

**Si es otra app del mismo VPS**, cada una necesita su propio puerto interno, porque dos procesos no pueden escuchar en el mismo. En la segunda app cambia el 8501 por otro libre (8502, 8503...) en dos sitios, siempre con el mismo número:

- `port = 8502` en su `.streamlit/config.toml` (Paso 3).
- `proxy_pass http://127.0.0.1:8502;` en su fichero de `sites-available` (este paso).

Los `listen 80` y `listen 443` de Nginx **no** se tocan: todas las apps comparten esos puertos públicos, y Nginx las distingue por `server_name` (subdominio) o por `location` (subruta). Para ver qué puertos internos están ya ocupados: `sudo ss -ltnp | grep 85`.

Activar el sitio:

```bash
# Activa el sitio con un enlace simbólico
sudo ln -s /etc/nginx/sites-available/miapp /etc/nginx/sites-enabled/

# Desactiva la página de bienvenida de Nginx
sudo rm /etc/nginx/sites-enabled/default

# Valida la sintaxis; debe decir "syntax is ok" y "test is successful"
sudo nginx -t

# Aplica la configuración sin cortar conexiones abiertas
sudo systemctl reload nginx
```

Ahora `http://app.midominio.es` ya debería mostrar la app. Ejecuta siempre `nginx -t` antes del `reload`: si hay un error de sintaxis, el reload no se aplica y el sitio sigue funcionando con la configuración anterior.

## Paso 6: HTTPS con Let's Encrypt

Certbot pide un certificado gratuito a Let's Encrypt, edita tu fichero de Nginx para usarlo y deja programada la renovación. Necesita que el dominio ya resuelva a tu VPS y que el puerto 80 esté abierto.

```bash
# Certbot + su plugin que sabe editar Nginx
sudo apt install -y certbot python3-certbot-nginx

# Pide el certificado y modifica el sitio.
# Te pedirá un email (avisos de caducidad) y aceptar los términos.
sudo certbot --nginx -d app.midominio.es

# Simula una renovación para comprobar que funcionará
sudo certbot renew --dry-run

# El paquete instala un timer que renueva solo, dos veces al día
systemctl list-timers | grep certbot
```

Los certificados duran 90 días y el timer los renueva cuando les quedan menos de 30; Nginx se recarga solo tras renovar.

Tras ejecutar certbot, tu fichero queda así (las líneas con `# managed by Certbot` las añade él):

```nginx
# Traduce la cabecera Upgrade del cliente en el valor correcto de Connection
map $http_upgrade $connection_upgrade {
    default upgrade;
    ''      close;
}

server {
    # HTTPS en IPv4; "ssl" activa TLS en este puerto
    listen 443 ssl;
    # HTTPS en IPv6
    listen [::]:443 ssl;
    # (Opcional, añádelo tú) HTTP/2: menos latencia al cargar la página
    http2 on;
    server_name app.midominio.es;

    # Certificado + cadena intermedia
    ssl_certificate /etc/letsencrypt/live/app.midominio.es/fullchain.pem;
    # Clave privada (solo legible por root)
    ssl_certificate_key /etc/letsencrypt/live/app.midominio.es/privkey.pem;
    # Protocolos y cifrados recomendados por Certbot
    include /etc/letsencrypt/options-ssl-nginx.conf;
    # Parámetros Diffie-Hellman para el intercambio de claves
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    client_max_body_size 200M;

    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
        proxy_read_timeout 86400;
        proxy_send_timeout 86400;
        proxy_buffering off;
    }
}

server {
    listen 80;
    listen [::]:80;
    server_name app.midominio.es;
    # Redirección permanente de http a https, conservando la ruta
    return 301 https://$host$request_uri;
}
```

Certbot suele escribir la redirección con un `if ($host = ...)`; funciona igual, la versión con `return 301` es solo más limpia. La línea `http2 on;` es la sintaxis de Nginx 1.25 o posterior (Debian 13 trae 1.26); en Debian 12 (Nginx 1.22) se escribe `listen 443 ssl http2;`.

Opcional, dentro del bloque 443, para que el navegador recuerde usar siempre HTTPS:

```nginx
# HSTS durante 1 año
add_header Strict-Transport-Security "max-age=31536000" always;
```

Añádelo solo cuando hayas comprobado que HTTPS funciona bien: si luego quitas el certificado, los navegadores que ya lo vieron no podrán entrar por HTTP.

Comprueba: `sudo nginx -t && sudo systemctl reload nginx` y abre `https://app.midominio.es`.

## Variantes habituales

### Varias apps en el mismo VPS (un subdominio cada una)

Cada app lleva su carpeta, su venv, su puerto interno y su servicio. Para la segunda:

1. En su `.streamlit/config.toml`, `port = 8502`.
2. Copia el servicio como `/etc/systemd/system/otraapp.service`, cambiando `Description`, `WorkingDirectory` y `ExecStart`.
3. Copia el sitio de Nginx como `otraapp`, con `server_name otra.midominio.es` y `proxy_pass http://127.0.0.1:8502`.
4. Mueve el `map` a `/etc/nginx/conf.d/websocket.conf` y bórralo de ambos sitios, para que exista una sola vez.
5. `sudo certbot --nginx -d otra.midominio.es`.

### Servir en una subruta (`midominio.es/inventario/`)

Ejemplo: una segunda app en `https://midominio.es/inventario/`, en la carpeta `/home/deploy/inventario` y en el puerto interno 8502. Pasos 2 y 4 igual que antes (venv propio y servicio propio, p. ej. `inventario.service`); cambian el `config.toml` y Nginx. No hace falta certificado nuevo: el dominio es el mismo.

Streamlit tiene que saber que vive bajo un prefijo, o generará enlaces a `/static/...` que no existen. `baseUrlPath` es el prefijo que quieres en la URL, no el nombre de la carpeta. Su `/home/deploy/inventario/.streamlit/config.toml` completo:

```toml
[server]
# Solo en local
address = "127.0.0.1"

# Un puerto distinto al de cualquier otra app del VPS
port = 8502

# Prefijo de la URL: la app vivirá en /inventario/ (sin barras al principio ni al final)
baseUrlPath = "inventario"

headless = true
runOnSave = false
fileWatcherType = "none"

[browser]
gatherUsageStats = false
```

Comprueba que responde en su prefijo antes de tocar Nginx (sin la barra final, Streamlit contesta 307 y redirige a ella, lo cual es correcto):

```bash
# Debe devolver 200 OK
curl -I http://127.0.0.1:8502/inventario/
```

En Nginx no se crea un sitio nuevo: estos dos `location` se pegan **dentro del `server` que ya atiende a `midominio.es` en el puerto 443**, junto a su `location /`. El nombre del `location` tiene que coincidir letra a letra con `baseUrlPath`:

```nginx
# Coincidencia exacta: /inventario sin barra final
location = /inventario {
    # Redirige a /inventario/ para que las rutas relativas funcionen
    return 301 /inventario/;
}

# Todo lo que empiece por /inventario/
location /inventario/ {
    # SIN ruta al final: Nginx reenvía la URI completa, /inventario/ incluido
    proxy_pass http://127.0.0.1:8502;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection $connection_upgrade;
    proxy_read_timeout 86400;
    proxy_send_timeout 86400;
    proxy_buffering off;
}
```

Aplica y prueba en `https://midominio.es/inventario/`:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

El detalle de `proxy_pass`: sin nada tras el puerto, Nginx pasa la ruta tal cual (`/inventario/...`), que es lo que espera Streamlit con `baseUrlPath`. Si escribieras `http://127.0.0.1:8502/`, Nginx quitaría el prefijo y la app no encontraría sus recursos.

### Proteger con usuario y contraseña

Autenticación básica en Nginx, sin tocar la app. Solo es segura sobre HTTPS.

```bash
# Trae el comando htpasswd
sudo apt install -y apache2-utils

# -c crea el fichero; pide la contraseña y la guarda cifrada
sudo htpasswd -c /etc/nginx/.htpasswd dani

# Más usuarios: sin -c, o borrarías el fichero
sudo htpasswd /etc/nginx/.htpasswd alumno1
```

Dentro del `location /` del bloque 443:

```nginx
# Activa la autenticación; el texto lo muestra el navegador
auth_basic "Acceso restringido";
# Fichero con los usuarios y contraseñas cifradas
auth_basic_user_file /etc/nginx/.htpasswd;
```

## Mantenimiento y problemas comunes

### Actualizar la app

```bash
cd /home/deploy/miapp

# Trae los cambios del repositorio (como usuario deploy)
git pull

# Instala dependencias nuevas, si las hay
.venv/bin/pip install -r requirements.txt

# Reinicia Streamlit para cargar el código nuevo
sudo systemctl restart miapp
```

Al reiniciar, los usuarios conectados verán un breve «Connecting...» y su sesión (`st.session_state`) se perderá.

### Ver logs

```bash
# Logs de Streamlit en directo (-f = follow); Ctrl+C para salir
journalctl -u miapp -f

# Logs de la última hora
journalctl -u miapp --since "1 hour ago"

# Errores de Nginx (502, permisos, upstream)
sudo tail -f /var/log/nginx/error.log

# Cada petición recibida
sudo tail -f /var/log/nginx/access.log
```

### Problemas típicos

| Síntoma | Causa probable | Solución |
| --- | --- | --- |
| 502 Bad Gateway | Streamlit no está corriendo o escucha en otro puerto | `systemctl status miapp` y `journalctl -u miapp`; revisa que `port` coincida con `proxy_pass` |
| «Please wait...» infinito o reconexiones | El WebSocket no pasa por Nginx | Revisa `proxy_http_version 1.1` y las cabeceras `Upgrade` y `Connection` |
| La app se desconecta tras \~1 min sin uso | Timeout por defecto de 60 s | `proxy_read_timeout 86400;` |
| Error 413 al subir un archivo | Límite de Nginx (1 MB por defecto) | `client_max_body_size` mayor o igual que `maxUploadSize` |
| Página en blanco en una subruta | Falta `baseUrlPath` o `proxy_pass` termina en `/` | Paso «Servir en una subruta» |
| Certbot falla al validar | DNS sin propagar o puerto 80 cerrado | `dig app.midominio.es` y `ufw status`; revisa también el firewall del proveedor |
| El servicio no arranca: *status=203/EXEC* | Ruta de `ExecStart` incorrecta, o venv movido o renombrado tras crearlo | Recrea el venv en su ruta definitiva y comprueba que existe `/home/deploy/miapp/.venv/bin/streamlit` |
| `ModuleNotFoundError` en el log | Paquete instalado fuera del venv | `.venv/bin/pip install` del paquete y reinicia el servicio |
