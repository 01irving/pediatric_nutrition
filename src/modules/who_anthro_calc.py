"""
Calculadora antropométrica OMS inspirada en WHO Anthro PC v3.2.2.
Wrapper sobre la librería 'anthro' con clasificaciones y banderas oficiales.
"""
import math
from datetime import date, timedelta
from typing import Dict, Optional, Any, Tuple

from anthro import compute as _anthro_compute, age_days as _anthro_age_days

# ── Conversión Z-score → Percentil ───────────────────────────────────────────

def z_to_percentile(z: float) -> float:
    """Aproximación normal CDF (Abramowitz & Stegun) → percentil (0-100)."""
    if z < -8:
        return 0.0
    if z > 8:
        return 100.0
    a1, a2, a3, a4, a5 = (0.254829592, -0.284496736, 1.421413741, -1.453152027, 1.061405429)
    p = 0.3275911
    sign = 1 if z >= 0 else -1
    x = abs(z) / math.sqrt(2)
    t = 1.0 / (1.0 + p * x)
    y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * math.exp(-x * x)
    return (0.5 * (1.0 + sign * y)) * 100.0


def clasificar_z(z: float) -> str:
    """Clasificación WHO según Z-score."""
    if z is None:
        return "N/A"
    if z < -3:
        return "Desnutrición severa"
    elif z < -2:
        return "Desnutrición moderada"
    elif z < -1:
        return "Riesgo de desnutrición"
    elif z <= 1:
        return "Normal"
    elif z <= 2:
        return "Riesgo de sobrepeso"
    elif z <= 3:
        return "Sobrepeso"
    else:
        return "Obesidad"


# ── Perímetro Cefálico para Edad (PC/Edad) ──────────────────────────────────
# WHO Child Growth Standards, Head-circumference-for-age, tablas LMS diarias
# oficiales (0-1856 días). Fuente: WHO Child Growth Standards expanded LMS tables.
from .hcfa_data import HC_LMS_BOYS_DAILY as _PC_LMS_BOYS, HC_LMS_GIRLS_DAILY as _PC_LMS_GIRLS


def _interpolate_pc_lms(table, age_days: int) -> Optional[Tuple[float, float, float]]:
    """Interpola L, M, S para una edad dada (en días) en la tabla diaria."""
    if age_days <= table[0][0]:
        return table[0][1], table[0][2], table[0][3]
    if age_days >= table[-1][0]:
        return table[-1][1], table[-1][2], table[-1][3]
    for i in range(len(table) - 1):
        d1, l1, m1, s1 = table[i]
        d2, l2, m2, s2 = table[i + 1]
        if d1 <= age_days <= d2:
            f = (age_days - d1) / (d2 - d1) if d2 != d1 else 0
            L = l1 + f * (l2 - l1)
            M = m1 + f * (m2 - m1)
            S = s1 + f * (s2 - s1)
            return L, M, S
    return None


def calcular_z_pc(sexo: str, edad_dias: int, pc_cm: float) -> Optional[float]:
    """Calcula Z-score de perímetro cefálico para la edad usando LMS OMS."""
    table = _PC_LMS_BOYS if sexo in ("M", "male") else _PC_LMS_GIRLS
    lms = _interpolate_pc_lms(table, edad_dias)
    if lms is None:
        return None
    L, M, S = lms
    if abs(L) < 1e-10:
        z = math.log(pc_cm / M) / S
    else:
        z = ((pc_cm / M) ** L - 1) / (L * S)
    return round(z, 2)


def calcular_edad(fecha_nacimiento: date, fecha_visita: date) -> int:
    """Edad en días según fórmula WHO: un año = 365.25 días, un mes = 30.4375 días."""
    return _anthro_age_days(str(fecha_nacimiento), str(fecha_visita))


