"""
Servicio de Reportes Astrológicos en PDF.
Compila la plantilla Jinja2 y la imprime a PDF (A4) usando Playwright.
"""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from playwright.async_api import async_playwright

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"

_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html"]),
)


async def generar_reporte_pdf(contexto: dict, plantilla: str = "carta_report.html") -> bytes:
    """
    Renderiza `plantilla` con `contexto` (debe incluir zona_horaria_detectada,
    hora_utc_calculada, planetas, casas, aspectos) y retorna los bytes del PDF.
    """
    template = _env.get_template(plantilla)
    html_renderizado = template.render(**contexto)

    async with async_playwright() as p:
        navegador = await p.chromium.launch()
        try:
            pagina = await navegador.new_page()
            await pagina.set_content(html_renderizado, wait_until="networkidle")

            pdf_bytes = await pagina.pdf(
                format="A4",
                print_background=True,
                prefer_css_page_size=False,
                margin={
                    "top": "2cm",
                    "bottom": "2cm",
                    "left": "1.5cm",
                    "right": "1.5cm",
                },
            )
        finally:
            await navegador.close()

    return pdf_bytes