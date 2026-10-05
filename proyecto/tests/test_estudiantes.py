import logging

import pytest
import requests

from conftest import VALIDO


# ---------- Operaciones exitosas ----------
def test_listar_vacio(cliente):
    r = cliente.get("/estudiantes/")
    assert r.status_code == 200 and r.json() == []


def test_crear_estudiante(cliente, api_externa_ok):
    r = cliente.post("/estudiantes/", json=VALIDO)
    assert r.status_code == 201
    assert r.json()["id"] == 1
    assert r.json()["estado_servicio_externo"] == "ok"
    assert "X-Request-ID" in r.headers and "X-Process-Time" in r.headers


def test_consultar_existente(cliente, api_externa_ok):
    cliente.post("/estudiantes/", json=VALIDO)
    r = cliente.get("/estudiantes/1")
    assert r.status_code == 200 and r.json()["nombre"] == "Ana"


# ---------- Validación ----------
@pytest.mark.parametrize("campo,valor", [
    ("semestre", -5), ("semestre", 0), ("semestre", 99),
    ("promedio", 99), ("promedio", -1), ("nombre", ""), ("programa", ""),
])
def test_datos_fuera_de_rango_rechazados(cliente, api_externa_ok, campo, valor):
    r = cliente.post("/estudiantes/", json={**VALIDO, campo: valor})
    assert r.status_code == 422


def test_campo_faltante(cliente):
    assert cliente.post("/estudiantes/", json={"nombre": "X"}).status_code == 422


def test_tipo_incorrecto(cliente):
    r = cliente.post("/estudiantes/", json={**VALIDO, "semestre": "abc"})
    assert r.status_code == 422


def test_promedio_nan_rechazado(cliente):
    cuerpo = ('{"nombre":"Ana","programa":"Sistemas",'
              '"semestre":3,"promedio":NaN}')
    r = cliente.post("/estudiantes/", content=cuerpo,
                     headers={"content-type": "application/json"})
    assert r.status_code == 422


def test_validacion_no_guarda_en_bd(cliente):
    cliente.post("/estudiantes/", json={**VALIDO, "semestre": -5})
    assert cliente.get("/estudiantes/").json() == []


# ---------- Recursos inexistentes ----------
def test_estudiante_inexistente(cliente):
    assert cliente.get("/estudiantes/99999").status_code == 404


def test_id_no_numerico(cliente):
    assert cliente.get("/estudiantes/abc").status_code == 422


# ---------- API externa ----------
@pytest.mark.parametrize("error", [
    requests.exceptions.Timeout("lento"),
    requests.exceptions.ConnectionError("caída"),
    requests.exceptions.HTTPError("500"),
    ValueError("JSON inválido"),
])
def test_api_externa_falla_no_rompe_el_registro(cliente, monkeypatch, error):
    from services import estudiante_service as svc

    def falla(*a, **k):
        raise error
    monkeypatch.setattr(svc.requests, "get", falla)
    r = cliente.post("/estudiantes/", json=VALIDO)
    assert r.status_code == 201
    assert r.json()["informacion_externa"] is None
    assert r.json()["estado_servicio_externo"] != "ok"
    # el estudiante sí quedó persistido
    assert len(cliente.get("/estudiantes/").json()) == 1


def test_api_externa_usa_timeout(cliente, monkeypatch):
    from services import estudiante_service as svc
    capturado = {}

    def espia(*a, **k):
        capturado.update(k)
        raise requests.exceptions.Timeout()
    monkeypatch.setattr(svc.requests, "get", espia)
    cliente.post("/estudiantes/", json=VALIDO)
    assert capturado.get("timeout") is not None


# ---------- Base de datos ----------
def test_error_de_bd_devuelve_503(cliente, monkeypatch):
    from repositories import estudiante_repository as repo
    monkeypatch.setattr(repo, "DB", "/ruta/inexistente/no.db")
    r = cliente.get("/estudiantes/")
    assert r.status_code == 503
    assert "sqlite" not in r.text.lower()  # no se filtran detalles internos


# ---------- Excepciones inesperadas ----------
def test_excepcion_inesperada_devuelve_500_generico(cliente, monkeypatch):
    from routes import estudiantes as rutas

    def explota():
        raise RuntimeError("secreto interno")
    monkeypatch.setattr(rutas, "obtener_estudiantes", explota)
    r = cliente.get("/estudiantes/")
    assert r.status_code == 500
    assert "secreto interno" not in r.text
    assert "id_solicitud" in r.json()


# ---------- Observabilidad (logs) ----------
def test_log_contiene_metodo_ruta_codigo_y_tiempo(cliente, caplog):
    logging.getLogger("academico").propagate = True
    with caplog.at_level(logging.INFO, logger="academico"):
        cliente.get("/estudiantes/99999")
    texto = caplog.text
    assert "GET /estudiantes/99999 404" in texto
    assert "Tiempo:" in texto and "Error del cliente" in texto
