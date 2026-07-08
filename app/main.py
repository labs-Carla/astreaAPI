from fastapi import FastAPI
from app.api.endpoints import router as astro_router
from app.core.database import engine, Base
import app.models.entities  # This forces SQLAlchemy to load your tables

# Create all database tables on application startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="API Astrológica Profesional",
    description=(
        "Cálculos astronómicos de alta precisión para aplicaciones "
        "astrológicas occidentales, basados en Swiss Ephemeris con persistencia de datos."
    ),
    version="0.3.0",
)

# Inject modular routes
app.include_router(astro_router)
