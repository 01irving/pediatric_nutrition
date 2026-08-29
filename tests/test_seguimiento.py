"""
Tests para el gestor de seguimiento de crecimiento.
"""
import os
import sys
import tempfile
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.database.db_manager import DatabaseManager
from src.modules.seguimiento_manager import SeguimientoManager, calcular_imc_local
from src.modules.patient_manager import PatientManager


def _tmp_db():
    path = os.path.join(tempfile.gettempdir(), 'seg_test_' + str(os.getpid()) + '.db')
    if os.path.exists(path):
        os.remove(path)
    db = DatabaseManager(path)
    db.connect()
    db.create_tables()
    return db, path


def test_calcular_imc_local():
    assert calcular_imc_local(10, 75) == round(10 / 0.75 ** 2, 2)
    assert calcular_imc_local(None, 75) is None
    assert calcular_imc_local(10, 0) is None


def test_seguimiento_crud():
    db, path = _tmp_db()
    try:
        pm = PatientManager(db)
        pid = pm.agregar_paciente("Niño Test", date(2025, 1, 1), 'M', 8.0, 62.0)
        mg = SeguimientoManager(db)

        s1 = mg.guardar(pid, date(2026, 1, 10), 8.5, 65.0, 'L', 41.0, 120, 'normal')
        s2 = mg.guardar(pid, date(2026, 6, 10), 9.8, 70.0, 'H', 44.0, 130, 'buena evolución')

        rows = mg.listar_por_paciente(pid)
        assert len(rows) == 2
        # IMC debe calcularse y guardarse
        assert rows[0]['imc'] == round(8.5 / 0.65 ** 2, 2)
        # Orden cronológico ascendente
        assert rows[0]['fecha_visita'] <= rows[1]['fecha_visita']

        mg.actualizar(s1, date(2026, 1, 10), 8.8, 65.0, 'L', 41.0, 120, 'actualizado')
        row = mg.obtener(s1)
        assert row['peso_kg'] == 8.8
        assert row['observaciones'] == 'actualizado'
        assert row['imc'] == round(8.8 / 0.65 ** 2, 2)

        mg.eliminar(s1)
        assert len(mg.listar_por_paciente(pid)) == 1

        # Eliminar el paciente debe borrar sus seguimientos (ON DELETE CASCADE)
        pm.eliminar_paciente(pid)
        assert mg.listar_por_paciente(pid) == []
    finally:
        db.close()
        os.remove(path)
