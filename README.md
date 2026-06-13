# ForesTIC

Prototipo del **Pasaporte Digital de Madera Legal OSINFOR** descrito en `SPEC.md`.

## Backend local

```powershell
cd backend
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Endpoints principales:

- `GET /v1/passports`
- `GET /verify/{qr_token}`
- `POST /v1/passports/issue`
- `POST /v1/passports/{passport_id}/revoke`
- `POST /v1/consistency/evaluate`
- `GET /docs`

El backend usa `data/real_forest.json` cuando existe. Ese archivo se genera desde los archivos reales entregados en `data/`:

```powershell
python scripts/import_real_files.py
```

El dataset sintético (`data/synthetic_forest.json`) queda como fallback y como fixture de pruebas controladas con escenarios Verde, Amarillo y Rojo.

## Frontend local

```powershell
cd frontend
npm install
npm run dev
```

Por defecto consume `http://localhost:8000`. Puedes cambiarlo con `VITE_API_URL`.

## Docker Compose

```powershell
docker compose up --build
```

- API: http://localhost:8000
- Frontend: http://localhost:5173

Mas detalle en `docs/DEPLOYMENT.md`.
