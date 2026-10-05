from fastapi import FastAPI

from core_logging import configurar_logging
from middleware_observabilidad import registrar_middleware
from repositories.estudiante_repository import inicializar
from routes.estudiantes import router

configurar_logging()
inicializar()  # crea la tabla si no existe (en la versión original no se llamaba)

app = FastAPI(title="Sistema Académico - Taller de Observabilidad")
registrar_middleware(app)
app.include_router(router)


@app.get("/")
def inicio():
    return {"mensaje": "Sistema académico activo"}
