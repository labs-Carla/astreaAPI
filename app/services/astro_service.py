"""Lógica de cálculo astronómico: signos y aspectos."""

from itertools import combinations
from typing import List

from app.core.config import SIGNOS, ASPECTOS_CONFIG
from app.models.astro import AspectoAstrologico


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
                break

    return aspectos_encontrados