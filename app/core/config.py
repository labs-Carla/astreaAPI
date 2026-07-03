"""Constantes del motor astrológico."""

import swisseph as swe

SIGNOS = [
    "Aries", "Tauro", "Géminis", "Cáncer", "Leo", "Virgo",
    "Libra", "Escorpio", "Sagitario", "Capricornio", "Acuario", "Piscis",
]

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

ASPECTOS_CONFIG = [
    {"nombre": "Conjunción", "angulo": 0, "orbe": 8.0},
    {"nombre": "Oposición", "angulo": 180, "orbe": 8.0},
    {"nombre": "Trígono", "angulo": 120, "orbe": 8.0},
    {"nombre": "Cuadratura", "angulo": 90, "orbe": 8.0},
    {"nombre": "Sextil", "angulo": 60, "orbe": 6.0},
]