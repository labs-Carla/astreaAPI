"""Punto de entrada de la aplicación."""

from fastapi import FastAPI

from app.api.endpoints import router

app = FastAPI(
    title="API Astrológica Profesional",
    description=(
        "Cálculos astronómicos de alta precisión para aplicaciones "
        "astrológicas occidentales, basados en Swiss Ephemeris."
    ),
    version="0.1.0",
)

app.include_router(router)