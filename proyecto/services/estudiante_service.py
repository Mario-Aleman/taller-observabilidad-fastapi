import logging
import os

import requests

from repositories.estudiante_repository import guardar, listar, buscar

log = logging.getLogger("academico.service")

URL_API_EXTERNA = os.getenv("API_EXTERNA_URL",
                            "https://jsonplaceholder.typicode.com/users")
TIMEOUT_API_EXTERNA = (3, 5)  # (conexión, lectura) en segundos


class ErrorServicioExterno(Exception):
    """La API externa no respondió o devolvió algo inválido."""


def consultar_api_externa(programa):
    try:
        respuesta = requests.get(
            URL_API_EXTERNA, params={"company": programa},
            timeout=TIMEOUT_API_EXTERNA)
        respuesta.raise_for_status()
        return respuesta.json()
    except requests.exceptions.Timeout:
        log.error("API externa: timeout (conexión=%ss, lectura=%ss)", *TIMEOUT_API_EXTERNA)
        raise ErrorServicioExterno("La API externa no respondió a tiempo")
    except (requests.exceptions.RequestException, ValueError) as exc:
        log.error("API externa: fallo (%s)", type(exc).__name__)
        raise ErrorServicioExterno("Error al comunicarse con la API externa")


def obtener_estudiantes():
    return listar()


def obtener_estudiante(id_estudiante):
    return buscar(id_estudiante)


def registrar_estudiante(estudiante):
    nuevo_id = guardar(estudiante)
    log.info("Estudiante guardado id=%s", nuevo_id)
    # La API externa es complementaria: si falla, el registro ya persistido
    # NO se pierde y la respuesta lo indica (degradación controlada).
    try:
        informacion = consultar_api_externa(estudiante.programa)
        estado_externo = "ok"
    except ErrorServicioExterno as exc:
        informacion = None
        estado_externo = str(exc)
    return {
        "id": nuevo_id,
        "estudiante": estudiante,
        "informacion_externa": informacion,
        "estado_servicio_externo": estado_externo,
    }
