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
        self, nombre: str, apellido: str,
        fecha_nacimiento: date, sexo: str,
        peso_kg: float = 0.0, talla_cm: float = 0.0
    ) -> int:
        cursor = self.db.execute(
            """INSERT INTO pacientes (nombre, apellido, fecha_nacimiento, sexo, peso_kg, talla_cm)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (nombre, apellido, fecha_nacimiento.isoformat(), sexo, peso_kg, talla_cm)
        )
        self.db.commit()
        return cursor.lastrowid

    def obtener_paciente(self, paciente_id: int) -> Optional[Dict[str, Any]]:
        row = self.db.fetchone(
            "SELECT * FROM pacientes WHERE id = ?", (paciente_id,)
        )
        return dict(row) if row else None

    def listar_pacientes(self) -> List[Dict[str, Any]]:
        rows = self.db.fetchall(
            "SELECT * FROM pacientes ORDER BY apellido, nombre"
        )
        return [dict(r) for r in rows]

    def buscar_pacientes(self, termino: str) -> List[Dict[str, Any]]:
        rows = self.db.fetchall(
            """SELECT * FROM pacientes
               WHERE nombre LIKE ? OR apellido LIKE ?
               ORDER BY apellido, nombre""",
            (f"%{termino}%", f"%{termino}%")
        )
        return [dict(r) for r in rows]

    def actualizar_paciente(
        self, paciente_id: int, nombre: str, apellido: str,
        fecha_nacimiento: date, sexo: str,
        peso_kg: float, talla_cm: float
    ):
        self.db.execute(
            """UPDATE pacientes
               SET nombre=?, apellido=?, fecha_nacimiento=?, sexo=?,
                   peso_kg=?, talla_cm=?, updated_at=CURRENT_TIMESTAMP
               WHERE id=?""",
            (nombre, apellido, fecha_nacimiento.isoformat(), sexo, peso_kg, talla_cm, paciente_id)
        )
        self.db.commit()

    def eliminar_paciente(self, paciente_id: int):
        self.db.execute("DELETE FROM pacientes WHERE id=?", (paciente_id,))
        self.db.commit()

    def agregar_registro_crecimiento(
        self, paciente_id: int, fecha: date,
        peso_kg: float, talla_cm: float,
        imc: float = 0.0, perimetro_cefalico: float = 0.0,
        perimetro_brazo: float = 0.0, pliegue_cutaneo: float = 0.0,
        observaciones: str = ""
    ) -> int:
        cursor = self.db.execute(
            """INSERT INTO registros_crecimiento
               (paciente_id, fecha, peso_kg, talla_cm, imc,
                perimetro_cefalico_cm, perimetro_brazo_cm, pliegue_cutaneo_mm, observaciones)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (paciente_id, fecha.isoformat(), peso_kg, talla_cm, imc,
             perimetro_cefalico, perimetro_brazo, pliegue_cutaneo, observaciones)
        )
        self.db.commit()
        return cursor.lastrowid

    def historial_crecimiento(self, paciente_id: int) -> List[Dict[str, Any]]:
        rows = self.db.fetchall(
            """SELECT * FROM registros_crecimiento
               WHERE paciente_id=? ORDER BY fecha""",
            (paciente_id,)
        )
        return [dict(r) for r in rows]

    def agregar_registro_nutricional(
        self, paciente_id: int, fecha: date,
        calorias: float, proteinas: float, grasas: float,
        carbohidratos: float, fibra: float = 0,
        hierro: float = 0, calcio: float = 0,
        vitamina_a: float = 0, vitamina_c: float = 0,
        zinc: float = 0, observaciones: str = ""
    ) -> int:
        cursor = self.db.execute(
            """INSERT INTO registros_nutricionales
               (paciente_id, fecha, calorias_kcal, proteinas_g, grasas_g,
                carbohidratos_g, fibra_g, hierro_mg, calcio_mg,
                vitamina_a_ui, vitamina_c_mg, zinc_mg, observaciones)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (paciente_id, fecha.isoformat(), calorias, proteinas, grasas,
             carbohidratos, fibra, hierro, calcio, vitamina_a, vitamina_c, zinc, observaciones)
        )
        self.db.commit()
        return cursor.lastrowid

    def historial_nutricional(self, paciente_id: int) -> List[Dict[str, Any]]:
        rows = self.db.fetchall(
            """SELECT * FROM registros_nutricionales
               WHERE paciente_id=? ORDER BY fecha""",
            (paciente_id,)
        )
        return [dict(r) for r in rows]
