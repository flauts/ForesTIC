from fastapi.testclient import TestClient

from app.main import app, passports


client = TestClient(app)


def test_demo_passports_cover_traffic_lights():
    response = client.get("/v1/passports")
    assert response.status_code == 200
    semaforos = {passport["gtf_id"]: passport["semaforo"] for passport in response.json()}
    assert semaforos["GTF-2026-001"] == "Verde"
    assert semaforos["GTF-2026-002"] == "Amarillo"
    assert semaforos["GTF-2026-003"] == "Rojo"


def test_public_verify_rejects_tampered_qr():
    response = client.get("/verify/token-manipulado")
    assert response.status_code == 400


def test_public_verify_returns_minimized_payload():
    passport = passports.passports["PASS-GTF-2026-001"]
    response = client.get(f"/verify/{passport.qr_token}")
    assert response.status_code == 200
    payload = response.json()
    assert payload["semaforo"] == "Verde"
    assert "qr_token" not in payload
    assert "usuario_origen_anonimizado" not in payload


def test_revoke_invalidates_passport_status():
    passport = client.post("/v1/passports/issue", json={"gtf_id": "GTF-2026-002"}).json()
    response = client.post(
        f"/v1/passports/{passport['passport_id']}/revoke",
        json={"reason": "Nueva evidencia sintetica de control", "user": "admin-osinfor"},
    )
    assert response.status_code == 200
    assert response.json()["estado_pasaporte"] == "revocado"
