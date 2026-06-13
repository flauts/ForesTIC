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

## Datos reales de la competencia

Los archivos originales entregados por la competencia viven en:

- `data/Censo Forestal/BD - CENSO FORESTAL.xlsx`
- `data/Muestra Supervisada/BD - MUESTRA SUPERVISADA.xlsx`
- `data/Libro Operaciones/*.xlsx`
- `data/Balance Extracción/*.pdf`

Para regenerar el dataset canónico:

```powershell
python scripts/import_real_files.py
```

El script produce `data/real_forest.json` con:

- árboles censados normalizados por `PC-XX-CODIGO`;
- muestras supervisadas OSINFOR;
- trozas despachadas y GTF agrupadas desde LOE;
- balances extraídos de PDF;
- alertas críticas por saldos negativos.

La API prefiere `data/real_forest.json` si existe y cae a `data/synthetic_forest.json` si no está disponible.

El archivo `data/pasaporte_datos_sinteticos.xlsx` se mantiene como dataset sintético de demo y pruebas explicables.

## Seguridad del prototipo

- Los QR se firman con HMAC-SHA-256.
- La vista publica no expone el token QR ni payloads internos.
- La auditoria es append-only en memoria y encadena hashes.
- Los datos son sinteticos; no se deben cargar datos personales reales en este repositorio.
