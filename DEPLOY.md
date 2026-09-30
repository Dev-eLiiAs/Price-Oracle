# Despliegue en Railway

Esta guía asume que el repositorio ya está en GitHub y que tienes una cuenta en
[Railway](https://railway.app). El repo incluye imágenes de producción listas para usar:

- `backend/Dockerfile.prod`
- `worker/Dockerfile.prod` (se reutiliza tanto para el worker de Celery como para Celery Beat)
- `frontend/Dockerfile.prod`

## 1. Crear el proyecto y las bases de datos gestionadas

1. En Railway, **New Project → Deploy from GitHub repo** y selecciona este repositorio.
2. Dentro del proyecto, añade dos plugins gestionados: **Add → Database → PostgreSQL** y
   **Add → Database → Redis**. Railway generará automáticamente sus variables de conexión.

## 2. Crear los 4 servicios de la aplicación

Para cada uno, usa **New → Empty Service**, conecta el mismo repo de GitHub, y en
**Settings → Build** configura `Root Directory` = `.` y `Dockerfile Path` según la tabla:

| Servicio   | Dockerfile Path           | Custom Start Command (Settings → Deploy)                     |
|------------|----------------------------|----------------------------------------------------------------|
| `backend`  | `backend/Dockerfile.prod`  | (dejar el `CMD` de la imagen)                                   |
| `worker`   | `worker/Dockerfile.prod`   | (dejar el `CMD` de la imagen)                                   |
| `beat`     | `worker/Dockerfile.prod`   | `celery -A app.core.celery_app beat --loglevel=info`             |
| `frontend` | `frontend/Dockerfile.prod` | (dejar el `CMD` de la imagen)                                   |

## 3. Variables de entorno

### `backend`, `worker`, `beat` (las tres comparten estas variables)

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

### `frontend`

`NEXT_PUBLIC_API_URL` se necesita como **build-time variable** (Settings → Variables, marcada
para build), no solo runtime, porque Next.js incrusta `NEXT_PUBLIC_*` al compilar:

```
NEXT_PUBLIC_API_URL=   # se rellena en el paso 4, con el dominio público del backend
```

## 4. Dominios públicos y healthcheck

1. En el servicio `backend`: **Settings → Networking → Generate Domain**, y en
   **Settings → Healthcheck Path** pon `/health`.
2. Copia ese dominio y ponlo como `NEXT_PUBLIC_API_URL` en el servicio `frontend`, luego haz
   **redeploy** del frontend (las variables `NEXT_PUBLIC_*` requieren rebuild).
3. En el servicio `frontend`: **Settings → Networking → Generate Domain**.
4. Copia el dominio del frontend y ponlo como `FRONTEND_ORIGIN` en el servicio `backend`
   (necesario para que CORS permita las peticiones del dashboard), luego redeploy del backend.

## 5. Primer despliegue: orden recomendado

1. Despliega `backend` primero (las migraciones se aplican solas al arrancar, vía
   `backend/entrypoint.sh`) y genera su dominio.
2. Configura `NEXT_PUBLIC_API_URL` en `frontend` con ese dominio y despliega `frontend`.
3. Genera el dominio del `frontend`, ponlo como `FRONTEND_ORIGIN` en `backend` y redeploy.
4. Despliega `worker` y `beat` (no necesitan dominio público).

## 6. Verificación

- `https://<dominio-backend>/health` debe responder `200`.
- El dashboard en `https://<dominio-frontend>` debe cargar sin errores de CORS en consola.
- Revisa los logs del servicio `beat` para confirmar que está programando el scraping periódico
  (`SCRAPE_INTERVAL_MINUTES`), y los del `worker` para confirmar que procesa las tareas.
