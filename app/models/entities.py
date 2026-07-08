"""
Modelos de persistencia (SQLAlchemy) para consultantes y reportes astrales.
"""

from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship

from ..core.database import Base


class Consultante(Base):
    __tablename__ = "consultantes"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    fecha_nacimiento = Column(String, nullable=False)
    hora_local = Column(String, nullable=False)
    latitud = Column(Float, nullable=False)
    longitud = Column(Float, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    reportes = relationship(
        "ReporteAstral", back_populates="consultante", cascade="all, delete-orphan"
    )


class ReporteAstral(Base):
    __tablename__ = "reportes_astrales"

    id = Column(Integer, primary_key=True, index=True)
    consultante_id = Column(Integer, ForeignKey("consultantes.id"), nullable=False)
    datos_matematicos = Column(Text, nullable=False)  # JSON serializado (Swiss Ephemeris)
    interpretacion_texto = Column(Text, nullable=True)  # Respuesta generada por Claude
    hash_unico = Column(String, index=True, unique=True, nullable=False)

    consultante = relationship("Consultante", back_populates="reportes")