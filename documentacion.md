# Documentación Técnica: API Astrológica Profesional

Esta API proporciona cálculos astronómicos de alta precisión para aplicaciones astrológicas occidentales. Utiliza los datos de las efemérides de la NASA a través de la biblioteca Swiss Ephemeris (`pyswisseph`).

## 🪐 Características Principales
* **Geolocalización Temporal:** Detección automática de zonas horarias históricas basadas en coordenadas terrestres (Latitud/Longitud).
* **Precisión Planetaria:** Posiciones exactas del Sol, la Luna y los planetas (incluyendo estado de retrogradación).
* **Sistemas de Casas Soportados:** Placidus, Koch y Signos Enteros (*Whole Signs*).
* **Motor de Aspectos:** Identificación dinámica de aspectos mayores (Conjunción, Sextil, Cuadratura, Trígono, Oposición) con orbes configurables.

---

## 🛠️ Especificación de Endpoints

### 1. Obtener Carta Natal Completa
Calcula las posiciones planetarias, cúspides de las casas, ascendente y aspectos astrológicos de una persona basándose en su tiempo y lugar de nacimiento local.

* **URL:** `/carta-natal-completa`
* **Método:** `GET`

#### Parámetros de Consulta (Request Parameters)

| Parámetro | Tipo | Requerido | Descripción | Ejemplo |
| :--- | :--- | :--- | :--- | :--- |
| `fecha` | String | **Sí** | Fecha en formato ISO (`YYYY-MM-DD`) | `1995-10-25` |
| `hora_local` | String | **Sí** | Hora en el reloj local (`HH:MM`) | `14:30` |
| `latitud` | Float | **Sí** | Latitud geográfica decimal (Rango: -90.0 a 90.0) | `4.5964` |
| `longitud` | Float | **Sí** | Longitud geográfica decimal (Rango: -180.0 a 180.0) | `-74.0721` |
| `sistema_casas` | String | No | Código del sistema. Por defecto: `P` (Placidus). Opciones: `K` (Koch), `W` (Whole Signs) | `P` |

#### Estructura de la Respuesta JSON (Response Body)
```json
{
  "zona_horaria_detectada": "America/Bogota",
  "hora_utc_calculada": "1995-10-25 19:30 UTC",
  "planetas": [
    {
      "planeta": "Sol",
      "longitud_total": 211.4521,
      "signo": "Escorpio",
      "grados_signo": 1.4521,
      "retrogrado": false
    }
  ],
  "casas": [
    {
      "casa": "Ascendente",
      "longitud_total": 315.2214,
      "signo": "Acuario",
      "grados_signo": 15.2214
    }
  ],
  "aspectos": [
    {
      "planeta1": "Sol",
      "planeta2": "Mercurio",
      "tipo": "Conjunción",
      "angulo_exacto": 0.0,
      "distancia": 16.3317
    }
  ]
}
```
