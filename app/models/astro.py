"""Esquemas Pydantic de entrada/salida."""

from typing import List
from pydantic import BaseModel, Field


class PosicionPlaneta(BaseModel):
    planeta: str
    longitud_total: float = Field(..., ge=0.0, lt=360.0)
    signo: str
    grados_signo: float = Field(..., ge=0.0, lt=30.0)
    retrogrado: bool


class PosicionCasa(BaseModel):
    casa: str
    longitud_total: float = Field(..., ge=0.0, lt=360.0)
    signo: str
    grados_signo: float = Field(..., ge=0.0, lt=30.0)


class AspectoAstrologico(BaseModel):
    planeta1: str
    planeta2: str
    tipo: str
    angulo_exacto: float
    distancia: float = Field(..., ge=0.0, le=180.0)


class RespuestaAstrologica(BaseModel):
    zona_horaria_detectada: str
    hora_utc_calculada: str
    planetas: List[PosicionPlaneta]
    casas: List[PosicionCasa]
    aspectos: List[AspectoAstrologico]