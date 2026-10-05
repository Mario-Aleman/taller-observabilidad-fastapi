from pydantic import BaseModel, Field


class Estudiante(BaseModel):
    nombre: str = Field(min_length=2, max_length=100)
    programa: str = Field(min_length=2, max_length=100)
    semestre: int = Field(ge=1, le=12)
    # allow_inf_nan=False rechaza NaN/Infinity (en la versión original rompían la respuesta)
    promedio: float = Field(ge=0.0, le=5.0, allow_inf_nan=False)