def calcular_edad_completada(fecha_nacimiento: date, fecha_visita: date) -> int:
    """Edad en meses completos."""
    dias = calcular_edad(fecha_nacimiento, fecha_visita)
    return int(dias // 30.4375)


def evaluar_antropometria(
    sexo: str,
    fecha_nacimiento: date,
    fecha_visita: date,
    peso_kg: Optional[float] = None,
    talla_cm: Optional[float] = None,
    tipo_medicion: str = "L",
    edema: bool = False,
    pc_cm: Optional[float] = None,
    muac_mm: Optional[float] = None,
    pliegue_triceps_mm: Optional[float] = None,
    pliegue_subescapular_mm: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Evaluación antropométrica completa estilo WHO Anthro AC.

    Args:
        sexo: 'M'/'F'/'male'/'female'
        fecha_nacimiento: Fecha de nacimiento
        fecha_visita: Fecha de evaluación
        peso_kg: Peso en kg (0.9-58.0)
        talla_cm: Longitud/altura en cm (38-150)
        tipo_medicion: 'L' = decúbito (longitud), 'H' = bipedestación (altura)
        edema: True si hay edema (no se calcula peso)
        pc_cm: Perímetro cefálico en cm (25-64)
        muac_mm: Perímetro braquial en mm (60-350)
        pliegue_triceps_mm: Pliegue triceps en mm (1.8-40)
        pliegue_subescapular_mm: Pliegue subescapular en mm (1.8-40)

    Returns:
        dict con z-scores, percentiles, clasificaciones, IMC, banderas, errores.
    """
    errores = []
    advertencias = []

    # Validaciones WHO Anthro
    if peso_kg is not None and not (0.9 <= peso_kg <= 58.0):
        errores.append(f"Peso {peso_kg} kg fuera de rango válido (0.9-58.0)")
    if talla_cm is not None and not (38.0 <= talla_cm <= 150.0):
        errores.append(f"Talla {talla_cm} cm fuera de rango válido (38-150)")
    if pc_cm is not None and not (25.0 <= pc_cm <= 64.0):
        errores.append(f"PC {pc_cm} cm fuera de rango válido (25-64)")
    if muac_mm is not None and not (60.0 <= muac_mm <= 350.0):
        errores.append(f"MUAC {muac_mm} mm fuera de rango válido (60-350)")
    if pliegue_triceps_mm is not None and not (1.8 <= pliegue_triceps_mm <= 40.0):
        errores.append(f"Pliegue triceps {pliegue_triceps_mm} mm fuera de rango (1.8-40)")
    if pliegue_subescapular_mm is not None and not (1.8 <= pliegue_subescapular_mm <= 40.0):
        errores.append(f"Pliegue subescapular {pliegue_subescapular_mm} mm fuera de rango (1.8-40)")

    if errores:
        return _resultado_con_errores(errores)

    edad_dias = calcular_edad(fecha_nacimiento, fecha_visita)
    edad_meses = edad_dias / 30.4375

    # Parámetros para anthro
    params: Dict[str, Any] = {
        "sex": "male" if sexo in ("M", "male") else "female",
        "age_days": edad_dias,
        "measure": tipo_medicion,
        "oedema": edema,
    }

    if peso_kg is not None and not edema:
        params["weight_kg"] = peso_kg
    elif edema:
        advertencias.append("Edema presente: el peso no se usa para z-scores de peso")

    if talla_cm is not None:
        params["height_cm"] = talla_cm

    if muac_mm is not None:
        params["muac_mm"] = muac_mm

    # Calcular con anthro
    try:
        resultado_anthro = _anthro_compute(params)
    except Exception as e:
        return _resultado_con_errores([f"Error en cálculo WHO: {e}"])

    # Extraer resultados
    z_lhfa = resultado_anthro.get("z_lhfa")
    z_wfa = resultado_anthro.get("z_wfa")
    z_wflh = resultado_anthro.get("z_wflh")
    z_bmi = resultado_anthro.get("z_bmi")
    z_acfa = resultado_anthro.get("z_acfa")

    # Clasificaciones
    clasif_lhfa = resultado_anthro.get("lhfa", "N/A")
    clasif_wfa = resultado_anthro.get("wfa", "N/A")
    clasif_wflh = resultado_anthro.get("wflh", "N/A")
    clasif_bmi = resultado_anthro.get("bmi", "N/A")
    clasif_muac = resultado_anthro.get("acfa", "N/A")

    # Banderas (flag limits WHO)
    flag_lhfa = resultado_anthro.get("flag_lhfa", 0)
    flag_wfa = resultado_anthro.get("flag_wfa", 0)
    flag_wflh = resultado_anthro.get("flag_wflh", 0)
    flag_bmi = resultado_anthro.get("flag_bmi", 0)
    flag_acfa = resultado_anthro.get("flag_acfa", 0)

    # IMC
    bmi_val = resultado_anthro.get("bmi_val")
    if talla_cm is not None and peso_kg is not None and talla_cm > 0:
        talla_m = talla_cm / 100.0
        bmi_val = round(peso_kg / (talla_m ** 2), 1)

    # Perímetro cefálico para edad
    z_pc = None
    clasif_pc = "N/A"
    if pc_cm is not None:
        z_pc = calcular_z_pc(sexo, edad_dias, pc_cm)
        if z_pc is not None:
            clasif_pc = clasificar_z(z_pc)

    # Percentiles
    perc_lhfa = round(z_to_percentile(z_lhfa), 1) if z_lhfa is not None else None
    perc_wfa = round(z_to_percentile(z_wfa), 1) if z_wfa is not None else None
    perc_wflh = round(z_to_percentile(z_wflh), 1) if z_wflh is not None else None
    perc_bmi = round(z_to_percentile(z_bmi), 1) if z_bmi is not None else None
    perc_acfa = round(z_to_percentile(z_acfa), 1) if z_acfa is not None else None
    perc_pc = round(z_to_percentile(z_pc), 1) if z_pc is not None else None

    # Clasificación Wellcome (solo si hay edema)
    clasificacion_wellcome = None
    if edema:
        clasificacion_wellcome = "Kwashiorkor (edema + desnutrición)"

    # Talla ajustada (con conversión L/H)
    talla_ajustada = resultado_anthro.get("height_cm_adj", talla_cm)
    conversion = resultado_anthro.get("measure_correction")

    return {
        "edad_dias": edad_dias,
        "edad_meses_completos": int(edad_meses),
        "edad_meses_decimal": round(edad_meses, 1),
        "sexo": "M" if sexo in ("M", "male") else "F",
        "talla_original_cm": talla_cm,
        "talla_ajustada_cm": talla_ajustada,
        "conversion_l_h": conversion,
        "peso_kg": peso_kg,
        "edema": edema,
        "pc_cm": pc_cm,
        "muac_mm": muac_mm,
        "imc": bmi_val,
        "z_lhfa": round(z_lhfa, 2) if z_lhfa is not None else None,
        "z_wfa": round(z_wfa, 2) if z_wfa is not None else None,
        "z_wflh": round(z_wflh, 2) if z_wflh is not None else None,
        "z_bmi": round(z_bmi, 2) if z_bmi is not None else None,
        "z_acfa": round(z_acfa, 2) if z_acfa is not None else None,
        "z_pc": z_pc,
        "clasif_lhfa": clasif_lhfa,
        "clasif_wfa": clasif_wfa,
        "clasif_wflh": clasif_wflh,
        "clasif_bmi": clasif_bmi,
        "clasif_muac": clasif_muac,
        "clasif_pc": clasif_pc,
        "clasif_wellcome": clasificacion_wellcome,
        "flag_lhfa": flag_lhfa,
        "flag_wfa": flag_wfa,
        "flag_wflh": flag_wflh,
        "flag_bmi": flag_bmi,
        "flag_acfa": flag_acfa,
        "perc_lhfa": perc_lhfa,
        "perc_wfa": perc_wfa,
        "perc_wflh": perc_wflh,
        "perc_bmi": perc_bmi,
        "perc_acfa": perc_acfa,
        "perc_pc": perc_pc,
        "z_tsfa": None,
        "z_ssfa": None,
        "perc_tsfa": None,
        "perc_ssfa": None,
        "clasif_tsfa": "Medición registrada (sin tabla OMS)" if pliegue_triceps_mm else "N/A",
        "clasif_ssfa": "Medición registrada (sin tabla OMS)" if pliegue_subescapular_mm else "N/A",
        "pliegue_triceps_mm": pliegue_triceps_mm,
        "pliegue_subescapular_mm": pliegue_subescapular_mm,
        "errores": errores,
        "advertencias": advertencias + resultado_anthro.get("warnings", []),
    }


def _resultado_con_errores(errores):
    return {
        "edad_dias": None, "edad_meses_completos": None, "edad_meses_decimal": None,
        "sexo": None, "talla_original_cm": None, "talla_ajustada_cm": None,
        "conversion_l_h": None, "peso_kg": None, "edema": False, "imc": None,
        "z_lhfa": None, "z_wfa": None, "z_wflh": None, "z_bmi": None, "z_acfa": None,
        "z_pc": None,
        "clasif_lhfa": "N/A", "clasif_wfa": "N/A", "clasif_wflh": "N/A",
        "clasif_bmi": "N/A", "clasif_muac": "N/A", "clasif_pc": "N/A",
        "clasif_wellcome": None,
        "flag_lhfa": 0, "flag_wfa": 0, "flag_wflh": 0, "flag_bmi": 0, "flag_acfa": 0,
        "perc_lhfa": None, "perc_wfa": None, "perc_wflh": None,
        "perc_bmi": None, "perc_acfa": None, "perc_pc": None,
        "z_tsfa": None, "z_ssfa": None,
        "perc_tsfa": None, "perc_ssfa": None,
        "clasif_tsfa": "N/A", "clasif_ssfa": "N/A",
        "pliegue_triceps_mm": None, "pliegue_subescapular_mm": None,
        "errores": errores, "advertencias": [],
    }


def formatear_resultado(r: Dict[str, Any]) -> str:
    """Formatea el resultado como texto legible estilo WHO Anthro."""
    if r["errores"]:
        return "ERRORES:\n" + "\n".join(f"  - {e}" for e in r["errores"])

    lineas = [
        "=" * 62,
        "   EVALUACION ANTROPOMETRICA — WHO CHILD GROWTH STANDARDS",
        "=" * 62,
        "",
        f"  Sexo: {'Niño' if r['sexo'] == 'M' else 'Niña'}    Edad: {r['edad_meses_completos']} meses ({r['edad_dias']} dias)",
        f"  Peso: {r['peso_kg']} kg" if r['peso_kg'] else "  Peso: N/A",
    ]

    if r['talla_original_cm']:
        talla_txt = f"Talla: {r['talla_original_cm']} cm"
        if r['conversion_l_h']:
            talla_txt += f" (convertida a {r['talla_ajustada_cm']} cm)"
        talla_txt += f" — {'Decubito (L)' if r.get('conversion_l_h') is None else 'Bipedestacion (H)'}"
        lineas.append(f"  {talla_txt}")

    if r['imc']:
        lineas.append(f"  IMC: {r['imc']} kg/m2")
    if r['edema']:
        lineas.append(f"  EDEMA: SI")

    lineas.extend(["", "-" * 62, "  INDICADORES (Z-score | Clasificacion | Bandera)", "-" * 62])

    indicadores = [
        ("Longitud/Altura-edad", r['z_lhfa'], r['clasif_lhfa'], r['flag_lhfa']),
        ("Peso-edad", r['z_wfa'], r['clasif_wfa'], r['flag_wfa']),
        ("Peso-longitud/altura", r['z_wflh'], r['clasif_wflh'], r['flag_wflh']),
        ("IMC-edad", r['z_bmi'], r['clasif_bmi'], r['flag_bmi']),
    ]

    if r['z_acfa'] is not None:
        indicadores.append(("MUAC-edad", r['z_acfa'], r['clasif_muac'], r['flag_acfa']))

    for nombre, z, clasif, flag in indicadores:
        z_txt = f"{z:+.2f}" if z is not None else "N/A"
        flag_txt = ""
        if flag != 0:
            flag_txt = f" [BANDERA: {flag}]"
        lineas.append(f"  {nombre:.<30s} {z_txt:>8s}  |  {clasif}{flag_txt}")

    if r['clasif_wellcome']:
        lineas.extend(["", "-" * 62, f"  CLASIFICACION WELLCOME: {r['clasif_wellcome']}"])

    if r['advertencias']:
        lineas.extend(["", "-" * 62, "  ADVERTENCIAS:"])
        for w in r['advertencias']:
            lineas.append(f"    - {w}")

    # Nota sobre mediciones extremas
    lineas.extend([
        "",
        "-" * 62,
        "  LIMITES DE BANDERA (WHO standards):",
        "  WAZ: -6 a +5  |  HAZ: -6 a +6  |  WHZ: -5 a +5",
        "  BAZ: -5 a +5  |  HCZ: -5 a +5  |  MUACZ: -5 a +5",
        "=" * 62,
    ])

    return "\n".join(lineas)
