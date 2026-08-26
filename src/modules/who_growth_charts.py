"""
Gráficas de crecimiento OMS usando las tablas LMS de la librería 'anthro'.
Genera gráficas con tkinter Canvas mostrando curvas Z-score y percentiles.
"""
import json
import math
import os
import tkinter as tk
from typing import Dict, List, Optional, Tuple

from anthro import lms_z

DAYS_PER_MONTH = 30.4375

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "..", "..", "venv", "Lib", "site-packages", "anthro", "data")
if not os.path.isdir(_DATA_DIR):
    _DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "..", "..", ".venv", "Lib", "site-packages", "anthro", "data")
if not os.path.isdir(_DATA_DIR):
    _DATA_DIR = os.path.join(os.path.expanduser("~"),
                             "anaconda3", "Lib", "site-packages", "anthro", "data")


_table_cache: Dict[str, dict] = {}


def _load_table(filename: str) -> dict:
    """Load JSON table and convert columnar arrays to dict keyed by index."""
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


def _get_lms(table: dict, sex: str, age_days: int) -> Optional[Tuple[float, float, float]]:
    sex_key = "M" if sex in ("M", "male") else "F"
    tbl = table.get(sex_key, {})
    row = tbl.get(age_days)
    if row:
        return row["l"], row["m"], row["s"]
    days = sorted(tbl.keys())
    if not days:
        return None
    if age_days <= days[0]:
        r = tbl[days[0]]
        return r["l"], r["m"], r["s"]
    if age_days >= days[-1]:
        r = tbl[days[-1]]
        return r["l"], r["m"], r["s"]
    for i in range(len(days) - 1):
        if days[i] <= age_days <= days[i + 1]:
            f = (age_days - days[i]) / (days[i + 1] - days[i])
            r1 = tbl[days[i]]
            r2 = tbl[days[i + 1]]
            L = r1["l"] + f * (r2["l"] - r1["l"])
            M = r1["m"] + f * (r2["m"] - r1["m"])
            S = r1["s"] + f * (r2["s"] - r1["s"])
            return L, M, S
    return None


def _get_lms_height(table: dict, sex: str, height_cm: float) -> Optional[Tuple[float, float, float]]:
    sex_key = "M" if sex in ("M", "male") else "F"
    tbl = table.get(sex_key, {})
    heights = sorted(tbl.keys())
    if not heights:
        return None
    if height_cm <= heights[0]:
        r = tbl[heights[0]]
        return r["l"], r["m"], r["s"]
    if height_cm >= heights[-1]:
        r = tbl[heights[-1]]
        return r["l"], r["m"], r["s"]
    for i in range(len(heights) - 1):
        if heights[i] <= height_cm <= heights[i + 1]:
            f = (height_cm - heights[i]) / (heights[i + 1] - heights[i])
            r1 = tbl[heights[i]]
            r2 = tbl[heights[i + 1]]
            L = r1["l"] + f * (r2["l"] - r1["l"])
            M = r1["m"] + f * (r2["m"] - r1["m"])
            S = r1["s"] + f * (r2["s"] - r1["s"])
            return L, M, S
    return None


def _lms_value(L: float, M: float, S: float, z: float) -> float:
    """Valor LMS = M * (1 + L*S*z)^(1/L)."""
    if abs(L) < 1e-10:
        return M * math.exp(S * z)
    return M * math.pow(1 + L * S * z, 1 / L)


PERCENTILES_Z = {
    'p3':   -1.881,
    'p15':  -1.036,
    'p25':  -0.674,
    'p50':   0.0,
    'p75':   0.674,
    'p85':   1.036,
    'p97':   1.881,
}


def generar_valores_curva(table: dict, sex: str, dias_min: int, dias_max: int, paso: int) -> Dict[str, List]:
    sex_key = "M" if sex in ("M", "male") else "F"
    tbl = table.get(sex_key, {})
    dias_disponibles = sorted(tbl.keys())
    dias_seleccionados = [d for d in dias_disponibles if dias_min <= d <= dias_max]
    if not dias_seleccionados:
        dias_seleccionados = dias_disponibles[:]

    meses = [d / DAYS_PER_MONTH for d in dias_seleccionados]
    sd3neg, sd2neg, sd1neg, sd0, sd1, sd2, sd3 = [], [], [], [], [], [], []
    perc = {k: [] for k in PERCENTILES_Z}

    for d in dias_seleccionados:
        row = tbl[d]
        L, M, S = row["l"], row["m"], row["s"]
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
        'meses': meses, 'dias': dias_seleccionados,
        'sd3neg': sd3neg, 'sd2neg': sd2neg, 'sd1neg': sd1neg,
        'sd0': sd0, 'sd1': sd1, 'sd2': sd2, 'sd3': sd3,
        'percentiles': perc,
    }


