"""Reproduce los hallazgos sobre la versión ORIGINAL (ejecutar desde su carpeta):
    cd taller_original && python ../proyecto/evidencias/hallazgos_original.py
"""
import os
import sys
from unittest.mock import MagicMock, patch

import requests
from fastapi.testclient import TestClient

sys.path.insert(0, os.getcwd())
import main  # noqa: E402
from repositories.estudiante_repository import inicializar  # noqa: E402

c = TestClient(main.app, raise_server_exceptions=False)
OK = {"nombre": "Ana", "programa": "Sistemas", "semestre": 5, "promedio": 4.2}


def mostrar(prueba, r):
    print(f"{prueba:44s} -> HTTP {r.status_code} | {r.text[:90]}")


print("--- H5: BD sin inicializar (app recién arrancada) ---")
if os.path.exists("academico.db"):
    os.remove("academico.db")
mostrar("GET /estudiantes/ sin tabla", c.get("/estudiantes/"))
inicializar()

falsa = MagicMock()
falsa.json.return_value = [{"id": 1}]
print("\n--- Validación (API externa simulada OK) ---")
with patch("services.estudiante_service.requests.get", return_value=falsa):
    mostrar("POST semestre=-5", c.post("/estudiantes/", json={**OK, "semestre": -5}))
    mostrar("POST promedio=99", c.post("/estudiantes/", json={**OK, "promedio": 99}))
    mostrar("POST nombre vacío", c.post("/estudiantes/", json={**OK, "nombre": ""}))
    mostrar("POST promedio=NaN", c.post(
        "/estudiantes/", headers={"content-type": "application/json"},
        content='{"nombre":"X","programa":"S","semestre":3,"promedio":NaN}'))
    mostrar("POST campo faltante", c.post("/estudiantes/", json={"nombre": "X"}))
    mostrar("POST válido (código de creación)", c.post("/estudiantes/", json=OK))
    mostrar("POST duplicado exacto", c.post("/estudiantes/", json=OK))

print("\n--- H4: recurso inexistente ---")
mostrar("GET /estudiantes/99999", c.get("/estudiantes/99999"))

print("\n--- H2: API externa caída / respuesta inválida ---")
antes = len(c.get("/estudiantes/").json())
with patch("services.estudiante_service.requests.get",
           side_effect=requests.exceptions.ConnectionError("simulado")):
    mostrar("POST con API externa caída", c.post("/estudiantes/", json=OK))
despues = len(c.get("/estudiantes/").json())
print(f"Registros en BD antes={antes} después={despues} -> "
      f"{'se guardó aunque el cliente recibió error' if despues > antes else 'sin cambios'}")

print("\n--- H6: formato de la lista (GET /estudiantes/) ---")
print(c.get("/estudiantes/").text[:100])
