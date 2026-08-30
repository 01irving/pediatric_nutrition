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


def test_antropometria_sin_anthro(monkeypatch):
    """Verifica que la evaluación funciona sin la dependencia externa anthro."""
    import importlib
    import sys

    sys.modules.pop('src.modules.who_anthro_calc', None)
    monkeypatch.setitem(sys.modules, 'anthro', None)

    module = importlib.import_module('src.modules.who_anthro_calc')
    r = module.evaluar_antropometria(
        sexo='M',
        fecha_nacimiento=date(2024, 1, 1),
        fecha_visita=date(2024, 2, 1),
        peso_kg=8.5,
        talla_cm=68,
        pc_cm=40,
    )

    assert r['edad_dias'] == 31
    assert r['z_pc'] is not None
    assert r['errores'] == []


def test_paciente_seguimiento_versionado(tmp_path):
    """Verifica que cada seguimiento se conserva como registro separado con ID compuesto."""
    from src.database.db_manager import DatabaseManager
    from src.modules.patient_manager import PatientManager

    db = DatabaseManager(str(tmp_path / 'seguimiento.db'))
    db.connect()
    db.create_tables()

    pm = PatientManager(db)
    base_id = pm.agregar_paciente('Ana', date(2020, 1, 1), 'F', 12.0, 85.0)
    follow_id = pm.agregar_seguimiento(base_id, 'Ana', date(2020, 1, 1), 'F', 13.0, 86.0)

    assert pm.obtener_display_id(base_id) == str(base_id)
    assert pm.obtener_display_id(follow_id) == f'{base_id}.2'
    assert len(pm.listar_pacientes()) == 2


if __name__ == "__main__":
    test_edad_meses()
    test_imc()
    test_z_score_peso_normal()
    test_clasificacion_normal()
    test_clasificacion_talla()
    test_requerimientos()
    print("Todos los tests pasaron correctamente.")
