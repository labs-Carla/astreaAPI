"""
Motor de Interpretación Astrológica Premium — Astrea Core Engine.
Utiliza el SDK asíncrono de Anthropic para generar narrativas ejecutivas y psicológicas.
"""

import json
from anthropic import AsyncAnthropic

client = AsyncAnthropic()

_SYSTEM_PROMPT = """
Eres el motor de interpretación del sistema Astrea Core Engine.

Tu identidad es la de un Consultor de Estrategia Personal, Psicólogo Evolutivo y Astrólogo de Alta Gama. Operas exclusivamente para perfiles que exigen precisión, profundidad y sofisticación intelectual.

TONO Y VOZ:
- Habla en segunda persona directa ("Tú tienes", "Tu estructura reveals").
- Tono: ejecutivo, refinado, conciso y sutilmente místico.
- Prohibido: lenguaje predictivo ("tendrás", "te pasará"), adivinatorio, comercial o esoterismo denso.
- Cada oración debe revelar, no decorar.

REGLA DE ORO — LA ECUACIÓN OBLIGATORIA:
Cada interpretación planetaria DEBE combinar de forma fluida los tres vectores:
[Planeta] + [Signo] → el qué y el cómo de esa energía.
[Casa]             → el dónde opera esa energía en la vida concreta.
Sin esta ecuación completa, la interpretación es inválida.

FORMATO DE SALIDA:
Responde ÚNICAMENTE con un objeto JSON válido. Sin texto previo, sin bloques de código markdown, sin explicaciones. Solo el JSON puro con esta estructura exacta:

{
  "introduccion_sintesis": "...",
  "capitulo_1_identidad": {
    "titulo": "CAPÍTULO I: El Vector de Liderazgo e Identidad",
    "sol": "...",
    "luna": "...",
    "ascendente": "..."
  },
  "capitulo_2_operacion": {
    "titulo": "CAPÍTULO II: Matriz Operativa y Toma de Decisiones",
    "mercurio": "...",
    "venus": "...",
    "marte": "..."
  },
  "capitulo_3_apalancamiento": {
    "titulo": "CAPÍTULO III: Puntos de Apalancamiento y Dinámica Geométrica",
    "analisis_aspectos": "..."
  },
  "cita_cierre": "..."
}
""".strip()


def _formatear_contexto(datos_matematicos: dict, nombre_usuario: str) -> str:
    """Convierte el output matemático del motor Swiss Ephemeris en texto plano para el prompt."""
    planetas = datos_matematicos.get("planetas", [])
    casas = datos_matematicos.get("casas", [])
    aspectos = datos_matematicos.get("aspectos", [])

    casas_index = {c["casa"]: c for c in casas}

    lineas = [f"CARTA NATAL — {nombre_usuario.upper()}", ""]
    lineas.append("POSICIONES PLANETARIAS Y CASAS:")
    for p in planetas:
        retro = " (Retrógrado)" if p.get("retrogrado") else ""
        lineas.append(
            f"  {p['planeta']}: {p['signo']} {round(p['grados_signo'], 2)}°{retro}"
        )

    asc = casas_index.get("Ascendente")
    mc = casas_index.get("Medio Cielo")
    if asc:
        lineas.append(f"  Ascendente: {asc['signo']} {round(asc['grados_signo'], 2)}°")
    if mc:
        lineas.append(f"  Medio Cielo: {mc['signo']} {round(mc['grados_signo'], 2)}°")

    lineas.append("\nASPECTOS GEOMÉTRICOS MÁS CERRADOS (top 3):")
    for a in aspectos[:3]:
        lineas.append(
            f"  {a['planeta1']} {a['tipo']} {a['planeta2']} (orbe: {round(a['distancia'], 2)}°)"
        )

    return "\n".join(lineas)


async def generar_interpretacion_premium(datos_matematicos: dict, nombre_usuario: str) -> dict:
    """
    Genera la interpretación astrológica premium usando Claude.
    """
    contexto = _formatear_contexto(datos_matematicos, nombre_usuario)

    mensaje_usuario = (
        f"Genera la interpretación astrológica premium completa para el siguiente perfil:\n\n"
        f"{contexto}\n\n"
        f"Aplica la ecuación Planeta + Signo + Casa en cada sección. "
        f"Devuelve exclusivamente el JSON estructurado."
    )

    respuesta = await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4000,
        system=_SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": mensaje_usuario}
        ],
    )

    texto_crudo = respuesta.content[0].text.strip()

    # Limpieza defensiva por si el modelo envuelve en markdown
    if texto_crudo.startswith("```"):
        texto_crudo = texto_crudo.split("```")[1]
        if texto_crudo.startswith("json"):
            texto_crudo = texto_crudo[4:]

    return json.loads(texto_crudo)
