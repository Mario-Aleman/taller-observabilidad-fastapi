import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture()
def cliente(tmp_path, monkeypatch):
    """Cliente de pruebas con una BD temporal limpia (no toca academico.db)."""
    from fastapi.testclient import TestClient
    from repositories import estudiante_repository as repo
    monkeypatch.setattr(repo, "DB", str(tmp_path / "test.db"))
    repo.inicializar()
    from main import app
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture()
def api_externa_ok(monkeypatch):
    """Simula una respuesta correcta de la API externa."""
    from unittest.mock import MagicMock
    from services import estudiante_service as svc
    falsa = MagicMock()
    falsa.json.return_value = [{"id": 1, "name": "Usuario de prueba"}]
    falsa.raise_for_status.return_value = None
    monkeypatch.setattr(svc.requests, "get", lambda *a, **k: falsa)


VALIDO = {"nombre": "Ana", "programa": "Ingeniería de Sistemas",
          "semestre": 5, "promedio": 4.2}
