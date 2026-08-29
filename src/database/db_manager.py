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
                fecha_nacimiento DATE NOT NULL,
                sexo TEXT NOT NULL CHECK(sexo IN ('M', 'F')),
                peso_kg REAL,
                talla_cm REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

            -- Tabla de historia médica
            CREATE TABLE IF NOT EXISTS historia_medica (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                paciente_id INTEGER NOT NULL,
                fecha_evaluacion DATE NOT NULL,
                evaluador TEXT,
                motivo_consulta TEXT,
                diagnosticos_actuales TEXT,
                antecedentes_personales TEXT,
                antecedentes_familiares TEXT,
                cirugias_hospitalizaciones TEXT,
                medicamentos_suplementos TEXT,
                alergias_intolerancias TEXT,
                observaciones_medicas TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (paciente_id) REFERENCES pacientes(id) ON DELETE CASCADE
            );

            -- Tabla de resultados de laboratorio
            CREATE TABLE IF NOT EXISTS laboratorios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                paciente_id INTEGER NOT NULL,
                fecha_toma DATE NOT NULL,
                tipo_prueba TEXT NOT NULL,
                valor TEXT NOT NULL,
                unidad TEXT,
                edad_meses_al_momento REAL,
                resultado_clasificacion TEXT,
                rango_referencia TEXT,
                observaciones TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (paciente_id) REFERENCES pacientes(id) ON DELETE CASCADE
            );

            -- Tabla de evaluaciones antropométricas (mediciones + z-scores calculados)
            CREATE TABLE IF NOT EXISTS evaluaciones_antropometricas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                paciente_id INTEGER NOT NULL,
                fecha_visita DATE NOT NULL,
                evaluador TEXT,
                -- Mediciones
                peso_kg REAL,
                talla_cm REAL,
                tipo_medicion TEXT,
                edema INTEGER DEFAULT 0,
                pc_cm REAL,
                muac_mm REAL,
                pliegue_triceps_mm REAL,
                pliegue_subescapular_mm REAL,
                -- Edad calculada
                edad_dias INTEGER,
                edad_meses_completos INTEGER,
                edad_meses_decimal REAL,
                -- Resultados (z-scores)
                z_lhfa REAL, perc_lhfa REAL, clasif_lhfa TEXT, flag_lhfa INTEGER,
                z_wfa REAL, perc_wfa REAL, clasif_wfa TEXT, flag_wfa INTEGER,
                z_wflh REAL, perc_wflh REAL, clasif_wflh TEXT, flag_wflh INTEGER,
                z_bmi REAL, perc_bmi REAL, clasif_bmi TEXT, flag_bmi INTEGER,
                z_pc REAL, perc_pc REAL, clasif_pc TEXT,
                z_acfa REAL, perc_acfa REAL, clasif_muac TEXT, flag_acfa INTEGER,
                z_tsfa REAL, perc_tsfa REAL, clasif_tsfa TEXT,
                z_ssfa REAL, perc_ssfa REAL, clasif_ssfa TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (paciente_id) REFERENCES pacientes(id) ON DELETE CASCADE
            );

            -- Tabla de seguimiento de crecimiento (historial evolutivo por paciente)
            CREATE TABLE IF NOT EXISTS seguimiento_crecimiento (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                paciente_id INTEGER NOT NULL,
                fecha_visita DATE NOT NULL,
                peso_kg REAL,
                talla_cm REAL,
                tipo_medicion TEXT,
                pc_cm REAL,
                muac_mm REAL,
                imc REAL,
                observaciones TEXT,
                edad_meses_decimal REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (paciente_id) REFERENCES pacientes(id) ON DELETE CASCADE
            );

            -- Índices
            CREATE INDEX IF NOT EXISTS idx_pacientes_nombre ON pacientes(nombre);
            CREATE INDEX IF NOT EXISTS idx_historia_paciente ON historia_alimentaria(paciente_id, fecha_evaluacion);
            CREATE INDEX IF NOT EXISTS idx_historia_medica_paciente ON historia_medica(paciente_id, fecha_evaluacion);
            CREATE INDEX IF NOT EXISTS idx_laboratorios_paciente ON laboratorios(paciente_id, fecha_toma);
            CREATE INDEX IF NOT EXISTS idx_antropometria_paciente ON evaluaciones_antropometricas(paciente_id, fecha_visita);
            CREATE INDEX IF NOT EXISTS idx_seguimiento_paciente ON seguimiento_crecimiento(paciente_id, fecha_visita);
        """)
        self.commit()
