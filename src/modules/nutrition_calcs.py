"""
Cálculos nutricionales pediátricos basados en tablas OMS.
Incluye IMC para edad, talla para edad, peso para edad,
requerimientos energéticos y evaluación nutricional.
"""
import math
from typing import Optional, Dict, Tuple
from datetime import date, datetime


# ============================================================
# Tablas de referencia OMS (simplificadas) para Z-scores
# Mediana y desviación estándar por edad (meses) y sexo
# ============================================================

# Peso para edad (0-60 meses) - Mediana en kg
PESO_EDAD_MEDIANA_M = {
    0: 3.3, 3: 5.6, 6: 7.9, 9: 9.6, 12: 10.9, 18: 12.8,
    24: 14.2, 30: 15.3, 36: 16.3, 42: 17.3, 48: 18.3, 54: 19.3, 60: 20.3
}
PESO_EDAD_MEDIANA_F = {
    0: 3.2, 3: 5.1, 6: 7.3, 9: 8.9, 12: 10.2, 18: 11.8,
    24: 13.1, 30: 14.2, 36: 15.2, 42: 16.1, 48: 17.0, 54: 18.0, 60: 18.9
}

# Talla para edad (0-60 meses) - Mediana en cm
TALLA_EDAD_MEDIANA_M = {
    0: 49.9, 3: 61.4, 6: 67.6, 9: 72.0, 12: 75.7, 18: 82.3,
    24: 87.8, 30: 92.4, 36: 96.1, 42: 99.9, 48: 103.3, 54: 106.4, 60: 109.4
}
TALLA_EDAD_MEDIANA_F = {
    0: 49.1, 3: 59.8, 6: 65.7, 9: 70.1, 12: 74.0, 18: 80.7,
    24: 86.4, 30: 91.1, 36: 95.1, 42: 99.0, 48: 102.7, 54: 106.2, 60: 109.3
}

# Peso para talla - Mediana en kg (por talla en cm)
PESO_TALLA_MEDIANA_M = {
    45: 2.4, 50: 3.3, 55: 4.6, 60: 6.0, 65: 7.7, 70: 9.6,
    75: 11.4, 80: 13.2, 85: 15.2, 90: 17.2
}
PESO_TALLA_MEDIANA_F = {
    45: 2.4, 50: 3.2, 55: 4.4, 60: 5.8, 65: 7.3, 70: 9.0,
    75: 10.8, 80: 12.5, 85: 14.3, 90: 16.3
}

# Factor de multiplicación para IMC/edad (kg/m²)
IMC_EDAD_MEDIANA = {
    24: 16.2, 36: 15.3, 48: 14.8, 60: 14.4,
    72: 14.5, 84: 15.0, 96: 15.6, 108: 16.4,
    120: 17.2, 132: 18.2, 144: 19.2, 156: 20.3,
    168: 21.4, 180: 22.5, 192: 23.6
}

# Constantes para cálculo de z-scores
DESV_PESO_EDAD_M = {
    0: 0.44, 3: 0.69, 6: 0.87, 9: 0.96, 12: 1.03, 18: 1.22,
    24: 1.34, 30: 1.41, 36: 1.49, 42: 1.56, 48: 1.63, 54: 1.71, 60: 1.78
}
DESV_PESO_EDAD_F = {
    0: 0.42, 3: 0.62, 6: 0.79, 9: 0.88, 12: 0.95, 18: 1.10,
    24: 1.20, 30: 1.29, 36: 1.37, 42: 1.44, 48: 1.51, 54: 1.58, 60: 1.65
}


def calcular_edad_meses(fecha_nacimiento: date, fecha_evaluacion: date) -> float:
    """Calcula la edad en meses entre dos fechas."""
    delta = fecha_evaluacion - fecha_nacimiento
    return round(delta.days / 30.44, 1)


def calcular_imc(peso_kg: float, talla_cm: float) -> float:
    """Calcula el IMC: peso (kg) / talla (m)²."""
    talla_m = talla_cm / 100
    return round(peso_kg / (talla_m ** 2), 2)


def interpolar_valor(tabla: Dict, edad_meses: float) -> float:
    """Interpola un valor entre dos puntos de la tabla de referencia OMS."""
    edades = sorted(tabla.keys())
    if edad_meses <= edades[0]:
        return tabla[edades[0]]
    if edad_meses >= edades[-1]:
        return tabla[edades[-1]]

    for i in range(len(edades) - 1):
        if edades[i] <= edad_meses <= edades[i + 1]:
            factor = (edad_meses - edades[i]) / (edades[i + 1] - edades[i])
            val_i = tabla[edades[i]]
            val_f = tabla[edades[i + 1]]
            return round(val_i + factor * (val_f - val_i), 2)
    return tabla[edades[0]]


def calcular_z_score_peso_edad(peso_kg: float, edad_meses: float, sexo: str) -> float:
    """Z-score de peso para edad."""
    tabla_med = PESO_EDAD_MEDIANA_M if sexo == 'M' else PESO_EDAD_MEDIANA_F
    tabla_desv = DESV_PESO_EDAD_M if sexo == 'M' else DESV_PESO_EDAD_F
    mediana = interpolar_valor(tabla_med, edad_meses)
    desv = interpolar_valor(tabla_desv, edad_meses)
    if desv == 0:
        return 0.0
    z = (peso_kg - mediana) / desv
    return round(z, 2)


