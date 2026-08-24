"""
Antropometría pediátrica basada en tablas OMS.
Incluye: peso, talla, IMC, perímetro cefálico, MUAC,
clasificación de desnutrición (OMS + Wellcome),
reglas de crecimiento y tasas esperadas por edad.
"""
from typing import Dict, Any, Optional
from datetime import date


# ============================================================
# TASAS DE CRECIMIENTO ESPERADAS (Reglas de oro)
# ============================================================
TASAS_PESO_SEMANAL = {
    # (meses_inicio, meses_fin): g/semana
    (0, 3): 200,
    (3, 6): 130,
    (6, 9): 85,
    (9, 12): 75,
}

TASAS_CRECIMIENTO = {
    'longitud_anio1_cm': 25,
    'longitud_anio2_cm': 12,
    'perimetro_cefalico_mes1_cm': 1,
    'perimetro_cefalico_anio2_cm': 2,
}


# ============================================================
# TABLAS OMS: PESO PARA EDAD (0-60 meses) - Mediana en kg
# ============================================================
PESO_EDAD_M = {
    0: 3.3, 1: 4.5, 2: 5.6, 3: 6.4, 4: 7.0, 5: 7.5, 6: 7.9,
    7: 8.3, 8: 8.6, 9: 8.9, 10: 9.2, 11: 9.4, 12: 9.6,
    15: 10.3, 18: 10.9, 21: 11.5, 24: 12.2, 27: 12.8, 30: 13.3,
    33: 13.9, 36: 14.3, 39: 14.8, 42: 15.3, 45: 15.8, 48: 16.3,
    51: 16.8, 54: 17.2, 57: 17.7, 60: 18.3
}
PESO_EDAD_F = {
    0: 3.2, 1: 4.2, 2: 5.1, 3: 5.8, 4: 6.4, 5: 6.9, 6: 7.3,
    7: 7.6, 8: 7.9, 9: 8.2, 10: 8.5, 11: 8.7, 12: 8.9,
    15: 9.6, 18: 10.2, 21: 10.9, 24: 11.5, 27: 12.0, 30: 12.5,
    33: 13.1, 36: 13.6, 39: 14.1, 42: 14.6, 45: 15.1, 48: 15.5,
    51: 16.0, 54: 16.5, 57: 17.0, 60: 17.4
}

# DESVIACIÓN ESTÁNDAR PESO/EDAD
DESV_PESO_M = {
    0: 0.44, 3: 0.70, 6: 0.87, 9: 0.98, 12: 1.03, 18: 1.22,
    24: 1.34, 30: 1.41, 36: 1.49, 42: 1.56, 48: 1.63, 54: 1.71, 60: 1.78
}
DESV_PESO_F = {
    0: 0.42, 3: 0.63, 6: 0.79, 9: 0.89, 12: 0.95, 18: 1.10,
    24: 1.20, 30: 1.29, 36: 1.37, 42: 1.44, 48: 1.51, 54: 1.58, 60: 1.65
}

# ============================================================
# TABLAS OMS: TALLA PARA EDAD (0-60 meses) - Mediana en cm
# ============================================================
TALLA_EDAD_M = {
    0: 49.9, 3: 61.4, 6: 67.6, 9: 72.0, 12: 75.7, 18: 82.3,
    24: 87.8, 30: 92.4, 36: 96.1, 42: 99.9, 48: 103.3, 54: 106.4, 60: 109.4
}
TALLA_EDAD_F = {
    0: 49.1, 3: 59.8, 6: 65.7, 9: 70.1, 12: 74.0, 18: 80.7,
    24: 86.4, 30: 91.1, 36: 95.1, 42: 99.0, 48: 102.7, 54: 106.2, 60: 109.3
}

# DESVIACIÓN ESTÁNDAR TALLA/EDAD (~3.5% de la mediana)
def desv_talla(mediana):
    return round(mediana * 0.035, 2)

# ============================================================
# TABLAS OMS: IMC PARA EDAD (2-20 años) - Mediana kg/m²
# ============================================================
IMC_EDAD_M = {
    24: 16.2, 36: 15.3, 48: 14.8, 60: 14.4,
    72: 14.5, 84: 15.0, 96: 15.6, 108: 16.4,
    120: 17.2, 132: 18.2, 144: 19.2, 156: 20.3,
    168: 21.4, 180: 22.5, 192: 23.6, 204: 24.7
}
IMC_EDAD_F = {
    24: 16.0, 36: 15.2, 48: 14.7, 60: 14.3,
    72: 14.4, 84: 14.9, 96: 15.5, 108: 16.3,
    120: 17.2, 132: 18.3, 144: 19.4, 156: 20.6,
    168: 21.8, 180: 23.0, 192: 24.2, 204: 25.4
}

