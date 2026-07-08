from typing import List, Optional, Union
from pydantic import BaseModel, Field

class PosicionPlaneta(BaseModel):
    planeta: str
    longitud_total: float
    signo: str
    grados_signo: float
    retrogrado: bool

class PosicionCasa(BaseModel):
    casa: str
    longitud_total: float
    signo: str
    grados_signo: float

class AspectoAstrologico(BaseModel):
    planeta1: str
    planeta2: str
    tipo: str
    angulo_exacto: float
    distancia: float

# NUEVO: Sub-esquemas para validar la estructura modular de la IA
class CapituloIdentidad(BaseModel):
    titulo: str
    sol: str
    luna: str
    ascendente: str

class CapituloOperacion(BaseModel):
    titulo: str
    mercurio: str
    venus: str
    marte: str

class CapituloApalancamiento(BaseModel):
    titulo: str
    analisis_aspectos: str

class InterpretacionPremiumSchema(BaseModel):
    introduccion_sintesis: str
    capitulo_1_identidad: CapituloIdentidad
    capitulo_2_operacion: CapituloOperacion
    capitulo_3_apalancamiento: CapituloApalancamiento
    cita_cierre: str

# El esquema principal ahora incluye la lectura opcional de la IA
class RespuestaAstrologica(BaseModel):
    zona_horaria_detectada: str
    hora_utc_calculada: str
    planetas: List[PosicionPlaneta]
    casas: List[PosicionCasa]
    aspectos: List[AspectoAstrologico]
    # Ahora acepta la lectura estructural O un diccionario de contingencia/error común
    interpretacion_premium: Optional[Union[InterpretacionPremiumSchema, dict]] = None 