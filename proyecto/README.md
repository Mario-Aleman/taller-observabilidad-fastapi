# Taller de Observabilidad – Sistema Académico (FastAPI)

Aplicación FastAPI de gestión académica analizada y mejorada en la
Actividad Evaluativa 3 (Observabilidad e identificación de puntos débiles).

## Ejecución

```bash
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload
```

Swagger: http://127.0.0.1:8000/docs

## Endpoints

| Método | Ruta | Descripción | Códigos |
|--------|------|-------------|---------|
| GET | `/` | Estado de la aplicación | 200 |
| GET | `/estudiantes/` | Lista estudiantes | 200, 503 |
| GET | `/estudiantes/{id}` | Consulta un estudiante | 200, 404, 422, 503 |
| POST | `/estudiantes/` | Registra un estudiante | 201, 422, 503 |

## Estructura

```
main.py                        # arranque, logging, middleware, init de BD
core_logging.py                # configuración de logs (consola + logs/app.log)
middleware_observabilidad.py   # log por solicitud + manejadores globales de error
routes/        models/        services/        repositories/
tests/                         # pruebas automáticas (pytest)
evidencias/                    # scripts que reproducen hallazgos y miden rendimiento
logs/                          # app.log (no se versiona)
```

## Observabilidad implementada

Cada solicitud genera una línea en `logs/app.log`:

```
2026-10-05 01:51:14 | WARNING  | academico.http | [a92dd96d] GET /estudiantes/99999 404 Tiempo: 0.001 s Error del cliente
```

Incluye fecha/hora, ID de solicitud (también en el encabezado `X-Request-ID`),
método, endpoint, código HTTP, tiempo de respuesta y resultado. Los errores de
validación, recursos inexistentes, base de datos, API externa y excepciones
inesperadas se registran con su nivel (WARNING/ERROR) y traza cuando aplica.

## Pruebas y mediciones

```bash
python -m pytest -q                                   # pruebas automáticas
python evidencias/escenarios_mejorada.py              # escenarios + logs
python evidencias/medir_rendimiento.py . mejorada     # rendimiento (servidor local)
```

La URL de la API externa puede cambiarse con la variable de entorno
`API_EXTERNA_URL`. No se incluyen credenciales, tokens ni claves.
