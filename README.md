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

El dataset sintetico vive en `data/synthetic_forest.json` y contiene escenarios Verde, Amarillo y Rojo.
