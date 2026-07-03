"""Router de la API Astrológica."""

from typing import List

import swisseph as swe
from fastapi import APIRouter, HTTPException

from app.core.config import PLANETAS
from app.models.astro import PosicionCasa, PosicionPlaneta, RespuestaAstrologica
from app.services.astro_service import calcular_aspectos, obtener_signo_y_grados
from app.services.time_service import calcular_tiempo_utc_y_juliano

router = APIRouter()


@router.get("/carta-natal-completa", response_model=RespuestaAstrologica)
def carta_natal_completa(
    fecha: str,
    hora_local: str,
    latitud: float,
    longitud: float,
    sistema_casas: str = "P",
):
    try:
        tiempo = calcular_tiempo_utc_y_juliano(fecha, hora_local, latitud, longitud)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Datos de entrada inválidos. Verifique fecha (YYYY-MM-DD), hora (HH:MM) o coordenadas. Detalle: {e}",
        )

    jd_utc = tiempo["jd_utc"]

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

    aspectos = calcular_aspectos(planetas_pos)

    return RespuestaAstrologica(
        zona_horaria_detectada=tiempo["zona_horaria_detectada"],
        hora_utc_calculada=tiempo["hora_utc_calculada"],
        planetas=planetas_resultado,
        casas=casas_resultado,
        aspectos=aspectos,
    )