"""
Gestor de base de datos SQLite para Nutrición Pediátrica.
Maneja conexión, creación de tablas y operaciones CRUD.
"""
import sqlite3
import os
from pathlib import Path
from typing import Optional, List, Tuple, Any


class DatabaseManager:
    """Conexión y operaciones sobre la base de datos SQLite."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            base = Path(__file__).resolve().parent.parent.parent
            db_path = str(base / "data" / "nutricion_pediátrica.db")
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.connection: Optional[sqlite3.Connection] = None

    def connect(self):
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")

    def close(self):
        if self.connection:
            self.connection.close()
            self.connection = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def execute(self, query: str, params: Tuple = ()) -> sqlite3.Cursor:
        if not self.connection:
            self.connect()
        return self.connection.execute(query, params)

    def executemany(self, query: str, params_list: List[Tuple]):
        if not self.connection:
            self.connect()
        self.connection.executemany(query, params_list)
        self.connection.commit()

    def commit(self):
        if self.connection:
            self.connection.commit()

    def fetchone(self, query: str, params: Tuple = ()) -> Optional[sqlite3.Row]:
        cursor = self.execute(query, params)
        return cursor.fetchone()

    def fetchall(self, query: str, params: Tuple = ()) -> List[sqlite3.Row]:
        cursor = self.execute(query, params)
        return cursor.fetchall()

    def create_tables(self):
        """Crea todas las tablas necesarias para el sistema."""
        self.connection.executescript("""
            -- Tabla de pacientes (niños)
            CREATE TABLE IF NOT EXISTS pacientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                apellido TEXT NOT NULL,
                fecha_nacimiento DATE NOT NULL,
                sexo TEXT NOT NULL CHECK(sexo IN ('M', 'F')),
                peso_kg REAL,
                talla_cm REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Tabla de registros de crecimiento
            CREATE TABLE IF NOT EXISTS registros_crecimiento (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                paciente_id INTEGER NOT NULL,
                fecha DATE NOT NULL,
                peso_kg REAL NOT NULL,
                talla_cm REAL NOT NULL,
                imc REAL,
                perimetro_cefalico_cm REAL,
                perimetro_brazo_cm REAL,
                pliegue_cutaneo_mm REAL,
                observaciones TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (paciente_id) REFERENCES pacientes(id) ON DELETE CASCADE
            );

            -- Tabla de registros nutricionales (dietas)
            CREATE TABLE IF NOT EXISTS registros_nutricionales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                paciente_id INTEGER NOT NULL,
                fecha DATE NOT NULL,
                calorias_kcal REAL,
                proteinas_g REAL,
                grasas_g REAL,
                carbohidratos_g REAL,
                fibra_g REAL,
                hierro_mg REAL,
                calcio_mg REAL,
                vitamina_a_ui REAL,
                vitamina_c_mg REAL,
                zinc_mg REAL,
                observaciones TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (paciente_id) REFERENCES pacientes(id) ON DELETE CASCADE
            );

            -- Tabla de alertas
            CREATE TABLE IF NOT EXISTS alertas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                paciente_id INTEGER NOT NULL,
                tipo_alerta TEXT NOT NULL,
                mensaje TEXT NOT NULL,
                severidad TEXT CHECK(severidad IN ('baja', 'media', 'alta', 'critica')),
                activa INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (paciente_id) REFERENCES pacientes(id) ON DELETE CASCADE
            );

            -- Tabla de alimentos
            CREATE TABLE IF NOT EXISTS alimentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                categoria TEXT,
                calorias_kcal REAL,
                proteinas_g REAL,
                grasas_g REAL,
                carbohidratos_g REAL,
                fibra_g REAL,
                hierro_mg REAL,
                calcio_mg REAL,
                vitamina_a_ui REAL,
                vitamina_c_mg REAL,
                zinc_mg REAL
            );

            -- Tabla de historia alimentaria
            CREATE TABLE IF NOT EXISTS historia_alimentaria (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                paciente_id INTEGER NOT NULL,
                fecha_evaluacion DATE NOT NULL,
                evaluador TEXT,
                -- Seccion 1: Tipo de alimentacion
                tipo_alimentacion TEXT CHECK(tipo_alimentacion IN ('lactancia_exclusiva', 'formula_exclusiva', 'mixta')),
                -- Seccion 2: Lactancia materna
                lm_frecuencia TEXT,
                lm_duracion_minutos TEXT,
                lm_posicion_tecnica TEXT,
                lm_suplementos INTEGER DEFAULT 0,
                lm_suplementos_detalle TEXT,
                -- Seccion 3: Formula infantil
                fi_tipo_formula TEXT,
                fi_preparacion TEXT,
                fi_kcal_100ml TEXT,
                fi_preparacion_fresca TEXT,
                fi_tomas_24h TEXT,
                fi_frecuencia TEXT,
                fi_volumen_ofrecido TEXT,
                fi_volumen_real TEXT,
                fi_duracion_toma TEXT,
                fi_adicional INTEGER DEFAULT 0,
                fi_adicional_detalle TEXT,
                -- Seccion 4: Alimentacion mayores
                comidas_snacks_dia TEXT,
                lugar_comidas TEXT,
                -- Patron de comidas
                patron_desayuno_hora TEXT,
                patron_desayuno_alimentos TEXT,
                patron_merienda_manana_hora TEXT,
                patron_merienda_manana_alimentos TEXT,
                patron_almuerzo_hora TEXT,
                patron_almuerzo_alimentos TEXT,
                patron_merienda_tarde_hora TEXT,
                patron_merienda_tarde_alimentos TEXT,
                patron_cena_hora TEXT,
                patron_cena_alimentos TEXT,
                patron_otra_merienda_hora TEXT,
                patron_otra_merienda_alimentos TEXT,
                -- Apetito y ambiente
                apetito TEXT CHECK(apetito IN ('excelente', 'bueno', 'regular', 'pobre')),
                apetito_comentarios TEXT,
                comidas_familia TEXT CHECK(comidas_familia IN ('siempre', 'a_veces', 'rara_vez', 'no')),
                ambiente_agradable TEXT CHECK(ambiente_agradable IN ('si', 'a_veces', 'no')),
                ambiente_dificultades TEXT,
                -- Leche y jugos
                leche_cantidad TEXT,
                leche_tipo TEXT,
                jugo_cantidad TEXT,
                snacks_frecuencia TEXT CHECK(snacks_frecuencia IN ('nunca', 'ocasionalmente', 'frecuentemente', 'varias_veces_dia')),
                snacks_tipo TEXT,
                -- Observaciones adicionales
                alergias TEXT CHECK(alergias IN ('si', 'no', 'en_estudio')),
                alergias_detalle TEXT,
                suplemento_vitaminico TEXT,
                otros_comentarios TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (paciente_id) REFERENCES pacientes(id) ON DELETE CASCADE
            );

            -- Tabla de usuario
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                nombre_completo TEXT,
                rol TEXT DEFAULT 'nutricionista',
                activo INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Índices
            CREATE INDEX IF NOT EXISTS idx_pacientes_nombre ON pacientes(apellido, nombre);
            CREATE INDEX IF NOT EXISTS idx_crecimiento_paciente ON registros_crecimiento(paciente_id, fecha);
            CREATE INDEX IF NOT EXISTS idx_nutricional_paciente ON registros_nutricionales(paciente_id, fecha);
            CREATE INDEX IF NOT EXISTS idx_alertas_paciente ON alertas(paciente_id, activa);
        """)
        self.commit()
