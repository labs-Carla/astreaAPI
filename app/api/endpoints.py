"""
Endpoints de la API Astrológica.
Incluye lógica de caché (hash único) y persistencia con SQLAlchemy.
"""

import hashlib
import json
from datetime import datetime, timezone

import swisseph as swe
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
from timezonefinder import TimezoneFinder
from zoneinfo import ZoneInfo

from ..core.database import get_db
from ..models.entities import Consultante, ReporteAstral
from ..models.astro import RespuestaAstrologica
from app.services.time_service import calcular_tiempo_utc_y_juliano
from app.services.astro_service import obtener_signo_y_grados, calcular_aspectos
from app.core.config import PLANETAS

router = APIRouter()


def _generar_hash_unico(fecha: str, hora_local: str, latitud: float, longitud: float, sistema_casas: str) -> str:
    """Combina los parámetros de la consulta en un hash SHA-256 determinístico."""
    base = f"{fecha}|{hora_local}|{latitud:.4f}|{longitud:.4f}|{sistema_casas}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


async def _calcular_o_recuperar_carta(
    fecha: str,
    hora_local: str,
    latitud: float,
    longitud: float,
    sistema_casas: str,
    nombre: str,
    db: Session,
) -> dict:
    """
    Lógica compartida: verifica caché, calcula si hace falta, persiste, y
    siempre retorna un dict con latitud/longitud incluidos explícitamente
    (necesarios para el PDF, no solo para el JSON de la API).
    """
    # 1. Hash único para caché
    hash_unico = _generar_hash_unico(fecha, hora_local, latitud, longitud, sistema_casas)

    # 2. Verificación de caché
    reporte_existente = db.query(ReporteAstral).filter(ReporteAstral.hash_unico == hash_unico).first()
    if reporte_existente:
        datos = json.loads(reporte_existente.datos_matematicos)
        if reporte_existente.interpretacion_texto:
            datos["interpretacion_premium"] = json.loads(reporte_existente.interpretacion_texto)
        datos["latitud"] = latitud
        datos["longitud"] = longitud
        return datos

    # 3. Cálculo astronómico
    try:
        tiempo = calcular_tiempo_utc_y_juliano(fecha, hora_local, latitud, longitud)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Datos de entrada inválidos: {e}")

    jd_utc = tiempo["jd_utc"]

    try:
        cusps, ascmc = swe.houses_ex(
            jd_utc, latitud, longitud, sistema_casas.encode("ascii")
        )
    except swe.Error as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error en el sistema de casas para estas coordenadas polares. Detalle: {e}"
        )

    planetas_pos = {}
    planetas_resultado = []
    for p_nombre, codigo_swe in PLANETAS.items():
        xx, _ = swe.calc_ut(jd_utc, codigo_swe)
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
    aspectos = [a.model_dump() if hasattr(a, 'model_dump') else a for a in calcular_aspectos(planetas_pos)]
    casas_resultado = []

    # Extraer Ascendente y Medio Cielo de forma segura (ascmc[0] y ascmc[1])
    signo_asc, grados_asc = obtener_signo_y_grados(ascmc[0])
    casas_resultado.append({"casa": "Ascendente", "longitud_total": round(ascmc[0], 4), "signo": signo_asc, "grados_signo": round(grados_asc, 4)})

    signo_mc, grados_mc = obtener_signo_y_grados(ascmc[1])
    casas_resultado.append({"casa": "Medio Cielo", "longitud_total": round(ascmc[1], 4), "signo": signo_mc, "grados_signo": round(grados_mc, 4)})

    # Mapeo defensivo de las 12 Casas
    if len(cusps) == 13:
        for i in range(1, 13):
            signo_c, grados_c = obtener_signo_y_grados(cusps[i])
            casas_resultado.append({
                "casa": f"Casa {i}",
                "longitud_total": round(cusps[i], 4),
                "signo": signo_c,
                "grados_signo": round(grados_c, 4)
            })
    else:
        for i in range(12):
            signo_c, grados_c = obtener_signo_y_grados(cusps[i])
            casas_resultado.append({
                "casa": f"Casa {i + 1}",
                "longitud_total": round(cusps[i], 4),
                "signo": signo_c,
                "grados_signo": round(grados_c, 4)
            })

    resultado = {
        "zona_horaria_detectada": tiempo["zona_horaria_detectada"],
        "hora_utc_calculada": tiempo["hora_utc_calculada"],
        "planetas": planetas_resultado,
        "casas": casas_resultado,
        "aspectos": aspectos,
    }

    # 4. Invocación modular a la API de Claude
    from app.services.ai_service import generar_interpretacion_premium
    try:
        interpretacion_json = await generar_interpretacion_premium(resultado, nombre)
    except Exception as e:
        interpretacion_json = {"error": f"No se pudo generar la interpretación de IA: {e}"}

    # 5. Persistencia
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

    nuevo_reporte = ReporteAstral(
        consultante_id=nuevo_consultante.id,
        datos_matematicos=json.dumps(resultado, ensure_ascii=False),
        interpretacion_texto=json.dumps(interpretacion_json, ensure_ascii=False),
        hash_unico=hash_unico,
    )
    db.add(nuevo_reporte)
    db.commit()

    return {**resultado, "interpretacion_premium": interpretacion_json, "latitud": latitud, "longitud": longitud}


@router.get("/carta-natal-completa", response_model=RespuestaAstrologica)
async def obtener_carta_natal(
    fecha: str,
    hora_local: str,
    latitud: float,
    longitud: float,
    sistema_casas: str = "P",
    nombre: str = "Consultante",
    db: Session = Depends(get_db),
):
    return await _calcular_o_recuperar_carta(
        fecha, hora_local, latitud, longitud, sistema_casas, nombre, db
    )


@router.get("/carta-natal/pdf")
async def descargar_reporte_pdf(
    fecha: str,
    hora_local: str,
    latitud: float,
    longitud: float,
    sistema_casas: str = "P",
    nombre: str = "Consultante",
    db: Session = Depends(get_db),
):
    """
    Endpoint que genera y retorna el documento PDF definitivo con diseño premium
    para su descarga directa en el navegador.
    """
    try:
        resultado_completo = await _calcular_o_recuperar_carta(
            fecha, hora_local, latitud, longitud, sistema_casas, nombre, db
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al procesar el mapa base: {e}")

    from app.services.report_service import generar_pdf_reporte
    try:
        pdf_bytes = await generar_pdf_reporte(
            datos_astrales=resultado_completo,
            nombre_usuario=nombre,
            fecha_local=fecha,
            hora_local=hora_local
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error en el motor de impresión PDF (Playwright): {e}"
        )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=Reporte_Astral_{nombre.replace(' ', '_')}.pdf"
        }
    )