"""Middleware de observabilidad y manejadores globales de error."""
import logging
import time
import uuid

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from repositories.estudiante_repository import ErrorBaseDeDatos
from services.estudiante_service import ErrorServicioExterno

log = logging.getLogger("academico.http")


def _resultado(codigo):
    if codigo < 400:
        return "Operación exitosa"
    if codigo < 500:
        return "Error del cliente"
    return "Error del servidor"


def registrar_middleware(app):
    @app.middleware("http")
    async def medir_solicitud(request: Request, call_next):
        id_solicitud = uuid.uuid4().hex[:8]
        request.state.id_solicitud = id_solicitud
        inicio = time.perf_counter()
        try:
            respuesta = await call_next(request)
            codigo = respuesta.status_code
        except Exception:
            # Excepción inesperada: se registra con traza completa y se responde 500 genérico
            duracion = time.perf_counter() - inicio
            log.exception("[%s] %s %s 500 Tiempo: %.3f s Excepción inesperada",
                          id_solicitud, request.method, request.url.path, duracion)
            return JSONResponse(
                status_code=500,
                content={"detail": "Error interno del servidor",
                         "id_solicitud": id_solicitud})
        duracion = time.perf_counter() - inicio
        nivel = logging.INFO if codigo < 400 else (
            logging.WARNING if codigo < 500 else logging.ERROR)
        log.log(nivel, "[%s] %s %s %s Tiempo: %.3f s %s",
                id_solicitud, request.method, request.url.path, codigo,
                duracion, _resultado(codigo))
        respuesta.headers["X-Request-ID"] = id_solicitud
        respuesta.headers["X-Process-Time"] = f"{duracion:.4f}"
        return respuesta

    @app.exception_handler(RequestValidationError)
    async def validacion(request: Request, exc: RequestValidationError):
        campos = [".".join(str(p) for p in e["loc"]) + ": " + e["msg"]
                  for e in exc.errors()]
        log.warning("Datos inválidos en %s %s -> %s",
                    request.method, request.url.path, campos)
        return JSONResponse(status_code=422, content={
            "detail": "Datos inválidos", "errores": campos})

    @app.exception_handler(StarletteHTTPException)
    async def http_error(request: Request, exc: StarletteHTTPException):
        if exc.status_code == 404:
            log.warning("Recurso inexistente: %s %s",
                        request.method, request.url.path)
        return JSONResponse(status_code=exc.status_code,
                            content={"detail": exc.detail})

    @app.exception_handler(ErrorBaseDeDatos)
    async def error_bd(request: Request, exc: ErrorBaseDeDatos):
        log.error("Error de base de datos en %s %s: %s",
                  request.method, request.url.path, exc)
        return JSONResponse(status_code=503, content={
            "detail": "Servicio de datos no disponible"})

    @app.exception_handler(ErrorServicioExterno)
    async def error_externo(request: Request, exc: ErrorServicioExterno):
        return JSONResponse(status_code=502, content={"detail": str(exc)})