def calcular_z_score_talla_edad(talla_cm: float, edad_meses: float, sexo: str) -> float:
    """Z-score de talla para edad (aproximación)."""
    tabla = TALLA_EDAD_MEDIANA_M if sexo == 'M' else TALLA_EDAD_MEDIANA_F
    mediana = interpolar_valor(tabla, edad_meses)
    desv_est = round(mediana * 0.035, 2)
    if desv_est == 0:
        return 0.0
    z = (talla_cm - mediana) / desv_est
    return round(z, 2)


def calcular_z_score_peso_talla(peso_kg: float, talla_cm: float, sexo: str) -> float:
    """Z-score de peso para talla."""
    tabla = PESO_TALLA_MEDIANA_M if sexo == 'M' else PESO_TALLA_MEDIANA_F
    tallas = sorted(tabla.keys())
    talla_int = int(round(talla_cm / 5) * 5)
    talla_int = max(min(talla_int, tallas[-1]), tallas[0])

    mediana = tabla[talla_int]
    desv_est = round(mediana * 0.12, 2)
    if desv_est == 0:
        return 0.0
    z = (peso_kg - mediana) / desv_est
    return round(z, 2)


def calcular_z_score_imc_edad(imc: float, edad_meses: float) -> float:
    """Z-score de IMC para edad (simplificado)."""
    tabla = IMC_EDAD_MEDIANA
    edades = sorted(tabla.keys())
    edad_red = min(edades, key=lambda e: abs(e - edad_meses))
    mediana = tabla[edad_red]
    desv_est = round(mediana * 0.10, 2)
    if desv_est == 0:
        return 0.0
    z = (imc - mediana) / desv_est
    return round(z, 2)


def clasificar_estado_nutricional(z_peso_edad: float) -> str:
    """Clasifica el estado nutricional según Z-score de peso/edad."""
    if z_peso_edad < -3.0:
        return "Desnutrición severa"
    elif z_peso_edad < -2.0:
        return "Desnutrición moderada"
    elif z_peso_edad < -1.0:
        return "Riesgo de desnutrición"
    elif z_peso_edad <= 1.0:
        return "Normal"
    elif z_peso_edad <= 2.0:
        return "Sobrepeso"
    elif z_peso_edad <= 3.0:
        return "Obesidad"
    else:
        return "Obesidad severa"


def clasificar_talla_edad(z_talla: float) -> str:
    """Clasifica el estado nutricional según talla/edad."""
    if z_talla < -3.0:
        return "Talla baja severa (raquitismo)"
    elif z_talla < -2.0:
        return "Talla baja"
    elif z_talla < -1.0:
        return "Riesgo de talla baja"
    else:
        return "Normal"


def calcular_requerimientos_caloricos(edad_meses: float, peso_kg: float, talla_cm: float) -> Dict[str, float]:
    """
    Calcula requerimientos energéticos diarios (FAO/OMS).
    """
    if edad_meses < 12:
        kcal = 95 * peso_kg
    elif edad_meses < 36:
        kcal = 80 * peso_kg
    elif edad_meses < 60:
        kcal = 75 * peso_kg
    elif edad_meses < 84:
        kcal = 70 * peso_kg
    else:
        kcal = 65 * peso_kg

    proteinas_g = round(peso_kg * 1.5, 1)
    grasas_g = round(kcal * 0.35 / 9, 1)
    carbohidratos_g = round(kcal * 0.55 / 4, 1)

    return {
        'calorias_kcal': round(kcal),
        'proteinas_g': proteinas_g,
        'grasas_g': grasas_g,
        'carbohidratos_g': carbohidratos_g,
        'fibra_g': round(edad_meses / 10 + 5, 1) if edad_meses >= 60 else 3.0,
        'hierro_mg': round(11 if edad_meses < 36 else 7, 1),
        'calcio_mg': 500 if edad_meses < 36 else 800,
        'vitamina_a_ui': 400 if edad_meses < 36 else 400,
        'vitamina_c_mg': 40 if edad_meses < 36 else 45,
        'zinc_mg': round(3 if edad_meses < 36 else 5, 1),
    }


def generar_reporte_evaluacion(
    nombre: str, apellido: str, fecha_nac: date, sexo: str,
    peso_kg: float, talla_cm: float, fecha_eval: date
) -> Dict[str, Any]:
    """
    Genera un reporte completo de evaluación nutricional del paciente.
    """
    edad = calcular_edad_meses(fecha_nac, fecha_eval)
    imc = calcular_imc(peso_kg, talla_cm)

    z_peso = calcular_z_score_peso_edad(peso_kg, edad, sexo)
    z_talla = calcular_z_score_talla_edad(talla_cm, edad, sexo)
    z_peso_talla = calcular_z_score_peso_talla(peso_kg, talla_cm, sexo)
    z_imc = calcular_z_score_imc_edad(imc, edad)

    clasif_peso = clasificar_estado_nutricional(z_peso)
    clasif_talla = clasificar_talla_edad(z_talla)
    requerimientos = calcular_requerimientos_caloricos(edad, peso_kg, talla_cm)

    return {
        'paciente': f"{nombre} {apellido}",
        'edad_meses': edad,
        'peso_kg': peso_kg,
        'talla_cm': talla_cm,
        'imc': imc,
        'z_score_peso_edad': z_peso,
        'z_score_talla_edad': z_talla,
        'z_score_peso_talla': z_peso_talla,
        'z_score_imc_edad': z_imc,
        'clasificacion_peso': clasif_peso,
        'clasificacion_talla': clasif_talla,
        'requerimientos': requerimientos,
    }