# ============================================================
# MUAC (cm) - Perímetro braquial medio
# ============================================================
MUAC_REF = {
    # (meses_min, meses_max): {percentil_3, percentil_50, percentil_97}
    (6, 12): (11.5, 14.5, 17.0),
    (12, 60): (11.5, 15.5, 18.5),
}

# Umbral crítico OMS
MUAC_CRITICO_MM = 115  # < 115 mm = riesgo alto de muerte


# ============================================================
# FUNCIONES DE INTERPOLACIÓN
# ============================================================
def interpolar(tabla: Dict, edad_meses: float) -> float:
    """Interpola un valor entre dos puntos de una tabla."""
    edades = sorted(tabla.keys())
    if edad_meses <= edades[0]:
        return tabla[edades[0]]
    if edad_meses >= edades[-1]:
        return tabla[edades[-1]]
    for i in range(len(edades) - 1):
        if edades[i] <= edad_meses <= edades[i + 1]:
            f = (edad_meses - edades[i]) / (edades[i + 1] - edades[i])
            return round(tabla[edades[i]] + f * (tabla[edades[i + 1]] - tabla[edades[i]]), 2)
    return tabla[edades[0]]


# ============================================================
# CÁLCULOS ANTROPOMÉTRICOS
# ============================================================
def calcular_edad_meses(fecha_nac: date, fecha_eval: date) -> float:
    delta = fecha_eval - fecha_nac
    return round(delta.days / 30.44, 1)


def calcular_edad_texto(fecha_nac: date, fecha_eval: date) -> str:
    """Devuelve la edad legible en días, meses o años."""
    dias = (fecha_eval - fecha_nac).days
    if dias < 30:
        return f"{dias} días"
    elif dias < 365:
        meses = round(dias / 30.44)
        return f"{meses} meses"
    else:
        anios = round(dias / 365.25, 1)
        return f"{anios} años"


def calcular_imc(peso_kg: float, talla_cm: float) -> float:
    talla_m = talla_cm / 100
    return round(peso_kg / (talla_m ** 2), 2)


def calcular_z_score(valor: float, mediana: float, desviacion: float) -> float:
    if desviacion == 0:
        return 0.0
    return round((valor - mediana) / desviacion, 2)


def z_peso_edad(peso_kg: float, edad_meses: float, sexo: str) -> float:
    tabla = PESO_EDAD_M if sexo == 'M' else PESO_EDAD_F
    tabla_d = DESV_PESO_M if sexo == 'M' else DESV_PESO_F
    med = interpolar(tabla, edad_meses)
    des = interpolar(tabla_d, edad_meses)
    return calcular_z_score(peso_kg, med, des)


def z_talla_edad(talla_cm: float, edad_meses: float, sexo: str) -> float:
    tabla = TALLA_EDAD_M if sexo == 'M' else TALLA_EDAD_F
    med = interpolar(tabla, edad_meses)
    des = desv_talla(med)
    return calcular_z_score(talla_cm, med, des)


def z_imc_edad(imc: float, edad_meses: float, sexo: str) -> float:
    tabla = IMC_EDAD_M if sexo == 'M' else IMC_EDAD_F
    med = interpolar(tabla, edad_meses)
    des = round(med * 0.10, 2)
    return calcular_z_score(imc, med, des)


def peso_porcentaje_esperado(peso_kg: float, edad_meses: float, sexo: str) -> float:
    """Peso actual como porcentaje del peso esperado (OMS)."""
    tabla = PESO_EDAD_M if sexo == 'M' else PESO_EDAD_F
    esperado = interpolar(tabla, edad_meses)
    if esperado == 0:
        return 0.0
    return round((peso_kg / esperado) * 100, 1)


def peso_talla_porcentaje(peso_kg: float, talla_cm: float) -> float:
    """Peso para talla como porcentaje (aproximación)."""
    # Peso esperado para talla (50th centile aproximado)
    peso_50 = round(0.0003 * talla_cm ** 2.7, 2)
    if peso_50 == 0:
        return 0.0
    return round((peso_kg / peso_50) * 100, 1)


