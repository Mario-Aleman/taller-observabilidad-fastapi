"""Configuración central de logging (observabilidad)."""
import logging
import os
from logging.handlers import RotatingFileHandler

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
FORMATO = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"


def configurar_logging():
    os.makedirs(LOG_DIR, exist_ok=True)
    raiz = logging.getLogger("academico")
    if raiz.handlers:  # evita duplicar handlers con --reload
        return raiz
    raiz.setLevel(logging.INFO)
    formato = logging.Formatter(FORMATO, "%Y-%m-%d %H:%M:%S")
    archivo = RotatingFileHandler(
        os.path.join(LOG_DIR, "app.log"), maxBytes=1_000_000,
        backupCount=3, encoding="utf-8")
    archivo.setFormatter(formato)
    consola = logging.StreamHandler()
    consola.setFormatter(formato)
    raiz.addHandler(archivo)
    raiz.addHandler(consola)
    return raiz
