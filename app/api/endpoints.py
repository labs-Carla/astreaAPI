import hashlib
import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.entities import Consultante, ReporteAstral
from app.models.astro import RespuestaAstrologica
from app.services.time_service import calcular_tiempo_utc_y_juliano
from app.services.astro_service import obtener_signo_y_grados, calcular_aspectos
from app.core.config import PLANETAS

import swisseph as swe

router = APIRouter()

def _generar_hash_unico(fecha: str, hora_local: str, latitud: float, longitud: float, sistema_casas: str) -> str:
    """Combina los parámetros de la consulta en un hash SHA-256 determinístico."""
    base = f"{fecha}|{hora_local}|{latitud:.4f}|{longitud:.4f}|{sistema_casas}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


@router.get("/carta-natal-completa", response_model=RespuestaAstrologica)
def obtener_carta_natal(
    fecha: str,
    hora_local: str,
    latitud: float,
    longitud: float,
    sistema_casas: str = "P",
    nombre: str = "Consultante",
    db: Session = Depends(get_db),
):
    # 1. Generar Hash Único de Seguridad para el Caché
    hash_unico = _generar_hash_unico(fecha, hora_local, latitud, longitud, sistema_casas)

    # 2. Verificación de Caché (Fase de Lectura instantánea)
    reporte_existente = db.query(ReporteAstral).filter(ReporteAstral.hash_unico == hash_unico).first()
    if reporte_existente:
        return json.loads(reporte_existente.datos_matematicos)

    # 3. Fase de Cálculo (Si es una consulta nueva)
    try:
        tiempo = calcular_tiempo_utc_y_juliano(fecha, hora_local, latitud, longitud)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Datos de entrada inválidos: {e}")

    jd_utc = tiempo["jd_utc"]

    # Cálculo de Casas con Validación Polar
    try:
        cusps, ascmc = swe.houses_ex(
            jd_utc, latitud, longitud, sistema_casas.encode("ascii")
        )
    except swe.Error as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error en el sistema de casas Placidus para estas coordenadas polares. Detalle: {e}"
        )

    # Cálculo de planetas usando el motor modular
    planetas_pos = {}
    planetas_resultado = []
    for p_nombre, codigo_swe in PLANETAS.items():
        xx, _ = swe.calc_ut(jd_utc, codigo_swe, swe.FLG_SWIEPH | swe.FLG_SPEED)

        longitud_total = xx[0]
        velocidad_longitud = xx[3]

        signo, grados = obtener_signo_y_grados(longitud_total)
        planetas_pos[p_nombre] = longitud_total

        planetas_resultado.append({
            "planeta": p_nombre,
            "longitud_total": round(longitud_total, 4),
            "signo": signo,
            "grados_signo": round(grados, 4),
            "retrogrado": velocidad_longitud < 0
        })

    # Cálculo de aspectos e intercalación de casas
    aspectos = [a.model_dump() for a in calcular_aspectos(planetas_pos)]
    casas_resultado = []

    signo_asc, grados_asc = obtener_signo_y_grados(ascmc[0])
    casas_resultado.append({"casa": "Ascendente", "longitud_total": round(ascmc[0], 4), "signo": signo_asc, "grados_signo": round(grados_asc, 4)})

    signo_mc, grados_mc = obtener_signo_y_grados(ascmc[1])
    casas_resultado.append({"casa": "Medio Cielo", "longitud_total": round(ascmc[1], 4), "signo": signo_mc, "grados_signo": round(grados_mc, 4)})

    for i, cusp in enumerate(cusps):
        signo_c, grados_c = obtener_signo_y_grados(cusp)
        casas_resultado.append({
            "casa": f"Casa {i + 1}",
            "longitud_total": round(cusp, 4),
            "signo": signo_c,
            "grados_signo": round(grados_c, 4)
        })

    # Estructura final del resultado
    resultado = {
        "zona_horaria_detectada": tiempo["zona_horaria_detectada"],
        "hora_utc_calculada": tiempo["hora_utc_calculada"],
        "planetas": planetas_resultado,
        "casas": casas_resultado,
        "aspectos": aspectos,
    }

    # 4. Persistencia: Guardar nuevo consultante en SQLite
    nuevo_consultante = Consultante(
        nombre=nombre,
        fecha_nacimiento=fecha,
        hora_local=hora_local,
        latitud=latitud,
        longitud=longitud,
        created_at=datetime.now(timezone.utc),
    )
    db.add(nuevo_consultante)
    db.flush()

    # 5. Persistencia: Guardar el reporte en el Caché de la BD
    nuevo_reporte = ReporteAstral(
        consultante_id=nuevo_consultante.id,
        datos_matematicos=json.dumps(resultado, ensure_ascii=False),
        interpretacion_texto=None,
        hash_unico=hash_unico,
    )
    db.add(nuevo_reporte)
    db.commit()

    return resultado