def generar_grafica_longitudaltura(
    parent: tk.Widget, sexo: str, edad_meses: float,
    longitud_cm: float, nombre_paciente: str = "", **kwargs
) -> tk.Canvas:
    table = _load_table("day_lhfa.json")
    sex_key = "M" if sexo in ("M", "male") else "F"
    tbl = table.get(sex_key, {})
    dias_disponibles = sorted(tbl.keys())
    if not dias_disponibles:
        canvas = tk.Canvas(parent, width=600, height=400, bg='white')
        canvas.create_text(300, 200, text="No hay datos LMS disponibles", font=('Segoe UI', 12))
        return canvas

    dias_min = max(dias_disponibles[0], 0)
    dias_max = min(dias_disponibles[-1], 1826)
    curva = generar_valores_curva(table, sexo, dias_min, dias_max, 1)

    meses = curva['meses']
    sd3neg, sd2neg, sd1neg = curva['sd3neg'], curva['sd2neg'], curva['sd1neg']
    sd0, sd1, sd2, sd3 = curva['sd0'], curva['sd1'], curva['sd2'], curva['sd3']
    perc = curva['percentiles']

    W, H = 860, 520
    margin_l, margin_r, margin_t, margin_b = 75, 80, 50, 60
    plot_w = W - margin_l - margin_r
    plot_h = H - margin_t - margin_b

    canvas = tk.Canvas(parent, width=W, height=H, bg='#ffffff', highlightthickness=1, highlightbackground='#cccccc')

    x_min, x_max = min(meses), max(meses)
    all_vals = sd3neg + sd3 + [longitud_cm]
    y_min = min(all_vals) - 3
    y_max = max(all_vals) + 3

    def to_x(m):
        return margin_l + (m - x_min) / (x_max - x_min) * plot_w

    def to_y(v):
        return margin_t + (1 - (v - y_min) / (y_max - y_min)) * plot_h

    canvas.create_rectangle(margin_l, margin_t, W - margin_r, H - margin_b, fill='#f9fbfd', outline='#dddddd')

    # Zona -2SD a +2SD (verde)
    pts_verde = []
    for i in range(len(meses)):
        pts_verde.append((to_x(meses[i]), to_y(sd2[i])))
    for i in range(len(meses) - 1, -1, -1):
        pts_verde.append((to_x(meses[i]), to_y(sd2neg[i])))
    flat = [c for p in pts_verde for c in p]
    canvas.create_polygon(flat, fill='#d5f5e3', outline='', stipple='gray25')

    # Zona -1SD a +1SD (azul)
    pts_azul = []
    for i in range(len(meses)):
        pts_azul.append((to_x(meses[i]), to_y(sd1[i])))
    for i in range(len(meses) - 1, -1, -1):
        pts_azul.append((to_x(meses[i]), to_y(sd1neg[i])))
    flat2 = [c for p in pts_azul for c in p]
    canvas.create_polygon(flat2, fill='#d6eaf8', outline='', stipple='gray25')

    def dibujar_curva(datos, color, dash, ancho=1):
        coords = []
        for i in range(len(meses)):
            coords.extend([to_x(meses[i]), to_y(datos[i])])
        canvas.create_line(coords, fill=color, width=ancho, dash=dash, smooth=True)

    dibujar_curva(sd3, '#c0392b', (8, 4), 1.5)
    dibujar_curva(sd2, '#e74c3c', (4, 4), 1.5)
    dibujar_curva(sd1, '#f39c12', (4, 4), 1.5)
    dibujar_curva(sd0, '#2c3e50', (), 2.5)
    dibujar_curva(sd1neg, '#f39c12', (4, 4), 1.5)
    dibujar_curva(sd2neg, '#e74c3c', (4, 4), 1.5)
    dibujar_curva(sd3neg, '#c0392b', (8, 4), 1.5)

    perc_colors = {
        'p3': '#8e44ad', 'p15': '#16a085', 'p25': '#2980b9',
        'p75': '#2980b9', 'p85': '#16a085', 'p97': '#8e44ad',
    }
    perc_styles = {
        'p3': (2, 4), 'p15': (6, 3), 'p25': (1, 3),
        'p75': (1, 3), 'p85': (6, 3), 'p97': (2, 4),
    }
    for pk in ('p3', 'p15', 'p25', 'p75', 'p85', 'p97'):
        dibujar_curva(perc[pk], perc_colors[pk], perc_styles[pk], 1)

    ultimo = len(meses) - 1
    z_labels = [
        ('Z=+3', sd3, '#c0392b'), ('Z=+2', sd2, '#e74c3c'), ('Z=+1', sd1, '#f39c12'),
        ('Z=0', sd0, '#2c3e50'), ('Z=-1', sd1neg, '#f39c12'), ('Z=-2', sd2neg, '#e74c3c'),
        ('Z=-3', sd3neg, '#c0392b'),
    ]
    for txt, vals, col in z_labels:
        y_et = to_y(vals[ultimo])
        canvas.create_text(W - margin_r + 8, y_et, text=txt, fill=col, font=('Segoe UI', 8, 'bold'), anchor=tk.W)

    # Líneas guía
    px = to_x(edad_meses)
    py = to_y(longitud_cm)
    canvas.create_line(px, margin_t, px, H - margin_b, fill='#95a5a6', width=1, dash=(3, 5))
    canvas.create_line(margin_l, py, W - margin_r, py, fill='#95a5a6', width=1, dash=(3, 5))

    # Calcular Z-score del paciente
    from anthro import compute as _compute
    params = {'sex': 'male' if sexo in ('M', 'male') else 'female',
              'age_days': int(edad_meses * DAYS_PER_MONTH), 'height_cm': longitud_cm}
    try:
        res = _compute(params)
        z_paciente = res.get('z_lhfa', 0)
    except Exception:
        z_paciente = 0

    color_punto = '#27ae60' if abs(z_paciente) <= 2 else '#e74c3c'
    canvas.create_oval(px - 8, py - 8, px + 8, py + 8, fill=color_punto, outline='white', width=2)
    label_txt = f"{nombre_paciente}\n{longitud_cm} cm\nZ={z_paciente:+.2f}" if nombre_paciente else f"{longitud_cm} cm\nZ={z_paciente:+.2f}"
    canvas.create_text(px + 14, py - 14, text=label_txt, font=('Segoe UI', 8, 'bold'), fill=color_punto, anchor=tk.W)

    # Ejes
    canvas.create_line(margin_l, H - margin_b, W - margin_r, H - margin_b, fill='#333', width=1.5)
    canvas.create_line(margin_l, margin_t, margin_l, H - margin_b, fill='#333', width=1.5)

    for m in range(int(x_min), int(x_max) + 1, 6):
        x = to_x(m)
        canvas.create_line(x, H - margin_b, x, H - margin_b + 4, fill='#333')
        canvas.create_text(x, H - margin_b + 15, text=str(m), font=('Segoe UI', 8), fill='#333')
    canvas.create_text(W // 2, H - 10, text="Edad (meses)", font=('Segoe UI', 10, 'bold'), fill='#333')

    paso = max(1, int((y_max - y_min) / 10))
    v = int(y_min // paso * paso)
    while v <= y_max:
        y = to_y(v)
        canvas.create_line(margin_l - 4, y, margin_l, y, fill='#333')
        canvas.create_text(margin_l - 8, y, text=f"{v:.0f}", font=('Segoe UI', 8), fill='#333', anchor=tk.E)
        v += paso
    canvas.create_text(15, H // 2, text="Longitud / Altura (cm)", font=('Segoe UI', 10, 'bold'), fill='#333', angle=90)

    sexo_txt = "Niño" if sexo in ('M', 'male') else "Niña"
    canvas.create_text(W // 2, 15, text=f"Longitud/Altura para Edad — {sexo_txt} (WHO Child Growth Standards)",
                       font=('Segoe UI', 12, 'bold'), fill='#1a5276')

    # Leyenda
    ly = 32
    canvas.create_rectangle(W // 2 - 220, ly - 5, W // 2 + 220, ly + 75, fill='#f0f0f0', outline='#ccc')
    canvas.create_text(W // 2 - 200, ly + 6, text="--- Z=+-1 (amarillo)", font=('Segoe UI', 7), fill='#f39c12')
    canvas.create_text(W // 2 - 200, ly + 18, text="--- Z=+-2 (rojo)", font=('Segoe UI', 7), fill='#e74c3c')
    canvas.create_text(W // 2 - 200, ly + 30, text="- - Z=+-3 (granate)", font=('Segoe UI', 7), fill='#c0392b')
    canvas.create_text(W // 2 - 200, ly + 42, text="─── Mediana (Z=0)", font=('Segoe UI', 7), fill='#2c3e50')
    canvas.create_text(W // 2 - 200, ly + 54, text="Zona normal", font=('Segoe UI', 7), fill='#27ae60')
    canvas.create_text(W // 2 - 200, ly + 66, text="Zona -1SD a +1SD", font=('Segoe UI', 7), fill='#5dade2')

    canvas.create_text(W // 2 - 30, ly + 6, text="Percentiles:", font=('Segoe UI', 7, 'bold'), fill='#333')
    canvas.create_text(W // 2 - 30, ly + 18, text="--  P3, P97", font=('Segoe UI', 7), fill='#8e44ad')
    canvas.create_text(W // 2 - 30, ly + 30, text="--  P15, P85", font=('Segoe UI', 7), fill='#16a085')
    canvas.create_text(W // 2 - 30, ly + 42, text="--  P25, P75", font=('Segoe UI', 7), fill='#2980b9')

    canvas.create_text(W // 2 + 120, ly + 6, text="Paciente:", font=('Segoe UI', 7, 'bold'), fill='#333')
    canvas.create_text(W // 2 + 120, ly + 18, text=f"Z={z_paciente:+.2f}", font=('Segoe UI', 7, 'bold'), fill=color_punto)
    canvas.create_text(W // 2 + 120, ly + 34, text=f"{longitud_cm} cm", font=('Segoe UI', 7), fill=color_punto)

    return canvas
