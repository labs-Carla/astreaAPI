"""
Suite de pruebas para la API Astrológica.
Ejecutar con: pytest test_main.py -v
"""

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestCartaNatalValida:
    """Caso de referencia verificado: Bogotá, 2000-08-25, 14:50 local."""

    def setup_method(self):
        self.params = {
            "fecha": "2000-08-25",
            "hora_local": "14:50",
            "latitud": 4.5964,
            "longitud": -74.0721,
            "sistema_casas": "P",
        }
        self.response = client.get("/carta-natal-completa", params=self.params)

    def test_status_code_200(self):
        assert self.response.status_code == 200

    def test_zona_horaria_bogota(self):
        data = self.response.json()
        assert data["zona_horaria_detectada"] == "America/Bogota"

    def test_sol_en_virgo(self):
        data = self.response.json()
        sol = next(p for p in data["planetas"] if p["planeta"] == "Sol")
        assert sol["signo"] == "Virgo"

    def test_ascendente_en_capricornio(self):
        data = self.response.json()
        asc = next(c for c in data["casas"] if c["casa"] == "Ascendente")
        assert asc["signo"] == "Capricornio"


class TestFechaInvalida:
    def test_fecha_corrupta_devuelve_error(self):
        params = {
            "fecha": "2000-13-45",  # mes/día inexistentes
            "hora_local": "14:50",
            "latitud": 4.5964,
            "longitud": -74.0721,
        }
        response = client.get("/carta-natal-completa", params=params)
        assert response.status_code in (400, 422, 500)

    def test_formato_hora_corrupto(self):
        params = {
            "fecha": "2000-08-25",
            "hora_local": "25:99",  # hora inválida
            "latitud": 4.5964,
            "longitud": -74.0721,
        }
        response = client.get("/carta-natal-completa", params=params)
        assert response.status_code in (400, 422, 500)


class TestCoordenadasExtremas:
    def test_polo_norte_maneja_excepcion_casas(self):
        params = {
            "fecha": "2000-08-25",
            "hora_local": "14:50",
            "latitud": 89.9,
            "longitud": 0.0,
            "sistema_casas": "P",  # Placidus falla en latitudes polares
        }
        response = client.get("/carta-natal-completa", params=params)
        assert response.status_code == 400
        assert "sistema de casas" in response.json()["detail"].lower()