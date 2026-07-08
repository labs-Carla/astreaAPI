"""
Servicio de Renderizado y Generación de Reportes PDF — Astrea Core Engine.
Utiliza Jinja2 para la compilación de HTML y Playwright para la impresión a PDF.
"""

import os
from jinja2 import Environment, FileSystemLoader
from playwright.async_api import async_playwright

# Configurar de forma robusta la ruta absoluta de los templates HTML
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
templates_dir = os.path.join(BASE_DIR, "templates")
env = Environment(loader=FileSystemLoader(templates_dir))

async def generar_pdf_reporte(datos_astrales: dict, nombre_usuario: str, fecha_local: str, hora_local: str) -> bytes:
    """
    Toma los datos del cálculo astral consolidado (efemérides + IA), compila 
    la plantilla HTML mística/ejecutiva y genera un documento PDF binario de alta calidad.
    """
    # Extraer de forma segura el nodo interpretativo de la IA
    interpretacion = datos_astrales.get("interpretacion_premium", {})

    # Construir el contexto unificado para Jinja2
    contexto = {
        "nombre_usuario": nombre_usuario,
        "fecha_local": fecha_local,
        "hora_local": hora_local,
        "latitud": datos_astrales.get("latitud", 4.61),
        "longitud": datos_astrales.get("longitud", -74.08),
        "zona_horaria_detectada": datos_astrales.get("zona_horaria_detectada", "America/Bogota"),
        "planetas": datos_astrales.get("planetas", []),
        "casas": datos_astrales.get("casas", []),
        "aspectos": datos_astrales.get("aspectos", []),
        "interpretacion_premium": interpretacion
    }

    # Renderizar el HTML dinámico
    template = env.get_template("carta_report.html")
    html_contenido = template.render(contexto)

    # Levantar Chromium en segundo plano para imprimir el PDF
        # Levantar Chromium en segundo plano para imprimir el PDF (MÉTODO VELOZ)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # 1. Ajustar el timeout general a 60 segundos por seguridad
        page.set_default_timeout(60000)
        
        # 2. Inyectar el HTML y esperar a que el DOM esté listo, no a que internet guarde silencio
        await page.set_content(html_contenido, wait_until="domcontentloaded")
        
        # Un pequeño respiro de 500ms para asegurar la estabilización del layout
        await page.wait_for_timeout(500)
        
        # 3. Generar la impresión física en A4 sin márgenes nativos del sistema
        pdf_bytes = await page.pdf(
            format="A4",
            print_background=True,
            margin={"top": "0mm", "bottom": "0mm", "left": "0mm", "right": "0mm"}
        )
        
        await browser.close()
        return pdf_bytes

