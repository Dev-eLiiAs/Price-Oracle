# Price Oracle

Tracker inteligente de precios y asesor de compras. Extrae metadatos de productos desde una URL, trackea su precio en background y recomienda cuándo comprar.

## Arquitectura

- `backend/` — API REST en FastAPI.
- `worker/` — tareas Celery (scraping con Playwright, notificaciones) y Celery Beat.
- `frontend/` — dashboard en Next.js.
- PostgreSQL como base de datos, Redis como broker/result backend de Celery.

## Desarrollo local

```bash
cp .env.example .env
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000 (health check en `/health`)
- Adminer (inspección de BD): http://localhost:8080
