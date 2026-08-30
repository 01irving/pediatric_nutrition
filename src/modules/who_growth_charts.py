"""
Gráficas de crecimiento OMS usando las tablas LMS de la librería 'anthro'.
Genera gráficas con tkinter Canvas mostrando curvas Z-score y percentiles.
Dos modos: 'zscore' (curvas SD) y 'percentil' (curvas P3-P97).
"""
import json
import math
import os
import tkinter as tk
from typing import Dict, List, Optional, Tuple

try:
    from anthro import lms_z
except ModuleNotFoundError:  # pragma: no cover - fallback para entornos sin anthro
    def lms_z(*args, **kwargs):
        raise RuntimeError("La dependencia 'anthro' no está disponible; la generación de gráficos no puede ejecutarse.")

DAYS_PER_MONTH = 30.4375

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "..", "..", "venv", "Lib", "site-packages", "anthro", "data")
if not os.path.isdir(_DATA_DIR):
    _DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "..", "..", ".venv", "Lib", "site-packages", "anthro", "data")
if not os.path.isdir(_DATA_DIR):
    _DATA_DIR = os.path.join(os.path.expanduser("~"),
                             "anaconda3", "Lib", "site-packages", "anthro", "data")
if not os.path.isdir(_DATA_DIR):
    _DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "..", "..", "src", "anthro_data")


_table_cache: Dict[str, dict] = {}


def _load_table(filename: str) -> dict:
    if filename not in _table_cache:
        path = os.path.join(_DATA_DIR, filename)
        with open(path, "r") as f:
            raw = json.load(f)
        result = {}
        for sex in ("M", "F"):
            tbl = raw.get(sex, {})
            keys = tbl.get("i", [])
            cols = {k: tbl[k] for k in tbl if k != "i"}
            rows = {}
            for idx, key in enumerate(keys):
                rows[key] = {k: cols[k][idx] for k in cols}
            result[sex] = rows
        _table_cache[filename] = result
    return _table_cache[filename]


def _build_table_from_tuples(sex_data: list) -> dict:
    """Convierte lista de tuplas (days, l, m, s) a dict keyed by days."""
    return {row[0]: {"l": row[1], "m": row[2], "s": row[3]} for row in sex_data}


def _get_lms(table: dict, sex: str, key: int) -> Optional[Tuple[float, float, float]]:
    sex_key = "M" if sex in ("M", "male") else "F"
    tbl = table.get(sex_key, {})
    row = tbl.get(key)
    if row:
        return row["l"], row["m"], row["s"]
    keys = sorted(tbl.keys())
    if not keys:
        return None
    if key <= keys[0]:
        r = tbl[keys[0]]
        return r["l"], r["m"], r["s"]
    if key >= keys[-1]:
        r = tbl[keys[-1]]
        return r["l"], r["m"], r["s"]
    for i in range(len(keys) - 1):
        if keys[i] <= key <= keys[i + 1]:
            f = (key - keys[i]) / (keys[i + 1] - keys[i]) if keys[i + 1] != keys[i] else 0
            r1 = tbl[keys[i]]
            r2 = tbl[keys[i + 1]]
            L = r1["l"] + f * (r2["l"] - r1["l"])
            M = r1["m"] + f * (r2["m"] - r1["m"])
            S = r1["s"] + f * (r2["s"] - r1["s"])
            return L, M, S
    return None


def _lms_value(L: float, M: float, S: float, z: float) -> float:
    if abs(L) < 1e-10:
        return M * math.exp(S * z)
    return M * math.pow(1 + L * S * z, 1 / L)


PERCENTILES_Z = {
    'p3': -1.881, 'p15': -1.036, 'p25': -0.674,
    'p50': 0.0, 'p75': 0.674, 'p85': 1.036, 'p97': 1.881,
}


