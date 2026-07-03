# Requerimientos Técnicos del Proyecto

Este documento detalla las dependencias necesarias y el entorno de ejecución para que el motor astrológico funcione correctamente.

## 1. Entorno de Ejecución
* **Lenguaje:** Python 3.10 o superior.
* **Paradigma:** API basada en eventos asíncronos (FastAPI).

## 2. Dependencias del Núcleo (Core Dependencies)
* `fastapi`: Framework web moderno, rápido y de alto rendimiento para construir APIs con Python.
* `uvicorn`: Servidor ASGI de alta velocidad para ejecutar la aplicación de FastAPI.
* `pydantic`: Validación de datos y gestión de configuraciones mediante tipos de datos nativos de Python.

## 3. Dependencias de Cálculo y Tiempo (Astrology & Time)
* `pyswisseph`: Enlace oficial en Python para la biblioteca *Swiss Ephemeris*. Es indispensable ya que contiene los algoritmos de la NASA para calcular posiciones exactas de los planetas.
* `timezonefinder`: Librería para buscar de forma local y offline el nombre de la zona horaria (ej: `America/Bogota`) utilizando únicamente un par de coordenadas (latitud y longitud).
* `zoneinfo`: Módulo nativo de Python (disponible desde Python 3.9) para manejar las conversiones de zonas horarias históricas utilizando la base de datos de IANA.

## 4. Requerimientos del Sistema (Compilación)
* **Nota sobre `pyswisseph`:** Al instalar esta librería mediante `pip`, el sistema intentará compilar código fuente en C. Por lo tanto, tu computadora necesita tener instalado un compilador:
  * **Windows:** Herramientas de compilación de Visual Studio (C++ build tools).
  * **macOS:** Xcode Command Line Tools (`xcode-select --install`).
  * **Linux:** Paquete esencial de desarrollo (`build-essential`).
