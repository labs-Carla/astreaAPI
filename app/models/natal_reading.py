"""
NatalReading — Nuevo modelo de producto para la lectura natal (v2).

Este modelo reemplaza conceptualmente a `Reading` (app/models/reading.py),
pero vive en un archivo separado mientras se valida el flujo completo.
`ai_service.py` sigue usando `Reading` hasta que este nuevo modelo esté
integrado y probado end-to-end.

DECISIONES FIRMES (acordadas explícitamente en conversación):
- Cada entidad individual (planeta o punto sensible: Sol, Luna, Mercurio,
  Venus, Marte, Júpiter, Saturno, Urano, Neptuno, Plutón, Nodo Norte,
  Quirón, etc.) se representa con `PlanetCard`, un esquema único reutilizado.
- Los aspectos NO reutilizan `PlanetCard`: tienen su propio modelo `AspectCard`,
  porque un aspecto es una relación binaria, no una entidad individual.
- `PlanetCard.ficha_tecnica` viene EXCLUSIVAMENTE del motor astrológico
  (Swiss Ephemeris / astro_service), nunca de la IA. Es una ficha técnica
  de respaldo, no prosa.
- `casa` en la ficha técnica es Optional: no todo concepto astrológico
  vive en una casa (ej. un aspecto no tiene casa propia). Se evitan
  valores centinela: si no aplica, es None.
- Fortalezas y Desafíos son listas de objetos (título + explicación breve),
  no strings sueltos.
- Identificación/metadata de renderizado (`id`, `entity_type`, `display_name`)
  vive en el modelo de contenido porque es estructural (para mapear la
  tarjeta a su lugar en la UI/PDF), pero NO incluye nada visual (sin
  colores, iconos ni símbolos — eso pertenece a un catálogo de presentación
  separado, fuera de este modelo).

PENDIENTE DE VALIDACIÓN (no se cerró un contrato explícito en conversación):
- La estructura de nivel superior (`Overview`, `LifeAreaCard`, y cómo se
  agrupan las `PlanetCard`/`AspectCard` dentro de `NatalReading`) se deja
  aquí en su forma más simple y modular posible. Esto es un borrador
  razonable, NO una decisión firme — debe confirmarse antes de integrarlo
  con la plantilla HTML/PDF.
"""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field

EntityType = Literal["planet", "point", "house", "aspect"]


# ---------------------------------------------------------------------------
# Bloques reutilizables
# ---------------------------------------------------------------------------

class Fortaleza(BaseModel):
    titulo: str
    explicacion: str


class Desafio(BaseModel):
    titulo: str
    explicacion: str


class AspectoRelevante(BaseModel):
    """Referencia embebida a un aspecto que involucra a la entidad de la tarjeta."""
    entidad_relacionada: str
    tipo_aspecto: str
    angulo_exacto: float
    orbe: float


class FichaTecnica(BaseModel):
    """
    Datos técnicos calculados por el motor astrológico (astro_service /
    time_service). Nunca generados por la IA — funcionan como respaldo
    verificable de la interpretación.
    """
    signo: str
    grados_signo: float
    casa: Optional[str] = None  # None cuando el concepto no vive en una casa
    movimiento: Literal["directo", "retrogrado"]
    dispositor: Optional[str] = None
    aspectos_relevantes: List[AspectoRelevante] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Tarjeta de entidad individual (planeta o punto sensible)
# ---------------------------------------------------------------------------

class PlanetCard(BaseModel):
    """
    Tarjeta reutilizable para cada entidad individual de la carta natal:
    Sol, Luna, Mercurio, Venus, Marte, Júpiter, Saturno, Urano, Neptuno,
    Plutón, y puntos sensibles como Nodo Norte o Quirón cuando corresponda.
    """
    id: str  # ej: "sun", "moon", "north_node", "chiron"
    entity_type: EntityType
    display_name: str

    titulo: str  # ej: "Sol en Virgo, Casa 6" — generado por la IA
    resumen_ejecutivo: str
    interpretacion_profunda: str
    manifestacion_practica: str
    fortalezas: List[Fortaleza]
    desafios: List[Desafio]
    como_potenciar: str
    ficha_tecnica: FichaTecnica
    frase_cierre: str


# ---------------------------------------------------------------------------
# Tarjeta de aspecto (relación binaria, esquema propio)
# ---------------------------------------------------------------------------

class BaseTecnicaAspecto(BaseModel):
    """Datos técnicos del aspecto, calculados por el motor astrológico."""
    cuerpo1: str
    cuerpo2: str
    tipo_aspecto: str
    angulo_exacto: float
    orbe: float


class AspectCard(BaseModel):
    """
    Tarjeta para un aspecto astrológico (ej. "Sol cuadratura Marte").
    No reutiliza PlanetCard: un aspecto es una relación entre dos
    entidades, no una entidad individual.
    """
    id: str  # ej: "sun_square_mars"
    entity_type: Literal["aspect"] = "aspect"
    display_name: str

    titulo: str  # ej: "Sol cuadratura Mercurio"
    cuerpos_involucrados: List[str]  # [cuerpo1, cuerpo2]
    tipo_aspecto: str
    orbe: float
    interpretacion: str
    manifestacion: str
    potencial: str
    desafios: List[Desafio] = Field(default_factory=list)
    recomendacion: str
    base_tecnica: BaseTecnicaAspecto


# ---------------------------------------------------------------------------
# Estructura de nivel superior (borrador — pendiente de validar)
# ---------------------------------------------------------------------------

class Overview(BaseModel):
    """
    Síntesis introductoria de la lectura completa.
    Borrador simple: pendiente de confirmar su forma final.
    """
    introduccion: str
    sintesis_general: str


class LifeAreaCard(BaseModel):
    """
    Agrupación temática opcional (ej. Carrera, Relaciones, Bienestar) que
    conecta varias PlanetCard/AspectCard bajo una lectura integrada.
    Borrador simple: pendiente de confirmar su forma final y si aplica
    a esta versión del producto.
    """
    id: str
    titulo: str
    interpretacion: str
    entidades_relacionadas: List[str] = Field(default_factory=list)  # ids de PlanetCard/AspectCard


class NatalReading(BaseModel):
    """
    Modelo completo de la lectura natal (v2) — reemplaza conceptualmente
    a `Reading`. Aún no integrado con report_service ni la plantilla HTML.
    """
    overview: Overview
    planetas: List[PlanetCard]
    aspectos: List[AspectCard]
    areas_de_vida: List[LifeAreaCard] = Field(default_factory=list)
    cita_cierre: str