"""
Gestor de seguimiento de crecimiento.
Operaciones CRUD sobre la tabla seguimiento_crecimiento (historial evolutivo).
"""
from typing import List, Optional, Dict, Any
from datetime import date
from src.database.db_manager import DatabaseManager


def calcular_imc_local(peso_kg: Optional[float], talla_cm: Optional[float]) -> Optional[float]:
    """Calcula el IMC a partir de peso y talla."""
    if peso_kg is None or talla_cm is None or talla_cm <= 0:
        return None
    try:
        return round(peso_kg / ((talla_cm / 100.0) ** 2), 2)
    except (ZeroDivisionError, TypeError):
        return None


class SeguimientoManager:
    """Maneja las operaciones CRUD del seguimiento de crecimiento."""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def guardar(self, paciente_id: int, fecha_visita: date, peso_kg: Optional[float],
                talla_cm: Optional[float], tipo_medicion: str,
                pc_cm: Optional[float], muac_mm: Optional[float],
                observaciones: str, edad_meses_decimal: Optional[float] = None) -> int:
        """Guarda un registro de seguimiento de crecimiento."""
        imc = calcular_imc_local(peso_kg, talla_cm)
        cursor = self.db.execute(
            """INSERT INTO seguimiento_crecimiento
               (paciente_id, fecha_visita, peso_kg, talla_cm, tipo_medicion,
                pc_cm, muac_mm, imc, observaciones, edad_meses_decimal)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (paciente_id, fecha_visita.isoformat(), peso_kg, talla_cm, tipo_medicion,
             pc_cm, muac_mm, imc, observaciones, edad_meses_decimal)
        )
        self.db.commit()
        return cursor.lastrowid

    def actualizar(self, seguimiento_id: int, fecha_visita: date,
                   peso_kg: Optional[float], talla_cm: Optional[float],
                   tipo_medicion: str, pc_cm: Optional[float], muac_mm: Optional[float],
                   observaciones: str, edad_meses_decimal: Optional[float] = None):
        """Actualiza un registro de seguimiento de crecimiento existente."""
        imc = calcular_imc_local(peso_kg, talla_cm)
        self.db.execute(
            """UPDATE seguimiento_crecimiento SET
                fecha_visita = ?, peso_kg = ?, talla_cm = ?, tipo_medicion = ?,
                pc_cm = ?, muac_mm = ?, imc = ?, observaciones = ?,
                edad_meses_decimal = ?, updated_at = CURRENT_TIMESTAMP
             WHERE id = ?""",
            (fecha_visita.isoformat(), peso_kg, talla_cm, tipo_medicion,
             pc_cm, muac_mm, imc, observaciones, edad_meses_decimal, seguimiento_id)
        )
        self.db.commit()

    def obtener(self, seguimiento_id: int) -> Optional[Dict[str, Any]]:
        row = self.db.fetchone(
            "SELECT * FROM seguimiento_crecimiento WHERE id = ?", (seguimiento_id,)
        )
        return dict(row) if row else None

    def listar_por_paciente(self, paciente_id: int) -> List[Dict[str, Any]]:
        """Lista los registros de un paciente del más reciente al más antiguo."""
        rows = self.db.fetchall(
            "SELECT * FROM seguimiento_crecimiento WHERE paciente_id = ? "
            "ORDER BY fecha_visita ASC, id ASC",
            (paciente_id,)
        )
        return [dict(r) for r in rows]

    def eliminar(self, seguimiento_id: int):
        self.db.execute("DELETE FROM seguimiento_crecimiento WHERE id = ?", (seguimiento_id,))
        self.db.commit()