# ============================================================
# CLASIFICACIÓN DE DESNUTRICIÓN
# ============================================================
def clasificar_oms(z_peso: float, z_talla: float, z_imc: float) -> Dict[str, str]:
    """
    Clasificación según criterios OMS (tablas 1 del documento).
    """
    # Peso para talla (basado en z-score)
    if z_peso < -3:
        pn = "Desnutrición severa"
    elif z_peso < -2:
        pn = "Desnutrición moderada"
    elif z_peso < -1:
        pn = "Riesgo de desnutrición"
    elif z_peso <= 1:
        pn = "Normal"
    elif z_peso <= 2:
        pn = "Sobrepeso"
    elif z_peso <= 3:
        pn = "Obesidad"
    else:
        pn = "Obesidad severa"

    # Talla para edad
    if z_talla < -3:
        ta = "Enanismo severo (raquitismo)"
    elif z_talla < -2:
        ta = "Talla baja (stunting)"
    elif z_talla < -1:
        ta = "Riesgo de talla baja"
    else:
        ta = "Normal"

    # IMC para edad
    if z_imc < -3:
        imc_c = "Delgadez severa"
    elif z_imc < -2:
        imc_c = "Delgadez"
    elif z_imc < -1:
        imc_c = "Riesgo de delgadez"
    elif z_imc <= 1:
        imc_c = "Normal"
    elif z_imc <= 2:
        imc_c = "Sobrepeso"
    elif z_imc <= 3:
        imc_c = "Obesidad"
    else:
        imc_c = "Obesidad severa"

    return {
        'estado_nutricional': pn,
        'talla_edad': ta,
        'imc_edad': imc_c,
    }


def clasificar_wellcome(peso_porcentaje: float, edema: bool) -> str:
    """
    Clasificación de Wellcome (tabla 2 del documento).
    """
    if peso_porcentaje < 60:
        if edema:
            return "Marasmic-Kwashiorkor"
        else:
            return "Marasmo"
    elif peso_porcentaje < 80:
        if edema:
            return "Kwashiorkor"
        else:
            return "Desnutrición moderada (< 80% peso esperado)"
    elif peso_porcentaje <= 100:
        return "Normal / Leve"
    elif peso_porcentaje <= 120:
        return "Sobrepeso"
    else:
        return "Obesidad"


def clasificar_muac(muac_mm: float, edad_meses: float) -> str:
    """
    Clasificación según MUAC (perímetro braquial medio).
    """
    muac_cm = muac_mm / 10
    if muac_mm < MUAC_CRITICO_MM:
        return f"CRÍTICO — MUAC {muac_cm:.1f} cm (< {MUAC_CRITICO_MM} mm = alto riesgo de muerte)"
    elif muac_mm < 125:
        return f"Alerta — MUAC {muac_cm:.1f} cm (riesgo de desnutrición)"
    elif muac_mm < 140:
        return f"Leve — MUAC {muac_cm:.1f} cm (atención)"
    else:
        return f"Normal — MUAC {muac_cm:.1f} cm"


def clasificar_perimetro_cefalico(pc_cm: float, edad_meses: float, sexo: str) -> str:
    """Clasificación aproximada del perímetro cefálico."""
    # Valores de referencia OMS simplificados
    ref_m = {0: 34.5, 3: 40.5, 6: 43.5, 12: 46.5, 24: 49.5, 36: 51.0, 48: 52.0, 60: 52.8}
    ref_f = {0: 34.0, 3: 39.5, 6: 42.5, 12: 45.5, 24: 48.5, 36: 50.0, 48: 51.5, 60: 52.2}
    tabla = ref_m if sexo == 'M' else ref_f
    med = interpolar(tabla, edad_meses)
    z = calcular_z_score(pc_cm, med, round(med * 0.03, 2))
    if z < -2:
        return f"Microcefalia (Z={z})"
    elif z > 2:
        return f"Macrocefalia (Z={z})"
    else:
        return f"Normal (Z={z})"


