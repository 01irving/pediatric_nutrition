"""
Gestor de evaluaciones antropométricas.
Operaciones CRUD para evaluaciones (mediciones + z-scores) asociadas a un paciente.
"""
from typing import List, Optional, Dict, Any
from datetime import date
from src.database.db_manager import DatabaseManager


class AntropometriaManager:
    """Maneja las operaciones CRUD de evaluaciones antropométricas."""

    def __init__(self, db: DatabaseManager):
        self.db = db
        self._columnas = [
            "peso_kg", "talla_cm", "tipo_medicion", "edema", "pc_cm", "muac_mm",
            "pliegue_triceps_mm", "pliegue_subescapular_mm", "edad_dias",
            "edad_meses_completos", "edad_meses_decimal",
            "z_lhfa", "perc_lhfa", "clasif_lhfa", "flag_lhfa",
            "z_wfa", "perc_wfa", "clasif_wfa", "flag_wfa",
            "z_wflh", "perc_wflh", "clasif_wflh", "flag_wflh",
            "z_bmi", "perc_bmi", "clasif_bmi", "flag_bmi",
            "z_pc", "perc_pc", "clasif_pc",
            "z_acfa", "perc_acfa", "clasif_muac", "flag_acfa",
            "z_tsfa", "perc_tsfa", "clasif_tsfa",
            "z_ssfa", "perc_ssfa", "clasif_ssfa",
        ]

    def guardar(self, paciente_id: int, fecha_visita: date, evaluador: str,
                campos: Dict[str, Any]) -> int:
        """Guarda (o actualiza si existe) una evaluación para una fecha de visita.

        campos debe contener las claves de _columnas (todas opcionales excepto fecha).
        Si ya existe una evaluación del paciente en esa fecha, la actualiza y devuelve su id.
        """
        fecha_iso = fecha_visita.isoformat()
        existente = self.db.fetchone(
            "SELECT id FROM evaluaciones_antropometricas "
            "WHERE paciente_id = ? AND fecha_visita = ?",
            (paciente_id, fecha_iso)
        )
        cols = [c for c in self._columnas if c in campos]

        if existente:
            sets = ", ".join(f"{c} = ?" for c in cols)
            sets += ", updated_at = CURRENT_TIMESTAMP"
            params = [campos[c] for c in cols] + [existente["id"]]
            self.db.execute(
                f"UPDATE evaluaciones_antropometricas SET {sets} WHERE id = ?",
                params
            )
            self.db.commit()
            return existente["id"]

        insert_cols = ["paciente_id", "fecha_visita", "evaluador"] + cols
        placeholders = ", ".join("?" for _ in insert_cols)
        params = [paciente_id, fecha_iso, evaluador] + [campos.get(c) for c in cols]
        cursor = self.db.execute(
            f"INSERT INTO evaluaciones_antropometricas ({', '.join(insert_cols)}) "
            f"VALUES ({placeholders})",
            params
        )
        self.db.commit()
        return cursor.lastrowid

    def obtener(self, evaluacion_id: int) -> Optional[Dict[str, Any]]:
        row = self.db.fetchone(
            "SELECT * FROM evaluaciones_antropometricas WHERE id = ?", (evaluacion_id,))
        return dict(row) if row else None

    def obtener_por_fecha(self, paciente_id: int, fecha_visita: date) -> Optional[Dict[str, Any]]:
        row = self.db.fetchone(
            "SELECT * FROM evaluaciones_antropometricas "
            "WHERE paciente_id = ? AND fecha_visita = ?",
            (paciente_id, fecha_visita.isoformat())
        )
        return dict(row) if row else None

    def listar_por_paciente(self, paciente_id: int) -> List[Dict[str, Any]]:
        rows = self.db.fetchall(
            "SELECT * FROM evaluaciones_antropometricas "
            "WHERE paciente_id = ? ORDER BY fecha_visita DESC, id DESC",
            (paciente_id,)
        )
        return [dict(r) for r in rows]

    def eliminar(self, evaluacion_id: int):
        self.db.execute(
            "DELETE FROM evaluaciones_antropometricas WHERE id = ?", (evaluacion_id,))
        self.db.commit()
