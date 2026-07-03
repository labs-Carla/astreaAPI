from datetime import datetime
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
import swisseph as swe

app = FastAPI(
    title="API Astrológica Completa", 
    description="Cálculo de posiciones planetarias, Casas y Ascendente usando Swiss Ephemeris"
)

SIGNOS = [
    "Aries", "Tauro", "Géminis", "Cáncer", 
    "Leo", "Virgo", "Libra", "Escorpio", 
    "Sagitario", "Capricornio", "Acuario", "Piscis"
]

PLANETAS = {
    "Sol": swe.SUN, "Luna": swe.MOON, "Mercurio": swe.MERCURY, 
    "Venus": swe.VENUS, "Marte": swe.MARS, "Júpiter": swe.JUPITER, 
    "Saturno": swe.SATURN, "Urano": swe.URANUS, "Neptuno": swe.NEPTUNE, 
    "Plutón": swe.PLUTO
}

# --- Esquemas de salida de datos (Pydantic) ---
class PosicionPlaneta(BaseModel):
    planeta: str
    longitud_total: float
    signo: str
    grados_signo: float
    retrogrado: bool

class PosicionCasa(BaseModel):
    casa: str  # Ej: "Casa 1", "Ascendente", "Medio Cielo"
    longitud_total: float
    signo: str
    grados_signo: float

class RespuestaAstrologica(BaseModel):
    planetas: list[PosicionPlaneta]
    casas: list[PosicionCasa]


def obtener_signo_y_grados(longitud_ecliptica: float):
    """Divide los 360 grados de la eclíptica en los 12 signos."""
    id_signo = int(longitud_ecliptica // 30)
    grados_en_signo = longitud_ecliptica % 30
    return SIGNOS[id_signo], round(grados_en_signo, 4)


@app.get("/carta-natal", response_model=RespuestaAstrologica)
def calcular_carta_natal(
    fecha: str = Query(..., description="Formato YYYY-MM-DD"),
    hora_utc: str = Query(..., description="Formato HH:MM en tiempo UTC"),
    latitud: float = Query(..., description="Latitud decimal (ej: 4.59)", ge=-90.0, le=90.0),
    longitud: float = Query(..., description="Longitud decimal (ej: -74.07)", ge=-180.0, le=180.0),
    sistema_casas: str = Query("P", description="P=Placidus, K=Koch, W=Whole Signs (Signos Enteros)")
):
    try:
        # 1. Parsear tiempo y calcular Día Juliano
        dt = datetime.strptime(f"{fecha} {hora_utc}", "%Y-%m-%d %H:%M")
        hora_decimal = dt.hour + dt.minute / 60.0
        julian_day = swe.julday(dt.year, dt.month, dt.day, hora_decimal)
        
        # Validar sistema de casas
        sistema_casas_bytes = sistema_casas.encode('utf-8')
        if sistema_casas_bytes not in [b'P', b'K', b'W']:
            raise HTTPException(status_code=400, detail="Sistema de casas no soportado. Use P, K o W.")

        # 2. Calcular Casas y Cúspides
        # swe.houses_ex devuelve: (cusps, ascmc)
        # cusps: lista de 13 elementos (el índice 0 se ignora, 1 a 12 son las casas)
        # ascmc: lista con [Ascendente, Medio Cielo, ARMC, Vertex...]
        cusps, ascmc = swe.houses_ex(julian_day, latitud, longitud, sistema_casas_bytes)
        
        lista_casas = []
        
        # Guardar explícitamente Ascendente y Medio Cielo primero
        signo_asc, grados_asc = obtener_signo_y_grados(ascmc[0])
        lista_casas.append(PosicionCasa(casa="Ascendente", longitud_total=round(ascmc[0], 4), signo=signo_asc, grados_signo=grados_asc))
        
        signo_mc, grados_mc = obtener_signo_y_grados(ascmc[1])
        lista_casas.append(PosicionCasa(casa="Medio Cielo", longitud_total=round(ascmc[1], 4), signo=signo_mc, grados_signo=grados_mc))

        # Mapear las 12 casas individuales
        for i in range(1, 13):
            signo_c, grados_c = obtener_signo_y_grados(cusps[i])
            lista_casas.append(
                PosicionCasa(
                    casa=f"Casa {i}",
                    longitud_total=round(cusps[i], 4),
                    signo=signo_c,
                    grados_signo=grados_c
                )
            )

        # 3. Calcular Planetas
        lista_planetas = []
        for nombre, codigo_swe in PLANETAS.items():
            res, _ = swe.calc_ut(julian_day, codigo_swe)
            
            longitud_p = res[0]
            velocidad_p = res[3]  # El índice 3 de la respuesta contiene la velocidad angular
            
            signo_p, grados_p = obtener_signo_y_grados(longitud_p)
            is_retrogrado = velocidad_p < 0

            lista_planetas.append(
                PosicionPlaneta(
                    planeta=nombre,
                    longitud_total=round(longitud_p, 4),
                    signo=signo_p,
                    grados_signo=grados_p,
                    retrogrado=is_retrogrado
                )
            )
            
        return RespuestaAstrologica(planetas=lista_planetas, casas=lista_casas)

    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de fecha u hora inválido. Use YYYY-MM-DD y HH:MM.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en el cálculo astronómico: {str(e)}")