# ============================================================
# CRITERIOS PARA INTERVENCIÓN (tubo nasogástrico)
# ============================================================
def evaluar_necesidad_intervencion(edad_meses: float, peso_kg: float, talla_cm: float,
                                    peso_anterior_kg: float = None, talla_anterior_cm: float = None,
                                    meses_desde_eval_anterior: float = None) -> list:
    """
    Evalúa si el niño necesita intervención according a los criterios del documento.
    Retorna lista de alertas/criterios cumplidos.
    """
    alertas = []

    if peso_anterior_kg and meses_desde_eval_anterior:
        cambio_peso = peso_kg - peso_anterior_kg

        # Criterios para < 2 años
        if edad_meses < 24:
            if cambio_peso <= 0 and meses_desde_eval_anterior >= 3:
                alertas.append("Pérdida o ausencia de ganancia de peso por >3 meses (< 2 años)")
            elif peso_kg < peso_anterior_kg and meses_desde_eval_anterior >= 1:
                alertas.append("Pérdida de peso en 1 mes (< 2 años)")

        # Criterios para > 2 años
        else:
            if cambio_peso <= 0 and meses_desde_eval_anterior >= 3:
                alertas.append("Pérdida o ausencia de ganancia de peso por >3 meses (> 2 años)")

    if talla_anterior_cm and meses_desde_eval_anterior:
        # Disminución de velocidad de talla
        if meses_desde_eval_anterior >= 12:
            cambio_talla = talla_cm - talla_anterior_cm
            if edad_meses < 48:  # < 4 años
                tasa_esperada = TASAS_CRECIMIENTO['longitud_anio1_cm'] * (meses_desde_eval_anterior / 12)
            else:
                tasa_esperada = 6  # ~6 cm/año en edad escolar
            if cambio_talla < tasa_esperada * 0.5:
                alertas.append(f"Velocidad de talla disminuida ({cambio_talla:.1f} cm en {meses_desde_eval_anterior:.0f} meses)")

    return alertas


# ============================================================
# REPORTE COMPLETO
# ============================================================
def generar_reporte_antropometrico(
    nombre: str, fecha_nac: date, sexo: str,
    peso_kg: float, talla_cm: float,
    perimetro_cefalico_cm: float = 0,
    muac_mm: float = 0,
    pliegue_triceps_mm: float = 0,
    edema: bool = False,
    fecha_eval: date = None,
    peso_anterior_kg: float = None,
    talla_anterior_cm: float = None,
    meses_eval_anterior: float = None,
) -> Dict[str, Any]:
    """Genera reporte antropométrico completo."""
    if fecha_eval is None:
        fecha_eval = date.today()

    edad_meses = calcular_edad_meses(fecha_nac, fecha_eval)
    imc = calcular_imc(peso_kg, talla_cm)

    zp = z_peso_edad(peso_kg, edad_meses, sexo)
    zt = z_talla_edad(talla_cm, edad_meses, sexo)
    zi = z_imc_edad(imc, edad_meses, sexo)

    peso_pct = peso_porcentaje_esperado(peso_kg, edad_meses, sexo)
    peso_talla_pct = peso_talla_porcentaje(peso_kg, talla_cm)

    clasif = clasificar_oms(zp, zt, zi)
    wellcome = clasificar_wellcome(peso_pct, edema)

    alertas = evaluar_necesidad_intervencion(
        edad_meses, peso_kg, talla_cm,
        peso_anterior_kg, talla_anterior_cm, meses_eval_anterior
    )

    muac_clasif = ""
    if muac_mm > 0:
        muac_clasif = clasificar_muac(muac_mm, edad_meses)

    pc_clasif = ""
    if perimetro_cefalico_cm > 0:
        pc_clasif = clasificar_perimetro_cefalico(perimetro_cefalico_cm, edad_meses, sexo)

    return {
        'nombre': nombre,
        'edad_meses': edad_meses,
        'edad_texto': calcular_edad_texto(fecha_nac, fecha_eval),
        'sexo': 'Masculino' if sexo == 'M' else 'Femenino',
        'peso_kg': peso_kg,
        'talla_cm': talla_cm,
        'imc': imc,
        'perimetro_cefalico_cm': perimetro_cefalico_cm,
        'muac_mm': muac_mm,
        'pliegue_triceps_mm': pliegue_triceps_mm,
        'z_peso_edad': zp,
        'z_talla_edad': zt,
        'z_imc_edad': zi,
        'peso_porcentaje': peso_pct,
        'peso_talla_porcentaje': peso_talla_pct,
        'clasificacion_oms': clasif,
        'clasificacion_wellcome': wellcome,
        'muac_clasificacion': muac_clasif,
        'pc_clasificacion': pc_clasif,
        'alertas': alertas,
        'tasa_peso_semanal': interpolar(
            {k[0]: v for k, v in TASAS_PESO_SEMANAL.items()}, edad_meses
        ) if edad_meses < 12 else None,
    }