def _generar_curvas(table: dict, sex: str, keys: list) -> dict:
    """Genera valores de curvas Z-score y percentiles para una lista de keys (días o cm)."""
    sd3neg, sd2neg, sd1neg, sd0, sd1, sd2, sd3 = [], [], [], [], [], [], []
    perc = {k: [] for k in PERCENTILES_Z}

    for k in keys:
        lms = _get_lms(table, sex, k)
        if lms is None:
            for lst in (sd3neg, sd2neg, sd1neg, sd0, sd1, sd2, sd3):
                lst.append(0)
            for pk in PERCENTILES_Z:
                perc[pk].append(0)
            continue
        L, M, S = lms
        sd3neg.append(_lms_value(L, M, S, -3))
        sd2neg.append(_lms_value(L, M, S, -2))
        sd1neg.append(_lms_value(L, M, S, -1))
        sd0.append(M)
        sd1.append(_lms_value(L, M, S, 1))
        sd2.append(_lms_value(L, M, S, 2))
        sd3.append(_lms_value(L, M, S, 3))
        for pk, pz in PERCENTILES_Z.items():
            perc[pk].append(_lms_value(L, M, S, pz))

    return {
        'sd3neg': sd3neg, 'sd2neg': sd2neg, 'sd1neg': sd1neg,
        'sd0': sd0, 'sd1': sd1, 'sd2': sd2, 'sd3': sd3,
        'percentiles': perc,
    }


