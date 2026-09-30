# Despliegue

El repo incluye imágenes de producción listas para usar:

- `backend/Dockerfile.prod`
- `worker/Dockerfile.prod` (se reutiliza tanto para el worker de Celery como para Celery Beat)
- `frontend/Dockerfile.prod`

Hay dos rutas documentadas:

- **Opción A — Railway**: más rápida de configurar, pero **no es gratis indefinidamente** (da un
  crédito de prueba y luego cobra por uso; con 4 servicios + Postgres + Redis corriendo 24/7 el
  crédito se agota en días).
- **Opción B — Oracle Cloud Free Tier**: una VM **gratuita para siempre** (Always Free), más manual
  de configurar (tú administras el servidor), pero sin coste recurrente.

---

## Opción A: Railway

Asume que el repo ya está en GitHub y que tienes cuenta en [Railway](https://railway.app).

### 1. Crear el proyecto y las bases de datos gestionadas

1. En Railway, **New Project → Deploy from GitHub repo** y selecciona este repositorio.
2. Dentro del proyecto, añade dos plugins gestionados: **Add → Database → PostgreSQL** y
   **Add → Database → Redis**. Railway generará automáticamente sus variables de conexión.

### 2. Crear los 4 servicios de la aplicación

Para cada uno, usa **New → Empty Service**, conecta el mismo repo de GitHub, y en
**Settings → Build** configura `Root Directory` = `.` y `Dockerfile Path` según la tabla:

| Servicio   | Dockerfile Path           | Custom Start Command (Settings → Deploy)                     |
|------------|----------------------------|----------------------------------------------------------------|
| `backend`  | `backend/Dockerfile.prod`  | (dejar el `CMD` de la imagen)                                   |
| `worker`   | `worker/Dockerfile.prod`   | (dejar el `CMD` de la imagen)                                   |
| `beat`     | `worker/Dockerfile.prod`   | `celery -A app.core.celery_app beat --loglevel=info`             |
| `frontend` | `frontend/Dockerfile.prod` | (dejar el `CMD` de la imagen)                                   |

### 3. Variables de entorno

#### `backend`, `worker`, `beat` (las tres comparten estas variables)

Railway expone Postgres/Redis con variables de referencia. **Ojo con `DATABASE_URL`**: Railway
usa el esquema `postgres://`, pero esta app necesita el dialecto `asyncpg`, así que no uses la
`DATABASE_URL` de Railway directamente — constrúyela a mano con las variables de referencia del
plugin de Postgres (verás sus nombres exactos en la pestaña **Variables** del plugin, típicamente
`PGUSER`, `PGPASSWORD`, `PGHOST`, `PGPORT`, `PGDATABASE`):

```
DATABASE_URL=postgresql+asyncpg://${{Postgres.PGUSER}}:${{Postgres.PGPASSWORD}}@${{Postgres.PGHOST}}:${{Postgres.PGPORT}}/${{Postgres.PGDATABASE}}
REDIS_URL=${{Redis.REDIS_URL}}
DEFAULT_USER_ID=00000000-0000-0000-0000-000000000001
SCRAPE_INTERVAL_MINUTES=45
SMTP_HOST=...
SMTP_PORT=587
SMTP_USER=...
SMTP_PASSWORD=...
SMTP_FROM=...
TELEGRAM_BOT_TOKEN=...
FRONTEND_ORIGIN=   # se rellena en el paso 5, después de desplegar el frontend
```

#### `frontend`

`NEXT_PUBLIC_API_URL` se necesita como **build-time variable** (Settings → Variables, marcada
para build), no solo runtime, porque Next.js incrusta `NEXT_PUBLIC_*` al compilar:

```
NEXT_PUBLIC_API_URL=   # se rellena en el paso 4, con el dominio público del backend
```

### 4. Dominios públicos y healthcheck

1. En el servicio `backend`: **Settings → Networking → Generate Domain**, y en
   **Settings → Healthcheck Path** pon `/health`.
2. Copia ese dominio y ponlo como `NEXT_PUBLIC_API_URL` en el servicio `frontend`, luego haz
   **redeploy** del frontend (las variables `NEXT_PUBLIC_*` requieren rebuild).
3. En el servicio `frontend`: **Settings → Networking → Generate Domain**.
4. Copia el dominio del frontend y ponlo como `FRONTEND_ORIGIN` en el servicio `backend`
   (necesario para que CORS permita las peticiones del dashboard), luego redeploy del backend.

### 5. Primer despliegue: orden recomendado

1. Despliega `backend` primero (las migraciones se aplican solas al arrancar, vía
   `backend/entrypoint.sh`) y genera su dominio.
2. Configura `NEXT_PUBLIC_API_URL` en `frontend` con ese dominio y despliega `frontend`.
3. Genera el dominio del `frontend`, ponlo como `FRONTEND_ORIGIN` en `backend` y redeploy.
4. Despliega `worker` y `beat` (no necesitan dominio público).

### 6. Verificación

- `https://<dominio-backend>/health` debe responder `200`.
- El dashboard en `https://<dominio-frontend>` debe cargar sin errores de CORS en consola.
- Revisa los logs del servicio `beat` para confirmar que está programando el scraping periódico
  (`SCRAPE_INTERVAL_MINUTES`), y los del `worker` para confirmar que procesa las tareas.

---

## Opción B: Oracle Cloud Free Tier (gratis para siempre)

Aquí no hay servicios separados por proveedor — se levanta el `docker-compose.prod.yml` del repo
(las mismas imágenes de producción, pero como un solo stack, igual que en local) dentro de una
única VM que Oracle da gratis de forma permanente.

### 1. Crear la cuenta y la VM

1. Crea una cuenta en [Oracle Cloud Free Tier](https://www.oracle.com/cloud/free/) (pide tarjeta
   solo para verificar identidad; los recursos "Always Free" no generan cargos mientras no
   cambies a recursos de pago).
2. **Compute → Instances → Create Instance**.
3. En **Image and shape**, elige shape **Always Free**: `VM.Standard.A1.Flex` (ARM Ampere, hasta
   4 OCPU / 24 GB gratis — recomendado, va sobrado para Playwright) o `VM.Standard.E2.1.Micro`
   (AMD, 1 GB, más justo). Imagen: **Ubuntu 22.04** o **24.04**.
4. En **Add SSH keys**, sube tu clave pública (o genera un par nuevo y guarda la privada) — es
   cómo te conectarás, no hay contraseña.
5. Crea la instancia y anota su **IP pública**.

### 2. Abrir los puertos necesarios

Oracle bloquea todo el tráfico entrante salvo SSH (22) por defecto, en **dos capas**:

1. **Security List de la VCN** (en la consola web): tu VM → pestaña **Subnet** → **Security
   Lists** → añade *Ingress Rules* para los puertos `3000` (frontend) y `8000` (backend), origen
   `0.0.0.0/0`.
2. **Firewall del propio Ubuntu** (por SSH, una vez conectado):
   ```bash
   sudo iptables -I INPUT -p tcp --dport 3000 -j ACCEPT
   sudo iptables -I INPUT -p tcp --dport 8000 -j ACCEPT
   sudo netfilter-persistent save   # si no existe, instálalo: sudo apt install -y iptables-persistent
   ```

### 3. Instalar Docker en la VM

Conéctate por SSH (`ssh ubuntu@<IP-pública>`) y ejecuta:

```bash
sudo apt update && sudo apt install -y ca-certificates curl gnupg git
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update && sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo usermod -aG docker $USER && newgrp docker
```

### 4. Clonar el repo y configurar `.env`

```bash
git clone https://github.com/Dev-eLiiAs/Price-Oracle.git
cd Price-Oracle
cp .env.example .env
nano .env   # o vim/vi
```

En el `.env` de la VM, ajusta estas variables con la **IP pública de la VM** (o un dominio si le
apuntas uno):

```
FRONTEND_ORIGIN=http://<IP-pública>:3000
NEXT_PUBLIC_API_URL=http://<IP-pública>:8000
```

Y rellena el resto igual que en tu `.env` local (`TELEGRAM_BOT_TOKEN`, `SMTP_*`, etc. — cópialos
desde tu máquina, nunca se suben al repo).

### 5. Levantar el stack

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

Esto construye las 4 imágenes de producción y arranca Postgres, Redis, backend, worker, beat y
frontend — las migraciones se aplican solas al arrancar el backend (`backend/entrypoint.sh`).
`restart: unless-stopped` hace que todo vuelva a arrancar solo si la VM se reinicia.

### 6. Verificación

```bash
curl http://localhost:8000/health   # desde la propia VM
```

Desde tu ordenador: `http://<IP-pública>:8000/health` debe responder `200`, y
`http://<IP-pública>:3000` debe cargar el dashboard. Revisa logs con
`docker compose -f docker-compose.prod.yml logs -f beat` (o `worker`, `backend`) si algo falla.

### Nota sobre HTTPS

Esta guía deja la app en HTTP plano sobre la IP pública, suficiente para uso personal. Si más
adelante quieres HTTPS con un dominio propio, la forma más simple es añadir
[Caddy](https://caddyserver.com/) como proxy inverso delante de `backend`/`frontend` — no está
incluido aquí porque requiere que primero tengas un dominio apuntando a la IP de la VM.
