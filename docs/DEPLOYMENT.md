# Guia de despliegue local

## Opcion rapida con Docker Compose

```powershell
docker compose up --build
```

Servicios:

- API FastAPI: http://localhost:8000
- OpenAPI: http://localhost:8000/docs
- Frontend: http://localhost:5173

## Opcion desarrollo

Backend:

```powershell
cd backend
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Frontend:

```powershell
cd frontend
npm install
npm run dev
```

## Escenarios de demo

- Verde: `GTF-2026-001`
- Amarillo: `GTF-2026-002`
- Rojo: `GTF-2026-003`

El archivo `data/pasaporte_datos_sinteticos.xlsx` contiene las hojas simuladas descritas en el SPEC. La API usa `data/synthetic_forest.json` como fuente cargable para mantener el prototipo ligero y reproducible.

## Seguridad del prototipo

- Los QR se firman con HMAC-SHA-256.
- La vista publica no expone el token QR ni payloads internos.
- La auditoria es append-only en memoria y encadena hashes.
- Los datos son sinteticos; no se deben cargar datos personales reales en este repositorio.
