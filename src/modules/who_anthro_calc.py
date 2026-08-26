"""
Calculadora antropométrica OMS inspirada en WHO Anthro PC v3.2.2.
Wrapper sobre la librería 'anthro' con clasificaciones y banderas oficiales.
"""
from datetime import date, timedelta
from typing import Dict, Optional, Any

from anthro import compute as _anthro_compute, age_days as _anthro_age_days


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
        "imc": bmi_val,
        "z_lhfa": round(z_lhfa, 2) if z_lhfa is not None else None,
        "z_wfa": round(z_wfa, 2) if z_wfa is not None else None,
        "z_wflh": round(z_wflh, 2) if z_wflh is not None else None,
        "z_bmi": round(z_bmi, 2) if z_bmi is not None else None,
        "z_acfa": round(z_acfa, 2) if z_acfa is not None else None,
        "clasif_lhfa": clasif_lhfa,
        "clasif_wfa": clasif_wfa,
        "clasif_wflh": clasif_wflh,
        "clasif_bmi": clasif_bmi,
        "clasif_muac": clasif_muac,
        "clasif_wellcome": clasificacion_wellcome,
        "flag_lhfa": flag_lhfa,
        "flag_wfa": flag_wfa,
        "flag_wflh": flag_wflh,
        "flag_bmi": flag_bmi,
        "flag_acfa": flag_acfa,
        "errores": errores,
        "advertencias": advertencias + resultado_anthro.get("warnings", []),
    }


def _resultado_con_errores(errores):
    return {
        "edad_dias": None, "edad_meses_completos": None, "edad_meses_decimal": None,
        "sexo": None, "talla_original_cm": None, "talla_ajustada_cm": None,
        "conversion_l_h": None, "peso_kg": None, "edema": False, "imc": None,
        "z_lhfa": None, "z_wfa": None, "z_wflh": None, "z_bmi": None, "z_acfa": None,
        "clasif_lhfa": "N/A", "clasif_wfa": "N/A", "clasif_wflh": "N/A",
        "clasif_bmi": "N/A", "clasif_muac": "N/A", "clasif_wellcome": None,
        "flag_lhfa": 0, "flag_wfa": 0, "flag_wflh": 0, "flag_bmi": 0, "flag_acfa": 0,
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
