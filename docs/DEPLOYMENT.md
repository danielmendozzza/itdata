# Despliegue de producción con Docker

## Arquitectura

El único servicio expuesto públicamente es Nginx:

```text
Usuario -> http://IP_DEL_SERVIDOR:80 -> Nginx
                                      |-> Angular
                                      |-> /api y /admin -> Gunicorn/Django
                                      |-> /static y /media -> volúmenes

Django -> PostgreSQL (red interna de Docker)
```

PostgreSQL y Gunicorn no publican puertos en el servidor.

## Requisitos del servidor

- Git.
- Docker Engine.
- Docker Compose v2 (`docker compose`).
- Puerto TCP 80 permitido en el firewall.

## Primera instalación

```bash
git clone URL_DEL_REPOSITORIO itdata
cd itdata
cp .env.example .env
```

Generar una clave para Django:

```bash
openssl rand -base64 48
```

Editar `.env` y reemplazar:

- `SECRET_KEY` por la clave generada.
- `DB_PASSWORD` por una contraseña distinta y segura.
- `ALLOWED_HOSTS` por la IP del servidor.
- La IP de `CSRF_TRUSTED_ORIGINS` y `CORS_ALLOWED_ORIGINS`.

Construir e iniciar:

```bash
docker compose -f compose.production.yml up -d --build
```

Las migraciones y `collectstatic` se ejecutan automáticamente al iniciar el
backend.

Crear el primer administrador:

```bash
docker compose -f compose.production.yml exec backend \
  python manage.py createsuperuser
```

Verificar los contenedores:

```bash
docker compose -f compose.production.yml ps
docker compose -f compose.production.yml logs -f backend web
```

La aplicación quedará disponible en:

```text
http://IP_DEL_SERVIDOR
```

## Instalación desde el archivo TAR

Un solo archivo TAR puede contener varias imágenes. `itdata-images.tar`
incluye `itdata-backend:latest`, `itdata-web:latest` y
`postgres:17-alpine`.

Importarlas:

```bash
docker load -i itdata-images.tar
```

Levantar sin compilar y sin necesitar el código fuente:

```bash
docker compose -f compose.images.yml up -d
```

Para actualizar desde otro TAR:

```bash
docker compose -f compose.images.yml down
docker load -i itdata-images.tar
docker compose -f compose.images.yml up -d
```

No agregar `-v` al comando `down`, porque eliminaría la base de datos.

## Actualizaciones posteriores

```bash
git pull
docker compose -f compose.production.yml up -d --build
docker image prune -f
```

## Puertos

`HTTP_PORT=80` publica Nginx en el puerto HTTP estándar. El navegador no
muestra `:80`, por lo que se usa solamente `http://IP_DEL_SERVIDOR`.

Si el puerto 80 estuviera ocupado, se puede definir, por ejemplo:

```env
HTTP_PORT=8080
```

En ese caso la dirección sí sería:

```text
http://IP_DEL_SERVIDOR:8080
```

## HTTPS

Para HTTPS se recomienda asignar un dominio y colocar un proxy con certificado
TLS delante de este Compose, por ejemplo Caddy, Traefik o Nginx con Certbot.
Cuando exista HTTPS:

```env
ALLOWED_HOSTS=itdata.ejemplo.com
CSRF_TRUSTED_ORIGINS=https://itdata.ejemplo.com
CORS_ALLOWED_ORIGINS=https://itdata.ejemplo.com
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
```

No se debe activar `SECURE_SSL_REDIRECT` hasta que el certificado y el proxy
HTTPS estén funcionando.

## Copias de seguridad

Crear un respaldo:

```bash
docker compose -f compose.production.yml exec -T db \
  sh -c 'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"' > itdata-backup.sql
```

También debe respaldarse el volumen `media_data`, que contiene los archivos
subidos por los usuarios.

El archivo `.env`, los respaldos y las bases locales están excluidos de Git.
