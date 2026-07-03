"""
AstroDev Agent - API Astrológica Profesional
Esqueleto inicial: imports, app, esquemas y constantes.
Sin endpoints ni lógica de cálculo (paso siguiente).
"""

from datetime import datetime
from typing import List
from zoneinfo import ZoneInfo

from fastapi import FastAPI
from pydantic import BaseModel, Field
from timezonefinder import TimezoneFinder
import swisseph as swe

# ---------------------------------------------------------------------------
# Inicialización de la aplicación
# ---------------------------------------------------------------------------

app = FastAPI(
    title="API Astrológica Profesional",
    description=(
        "Cálculos astronómicos de alta precisión para aplicaciones "
        "astrológicas occidentales, basados en Swiss Ephemeris."
    ),
    version="0.1.0",
)

# ---------------------------------------------------------------------------
# Esquemas de validación de salida (Pydantic)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Constantes: Signos zodiacales
# ---------------------------------------------------------------------------

SIGNOS = [
    "Aries",
    "Tauro",
    "Géminis",
    "Cáncer",
    "Leo",
    "Virgo",
    "Libra",
    "Escorpio",
    "Sagitario",
    "Capricornio",
    "Acuario",
    "Piscis",
]

# ---------------------------------------------------------------------------
# Constantes: Cuerpos celestes soportados (Swiss Ephemeris)
# ---------------------------------------------------------------------------

PLANETAS = {
    "Sol": swe.SUN,
    "Luna": swe.MOON,
    "Mercurio": swe.MERCURY,
    "Venus": swe.VENUS,
    "Marte": swe.MARS,
    "Júpiter": swe.JUPITER,
    "Saturno": swe.SATURN,
    "Urano": swe.URANUS,
    "Neptuno": swe.NEPTUNE,
    "Plutón": swe.PLUTO,
}

# ---------------------------------------------------------------------------
# Geolocalización temporal y cálculo de tiempo (Paso 2)
# ---------------------------------------------------------------------------

tf = TimezoneFinder()


def calcular_tiempo_utc_y_juliano(
    fecha: str, hora_local: str, latitud: float, longitud: float
) -> dict:
    """
    Detecta la zona horaria histórica según coordenadas, convierte la hora
    local a UTC y calcula el Día Juliano decimal para Swiss Ephemeris.
    """
    zona_horaria = tf.timezone_at(lat=latitud, lng=longitud)
    if zona_horaria is None:
        raise ValueError("No se pudo determinar la zona horaria para estas coordenadas.")

    dt_naive = datetime.strptime(f"{fecha} {hora_local}", "%Y-%m-%d %H:%M")
    dt_local = dt_naive.replace(tzinfo=ZoneInfo(zona_horaria))
    dt_utc = dt_local.astimezone(ZoneInfo("UTC"))

    hora_utc_str = dt_utc.strftime("%Y-%m-%d %H:%M UTC")

    hora_decimal = dt_utc.hour + dt_utc.minute / 60 + dt_utc.second / 3600
    jd_utc = swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, hora_decimal)

    return {
        "zona_horaria_detectada": zona_horaria,
        "hora_utc_calculada": hora_utc_str,
        "jd_utc": jd_utc,
    }