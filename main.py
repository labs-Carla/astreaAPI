"""
AstroDev Agent - API Astrológica Profesional
Esqueleto inicial: imports, app, esquemas y constantes.
Sin endpoints ni lógica de cálculo (paso siguiente).
"""

from datetime import datetime
from itertools import combinations
from typing import List
from zoneinfo import ZoneInfo

from fastapi import FastAPI, HTTPException
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

# ---------------------------------------------------------------------------
# Motor astrológico (Paso 3)
# ---------------------------------------------------------------------------

ASPECTOS_CONFIG = [
    {"nombre": "Conjunción", "angulo": 0, "orbe": 8.0},
    {"nombre": "Oposición", "angulo": 180, "orbe": 8.0},
    {"nombre": "Trígono", "angulo": 120, "orbe": 8.0},
    {"nombre": "Cuadratura", "angulo": 90, "orbe": 8.0},
    {"nombre": "Sextil", "angulo": 60, "orbe": 6.0},
]


def obtener_signo_y_grados(longitud_ecliptica: float) -> tuple[str, float]:
    """Segmenta 0°-360° en los 12 signos de 30° y retorna (signo, grados_dentro_del_signo)."""
    longitud_normalizada = longitud_ecliptica % 360.0
    indice_signo = int(longitud_normalizada // 30)
    grados_signo = longitud_normalizada % 30
    return SIGNOS[indice_signo], grados_signo


def calcular_aspectos(planetas_pos: dict) -> List[AspectoAstrologico]:
    """
    Recibe {nombre_planeta: longitud_eclíptica} y retorna los aspectos mayores
    válidos, usando la distancia angular más corta del círculo de 360°.
    """
    aspectos_encontrados: List[AspectoAstrologico] = []

    for (planeta1, lon1), (planeta2, lon2) in combinations(planetas_pos.items(), 2):
        diferencia = abs(lon1 - lon2) % 360.0
        distancia_angular = min(diferencia, 360.0 - diferencia)

        for config in ASPECTOS_CONFIG:
            orbe_actual = abs(distancia_angular - config["angulo"])
            if orbe_actual <= config["orbe"]:
                aspectos_encontrados.append(
                    AspectoAstrologico(
                        planeta1=planeta1,
                        planeta2=planeta2,
                        tipo=config["nombre"],
                        angulo_exacto=float(config["angulo"]),
                        distancia=distancia_angular,
                    )
                )
                break  # un solo aspecto por par de planetas

    return aspectos_encontrados


# ---------------------------------------------------------------------------
# Endpoint definitivo
# ---------------------------------------------------------------------------

@app.get("/carta-natal-completa", response_model=RespuestaAstrologica)
def carta_natal_completa(
    fecha: str,
    hora_local: str,
    latitud: float,
    longitud: float,
    sistema_casas: str = "P",
):
    # BLINDAJE DE VALIDACIÓN DE FORMATOS DE TIEMPO
    try:
        tiempo = calcular_tiempo_utc_y_juliano(fecha, hora_local, latitud, longitud)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Datos de entrada inválidos. Verifique el formato de fecha (YYYY-MM-DD), hora (HH:MM) o coordenadas reales. Detalle: {e}"
        )
        
    jd_utc = tiempo["jd_utc"]
    # --- Cúspides de casas y ángulos (Asc/MC) ---
    try:
        cusps, ascmc = swe.houses_ex(
            jd_utc, latitud, longitud, sistema_casas.encode("ascii")
        )
    except swe.Error as e:
        raise HTTPException(
            status_code=400,
            detail=(
                "No se pudo calcular el sistema de casas solicitado "
                f"('{sistema_casas}') para estas coordenadas. Esto es común en "
                "latitudes polares (>66°) con sistemas como Placidus, donde "
                "algunas cúspides no convergen matemáticamente. "
                "Prueba con el sistema 'W' (Whole Signs). "
                f"Detalle técnico: {e}"
            ),
        )

    # --- Construir la lista de objetos PosicionCasa ---
    casas_resultado: List[PosicionCasa] = []

    signo_asc, grados_asc = obtener_signo_y_grados(ascmc[0])
    casas_resultado.append(
        PosicionCasa(casa="Ascendente", longitud_total=ascmc[0] % 360.0, signo=signo_asc, grados_signo=grados_asc)
    )

    signo_mc, grados_mc = obtener_signo_y_grados(ascmc[1])
    casas_resultado.append(
        PosicionCasa(casa="Medio Cielo", longitud_total=ascmc[1] % 360.0, signo=signo_mc, grados_signo=grados_mc)
    )

    for i, longitud_cuspide in enumerate(cusps):
        signo_c, grados_c = obtener_signo_y_grados(longitud_cuspide)
        casas_resultado.append(
            PosicionCasa(casa=f"Casa {i + 1}", longitud_total=longitud_cuspide % 360.0, signo=signo_c, grados_signo=grados_c)
        )
    # --- Posiciones planetarias ---
    planetas_pos: dict = {}
    planetas_resultado: List[PosicionPlaneta] = []
    for nombre, codigo_swe in PLANETAS.items():
        xx, _ = swe.calc_ut(jd_utc, codigo_swe)
        longitud_total = xx[0]
        velocidad_longitud = xx[3]

        signo, grados = obtener_signo_y_grados(longitud_total)
        planetas_pos[nombre] = longitud_total

        planetas_resultado.append(
            PosicionPlaneta(
                planeta=nombre,
                longitud_total=longitud_total,
                signo=signo,
                grados_signo=grados,
                retrogrado=velocidad_longitud < 0,
            )
        )

    # --- Aspectos ---
    aspectos = calcular_aspectos(planetas_pos)

    return RespuestaAstrologica(
        zona_horaria_detectada=tiempo["zona_horaria_detectada"],
        hora_utc_calculada=tiempo["hora_utc_calculada"],
        planetas=planetas_resultado,
        casas=casas_resultado,
        aspectos=aspectos,
    )