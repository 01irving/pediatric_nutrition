"""
Gestor de resultados de laboratorio.
Operaciones CRUD para pruebas de laboratorio asociadas a un paciente.
"""
from typing import List, Optional, Dict, Any
from datetime import date
from src.database.db_manager import DatabaseManager


class LaboratorioManager:
    """Maneja las operaciones CRUD de resultados de laboratorio."""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def guardar(self, paciente_id: int, fecha_toma: date, tipo_prueba: str,
                valor: str, unidad: str, edad_meses: Optional[float],
                clasificacion: str, rango_referencia: str,
                observaciones: str = "") -> int:
        """Guarda un resultado de laboratorio."""
        cursor = self.db.execute(
            """INSERT INTO laboratorios
               (paciente_id, fecha_toma, tipo_prueba, valor, unidad,
                edad_meses_al_momento, resultado_clasificacion,
                rango_referencia, observaciones)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (paciente_id, fecha_toma.isoformat(), tipo_prueba, valor, unidad,
             edad_meses, clasificacion, rango_referencia, observaciones)
        )
        self.db.commit()
        return cursor.lastrowid

    def obtener(self, resultado_id: int) -> Optional[Dict[str, Any]]:
        row = self.db.fetchone("SELECT * FROM laboratorios WHERE id = ?", (resultado_id,))
        return dict(row) if row else None

    def listar_por_paciente(self, paciente_id: int) -> List[Dict[str, Any]]:
        """Lista todos los resultados de laboratorio de un paciente, del más reciente al más antiguo."""
        rows = self.db.fetchall(
            "SELECT * FROM laboratorios WHERE paciente_id = ? ORDER BY fecha_toma DESC, id DESC",
            (paciente_id,)
        )
        return [dict(r) for r in rows]

    def eliminar(self, resultado_id: int):
        self.db.execute("DELETE FROM laboratorios WHERE id = ?", (resultado_id,))
        self.db.commit()
