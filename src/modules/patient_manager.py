"""
Gestor de pacientes: operaciones CRUD sobre la tabla de pacientes.
"""
from typing import List, Optional, Dict, Any
from datetime import date
from src.database.db_manager import DatabaseManager


class PatientManager:
    """Maneja las operaciones CRUD de los pacientes."""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def agregar_paciente(
        self, nombre: str,
        fecha_nacimiento: date, sexo: str,
        peso_kg: float = 0.0, talla_cm: float = 0.0
    ) -> int:
        cursor = self.db.execute(
            """INSERT INTO pacientes (parent_id, version, nombre, fecha_nacimiento, sexo, peso_kg, talla_cm)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (None, 1, nombre, fecha_nacimiento.isoformat(), sexo, peso_kg, talla_cm)
        )
        self.db.commit()
        return cursor.lastrowid

    def agregar_seguimiento(
        self, paciente_id: int, nombre: str,
        fecha_nacimiento: date, sexo: str,
        peso_kg: float = 0.0, talla_cm: float = 0.0
    ) -> int:
        base = self.obtener_paciente(paciente_id)
        if not base:
            raise ValueError(f"Paciente {paciente_id} no existe")

        version = self.db.fetchone(
            "SELECT COALESCE(MAX(version), 1) + 1 FROM pacientes WHERE parent_id = ?",
            (paciente_id,),
        )[0]

        cursor = self.db.execute(
            """INSERT INTO pacientes (parent_id, version, nombre, fecha_nacimiento, sexo, peso_kg, talla_cm)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (paciente_id, version, nombre, fecha_nacimiento.isoformat(), sexo, peso_kg, talla_cm)
        )
        self.db.commit()
        return cursor.lastrowid

    def obtener_display_id(self, paciente_id: int) -> str:
        paciente = self.obtener_paciente(paciente_id)
        if not paciente:
            return str(paciente_id)
        if paciente.get('parent_id') is None or paciente.get('parent_id') == paciente.get('id'):
            return str(paciente['id'])
        return f"{paciente['parent_id']}.{paciente['version']}"

    def obtener_paciente(self, paciente_id: int) -> Optional[Dict[str, Any]]:
        row = self.db.fetchone(
            "SELECT * FROM pacientes WHERE id = ?", (paciente_id,)
        )
        return dict(row) if row else None

    def listar_pacientes(self) -> List[Dict[str, Any]]:
        rows = self.db.fetchall(
            "SELECT * FROM pacientes ORDER BY COALESCE(parent_id, id), version, nombre"
        )
        return [dict(r) for r in rows]

    def buscar_pacientes(self, termino: str) -> List[Dict[str, Any]]:
        rows = self.db.fetchall(
            """SELECT * FROM pacientes
               WHERE nombre LIKE ?
               ORDER BY nombre""",
            (f"%{termino}%",)
        )
        return [dict(r) for r in rows]

    def actualizar_paciente(
        self, paciente_id: int, nombre: str,
        fecha_nacimiento: date, sexo: str,
        peso_kg: float, talla_cm: float
    ):
        self.db.execute(
            """UPDATE pacientes
               SET nombre=?, fecha_nacimiento=?, sexo=?,
                   peso_kg=?, talla_cm=?, updated_at=CURRENT_TIMESTAMP
               WHERE id=?""",
            (nombre, fecha_nacimiento.isoformat(), sexo, peso_kg, talla_cm, paciente_id)
        )
        self.db.commit()

    def eliminar_paciente(self, paciente_id: int):
        self.db.execute("DELETE FROM pacientes WHERE id=?", (paciente_id,))
        self.db.commit()
