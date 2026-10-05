from fastapi import APIRouter, HTTPException, status

from models.estudiante import Estudiante
from services.estudiante_service import (
    obtener_estudiantes, obtener_estudiante, registrar_estudiante
)

router = APIRouter(prefix="/estudiantes", tags=["Estudiantes"])


def _a_dict(fila):
    return {"id": fila[0], "nombre": fila[1], "programa": fila[2],
            "semestre": fila[3], "promedio": fila[4]}


@router.get("/")
def listar_estudiantes():
    return [_a_dict(f) for f in obtener_estudiantes()]


@router.get("/{id_estudiante}")
def consultar_estudiante(id_estudiante: int):
    fila = obtener_estudiante(id_estudiante)
    if not fila:
        raise HTTPException(status.HTTP_404_NOT_FOUND,
                            "Estudiante no encontrado")
    return _a_dict(fila)


@router.post("/", status_code=status.HTTP_201_CREATED)
def crear_estudiante(estudiante: Estudiante):
    return registrar_estudiante(estudiante)
