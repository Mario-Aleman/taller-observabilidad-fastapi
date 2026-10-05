"""Ejecuta los mismos escenarios sobre la versión MEJORADA y genera logs/app.log
    python evidencias/escenarios_mejorada.py
"""
import os
import sys
from unittest.mock import MagicMock, patch

import requests
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import main  # noqa: E402
from repositories import estudiante_repository as repo  # noqa: E402

c = TestClient(main.app, raise_server_exceptions=False)
OK = {"nombre": "Ana", "programa": "Sistemas", "semestre": 5, "promedio": 4.2}


def mostrar(prueba, r):
    print(f"{prueba:44s} -> HTTP {r.status_code} | {r.text[:90]}")


falsa = MagicMock()
falsa.json.return_value = [{"id": 1}]
with patch("services.estudiante_service.requests.get", return_value=falsa):
    mostrar("POST válido", c.post("/estudiantes/", json=OK))
    mostrar("POST semestre=-5", c.post("/estudiantes/", json={**OK, "semestre": -5}))
    mostrar("POST promedio=99", c.post("/estudiantes/", json={**OK, "promedio": 99}))
    mostrar("POST nombre vacío", c.post("/estudiantes/", json={**OK, "nombre": ""}))
    mostrar("POST promedio=NaN", c.post(
        "/estudiantes/", headers={"content-type": "application/json"},
        content='{"nombre":"X","programa":"S","semestre":3,"promedio":NaN}'))
    mostrar("GET existente", c.get("/estudiantes/1"))
mostrar("GET inexistente", c.get("/estudiantes/99999"))
with patch("services.estudiante_service.requests.get",
           side_effect=requests.exceptions.ConnectionError("simulado")):
    mostrar("POST con API externa caída", c.post("/estudiantes/", json=OK))
with patch("services.estudiante_service.requests.get",
           side_effect=requests.exceptions.Timeout("simulado")):
    mostrar("POST con API externa lenta (timeout)", c.post("/estudiantes/", json=OK))
bd = repo.DB
repo.DB = "/ruta/inexistente/no.db"
mostrar("GET con BD inaccesible", c.get("/estudiantes/"))
repo.DB = bd
with patch("routes.estudiantes.obtener_estudiantes", side_effect=RuntimeError("x")):
    mostrar("GET con excepción inesperada", c.get("/estudiantes/"))
