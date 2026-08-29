"""
Tests para los módulos de cálculos nutricionales.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from datetime import date
from src.modules.nutrition_calcs import (
    calcular_edad_meses,
    calcular_imc,
    calcular_z_score_peso_edad,
    calcular_z_score_talla_edad,
    clasificar_estado_nutricional,
    clasificar_talla_edad,
    calcular_requerimientos_caloricos,
)


def test_pc_edad_z_anthro():
    """Verifica Z de perímetro cefálico contra referencia WHO Anthro (caso -0.75)."""
    from src.modules.who_anthro_calc import evaluar_antropometria
    r = evaluar_antropometria(
        sexo='M', fecha_nacimiento=date(2026, 5, 20), fecha_visita=date(2026, 8, 29),
        pc_cm=40,
    )
    assert r['edad_dias'] == 101
    assert r['z_pc'] == -0.75


def test_edad_meses():
    nac = date(2024, 1, 1)
    eval_ = date(2025, 1, 1)
    assert round(calcular_edad_meses(nac, eval_)) == 12


def test_imc():
    assert calcular_imc(10, 75) == round(10 / (0.75 ** 2), 2)


def test_z_score_peso_normal():
    z = calcular_z_score_peso_edad(10.9, 12, 'M')
    assert -0.5 < z < 0.5


def test_clasificacion_normal():
    assert clasificar_estado_nutricional(0.0) == "Normal"
    assert "Desnutrición" in clasificar_estado_nutricional(-3.5)
    assert "Obesidad" in clasificar_estado_nutricional(3.5)


def test_clasificacion_talla():
    assert clasificar_talla_edad(0.0) == "Normal"
    assert "baja" in clasificar_talla_edad(-3.0).lower()


def test_requerimientos():
    req = calcular_requerimientos_caloricos(24, 12, 85)
    assert req['calorias_kcal'] > 0
    assert req['proteinas_g'] > 0
    assert req['grasas_g'] > 0
    assert req['carbohidratos_g'] > 0


if __name__ == "__main__":
    test_edad_meses()
    test_imc()
    test_z_score_peso_normal()
    test_clasificacion_normal()
    test_clasificacion_talla()
    test_requerimientos()
    print("Todos los tests pasaron correctamente.")
