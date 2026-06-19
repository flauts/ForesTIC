# ForesTIC

Prototipo del **Pasaporte Digital de Madera Legal OSINFOR** descrito en `SPEC.md`.

## 🌐 Demo en línea

La aplicación se encuentra desplegada y puede probarse desde el siguiente enlace:

**👉 https://forestic.vercel.app/**

El entorno web permite explorar el flujo principal del prototipo, incluyendo la consulta y verificación de pasaportes digitales de madera.

---

## Backend local

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Endpoints principales

* `GET /v1/passports`
* `GET /verify/{qr_token}`
* `POST /v1/passports/issue`
* `POST /v1/passports/{passport_id}/revoke`
* `POST /v1/consistency/evaluate`
* `GET /docs`

El backend utiliza `data/real_forest.json` cuando está disponible. Este archivo se genera a partir de los archivos reales incluidos en `data/`:

```powershell
python scripts/import_real_files.py
```

El dataset sintético (`data/synthetic_forest.json`) se mantiene como mecanismo de respaldo y como conjunto de pruebas controladas con escenarios Verde, Amarillo y Rojo.

---

## Frontend local

```powershell
cd frontend
npm install
npm run dev
```

Por defecto, el frontend consume la API en `http://localhost:8000`. Esta dirección puede modificarse mediante la variable de entorno `VITE_API_URL`.

---

## Docker Compose

```powershell
docker compose up --build
```

Servicios disponibles:

* **API:** http://localhost:8000
* **Frontend:** http://localhost:5173

Para más información sobre el despliegue y la configuración del proyecto, consulta `docs/DEPLOYMENT.md`.
