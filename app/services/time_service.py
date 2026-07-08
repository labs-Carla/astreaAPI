"""Geolocalización temporal y conversión a Día Juliano UTC."""

from datetime import datetime
from zoneinfo import ZoneInfo

import swisseph as swe
from timezonefinder import TimezoneFinder

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