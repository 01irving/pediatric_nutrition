"""
Gestor de Historia Médica.
Operaciones CRUD para el formulario de historia médica del paciente.
"""
from typing import List, Optional, Dict, Any
from datetime import date
from src.database.db_manager import DatabaseManager


class HistoriaMedicaManager:
    """Maneja las operaciones CRUD de historia médica."""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def guardar(self, paciente_id: int, fecha_evaluacion: date, evaluador: str,
                datos: Dict[str, str]) -> int:
        """Guarda un registro completo de historia médica."""
        cursor = self.db.execute(
            """INSERT INTO historia_medica
               (paciente_id, fecha_evaluacion, evaluador,
                motivo_consulta, diagnosticos_actuales,
                antecedentes_personales, antecedentes_familiares,
                cirugias_hospitalizaciones, medicamentos_suplementos,
                alergias_intolerancias, observaciones_medicas)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (paciente_id, fecha_evaluacion.isoformat(), evaluador,
             datos.get('motivo_consulta', ''),
             datos.get('diagnosticos_actuales', ''),
             datos.get('antecedentes_personales', ''),
             datos.get('antecedentes_familiares', ''),
             datos.get('cirugias_hospitalizaciones', ''),
             datos.get('medicamentos_suplementos', ''),
             datos.get('alergias_intolerancias', ''),
             datos.get('observaciones_medicas', ''))
        )
        self.db.commit()
        return cursor.lastrowid

    def obtener(self, historia_id: int) -> Optional[Dict[str, Any]]:
        """Obtiene un registro de historia médica por ID."""
        row = self.db.fetchone(
            "SELECT * FROM historia_medica WHERE id = ?", (historia_id,)
        )
        return dict(row) if row else None

    def listar_por_paciente(self, paciente_id: int) -> List[Dict[str, Any]]:
        """Lista todas las historias médicas de un paciente."""
        rows = self.db.fetchall(
            "SELECT * FROM historia_medica WHERE paciente_id = ? ORDER BY fecha_evaluacion DESC",
            (paciente_id,)
        )
        return [dict(r) for r in rows]

    def eliminar(self, historia_id: int):
        """Elimina un registro de historia médica."""
        self.db.execute("DELETE FROM historia_medica WHERE id = ?", (historia_id,))
        self.db.commit()

    def generar_texto_reporte(self, datos: Dict[str, Any]) -> str:
        """Genera un reporte en texto plano de la historia médica."""
        lineas = [
            "=" * 65,
            "   HISTORIA MÉDICA DEL PACIENTE",
            "=" * 65,
            "",
            f"  Fecha de evaluación:  {datos.get('fecha_evaluacion', '')}",
            f"  Evaluador:            {datos.get('evaluador', '')}",
            "",
            "-" * 65,
            "  MOTIVO DE CONSULTA",
            "-" * 65,
            f"  {datos.get('motivo_consulta', '')}",
            "",
            "-" * 65,
            "  DIAGNÓSTICOS ACTUALES",
            "-" * 65,
            f"  {datos.get('diagnosticos_actuales', '')}",
            "",
            "-" * 65,
            "  ANTECEDENTES PERSONALES PATOLÓGICOS",
            "-" * 65,
            f"  {datos.get('antecedentes_personales', '')}",
            "",
            "-" * 65,
            "  ANTECEDENTES FAMILIARES RELEVANTES",
            "-" * 65,
            f"  {datos.get('antecedentes_familiares', '')}",
            "",
            "-" * 65,
            "  CIRUGÍAS, TRAUMATISMOS U HOSPITALIZACIONES",
            "-" * 65,
            f"  {datos.get('cirugias_hospitalizaciones', '')}",
            "",
            "-" * 65,
            "  MEDICAMENTOS Y SUPLEMENTOS ACTUALES",
            "-" * 65,
            f"  {datos.get('medicamentos_suplementos', '')}",
            "",
            "-" * 65,
            "  ALERGIAS E INTOLERANCIAS ALIMENTARIAS",
            "-" * 65,
            f"  {datos.get('alergias_intolerancias', '')}",
            "",
            "-" * 65,
            "  OBSERVACIONES MÉDICAS ADICIONALES",
            "-" * 65,
            f"  {datos.get('observaciones_medicas', '')}",
            "",
            "=" * 65,
        ]
        return "\n".join(lineas)