def _dibujar_grafica(
    parent: tk.Widget,
    sex: str,
    x_vals: list,
    y_vals_curve: dict,
    paciente_x: float,
    paciente_y: float,
    z_paciente: float,
    nombre_paciente: str,
    titulo: str,
    eje_x_text: str,
    eje_y_text: str,
    modo: str = "zscore",
    x_formatter=None,
    percentil_paciente: float = None,
) -> tk.Canvas:
    """
    Función genérica para dibujar gráfica OMS en Canvas.

    modo: 'zscore' (curvas SD) o 'percentil' (curvas P3-P97).
    """
    W, H = 860, 540
    ml, mr, mt, mb = 75, 80, 50, 60
    pw = W - ml - mr
    ph = H - mt - mb

    canvas = tk.Canvas(parent, width=W, height=H, bg='#ffffff',
                       highlightthickness=1, highlightbackground='#cccccc')

    x_min, x_max = min(x_vals), max(x_vals)
    all_y = y_vals_curve.get('sd3', []) + y_vals_curve.get('sd3neg', [])
    all_y += y_vals_curve.get('percentiles', {}).get('p97', [])
    all_y += y_vals_curve.get('percentiles', {}).get('p3', [])
    all_y = [v for v in all_y if v > 0]
    all_y.append(paciente_y)
    if not all_y:
        canvas.create_text(W // 2, H // 2, text="Sin datos para graficar",
                           font=('Segoe UI', 12))
        return canvas

    y_min = min(all_y) - (max(all_y) - min(all_y)) * 0.1
    y_max = max(all_y) + (max(all_y) - min(all_y)) * 0.1

    def to_x(v):
        return ml + (v - x_min) / (x_max - x_min) * pw if x_max != x_min else ml + pw / 2

    def to_y(v):
        return mt + (1 - (v - y_min) / (y_max - y_min)) * ph if y_max != y_min else mt + ph / 2

    def fmt_x(v):
        return f"{v:.0f}" if x_formatter is None else x_formatter(v)

    canvas.create_rectangle(ml, mt, W - mr, H - mb, fill='#f9fbfd', outline='#dddddd')

    perc = y_vals_curve.get('percentiles', {})

    if modo == "zscore":
        sd3neg = y_vals_curve.get('sd3neg', [])
        sd2neg = y_vals_curve.get('sd2neg', [])
        sd1neg = y_vals_curve.get('sd1neg', [])
        sd0 = y_vals_curve.get('sd0', [])
        sd1 = y_vals_curve.get('sd1', [])
        sd2 = y_vals_curve.get('sd2', [])
        sd3 = y_vals_curve.get('sd3', [])

        # Zona verde: -2SD a +2SD
        if sd2 and sd2neg:
            pts = []
            for i in range(len(x_vals)):
                pts.append((to_x(x_vals[i]), to_y(sd2[i])))
            for i in range(len(x_vals) - 1, -1, -1):
                pts.append((to_x(x_vals[i]), to_y(sd2neg[i])))
            canvas.create_polygon([c for p in pts for c in p], fill='#d5f5e3', outline='', stipple='gray25')

        # Zona azul: -1SD a +1SD
        if sd1 and sd1neg:
            pts = []
            for i in range(len(x_vals)):
                pts.append((to_x(x_vals[i]), to_y(sd1[i])))
            for i in range(len(x_vals) - 1, -1, -1):
                pts.append((to_x(x_vals[i]), to_y(sd1neg[i])))
            canvas.create_polygon([c for p in pts for c in p], fill='#d6eaf8', outline='', stipple='gray25')

        def dibujar(datos, color, dash, ancho=1):
            coords = []
            for i in range(len(x_vals)):
                coords.extend([to_x(x_vals[i]), to_y(datos[i])])
            canvas.create_line(coords, fill=color, width=ancho, dash=dash, smooth=True)

        dibujar(sd3, '#c0392b', (8, 4), 1.5)
        dibujar(sd2, '#e74c3c', (4, 4), 1.5)
        dibujar(sd1, '#f39c12', (4, 4), 1.5)
        dibujar(sd0, '#2c3e50', (), 2.5)
        dibujar(sd1neg, '#f39c12', (4, 4), 1.5)
        dibujar(sd2neg, '#e74c3c', (4, 4), 1.5)
        dibujar(sd3neg, '#c0392b', (8, 4), 1.5)

        ultimo = len(x_vals) - 1
        z_labels = [
            ('Z=+3', sd3, '#c0392b'), ('Z=+2', sd2, '#e74c3c'), ('Z=+1', sd1, '#f39c12'),
            ('Z=0', sd0, '#2c3e50'), ('Z=-1', sd1neg, '#f39c12'), ('Z=-2', sd2neg, '#e74c3c'),
            ('Z=-3', sd3neg, '#c0392b'),
        ]
        for txt, vals, col in z_labels:
            if vals:
                y_et = to_y(vals[ultimo])
                canvas.create_text(W - mr + 8, y_et, text=txt, fill=col,
                                   font=('Segoe UI', 8, 'bold'), anchor=tk.W)

    else:
        perc_styles = {
            'p3': ('#8e44ad', (2, 4), 1), 'p15': ('#16a085', (6, 3), 1),
            'p25': ('#2980b9', (1, 3), 1), 'p50': ('#2c3e50', (), 2.5),
            'p75': ('#2980b9', (1, 3), 1), 'p85': ('#16a085', (6, 3), 1),
            'p97': ('#8e44ad', (2, 4), 1),
        }
        for pk, (color, dash, ancho) in perc_styles.items():
            vals = perc.get(pk, [])
            if not vals:
                continue
            coords = []
            for i in range(len(x_vals)):
                coords.extend([to_x(x_vals[i]), to_y(vals[i])])
            canvas.create_line(coords, fill=color, width=ancho, dash=dash, smooth=True)

        ultimo = len(x_vals) - 1
        perc_labels = [
            ('P97', perc.get('p97', []), '#8e44ad'),
            ('P85', perc.get('p85', []), '#16a085'),
            ('P75', perc.get('p75', []), '#2980b9'),
            ('P50', perc.get('p50', []), '#2c3e50'),
            ('P25', perc.get('p25', []), '#2980b9'),
            ('P15', perc.get('p15', []), '#16a085'),
            ('P3', perc.get('p3', []), '#8e44ad'),
        ]
        for txt, vals, col in perc_labels:
            if vals:
                y_et = to_y(vals[ultimo])
                canvas.create_text(W - mr + 8, y_et, text=txt, fill=col,
                                   font=('Segoe UI', 8, 'bold'), anchor=tk.W)

    # Punto del paciente
    px = to_x(paciente_x)
    py = to_y(paciente_y)
    canvas.create_line(px, mt, px, H - mb, fill='#95a5a6', width=1, dash=(3, 5))
    canvas.create_line(ml, py, W - mr, py, fill='#95a5a6', width=1, dash=(3, 5))

    color_punto = '#27ae60' if abs(z_paciente) <= 2 else '#e74c3c'
    canvas.create_oval(px - 8, py - 8, px + 8, py + 8, fill=color_punto, outline='white', width=2)
    if modo == "percentil" and percentil_paciente is not None:
        marca = f"P{percentil_paciente:.0f}"
    else:
        marca = f"Z={z_paciente:+.2f}"
    label_txt = f"{nombre_paciente}\n{paciente_y:.1f}\n{marca}" if nombre_paciente else f"{paciente_y:.1f}\n{marca}"
    canvas.create_text(px + 14, py - 14, text=label_txt, font=('Segoe UI', 8, 'bold'),
                       fill=color_punto, anchor=tk.W)

    # Ejes
    canvas.create_line(ml, H - mb, W - mr, H - mb, fill='#333', width=1.5)
    canvas.create_line(ml, mt, ml, H - mb, fill='#333', width=1.5)

    step = max(1, int((x_max - x_min) / 10))
    v = int(x_min // step * step)
    while v <= x_max:
        x = to_x(v)
        canvas.create_line(x, H - mb, x, H - mb + 4, fill='#333')
        canvas.create_text(x, H - mb + 15, text=fmt_x(v), font=('Segoe UI', 8), fill='#333')
        v += step
    canvas.create_text(W // 2, H - 10, text=eje_x_text, font=('Segoe UI', 10, 'bold'), fill='#333')

    y_step = max(1, int((y_max - y_min) / 10))
    yv = int(y_min // y_step * y_step)
    while yv <= y_max:
        y = to_y(yv)
        canvas.create_line(ml - 4, y, ml, y, fill='#333')
        canvas.create_text(ml - 8, y, text=f"{yv:.1f}", font=('Segoe UI', 8), fill='#333', anchor=tk.E)
        yv += y_step
    canvas.create_text(15, H // 2, text=eje_y_text, font=('Segoe UI', 10, 'bold'),
                       fill='#333', angle=90)

    sexo_txt = "Niño" if sex in ('M', 'male') else "Niña"
    modo_txt = "Z-Scores" if modo == "zscore" else "Percentiles"
    canvas.create_text(W // 2, 15, text=f"{titulo} — {sexo_txt} — {modo_txt} (WHO)",
                       font=('Segoe UI', 12, 'bold'), fill='#1a5276')

    # Leyenda
    ly = 32
    canvas.create_rectangle(W // 2 - 220, ly - 5, W // 2 + 220, ly + 75, fill='#f0f0f0', outline='#ccc')
    if modo == "zscore":
        canvas.create_text(W // 2 - 200, ly + 6, text="--- Z=+-1 (amarillo)", font=('Segoe UI', 7), fill='#f39c12')
        canvas.create_text(W // 2 - 200, ly + 18, text="--- Z=+-2 (rojo)", font=('Segoe UI', 7), fill='#e74c3c')
        canvas.create_text(W // 2 - 200, ly + 30, text="- - Z=+-3 (granate)", font=('Segoe UI', 7), fill='#c0392b')
        canvas.create_text(W // 2 - 200, ly + 42, text="─── Mediana (Z=0)", font=('Segoe UI', 7), fill='#2c3e50')
        canvas.create_text(W // 2 - 200, ly + 54, text="Zona normal (-2SD a +2SD)", font=('Segoe UI', 7), fill='#27ae60')
        canvas.create_text(W // 2 - 200, ly + 66, text="Zona -1SD a +1SD", font=('Segoe UI', 7), fill='#5dade2')
    else:
        canvas.create_text(W // 2 - 200, ly + 6, text="--  P3, P97", font=('Segoe UI', 7), fill='#8e44ad')
        canvas.create_text(W // 2 - 200, ly + 18, text="--  P15, P85", font=('Segoe UI', 7), fill='#16a085')
        canvas.create_text(W // 2 - 200, ly + 30, text="--  P25, P75", font=('Segoe UI', 7), fill='#2980b9')
        canvas.create_text(W // 2 - 200, ly + 42, text="─── P50 (mediana)", font=('Segoe UI', 7), fill='#2c3e50')

    canvas.create_text(W // 2 + 120, ly + 6, text="Paciente:", font=('Segoe UI', 7, 'bold'), fill='#333')
    canvas.create_text(W // 2 + 120, ly + 18, text=f"Z={z_paciente:+.2f}", font=('Segoe UI', 7, 'bold'), fill=color_punto)
    canvas.create_text(W // 2 + 120, ly + 34, text=f"{paciente_y:.1f}", font=('Segoe UI', 7), fill=color_punto)

    return canvas


def _edad_key_to_meses(key):
    return key / DAYS_PER_MONTH


# ── Funciones por indicador ─────────────────────────────────────────────────

def _z_to_percentil(z):
    from src.modules.who_anthro_calc import z_to_percentile
    return round(z_to_percentile(z), 1) if z is not None else None


def generar_grafica_lhfa(parent, sexo, edad_meses, talla_cm, nombre="", modo="zscore",
                         edad_dias=None, tipo_medicion="L"):
    table = _load_table("day_lhfa.json")
    sex_key = "M" if sexo in ("M", "male") else "F"
    tbl = table.get(sex_key, {})
    dias = sorted(tbl.keys())
    if not dias:
        c = tk.Canvas(parent, width=600, height=400, bg='white')
        c.create_text(300, 200, text="No hay datos disponibles", font=('Segoe UI', 12))
        return c
    dias = [d for d in dias if d <= 1826]
    meses = [d / DAYS_PER_MONTH for d in dias]
    curvas = _generar_curvas(table, sexo, dias)
    from anthro import compute as _compute
    age_d = int(edad_dias) if edad_dias is not None else int(edad_meses * DAYS_PER_MONTH)
    params = {'sex': 'male' if sexo in ('M', 'male') else 'female',
              'age_days': age_d, 'height_cm': talla_cm, 'measure': tipo_medicion}
    try:
        z = _compute(params).get('z_lhfa', 0)
    except Exception:
        z = 0
    return _dibujar_grafica(parent, sexo, meses, curvas, edad_meses, talla_cm,
                            z, nombre, "Longitud/Altura para Edad",
                            "Edad (meses)", "Longitud / Altura (cm)", modo,
                            percentil_paciente=_z_to_percentil(z))


def generar_grafica_wfa(parent, sexo, edad_meses, peso_kg, nombre="", modo="zscore",
                        edad_dias=None):
    table = _load_table("day_wfa.json")
    sex_key = "M" if sexo in ("M", "male") else "F"
    tbl = table.get(sex_key, {})
    dias = sorted(tbl.keys())
    if not dias:
        c = tk.Canvas(parent, width=600, height=400, bg='white')
        c.create_text(300, 200, text="No hay datos disponibles", font=('Segoe UI', 12))
        return c
    dias = [d for d in dias if d <= 1826]
    meses = [d / DAYS_PER_MONTH for d in dias]
    curvas = _generar_curvas(table, sexo, dias)
    from anthro import compute as _compute
    age_d = int(edad_dias) if edad_dias is not None else int(edad_meses * DAYS_PER_MONTH)
    params = {'sex': 'male' if sexo in ('M', 'male') else 'female',
              'age_days': age_d, 'weight_kg': peso_kg}
    try:
        z = _compute(params).get('z_wfa', 0)
    except Exception:
        z = 0
    return _dibujar_grafica(parent, sexo, meses, curvas, edad_meses, peso_kg,
                            z, nombre, "Peso para Edad",
                            "Edad (meses)", "Peso (kg)", modo,
                            percentil_paciente=_z_to_percentil(z))


def generar_grafica_wflh(parent, sexo, talla_cm, peso_kg, nombre="", modo="zscore", tipo_med="L"):
    fname = "day_wfl.json" if tipo_med == "L" else "day_wfh.json"
    table = _load_table(fname)
    sex_key = "M" if sexo in ("M", "male") else "F"
    tbl = table.get(sex_key, {})
    tallas = sorted(tbl.keys())
    if not tallas:
        c = tk.Canvas(parent, width=600, height=400, bg='white')
        c.create_text(300, 200, text="No hay datos disponibles", font=('Segoe UI', 12))
        return c
    tallas_filtradas = [t for t in tallas if t <= 150]
    curvas = _generar_curvas(table, sexo, tallas_filtradas)
    from anthro import compute as _compute
    params = {'sex': 'male' if sexo in ('M', 'male') else 'female',
              'age_days': 365, 'height_cm': talla_cm, 'weight_kg': peso_kg,
              'measure': tipo_med}
    try:
        z = _compute(params).get('z_wflh', 0)
    except Exception:
        z = 0
    return _dibujar_grafica(parent, sexo, tallas_filtradas, curvas, talla_cm, peso_kg,
                            z, nombre, "Peso para Longitud/Altura",
                            "Longitud / Altura (cm)", "Peso (kg)", modo,
                            percentil_paciente=_z_to_percentil(z))


def generar_grafica_bmi(parent, sexo, edad_meses, bmi_val, nombre="", modo="zscore",
                        edad_dias=None):
    table = _load_table("day_bmi.json")
    sex_key = "M" if sexo in ("M", "male") else "F"
    tbl = table.get(sex_key, {})
    dias = sorted(tbl.keys())
    if not dias:
        c = tk.Canvas(parent, width=600, height=400, bg='white')
        c.create_text(300, 200, text="No hay datos disponibles", font=('Segoe UI', 12))
        return c
    dias = [d for d in dias if d <= 1826]
    meses = [d / DAYS_PER_MONTH for d in dias]
    curvas = _generar_curvas(table, sexo, dias)
    from anthro import compute as _compute
    age_d = int(edad_dias) if edad_dias is not None else int(edad_meses * DAYS_PER_MONTH)
    params = {'sex': 'male' if sexo in ('M', 'male') else 'female',
              'age_days': age_d,
              'weight_kg': bmi_val, 'height_cm': 100}
    try:
        res = _compute(params)
        z = res.get('z_bmi', 0)
    except Exception:
        z = 0
    return _dibujar_grafica(parent, sexo, meses, curvas, edad_meses, bmi_val,
                            z, nombre, "IMC para Edad",
                            "Edad (meses)", "IMC (kg/m²)", modo,
                            percentil_paciente=_z_to_percentil(z))


def generar_grafica_hcfa(parent, sexo, edad_meses, pc_cm, nombre="", modo="zscore",
                         edad_dias=None):
    from src.modules.who_anthro_calc import _PC_LMS_BOYS, _PC_LMS_GIRLS
    table = {
        "M": _build_table_from_tuples(_PC_LMS_BOYS),
        "F": _build_table_from_tuples(_PC_LMS_GIRLS),
    }
    sex_key = "M" if sexo in ("M", "male") else "F"
    tbl = table.get(sex_key, {})
    dias = sorted(tbl.keys())
    if not dias:
        c = tk.Canvas(parent, width=600, height=400, bg='white')
        c.create_text(300, 200, text="No hay datos disponibles", font=('Segoe UI', 12))
        return c
    dias_filtrados = [d for d in dias if d <= 1826]
    meses = [d / DAYS_PER_MONTH for d in dias_filtrados]
    curvas = _generar_curvas(table, sexo, dias_filtrados)
    from src.modules.who_anthro_calc import calcular_z_pc
    age_d = int(edad_dias) if edad_dias is not None else int(edad_meses * DAYS_PER_MONTH)
    z = calcular_z_pc(sexo, age_d, pc_cm) or 0
    return _dibujar_grafica(parent, sexo, meses, curvas, edad_meses, pc_cm,
                            z, nombre, "Perímetro Cefálico para Edad",
                            "Edad (meses)", "Perímetro Cefálico (cm)", modo,
                            percentil_paciente=_z_to_percentil(z))


def generar_grafica_acfa(parent, sexo, edad_meses, muac_mm, nombre="", modo="zscore",
                         edad_dias=None):
    table = _load_table("day_acfa.json")
    sex_key = "M" if sexo in ("M", "male") else "F"
    tbl = table.get(sex_key, {})
    dias = sorted(tbl.keys())
    if not dias:
        c = tk.Canvas(parent, width=600, height=400, bg='white')
        c.create_text(300, 200, text="No hay datos disponibles", font=('Segoe UI', 12))
        return c
    dias = [d for d in dias if d <= 1826]
    meses = [d / DAYS_PER_MONTH for d in dias]
    curvas = _generar_curvas(table, sexo, dias)
    from anthro import compute as _compute
    age_d = int(edad_dias) if edad_dias is not None else int(edad_meses * DAYS_PER_MONTH)
    params = {'sex': 'male' if sexo in ('M', 'male') else 'female',
              'age_days': age_d, 'muac_mm': muac_mm}
    try:
        z = _compute(params).get('z_acfa', 0)
    except Exception:
        z = 0
    return _dibujar_grafica(parent, sexo, meses, curvas, edad_meses, muac_mm,
                            z, nombre, "MUAC para Edad",
                            "Edad (meses)", "MUAC (mm)", modo,
                            percentil_paciente=_z_to_percentil(z))


def generar_grafica_tsfa(parent, sexo, edad_meses, triceps_mm, nombre="", modo="zscore"):
    c = tk.Canvas(parent, width=600, height=400, bg='white')
    c.create_text(300, 180, text="Pliegue Tríceps para Edad", font=('Segoe UI', 14, 'bold'), fill='#1a5276')
    c.create_text(300, 210, text="No hay tablas LMS oficiales OMS", font=('Segoe UI', 10), fill='#888')
    c.create_text(300, 235, text=f"Valor medido: {triceps_mm:.1f} mm", font=('Segoe UI', 11, 'bold'))
    return c


def generar_grafica_ssfa(parent, sexo, edad_meses, subesc_mm, nombre="", modo="zscore"):
    c = tk.Canvas(parent, width=600, height=400, bg='white')
    c.create_text(300, 180, text="Pliegue Subescapular para Edad", font=('Segoe UI', 14, 'bold'), fill='#1a5276')
    c.create_text(300, 210, text="No hay tablas LMS oficiales OMS", font=('Segoe UI', 10), fill='#888')
    c.create_text(300, 235, text=f"Valor medido: {subesc_mm:.1f} mm", font=('Segoe UI', 11, 'bold'))
    return c


# ── Dispatcher ──────────────────────────────────────────────────────────────

CHART_MAP = {
    "lhfa": generar_grafica_lhfa,
    "wfa": generar_grafica_wfa,
    "wflh": generar_grafica_wflh,
    "bmi": generar_grafica_bmi,
    "hcfa": generar_grafica_hcfa,
    "acfa": generar_grafica_acfa,
    "tsfa": generar_grafica_tsfa,
    "ssfa": generar_grafica_ssfa,
}


# ── Backward compat ─────────────────────────────────────────────────────────

def generar_grafica_longitudaltura(parent, sexo, edad_meses, talla_cm, nombre="", **kwargs):
    return generar_grafica_lhfa(parent, sexo, edad_meses, talla_cm, nombre, modo="zscore")
