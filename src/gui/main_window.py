"""
Dashboard principal — Nutrición Pediátrica.
Incluye: Pacientes, Evaluación, Seguimiento, Requerimientos, Historia Alimentaria.
"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import date, datetime
from typing import Optional
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.database.db_manager import DatabaseManager
from src.modules.patient_manager import PatientManager
from src.modules.historia_alimentaria_manager import HistoriaAlimentariaManager
from src.modules.historia_medica_manager import HistoriaMedicaManager
from src.modules.laboratorio_manager import LaboratorioManager
from src.modules.laboratorio_data import (
    listar_pruebas, obtener_prueba, clasificar_resultado,
    unidades_disponibles, convertir_a_base
)
from src.modules.nutrition_calcs import (
    calcular_edad_meses,
    calcular_z_score_peso_edad, calcular_z_score_talla_edad,
    calcular_z_score_peso_talla, calcular_z_score_imc_edad,
    clasificar_estado_nutricional, clasificar_talla_edad,
    calcular_requerimientos_caloricos, generar_reporte_evaluacion
)
from src.modules.antropometria import (
    generar_reporte_antropometrico, calcular_edad_texto,
    clasificar_muac, clasificar_perimetro_cefalico,
    peso_porcentaje_esperado, TASAS_PESO_SEMANAL
)

COLOR_BG = "#f0f4f8"
COLOR_PRIMARY = "#1a5276"
COLOR_ACCENT = "#2e86c1"
COLOR_SECTION = "#d6eaf8"
COLOR_WHITE = "#ffffff"
COLOR_LABEL = "#2c3e50"
COLOR_ENTRY_BG = "#fdfefe"


def _parsear_fecha(texto: str) -> date:
    """Convierte una fecha de la interfaz (DD-MM-AAAA) a date."""
    return datetime.strptime(texto.strip(), "%d-%m-%Y").date()


def _mostrar_fecha(fecha: str) -> str:
    """Convierte una fecha ISO almacenada a DD-MM-AAAA para la interfaz."""
    try:
        return date.fromisoformat(fecha).strftime("%d-%m-%Y")
    except (TypeError, ValueError):
        return fecha or ""


class ScrollFrame(tk.Frame):
    """Frame con scroll vertical para formularios grandes."""

    def __init__(self, parent, **kw):
        super().__init__(parent, **kw)
        self.canvas = tk.Canvas(self, bg=kw.get('bg', COLOR_BG), highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.canvas.yview)
        self.inner = tk.Frame(self.canvas, bg=kw.get('bg', COLOR_BG))

        self.inner.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.inner, anchor=tk.NW)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.inner.bind("<Enter>", self._bind_mousewheel)
        self.inner.bind("<Leave>", self._unbind_mousewheel)

    def _bind_mousewheel(self, event):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbind_mousewheel(self, event):
        self.canvas.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


class MainWindow:
    """Dashboard principal de la aplicación."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Nutrición Pediátrica v1.0 — Dashboard")
        self.root.geometry("1350x900")
        self.root.minsize(1100, 750)
        self.root.configure(bg=COLOR_BG)

        self.db = DatabaseManager()
        self.db.connect()
        self.db.create_tables()
        self.patient_mgr = PatientManager(self.db)
        self.historia_mgr = HistoriaAlimentariaManager(self.db)
        self.historia_med_mgr = HistoriaMedicaManager(self.db)
        self.laboratorio_mgr = LaboratorioManager(self.db)
        from src.modules.antropometria_manager import AntropometriaManager
        self.antropometria_mgr = AntropometriaManager(self.db)

        self._configurar_estilo()
        self._crear_barra_superior()
        self._crear_barra_estado()
        self._crear_notebook()
        self._crear_pestanas()

        self.paciente_seleccionado: Optional[int] = None
        self.ha_editando_id: Optional[int] = None
        self.hm_editando_id: Optional[int] = None
        self.lab_editando_id: Optional[int] = None
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _configurar_estilo(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background=COLOR_BG)
        style.configure('TLabel', background=COLOR_BG, foreground=COLOR_LABEL, font=('Segoe UI', 10))
        style.configure('Title.TLabel', font=('Segoe UI', 14, 'bold'), foreground=COLOR_PRIMARY, background=COLOR_BG)
        style.configure('Subtitle.TLabel', font=('Segoe UI', 11, 'bold'), foreground=COLOR_ACCENT, background=COLOR_BG)
        style.configure('Section.TLabel', font=('Segoe UI', 10, 'bold'), foreground=COLOR_PRIMARY, background=COLOR_SECTION)
        style.configure('TButton', font=('Segoe UI', 10), padding=6)
        style.configure('Primary.TButton', font=('Segoe UI', 10, 'bold'))
        style.configure('TEntry', font=('Segoe UI', 10))
        style.configure('TCombobox', font=('Segoe UI', 10))
        style.configure('TLabelframe', background=COLOR_BG, foreground=COLOR_PRIMARY, font=('Segoe UI', 10, 'bold'))
        style.configure('TLabelframe.Label', background=COLOR_BG, foreground=COLOR_PRIMARY, font=('Segoe UI', 10, 'bold'))
        style.configure('Treeview', font=('Segoe UI', 9), rowheight=26)
        style.configure('Treeview.Heading', font=('Segoe UI', 9, 'bold'))
        style.configure('TNotebook.Tab', font=('Segoe UI', 10, 'bold'), padding=[12, 6])
        style.configure('Status.TLabel', font=('Segoe UI', 9), background='#e8e8e8', foreground=COLOR_LABEL)

    def _crear_barra_superior(self):
        top = tk.Frame(self.root, bg=COLOR_PRIMARY, height=60)
        top.pack(fill=tk.X)
        top.pack_propagate(False)
        tk.Label(top, text="NUTRICIÓN PEDIÁTRICA",
                 bg=COLOR_PRIMARY, fg="white",
                 font=('Segoe UI', 18, 'bold')).pack(side=tk.LEFT, padx=20)
        tk.Label(top, text="Dashboard de Evaluación y Seguimiento",
                 bg=COLOR_PRIMARY, fg="#aed6f1",
                 font=('Segoe UI', 11)).pack(side=tk.LEFT, padx=10)
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        archivo_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Archivo", menu=archivo_menu)
        archivo_menu.add_command(label="Salir", command=self._on_close)
        ayuda_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Ayuda", menu=ayuda_menu)
        ayuda_menu.add_command(label="Acerca de", command=self._acerca_de)

    def _crear_barra_estado(self):
        self.status_var = tk.StringVar(value="Listo")
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, style='Status.TLabel', relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _crear_notebook(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=8, pady=(4, 0))

    def _crear_pestanas(self):
        self._crear_pestana_pacientes()
        self._crear_pestana_historia_medica()
        self._crear_pestana_historia_alimentaria()
        self._crear_pestana_antropometria()
        self._crear_pestana_laboratorios()
        self._bloquear_pestanas()

    def _bloquear_pestanas(self):
        """Mantiene habilitadas todas las pestañas para permitir trabajar sin seleccionar un paciente."""
        self.pestanas_entrada = []
        for tid in self.notebook.tabs():
            texto = self.notebook.tab(tid, "text")
            if "Pacientes" not in texto:
                self.notebook.tab(tid, state='normal')
                self.pestanas_entrada.append(tid)

    def _habilitar_pestanas(self):
        """Habilita todas las pestañas de captura."""
        for tid in self.notebook.tabs():
            texto = self.notebook.tab(tid, "text")
            if "Pacientes" not in texto:
                self.notebook.tab(tid, state='normal')

    # ==================================================================
    # PESTAÑA 1: PACIENTES
    # ==================================================================
    def _crear_pestana_pacientes(self):
        frame = ScrollFrame(self.notebook, bg=COLOR_BG)
        self.notebook.add(frame, text="  Pacientes  ")
        parent = frame.inner

        ttk.Label(parent, text="Gestión de Pacientes", style='Title.TLabel').pack(anchor=tk.W, padx=5)
        ttk.Label(parent, text="Administre pacientes y su seguimiento de crecimiento. Las demás pestañas quedan disponibles para trabajar sin necesidad de seleccionar un paciente.",
                  style='Subtitle.TLabel').pack(anchor=tk.W, padx=5)
        ttk.Separator(parent, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5, padx=5)

        form_frame = ttk.LabelFrame(parent, text=" Datos del Paciente ", padding=10)
        form_frame.pack(fill=tk.X, padx=10, pady=5)

        row1 = ttk.Frame(form_frame)
        row1.pack(fill=tk.X, pady=2)
        ttk.Label(row1, text="Nombre completo:").pack(side=tk.LEFT, padx=5)
        self.entry_nombre = ttk.Entry(row1, width=55)
        self.entry_nombre.pack(side=tk.LEFT, padx=5)

        row2 = ttk.Frame(form_frame)
        row2.pack(fill=tk.X, pady=2)
        ttk.Label(row2, text="Fecha nac. (DD-MM-AAAA):").pack(side=tk.LEFT, padx=5)
        self.entry_fecha_nac = ttk.Entry(row2, width=15)
        self.entry_fecha_nac.pack(side=tk.LEFT, padx=5)
        ttk.Label(row2, text="Sexo:").pack(side=tk.LEFT, padx=5)
        self.combo_sexo = ttk.Combobox(row2, values=["M", "F"], width=5, state="readonly")
        self.combo_sexo.pack(side=tk.LEFT, padx=5)
        self.combo_sexo.set("M")
        ttk.Label(row2, text="Fecha actual:").pack(side=tk.LEFT, padx=5)
        self.entry_fecha_actual = ttk.Entry(row2, width=12)
        self.entry_fecha_actual.pack(side=tk.LEFT, padx=5)
        self.entry_fecha_actual.insert(0, date.today().strftime("%d-%m-%Y"))

        row3 = ttk.Frame(form_frame)
        row3.pack(fill=tk.X, pady=2)
        ttk.Label(row3, text="Peso (kg):").pack(side=tk.LEFT, padx=5)
        self.entry_peso = ttk.Entry(row3, width=10)
        self.entry_peso.pack(side=tk.LEFT, padx=5)
        ttk.Label(row3, text="Talla (cm):").pack(side=tk.LEFT, padx=5)
        self.entry_talla = ttk.Entry(row3, width=10)
        self.entry_talla.pack(side=tk.LEFT, padx=5)

        btn_frame = ttk.Frame(form_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="Guardar", style='Primary.TButton', command=self._guardar_paciente).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Seguir", command=self._seguir_paciente).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Nuevo", command=self._limpiar_formulario).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Eliminar", command=self._eliminar_paciente).pack(side=tk.LEFT, padx=5)

        ttk.Separator(parent, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5, padx=5)
        ttk.Label(parent, text="Lista de Pacientes", style='Subtitle.TLabel').pack(anchor=tk.W, padx=5)

        search_frame = ttk.Frame(parent)
        search_frame.pack(fill=tk.X, pady=5, padx=5)
        ttk.Label(search_frame, text="Buscar:").pack(side=tk.LEFT)
        self.entry_buscar = ttk.Entry(search_frame, width=30)
        self.entry_buscar.pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="Buscar", command=self._buscar_pacientes).pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="Todos", command=self._cargar_pacientes).pack(side=tk.LEFT, padx=5)

        cols = ("ID", "Nombre completo", "Nacimiento", "Sexo", "Peso", "Talla", "Seguir")
        self.tree_pacientes = ttk.Treeview(parent, columns=cols, show='headings', height=7)
        for c in cols:
            self.tree_pacientes.heading(c, text=c)
            self.tree_pacientes.column(c, width=140, anchor=tk.CENTER)
        self.tree_pacientes.column("ID", width=50)
        self.tree_pacientes.column("Nombre completo", width=250, anchor=tk.W)
        self.tree_pacientes.column("Seguir", width=70, anchor=tk.CENTER)
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.tree_pacientes.yview)
        self.tree_pacientes.configure(yscrollcommand=scrollbar.set)
        self.tree_pacientes.pack(fill=tk.X, side=tk.LEFT, padx=5)
        scrollbar.pack(fill=tk.Y, side=tk.RIGHT)
        self.tree_pacientes.bind("<<TreeviewSelect>>", self._seleccionar_paciente)
        self.tree_pacientes.bind("<Button-1>", self._clic_pacientes)

        self._cargar_pacientes()

    # ==================================================================
    # PESTAÑA 2: EVALUACIÓN NUTRICIONAL
    # ==================================================================
    def _crear_pestana_evaluacion(self):
        frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame, text="  Evaluación  ")
        ttk.Label(frame, text="Evaluación Nutricional Completa", style='Title.TLabel').pack(anchor=tk.W)
        ttk.Separator(frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)

        input_frame = ttk.LabelFrame(frame, text=" Datos de Evaluación ", padding=10)
        input_frame.pack(fill=tk.X, pady=5)
        row = ttk.Frame(input_frame)
        row.pack(fill=tk.X, pady=2)
        ttk.Label(row, text="ID Paciente:").pack(side=tk.LEFT, padx=5)
        self.entry_eval_paciente_id = ttk.Entry(row, width=10)
        self.entry_eval_paciente_id.pack(side=tk.LEFT, padx=5)
        ttk.Label(row, text="Fecha (DD-MM-AAAA):").pack(side=tk.LEFT, padx=5)
        self.entry_eval_fecha = ttk.Entry(row, width=15)
        self.entry_eval_fecha.insert(0, date.today().strftime("%d-%m-%Y"))
        self.entry_eval_fecha.pack(side=tk.LEFT, padx=5)
        ttk.Button(row, text="Evaluar", style='Primary.TButton', command=self._realizar_evaluacion).pack(side=tk.LEFT, padx=10)

        result_frame = ttk.LabelFrame(frame, text=" Resultado ", padding=10)
        result_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        self.text_evaluacion = scrolledtext.ScrolledText(result_frame, height=18, font=('Consolas', 10), bg=COLOR_WHITE)
        self.text_evaluacion.pack(fill=tk.BOTH, expand=True)

    # ==================================================================
    # PESTAÑA 4: REQUERIMIENTOS
    # ==================================================================
    def _crear_pestana_requerimientos(self):
        frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame, text="  Requerimientos  ")
        ttk.Label(frame, text="Cálculo de Requerimientos Nutricionales", style='Title.TLabel').pack(anchor=tk.W)
        ttk.Separator(frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)

        input_frame = ttk.LabelFrame(frame, text=" Datos del Paciente ", padding=10)
        input_frame.pack(fill=tk.X, pady=5)
        row = ttk.Frame(input_frame)
        row.pack(fill=tk.X, pady=2)
        ttk.Label(row, text="Edad (meses):").pack(side=tk.LEFT, padx=5)
        self.entry_req_edad = ttk.Entry(row, width=10)
        self.entry_req_edad.pack(side=tk.LEFT, padx=5)
        ttk.Label(row, text="Peso (kg):").pack(side=tk.LEFT, padx=5)
        self.entry_req_peso = ttk.Entry(row, width=10)
        self.entry_req_peso.pack(side=tk.LEFT, padx=5)
        ttk.Label(row, text="Talla (cm):").pack(side=tk.LEFT, padx=5)
        self.entry_req_talla = ttk.Entry(row, width=10)
        self.entry_req_talla.pack(side=tk.LEFT, padx=5)
        ttk.Button(row, text="Calcular", style='Primary.TButton', command=self._calcular_requerimientos).pack(side=tk.LEFT, padx=10)

        result_frame = ttk.LabelFrame(frame, text=" Requerimientos Calculados ", padding=10)
        result_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        self.text_requerimientos = scrolledtext.ScrolledText(result_frame, height=14, font=('Consolas', 10), bg=COLOR_WHITE)
        self.text_requerimientos.pack(fill=tk.BOTH, expand=True)

    # ==================================================================
    # PESTAÑA 5: HISTORIA ALIMENTARIA
    # ==================================================================
    def _crear_pestana_historia_alimentaria(self):
        frame = ScrollFrame(self.notebook, bg=COLOR_BG)
        self.notebook.add(frame, text="  Historia Alimentaria  ")
        parent = frame.inner

        ttk.Label(parent, text="Historial de Alimentación del Niño/a", style='Title.TLabel').pack(anchor=tk.W, padx=5)
        ttk.Label(parent, text="Formulario de Evaluación Nutricional — Historia Alimentaria", style='Subtitle.TLabel').pack(anchor=tk.W, padx=5)
        ttk.Separator(parent, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5, padx=5)

        # --- Datos del Paciente ---
        hdr = ttk.LabelFrame(parent, text=" Datos del Paciente ", padding=10)
        hdr.pack(fill=tk.X, padx=10, pady=5)

        r0 = ttk.Frame(hdr)
        r0.pack(fill=tk.X, pady=2)
        ttk.Label(r0, text="ID Paciente:").pack(side=tk.LEFT, padx=5)
        self.ha_paciente_id = ttk.Entry(r0, width=10)
        self.ha_paciente_id.pack(side=tk.LEFT, padx=5)
        ttk.Button(r0, text="Cargar Paciente", command=self._cargar_paciente_en_historia).pack(side=tk.LEFT, padx=5)
        self.ha_paciente_id.bind("<Return>", lambda e: self._cargar_paciente_en_historia())

        r1 = ttk.Frame(hdr)
        r1.pack(fill=tk.X, pady=2)
        ttk.Label(r1, text="Nombre del niño/a:").pack(side=tk.LEFT, padx=5)
        self.ha_nombre = ttk.Entry(r1, width=30)
        self.ha_nombre.pack(side=tk.LEFT, padx=5)
        ttk.Label(r1, text="Fecha de nacimiento:").pack(side=tk.LEFT, padx=5)
        self.ha_fecha_nac = ttk.Entry(r1, width=15)
        self.ha_fecha_nac.pack(side=tk.LEFT, padx=5)

        r2 = ttk.Frame(hdr)
        r2.pack(fill=tk.X, pady=2)
        ttk.Label(r2, text="Edad:").pack(side=tk.LEFT, padx=5)
        self.ha_edad = ttk.Entry(r2, width=20)
        self.ha_edad.pack(side=tk.LEFT, padx=5)
        ttk.Label(r2, text="Sexo:").pack(side=tk.LEFT, padx=5)
        self.ha_sexo = ttk.Combobox(r2, values=["M", "F"], width=5, state="readonly")
        self.ha_sexo.pack(side=tk.LEFT, padx=5)
        self.ha_sexo.set("M")

        r3 = ttk.Frame(hdr)
        r3.pack(fill=tk.X, pady=2)
        ttk.Label(r3, text="Fecha de evaluación:").pack(side=tk.LEFT, padx=5)
        self.ha_fecha_eval = ttk.Entry(r3, width=15)
        self.ha_fecha_eval.insert(0, date.today().strftime("%d-%m-%Y"))
        self.ha_fecha_eval.pack(side=tk.LEFT, padx=5)
        ttk.Label(r3, text="Nombre del evaluador:").pack(side=tk.LEFT, padx=5)
        self.ha_evaluador = ttk.Entry(r3, width=30)
        self.ha_evaluador.pack(side=tk.LEFT, padx=5)

        ttk.Separator(parent, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5, padx=5)

        # === SECCIÓN 1: Tipo de Alimentación ===
        s1 = ttk.LabelFrame(parent, text=" Sección 1: Tipo de Alimentación del Lactante ", padding=10)
        s1.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(s1, text="¿El bebé es alimentado con leche materna, fórmula infantil o ambos?").pack(anchor=tk.W, padx=5)
        self.ha_tipo_alimentacion = tk.StringVar(value="lactancia_exclusiva")
        r1f = ttk.Frame(s1)
        r1f.pack(fill=tk.X, pady=5)
        tk.Radiobutton(r1f, text="Lactancia materna exclusiva", variable=self.ha_tipo_alimentacion,
                       value="lactancia_exclusiva", bg=COLOR_BG, font=('Segoe UI', 10)).pack(side=tk.LEFT, padx=10)
        tk.Radiobutton(r1f, text="Fórmula infantil exclusiva", variable=self.ha_tipo_alimentacion,
                       value="formula_exclusiva", bg=COLOR_BG, font=('Segoe UI', 10)).pack(side=tk.LEFT, padx=10)
        tk.Radiobutton(r1f, text="Alimentación mixta (ambas)", variable=self.ha_tipo_alimentacion,
                       value="mixta", bg=COLOR_BG, font=('Segoe UI', 10)).pack(side=tk.LEFT, padx=10)

        # === SECCIÓN 2: Lactancia Materna ===
        s2 = ttk.LabelFrame(parent, text=" Sección 2: Lactancia Materna ", padding=10)
        s2.pack(fill=tk.X, padx=10, pady=5)

        def _row_s2(parent_frame, label_text, width=50):
            r = ttk.Frame(parent_frame)
            r.pack(fill=tk.X, pady=3)
            ttk.Label(r, text=label_text, width=45, anchor=tk.W).pack(side=tk.LEFT, padx=5)
            e = ttk.Entry(r, width=width)
            e.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
            return e

        self.ha_lm_frecuencia = _row_s2(s2, "Frecuencia de alimentación (ej. cada 2, 3 o 4 horas):")
        self.ha_lm_duracion = _row_s2(s2, "Tiempo de amamantamiento por pecho (min/lado):")
        self.ha_lm_posicion = _row_s2(s2, "Posición y técnica de amamantamiento (describir):")

        r_sup = ttk.Frame(s2)
        r_sup.pack(fill=tk.X, pady=3)
        ttk.Label(r_sup, text="¿Se ofrecen biberones suplementarios u otros alimentos?").pack(side=tk.LEFT, padx=5)
        self.ha_lm_suplementos = tk.StringVar(value="no")
        tk.Radiobutton(r_sup, text="Sí", variable=self.ha_lm_suplementos, value="si", bg=COLOR_BG).pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(r_sup, text="No", variable=self.ha_lm_suplementos, value="no", bg=COLOR_BG).pack(side=tk.LEFT, padx=5)
        self.ha_lm_suplementos_detalle = _row_s2(s2, "Si sí, especifique qué suplementos:")

        # === SECCIÓN 3: Fórmula Infantil ===
        s3 = ttk.LabelFrame(parent, text=" Sección 3: Alimentación con Fórmula Infantil ", padding=10)
        s3.pack(fill=tk.X, padx=10, pady=5)

        self.ha_fi_tipo = _row_s2(s3, "Tipo de fórmula (marca, nombre, tipo):")
        self.ha_fi_preparacion = _row_s2(s3, "Preparación (proporción polvo/agua por biberón):")
        self.ha_fi_kcal = _row_s2(s3, "Contenido energético estimado (kcal/100 ml):")

        r_prep = ttk.Frame(s3)
        r_prep.pack(fill=tk.X, pady=3)
        ttk.Label(r_prep, text="¿Cada toma se prepara de forma fresca?").pack(side=tk.LEFT, padx=5)
        self.ha_fi_preparacion_fresca = ttk.Combobox(r_prep, values=[
            "Sí, siempre", "La mayoría de las veces", "Ocasionalmente", "No"
        ], width=25, state="readonly")
        self.ha_fi_preparacion_fresca.pack(side=tk.LEFT, padx=5)

        self.ha_fi_tomas_24h = _row_s2(s3, "Tomas en 24 horas:")
        self.ha_fi_frecuencia = _row_s2(s3, "Frecuencia de alimentación (cada 2, 3 o 4 horas):")
        self.ha_fi_vol_ofrecido = _row_s2(s3, "Volumen de fórmula ofrecido por toma (ml):")
        self.ha_fi_vol_real = _row_s2(s3, "Volumen real consumido en cada toma (ml):")
        self.ha_fi_duracion = _row_s2(s3, "Tiempo que tarda en completar cada toma (min):")

        r_add = ttk.Frame(s3)
        r_add.pack(fill=tk.X, pady=3)
        ttk.Label(r_add, text="¿Se le añade algo al biberón? (cereales, azúcar, etc.)").pack(side=tk.LEFT, padx=5)
        self.ha_fi_adicional = tk.StringVar(value="no")
        tk.Radiobutton(r_add, text="Sí", variable=self.ha_fi_adicional, value="si", bg=COLOR_BG).pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(r_add, text="No", variable=self.ha_fi_adicional, value="no", bg=COLOR_BG).pack(side=tk.LEFT, padx=5)
        self.ha_fi_adicional_detalle = _row_s2(s3, "Si sí, especifique qué se añade:")

        # === SECCIÓN 4: Alimentación en Niños Mayores ===
        s4 = ttk.LabelFrame(parent, text=" Sección 4: Alimentación en Niños Mayores ", padding=10)
        s4.pack(fill=tk.X, padx=10, pady=5)
        self.ha_comidas_snacks = _row_s2(s4, "¿Cuántas comidas y snacks consume al día?")
        self.ha_lugar_comidas = _row_s2(s4, "¿Dónde come el niño? (cocina, comedor, sala, etc.)")

        ttk.Label(s4, text="Patrón de comidas de 1 día:", style='Subtitle.TLabel').pack(anchor=tk.W, padx=5, pady=5)
        pat_frame = ttk.Frame(s4)
        pat_frame.pack(fill=tk.X)
        headers_text = ["Comida / Merienda", "Hora aprox.", "Alimentos consumidos"]
        for i, h in enumerate(headers_text):
            ttk.Label(pat_frame, text=h, style='Subtitle.TLabel', width=22).grid(row=0, column=i, padx=5, pady=2)

        self.ha_patron_entries = {}
        comidas = ["Desayuno", "Merienda mañana", "Almuerzo", "Merienda tarde", "Cena", "Otra merienda"]
        for idx, comida in enumerate(comidas):
            ttk.Label(pat_frame, text=comida, width=20, anchor=tk.W).grid(row=idx + 1, column=0, padx=5, pady=2)
            e_hora = ttk.Entry(pat_frame, width=18)
            e_hora.grid(row=idx + 1, column=1, padx=5, pady=2)
            e_alim = ttk.Entry(pat_frame, width=45)
            e_alim.grid(row=idx + 1, column=2, padx=5, pady=2)
            key = comida.lower().replace(" ", "_").replace("á", "a").replace("é", "e").replace("í", "i")
            self.ha_patron_entries[key] = (e_hora, e_alim)

        # === Apetito y Ambiente ===
        s5 = ttk.LabelFrame(parent, text=" Apetito y Ambiente durante las Comidas ", padding=10)
        s5.pack(fill=tk.X, padx=10, pady=5)

        r_ap = ttk.Frame(s5)
        r_ap.pack(fill=tk.X, pady=3)
        ttk.Label(r_ap, text="¿Cómo describen los padres el apetito?").pack(side=tk.LEFT, padx=5)
        self.ha_apetito = ttk.Combobox(r_ap, values=["Excelente", "Bueno", "Regular", "Pobre"], width=15, state="readonly")
        self.ha_apetito.pack(side=tk.LEFT, padx=5)
        self.ha_apetito.set("Bueno")

        self.ha_apetito_comentarios = _row_s2(s5, "Comentarios adicionales sobre el apetito:")

        r_fam = ttk.Frame(s5)
        r_fam.pack(fill=tk.X, pady=3)
        ttk.Label(r_fam, text="¿Existen tiempos de comida en familia?").pack(side=tk.LEFT, padx=5)
        self.ha_comidas_familia = ttk.Combobox(r_fam, values=["Sí, siempre", "A veces", "Rara vez", "No"], width=18, state="readonly")
        self.ha_comidas_familia.pack(side=tk.LEFT, padx=5)
        self.ha_comidas_familia.set("A veces")

        r_amb = ttk.Frame(s5)
        r_amb.pack(fill=tk.X, pady=3)
        ttk.Label(r_amb, text="¿Son situaciones agradables y disfrutables?").pack(side=tk.LEFT, padx=5)
        self.ha_ambiente = ttk.Combobox(r_amb, values=["Sí", "A veces", "No"], width=15, state="readonly")
        self.ha_ambiente.pack(side=tk.LEFT, padx=5)
        self.ha_ambiente.set("Sí")

        self.ha_ambiente_dificultades = _row_s2(s5, "Si no, describa las dificultades durante las comidas:")

        # === Consumo de Leche y Jugos ===
        s6 = ttk.LabelFrame(parent, text=" Consumo de Leche y Jugos ", padding=10)
        s6.pack(fill=tk.X, padx=10, pady=5)
        self.ha_leche_cantidad = _row_s2(s6, "¿Cuánta leche consume al día? (ml/vastos):")
        self.ha_leche_tipo = _row_s2(s6, "¿Qué tipo de leche consume? (materna, fórmula, entera, etc.):")
        self.ha_jugo_cantidad = _row_s2(s6, "¿Cuánto jugo consume al día? (ml/vastos):")

        r_sn = ttk.Frame(s6)
        r_sn.pack(fill=tk.X, pady=3)
        ttk.Label(r_sn, text="¿Con qué frecuencia consume snacks/alimentos empaquetados?").pack(side=tk.LEFT, padx=5)
        self.ha_snacks_freq = ttk.Combobox(r_sn, values=[
            "Nunca", "Ocasionalmente (1-2 veces/sem)", "Frecuentemente (diario)", "Varias veces al día"
        ], width=30, state="readonly")
        self.ha_snacks_freq.pack(side=tk.LEFT, padx=5)
        self.ha_snacks_freq.set("Nunca")

        self.ha_snacks_tipo = _row_s2(s6, "Especifique qué tipo de snacks consume habitualmente:")

        # === Observaciones Adicionales ===
        s7 = ttk.LabelFrame(parent, text=" Observaciones Adicionales ", padding=10)
        s7.pack(fill=tk.X, padx=10, pady=5)

        r_al = ttk.Frame(s7)
        r_al.pack(fill=tk.X, pady=3)
        ttk.Label(r_al, text="¿Existen alergias o intolerancias alimentarias conocidas?").pack(side=tk.LEFT, padx=5)
        self.ha_alergias = ttk.Combobox(r_al, values=["Sí", "No", "En estudio"], width=15, state="readonly")
        self.ha_alergias.pack(side=tk.LEFT, padx=5)
        self.ha_alergias.set("No")

        self.ha_alergias_detalle = _row_s2(s7, "Si es sí, detalle cuáles:")
        self.ha_suplemento = _row_s2(s7, "¿Toma algún suplemento vitamínico o mineral?")
        self.ha_otros_comentarios = _row_s2(s7, "Otros comentarios o preocupaciones de los padres:")

        # === Firma ===
        sig_frame = ttk.Frame(parent)
        sig_frame.pack(fill=tk.X, padx=10, pady=10)
        ttk.Label(sig_frame, text="Firma del evaluador: _____________________").pack(side=tk.LEFT, padx=20)
        ttk.Label(sig_frame, text="Fecha: _____________________").pack(side=tk.LEFT, padx=20)

        # === Botones ===
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        ttk.Button(btn_frame, text="Guardar Historia Alimentaria", style='Primary.TButton',
                   command=self._guardar_historia).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cargar Historia", command=self._cargar_historia_alimentaria).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Ver Último Registro", command=self._ver_ultima_historia).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Seleccionar / Editar Registro", command=self._seleccionar_historia_a_editar).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancelar Edición", command=self._cancelar_edicion_historia).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Limpiar Formulario", command=self._limpiar_historia).pack(side=tk.LEFT, padx=5)

    # ==================================================================
    # PESTAÑA: HISTORIA MÉDICA
    # ==================================================================
    def _crear_pestana_historia_medica(self):
        frame = ScrollFrame(self.notebook, bg=COLOR_BG)
        self.notebook.add(frame, text="  Historia Médica  ")
        parent = frame.inner

        ttk.Label(parent, text="Historia Médica del Paciente", style='Title.TLabel').pack(anchor=tk.W, padx=5)
        ttk.Separator(parent, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5, padx=5)

        # --- Selección de Paciente ---
        sel_frame = ttk.LabelFrame(parent, text=" Paciente ", padding=10)
        sel_frame.pack(fill=tk.X, padx=10, pady=5)

        r0 = ttk.Frame(sel_frame)
        r0.pack(fill=tk.X, pady=2)
        ttk.Label(r0, text="ID Paciente:").pack(side=tk.LEFT, padx=5)
        self.hm_paciente_id = ttk.Entry(r0, width=10)
        self.hm_paciente_id.pack(side=tk.LEFT, padx=5)
        ttk.Button(r0, text="Cargar Paciente", command=self._hm_cargar_paciente).pack(side=tk.LEFT, padx=5)
        self.hm_paciente_id.bind("<Return>", lambda e: self._hm_cargar_paciente())

        r0b = ttk.Frame(sel_frame)
        r0b.pack(fill=tk.X, pady=2)
        ttk.Label(r0b, text="Nombre:").pack(side=tk.LEFT, padx=5)
        self.hm_nombre = ttk.Entry(r0b, width=30, state='readonly')
        self.hm_nombre.pack(side=tk.LEFT, padx=5)
        ttk.Label(r0b, text="Fecha de evaluación (DD-MM-AAAA):").pack(side=tk.LEFT, padx=5)
        self.hm_fecha_eval = ttk.Entry(r0b, width=15)
        self.hm_fecha_eval.insert(0, date.today().strftime("%d-%m-%Y"))
        self.hm_fecha_eval.pack(side=tk.LEFT, padx=5)
        ttk.Label(r0b, text="Evaluador:").pack(side=tk.LEFT, padx=5)
        self.hm_evaluador = ttk.Entry(r0b, width=25)
        self.hm_evaluador.pack(side=tk.LEFT, padx=5)

        ttk.Separator(parent, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5, padx=5)

        # --- Formulario de Historia Médica ---
        form_frame = ttk.LabelFrame(parent, text=" Antecedentes Médicos ", padding=10)
        form_frame.pack(fill=tk.X, padx=10, pady=5)

        self.hm_campos = {}
        campos = [
            ("motivo_consulta", "Motivo de consulta:"),
            ("diagnosticos_actuales", "Diagnósticos actuales:"),
            ("antecedentes_personales", "Antecedentes personales patológicos:"),
            ("antecedentes_familiares", "Antecedentes familiares relevantes:"),
            ("cirugias_hospitalizaciones", "Cirugías, traumatismos u hospitalizaciones:"),
            ("medicamentos_suplementos", "Medicamentos y suplementos actuales:"),
            ("alergias_intolerancias", "Alergias e intolerancias alimentarias:"),
            ("observaciones_medicas", "Observaciones médicas adicionales:"),
        ]

        for i, (nombre, etiqueta) in enumerate(campos):
            ttk.Label(form_frame, text=etiqueta, font=('Segoe UI', 10, 'bold')).grid(
                row=i * 2, column=0, sticky="w", pady=(8, 2), padx=5
            )
            campo = tk.Text(form_frame, height=3, width=75, wrap="word", font=('Segoe UI', 10))
            campo.grid(row=i * 2 + 1, column=0, sticky="ew", pady=(0, 5), padx=5)
            self.hm_campos[nombre] = campo

        form_frame.columnconfigure(0, weight=1)

        ttk.Separator(parent, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5, padx=5)

        # --- Botones ---
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Button(btn_frame, text="Guardar Historia Médica", style='Primary.TButton',
                   command=self._hm_guardar).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Ver Último Registro", command=self._hm_ver_ultimo).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Seleccionar / Editar Registro", command=self._seleccionar_historia_medica_a_editar).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancelar Edición", command=self._cancelar_edicion_historia_medica).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Limpiar Formulario", command=self._hm_limpiar).pack(side=tk.LEFT, padx=5)

    def _hm_cargar_paciente(self):
        """Carga datos del paciente en la pestaña historia médica."""
        pid = self.patient_mgr.resolver_id_a_database_id(self.hm_paciente_id.get())
        if pid is None:
            messagebox.showerror("Error", "Ingrese un ID válido (ej: 1 o 1.2).")
            return

        paciente = self.patient_mgr.obtener_paciente(pid)
        if not paciente:
            messagebox.showerror("Error", "Paciente no encontrado.")
            return

        self.hm_nombre.config(state='normal')
        self.hm_nombre.delete(0, tk.END)
        self.hm_nombre.insert(0, paciente['nombre'])
        self.hm_nombre.config(state='readonly')
        self.status_var.set(f"Paciente {paciente['nombre']} cargado en Historia Médica")

    def _hm_guardar(self):
        """Guarda la historia médica en la base de datos."""
        try:
            pid = int(self.hm_paciente_id.get().strip())
        except (ValueError, TypeError):
            messagebox.showerror("Error", "Ingrese un ID de paciente válido.")
            return

        paciente = self.patient_mgr.obtener_paciente(pid)
        if not paciente:
            messagebox.showerror("Error", "Paciente no encontrado.")
            return

        try:
            fecha_eval = _parsear_fecha(self.hm_fecha_eval.get())
        except ValueError:
            messagebox.showerror("Error", "Fecha de evaluación inválida (DD-MM-AAAA).")
            return

        evaluador = self.hm_evaluador.get().strip()
        datos = {}
        for nombre, campo in self.hm_campos.items():
            datos[nombre] = campo.get("1.0", tk.END).strip()

        if self.hm_editando_id is not None:
            self.historia_med_mgr.actualizar(self.hm_editando_id, fecha_eval, evaluador, datos)
            self.status_var.set(f"Historia médica actualizada (ID: {self.hm_editando_id})")
            messagebox.showinfo("Éxito", "Historia médica actualizada correctamente.")
            self.hm_editando_id = None
            return

        hid = self.historia_med_mgr.guardar(pid, fecha_eval, evaluador, datos)
        self.status_var.set(f"Historia médica guardada (ID: {hid})")
        messagebox.showinfo("Éxito", f"Historia médica guardada correctamente.\nID Registro: {hid}")

    def _seleccionar_historia_medica_a_editar(self):
        try:
            pid = int(self.hm_paciente_id.get().strip())
        except (ValueError, TypeError):
            messagebox.showerror("Error", "Ingrese un ID de paciente válido.")
            return
        historiales = self.historia_med_mgr.listar_por_paciente(pid)
        if not historiales:
            messagebox.showinfo("Sin registros", "No hay historias médicas para este paciente.")
            return

        ventana = tk.Toplevel(self.root)
        ventana.title(f"Seleccionar Historia Médica a editar — Paciente {pid}")
        ventana.geometry("720x400")

        tree = ttk.Treeview(ventana, columns=("id", "fecha", "evaluador"), show='headings', height=12)
        tree.heading("id", text="ID")
        tree.heading("fecha", text="Fecha Evaluación")
        tree.heading("evaluador", text="Evaluador")
        tree.column("id", width=60, anchor=tk.CENTER)
        tree.column("fecha", width=150, anchor=tk.CENTER)
        tree.column("evaluador", width=200, anchor=tk.W)
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        for h in historiales:
            tree.insert("", tk.END, values=(h['id'], h['fecha_evaluacion'], h['evaluador']))

        def _editar():
            sel = tree.selection()
            if not sel:
                messagebox.showwarning("Aviso", "Seleccione un registro de la lista.")
                return
            hid = int(tree.item(sel[0], "values")[0])
            registro = self.historia_med_mgr.obtener(hid)
            ventana.destroy()
            if not registro:
                messagebox.showerror("Error", "Registro no encontrado.")
                return
            self.hm_editando_id = hid
            self._hm_limpiar()
            self.hm_paciente_id.delete(0, tk.END)
            self.hm_paciente_id.insert(0, str(registro['paciente_id']))
            self._hm_cargar_paciente()
            self.hm_fecha_eval.delete(0, tk.END)
            self.hm_fecha_eval.insert(0, _mostrar_fecha(registro.get('fecha_evaluacion', '')))
            self.hm_evaluador.insert(0, registro.get('evaluador', '') or '')
            for nombre, campo in self.hm_campos.items():
                campo.insert("1.0", registro.get(nombre, '') or '')
            self.status_var.set(f"Editando historia médica ID: {hid} — presione Guardar para actualizar.")

        botones = ttk.Frame(ventana)
        botones.pack(fill=tk.X, padx=10, pady=10)
        ttk.Button(botones, text="Editar Seleccionado", style='Primary.TButton',
                   command=_editar).pack(side=tk.LEFT, padx=5)
        ttk.Button(botones, text="Eliminar Seleccionado",
                   command=lambda: self._eliminar_historia_medica_seleccionada(tree)).pack(side=tk.LEFT, padx=5)
        ttk.Button(botones, text="Cerrar", command=ventana.destroy).pack(side=tk.LEFT, padx=5)

    def _eliminar_historia_medica_seleccionada(self, tree):
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Seleccione un registro de la lista.")
            return
        hid = int(tree.item(sel[0], "values")[0])
        if messagebox.askyesno("Confirmar", f"¿Eliminar la historia médica ID {hid}?"):
            self.historia_med_mgr.eliminar(hid)
            if self.hm_editando_id == hid:
                self.hm_editando_id = None
            messagebox.showinfo("Eliminado", "Registro eliminado.")
            tree.delete(sel[0])

    def _cancelar_edicion_historia_medica(self):
        self.hm_editando_id = None
        self.status_var.set("Edición de historia médica cancelada.")

    def _hm_ver_ultimo(self):
        """Muestra el último registro de historia médica del paciente."""
        try:
            pid = int(self.hm_paciente_id.get().strip())
        except (ValueError, TypeError):
            messagebox.showerror("Error", "Ingrese un ID de paciente válido.")
            return

        historiales = self.historia_med_mgr.listar_por_paciente(pid)
        if not historiales:
            messagebox.showinfo("Sin registros", "No hay historias médicas para este paciente.")
            return

        ultimo = historiales[0]
        texto = self.historia_med_mgr.generar_texto_reporte(ultimo)

        win = tk.Toplevel(self.root)
        win.title(f"Historia Médica — Paciente {pid}")
        win.geometry("750x700")
        text = scrolledtext.ScrolledText(win, font=('Consolas', 10), bg=COLOR_WHITE)
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text.insert("1.0", texto)
        text.config(state=tk.DISABLED)

    def _hm_limpiar(self):
        """Limpia todos los campos del formulario."""
        self.hm_paciente_id.delete(0, tk.END)
        self.hm_nombre.config(state='normal')
        self.hm_nombre.delete(0, tk.END)
        self.hm_nombre.config(state='readonly')
        self.hm_evaluador.delete(0, tk.END)
        self.hm_fecha_eval.delete(0, tk.END)
        self.hm_fecha_eval.insert(0, date.today().strftime("%d-%m-%Y"))
        for campo in self.hm_campos.values():
            campo.delete("1.0", tk.END)

    # ==================================================================
    # PESTAÑA 3: ANTROPOMETRÍA
    # ==================================================================
    def _crear_pestana_antropometria(self):
        scroll = ScrollFrame(self.notebook, bg=COLOR_BG)
        self.notebook.add(scroll, text="  Antropometría  ")
        parent = scroll.inner

        ttk.Label(parent, text="Calculadora Antropométrica OMS (0-19 años)", style='Title.TLabel').pack(anchor=tk.W, padx=5)
        ttk.Label(parent, text="Estándares OMS 0-5 años + Referencia 2007 (AnthroPlus) para mayores de 5 años", style='Subtitle.TLabel').pack(anchor=tk.W, padx=5)
        ttk.Separator(parent, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5, padx=5)

        # --- Datos del niño ---
        datos_frame = ttk.LabelFrame(parent, text=" Datos del Niño ", padding=10)
        datos_frame.pack(fill=tk.X, padx=10, pady=5)

        r0 = ttk.Frame(datos_frame)
        r0.pack(fill=tk.X, pady=2)
        ttk.Label(r0, text="ID Paciente:").pack(side=tk.LEFT, padx=5)
        self.ant_paciente_id = ttk.Entry(r0, width=10)
        self.ant_paciente_id.pack(side=tk.LEFT, padx=5)
        ttk.Button(r0, text="Cargar", command=self._ant_cargar_paciente).pack(side=tk.LEFT, padx=5)
        self.ant_paciente_id.bind("<Return>", lambda e: self._ant_cargar_paciente())
        ttk.Label(r0, text="Nombre:").pack(side=tk.LEFT, padx=(20,5))
        self.ant_nombre = ttk.Entry(r0, width=25, state='readonly')
        self.ant_nombre.pack(side=tk.LEFT, padx=5)

        r1 = ttk.Frame(datos_frame)
        r1.pack(fill=tk.X, pady=2)
        ttk.Label(r1, text="Fecha nac.:").pack(side=tk.LEFT, padx=5)
        self.ant_fecha_nac = ttk.Entry(r1, width=12, state='readonly')
        self.ant_fecha_nac.pack(side=tk.LEFT, padx=5)
        ttk.Label(r1, text="Sexo:").pack(side=tk.LEFT, padx=(10,5))
        self.ant_sexo = ttk.Entry(r1, width=5, state='readonly')
        self.ant_sexo.pack(side=tk.LEFT, padx=5)
        ttk.Label(r1, text="Edad:").pack(side=tk.LEFT, padx=(10,5))
        self.ant_edad = ttk.Entry(r1, width=20, state='readonly')
        self.ant_edad.pack(side=tk.LEFT, padx=5)

        r2 = ttk.Frame(datos_frame)
        r2.pack(fill=tk.X, pady=2)
        ttk.Label(r2, text="Fecha visita:").pack(side=tk.LEFT, padx=5)
        self.ant_fecha_visita = ttk.Entry(r2, width=12)
        self.ant_fecha_visita.pack(side=tk.LEFT, padx=5)
        self.ant_fecha_visita.insert(0, date.today().strftime("%d-%m-%Y"))

        ttk.Separator(parent, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5, padx=5)

        # --- Mediciones ---
        med_frame = ttk.LabelFrame(parent, text=" Mediciones Antropométricas ", padding=10)
        med_frame.pack(fill=tk.X, padx=10, pady=5)

        rm_peso = ttk.Frame(med_frame)
        rm_peso.pack(fill=tk.X, pady=2)
        ttk.Label(rm_peso, text="Peso (kg):").pack(side=tk.LEFT, padx=5)
        self.ant_peso = ttk.Entry(rm_peso, width=10)
        self.ant_peso.pack(side=tk.LEFT, padx=5)

        rm_talla = ttk.Frame(med_frame)
        rm_talla.pack(fill=tk.X, pady=2)
        ttk.Label(rm_talla, text="Talla/Longitud (cm):").pack(side=tk.LEFT, padx=5)
        self.ant_talla = ttk.Entry(rm_talla, width=10)
        self.ant_talla.pack(side=tk.LEFT, padx=5)

        rm_tipo = ttk.Frame(med_frame)
        rm_tipo.pack(fill=tk.X, pady=2)
        ttk.Label(rm_tipo, text="Tipo medida:").pack(side=tk.LEFT, padx=5)
        self.ant_tipo_med = ttk.Combobox(rm_tipo, values=["Decúbito (L)", "Bipedestación (H)"], width=18, state="readonly")
        self.ant_tipo_med.pack(side=tk.LEFT, padx=5)
        self.ant_tipo_med.set("Decúbito (L)")

        rm_pc = ttk.Frame(med_frame)
        rm_pc.pack(fill=tk.X, pady=2)
        ttk.Label(rm_pc, text="Perímetro cefálico (cm):").pack(side=tk.LEFT, padx=5)
        self.ant_pc = ttk.Entry(rm_pc, width=10)
        self.ant_pc.pack(side=tk.LEFT, padx=5)

        rm_muac = ttk.Frame(med_frame)
        rm_muac.pack(fill=tk.X, pady=2)
        ttk.Label(rm_muac, text="MUAC (mm):").pack(side=tk.LEFT, padx=5)
        self.ant_muac = ttk.Entry(rm_muac, width=10)
        self.ant_muac.pack(side=tk.LEFT, padx=5)

        rm_tri = ttk.Frame(med_frame)
        rm_tri.pack(fill=tk.X, pady=2)
        ttk.Label(rm_tri, text="Pliegue triceps (mm):").pack(side=tk.LEFT, padx=5)
        self.ant_pliegue = ttk.Entry(rm_tri, width=10)
        self.ant_pliegue.pack(side=tk.LEFT, padx=5)

        rm_sub = ttk.Frame(med_frame)
        rm_sub.pack(fill=tk.X, pady=2)
        ttk.Label(rm_sub, text="Pliegue subescapular (mm):").pack(side=tk.LEFT, padx=5)
        self.ant_pliegue_sub = ttk.Entry(rm_sub, width=10)
        self.ant_pliegue_sub.pack(side=tk.LEFT, padx=5)

        rm_edema = ttk.Frame(med_frame)
        rm_edema.pack(fill=tk.X, pady=2)
        self.ant_edema = tk.StringVar(value="no")
        ttk.Label(rm_edema, text="Edema:").pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(rm_edema, text="Sí", variable=self.ant_edema, value="si", bg=COLOR_BG).pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(rm_edema, text="No", variable=self.ant_edema, value="no", bg=COLOR_BG).pack(side=tk.LEFT, padx=5)

        ttk.Separator(parent, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5, padx=5)

        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Button(btn_frame, text="Evaluar", style='Primary.TButton', command=self._ant_evaluar).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Ubicar en Gráfica", command=self._ant_ubicar_grafica).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Guardar", command=self._ant_guardar).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cargar/Editar", command=self._ant_cargar_evaluacion).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Limpiar", command=self._ant_limpiar).pack(side=tk.LEFT, padx=5)

        ttk.Separator(parent, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5, padx=5)

        res_frame = ttk.LabelFrame(parent, text=" Resultados ", padding=10)
        res_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        sel_res = ttk.LabelFrame(res_frame, text=" Indicador a Evaluar ", padding=5)
        sel_res.pack(fill=tk.X, pady=5)
        self.ant_indicador_var = tk.StringVar(value="lhfa")
        radio_grid = ttk.Frame(sel_res)
        radio_grid.pack(fill=tk.X, padx=5)
        for idx, (code, label) in enumerate(self.INDICADORES_RADIO):
            r, c = divmod(idx, 2)
            tk.Radiobutton(
                radio_grid, text=label, variable=self.ant_indicador_var, value=code,
                bg=COLOR_BG, font=('Segoe UI', 10),
                command=self._ant_cambiar_indicador
            ).grid(row=r, column=c, sticky=tk.W, padx=10, pady=2)
        self.ant_indicador = self.ant_indicador_var

        self.ant_resultado_frame = ttk.Frame(res_frame)
        self.ant_resultado_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.ant_resultado_text = tk.Text(self.ant_resultado_frame, height=16, font=('Consolas', 11),
                                          bg=COLOR_WHITE, relief=tk.FLAT, padx=15, pady=10)
        self.ant_resultado_text.pack(fill=tk.BOTH, expand=True)
        self.ant_resultado_text.insert("1.0", "Ingrese datos y presione 'Evaluar' para ver resultados.")
        self.ant_resultado_text.config(state=tk.DISABLED)

        self._resultado_actual = None
        self._ant_paciente_actual = None
        self._ant_cambiar_indicador()

    # ==================================================================
    # PESTAÑA 4: LABORATORIOS
    # ==================================================================
    def _crear_pestana_laboratorios(self):
        frame = ScrollFrame(self.notebook, bg=COLOR_BG)
        self.notebook.add(frame, text="  Laboratorios  ")
        parent = frame.inner

        ttk.Label(parent, text="Evaluación de Laboratorio en Nutrición Pediátrica", style='Title.TLabel').pack(anchor=tk.W, padx=5)
        ttk.Label(parent, text="Comparación de valores contra rangos normales según edad", style='Subtitle.TLabel').pack(anchor=tk.W, padx=5)
        ttk.Separator(parent, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5, padx=5)

        # --- Selección de Paciente ---
        sel_frame = ttk.LabelFrame(parent, text=" Paciente ", padding=10)
        sel_frame.pack(fill=tk.X, padx=10, pady=5)

        r0 = ttk.Frame(sel_frame)
        r0.pack(fill=tk.X, pady=2)
        ttk.Label(r0, text="ID Paciente:").pack(side=tk.LEFT, padx=5)
        self.lab_paciente_id = ttk.Entry(r0, width=10)
        self.lab_paciente_id.pack(side=tk.LEFT, padx=5)
        ttk.Button(r0, text="Cargar Paciente", command=self._lab_cargar_paciente).pack(side=tk.LEFT, padx=5)
        self.lab_paciente_id.bind("<Return>", lambda e: self._lab_cargar_paciente())

        r0b = ttk.Frame(sel_frame)
        r0b.pack(fill=tk.X, pady=2)
        ttk.Label(r0b, text="Nombre:").pack(side=tk.LEFT, padx=5)
        self.lab_nombre = ttk.Entry(r0b, width=30, state='readonly')
        self.lab_nombre.pack(side=tk.LEFT, padx=5)
        ttk.Label(r0b, text="Sexo:").pack(side=tk.LEFT, padx=5)
        self.lab_sexo = ttk.Entry(r0b, width=5, state='readonly')
        self.lab_sexo.pack(side=tk.LEFT, padx=5)
        ttk.Label(r0b, text="Edad:").pack(side=tk.LEFT, padx=5)
        self.lab_edad = ttk.Entry(r0b, width=15, state='readonly')
        self.lab_edad.pack(side=tk.LEFT, padx=5)

        ttk.Separator(parent, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5, padx=5)

        # --- Captura de la Prueba ---
        prueba_frame = ttk.LabelFrame(parent, text=" Nueva Prueba de Laboratorio ", padding=10)
        prueba_frame.pack(fill=tk.X, padx=10, pady=5)

        rp1 = ttk.Frame(prueba_frame)
        rp1.pack(fill=tk.X, pady=2)
        ttk.Label(rp1, text="Prueba:").pack(side=tk.LEFT, padx=5)
        self.lab_codigos = listar_pruebas()
        nombres = [obtener_prueba(c)["nombre"] for c in self.lab_codigos]
        self.lab_combo_prueba = ttk.Combobox(rp1, values=nombres, width=45, state="readonly")
        self.lab_combo_prueba.pack(side=tk.LEFT, padx=5)
        if nombres:
            self.lab_combo_prueba.current(0)
        self.lab_combo_prueba.bind("<<ComboboxSelected>>", self._lab_mostrar_info_prueba)
        ttk.Label(rp1, text="Fecha de toma:").pack(side=tk.LEFT, padx=5)
        self.lab_fecha_toma = ttk.Entry(rp1, width=15)
        self.lab_fecha_toma.insert(0, date.today().strftime("%d-%m-%Y"))
        self.lab_fecha_toma.pack(side=tk.LEFT, padx=5)

        rp2 = ttk.Frame(prueba_frame)
        rp2.pack(fill=tk.X, pady=2)
        ttk.Label(rp2, text="Valor:").pack(side=tk.LEFT, padx=5)
        self.lab_valor = ttk.Entry(rp2, width=15)
        self.lab_valor.pack(side=tk.LEFT, padx=5)
        ttk.Label(rp2, text="Unidad:").pack(side=tk.LEFT, padx=5)
        self.lab_combo_unidad = ttk.Combobox(rp2, values=[], width=12, state="readonly")
        self.lab_combo_unidad.pack(side=tk.LEFT, padx=5)
        ttk.Button(rp2, text="Evaluar y Guardar", style='Primary.TButton',
                   command=self._lab_evaluar_guardar).pack(side=tk.LEFT, padx=10)

        self.lab_info_prueba = ttk.Label(prueba_frame, text="", wraplength=1000, justify=tk.LEFT)
        self.lab_info_prueba.pack(fill=tk.X, padx=5, pady=5)
        self._lab_mostrar_info_prueba()

        ttk.Separator(parent, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5, padx=5)

        # --- Resultado de la última evaluación ---
        res_frame = ttk.LabelFrame(parent, text=" Resultado ", padding=10)
        res_frame.pack(fill=tk.X, padx=10, pady=5)
        self.lab_resultado_lbl = ttk.Label(res_frame, text="Sin evaluar.", font=('Segoe UI', 11, 'bold'))
        self.lab_resultado_lbl.pack(anchor=tk.W, padx=5)

        ttk.Separator(parent, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5, padx=5)

        # --- Historial de laboratorios ---
        hist_frame = ttk.LabelFrame(parent, text=" Historial de Laboratorios del Paciente ", padding=10)
        hist_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        cols = ("ID", "Fecha", "Prueba", "Valor", "Unidad", "Rango de referencia", "Resultado")
        self.tree_laboratorios = ttk.Treeview(hist_frame, columns=cols, show='headings', height=10)
        for c in cols:
            self.tree_laboratorios.heading(c, text=c)
            self.tree_laboratorios.column(c, width=120, anchor=tk.CENTER)
        self.tree_laboratorios.column("ID", width=40)
        self.tree_laboratorios.column("Prueba", width=200, anchor=tk.W)
        self.tree_laboratorios.column("Rango de referencia", width=180, anchor=tk.W)
        lab_scroll = ttk.Scrollbar(hist_frame, orient=tk.VERTICAL, command=self.tree_laboratorios.yview)
        self.tree_laboratorios.configure(yscrollcommand=lab_scroll.set)
        self.tree_laboratorios.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        lab_scroll.pack(fill=tk.Y, side=tk.RIGHT)

        btn_hist = ttk.Frame(parent)
        btn_hist.pack(fill=tk.X, padx=10, pady=5)
        ttk.Button(btn_hist, text="Editar Registro Seleccionado", command=self._lab_editar_seleccionado).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_hist, text="Eliminar Registro Seleccionado", command=self._lab_eliminar_seleccionado).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_hist, text="Cancelar Edición", command=self._lab_cancelar_edicion).pack(side=tk.LEFT, padx=5)

    def _lab_mostrar_info_prueba(self, event=None):
        idx = self.lab_combo_prueba.current()
        if idx < 0 or idx >= len(self.lab_codigos):
            return
        codigo = self.lab_codigos[idx]
        prueba = obtener_prueba(codigo)
        unidades = unidades_disponibles(codigo)
        self.lab_combo_unidad.config(values=unidades)
        self.lab_combo_unidad.current(0)
        info = f"{prueba.get('descripcion', '')}"
        if prueba.get('deficiencia'):
            info += f"\nDeficiencia: {prueba['deficiencia']}"
        if prueba.get('pitfalls'):
            info += f"\nAtención: {prueba['pitfalls']}"
        self.lab_info_prueba.config(text=info)

    def _lab_cargar_paciente(self):
        """Carga datos del paciente en la pestaña de laboratorios."""
        pid = self.patient_mgr.resolver_id_a_database_id(self.lab_paciente_id.get())
        if pid is None:
            messagebox.showerror("Error", "Ingrese un ID válido (ej: 1 o 1.2).")
            return

        paciente = self.patient_mgr.obtener_paciente(pid)
        if not paciente:
            messagebox.showerror("Error", "Paciente no encontrado.")
            return

        self.lab_nombre.config(state='normal')
        self.lab_nombre.delete(0, tk.END)
        self.lab_nombre.insert(0, paciente['nombre'])
        self.lab_nombre.config(state='readonly')

        self.lab_sexo.config(state='normal')
        self.lab_sexo.delete(0, tk.END)
        self.lab_sexo.insert(0, paciente['sexo'])
        self.lab_sexo.config(state='readonly')

        from datetime import date as date_cls
        try:
            fn = date_cls.fromisoformat(paciente['fecha_nacimiento'])
            edad_txt = calcular_edad_texto(fn, date_cls.today())
        except ValueError:
            edad_txt = ""
        self.lab_edad.config(state='normal')
        self.lab_edad.delete(0, tk.END)
        self.lab_edad.insert(0, edad_txt)
        self.lab_edad.config(state='readonly')

        self._lab_cargar_historial()
        self.status_var.set(f"Paciente {paciente['nombre']} cargado en Laboratorios")

    def _lab_evaluar_guardar(self):
        """Evalúa el valor de laboratorio ingresado contra el rango normal y lo guarda."""
        try:
            pid = int(self.lab_paciente_id.get().strip())
        except (ValueError, TypeError):
            messagebox.showerror("Error", "Ingrese un ID de paciente válido.")
            return

        paciente = self.patient_mgr.obtener_paciente(pid)
        if not paciente:
            messagebox.showerror("Error", "Paciente no encontrado.")
            return

        idx = self.lab_combo_prueba.current()
        if idx < 0:
            messagebox.showerror("Error", "Seleccione una prueba de laboratorio.")
            return
        codigo = self.lab_codigos[idx]
        prueba = obtener_prueba(codigo)
        unidad_ingresada = self.lab_combo_unidad.get() or prueba.get("unidad", "")

        valor = self.lab_valor.get().strip()
        if not valor:
            messagebox.showwarning("Campo requerido", "Ingrese el valor de la prueba.")
            return

        try:
            fecha_toma = _parsear_fecha(self.lab_fecha_toma.get())
        except ValueError:
            messagebox.showerror("Error", "Fecha de toma inválida (DD-MM-AAAA).")
            return

        fecha_nac = date.fromisoformat(paciente['fecha_nacimiento'])
        edad_meses = calcular_edad_meses(fecha_nac, fecha_toma)

        resultado = clasificar_resultado(codigo, valor, edad_meses, paciente['sexo'], unidad_ingresada)
        if "error" in resultado:
            messagebox.showerror("Error", resultado["error"])
            return

        observaciones = ""
        if unidad_ingresada != prueba.get("unidad", ""):
            observaciones = f"Valor original: {valor} {unidad_ingresada}"

        if self.lab_editando_id is not None:
            self.laboratorio_mgr.actualizar(
                self.lab_editando_id, fecha_toma, prueba["nombre"], f"{resultado['valor']:.4g}",
                prueba.get("unidad", ""), edad_meses, resultado["clasificacion"],
                resultado["rango_texto"], observaciones
            )
            self.lab_resultado_lbl.config(
                text=(f"Actualizado → {prueba['nombre']}: {valor} {unidad_ingresada}  →  "
                      f"{resultado['valor']:.4g} {prueba.get('unidad', '')}  →  "
                      f"{resultado['clasificacion']}  (Referencia: {resultado['rango_texto']})")
            )
            self.status_var.set(f"Resultado de laboratorio actualizado (ID: {self.lab_editando_id})")
            self.lab_editando_id = None
            self.lab_valor.delete(0, tk.END)
            self._lab_cargar_historial()
            return

        self.laboratorio_mgr.guardar(
            pid, fecha_toma, prueba["nombre"], f"{resultado['valor']:.4g}", prueba.get("unidad", ""),
            edad_meses, resultado["clasificacion"], resultado["rango_texto"], observaciones
        )

        self.lab_resultado_lbl.config(
            text=(f"{prueba['nombre']}: {valor} {unidad_ingresada}  →  {resultado['valor']:.4g} "
                  f"{prueba.get('unidad', '')}  →  {resultado['clasificacion']}  "
                  f"(Referencia: {resultado['rango_texto']} — {resultado['etiqueta_rango']})")
        )
        self.status_var.set(f"Resultado de laboratorio guardado: {resultado['clasificacion']}")
        self.lab_valor.delete(0, tk.END)
        self._lab_cargar_historial()

    def _lab_cargar_historial(self):
        try:
            pid = int(self.lab_paciente_id.get().strip())
        except (ValueError, TypeError):
            return
        for item in self.tree_laboratorios.get_children():
            self.tree_laboratorios.delete(item)
        registros = self.laboratorio_mgr.listar_por_paciente(pid)
        for r in registros:
            self.tree_laboratorios.insert("", tk.END, values=(
                r['id'], _mostrar_fecha(r['fecha_toma']), r['tipo_prueba'], r['valor'], r['unidad'],
                r['rango_referencia'], r['resultado_clasificacion']
            ))
        self.status_var.set(f"{len(registros)} resultado(s) de laboratorio")

    def _lab_eliminar_seleccionado(self):
        sel = self.tree_laboratorios.selection()
        if not sel:
            messagebox.showwarning("Seleccionar", "Seleccione un registro de la lista.")
            return
        if messagebox.askyesno("Confirmar", "¿Eliminar el registro de laboratorio seleccionado?"):
            vals = self.tree_laboratorios.item(sel[0], 'values')
            if self.lab_editando_id == int(vals[0]):
                self.lab_editando_id = None
            self.laboratorio_mgr.eliminar(int(vals[0]))
            self._lab_cargar_historial()

    def _lab_editar_seleccionado(self):
        """Carga el registro de laboratorio seleccionado en el formulario para editarlo."""
        sel = self.tree_laboratorios.selection()
        if not sel:
            messagebox.showwarning("Seleccionar", "Seleccione un registro de la lista.")
            return
        vals = self.tree_laboratorios.item(sel[0], 'values')
        rid = int(vals[0])
        registro = self.laboratorio_mgr.obtener(rid)
        if not registro:
            messagebox.showerror("Error", "Registro no encontrado.")
            return

        nombres = [obtener_prueba(c)["nombre"] for c in self.lab_codigos]
        idx = -1
        for i, n in enumerate(nombres):
            if n == registro['tipo_prueba']:
                idx = i
                break
        if idx < 0:
            messagebox.showerror("Error", "Prueba no reconocida en el catálogo.")
            return

        self.lab_editando_id = rid
        self.lab_combo_prueba.current(idx)
        self._lab_mostrar_info_prueba()

        unidades = unidades_disponibles(self.lab_codigos[idx])
        self.lab_combo_unidad.config(values=unidades)
        if registro['unidad'] in unidades:
            self.lab_combo_unidad.set(registro['unidad'])
        else:
            self.lab_combo_unidad.current(0)

        self.lab_valor.delete(0, tk.END)
        self.lab_valor.insert(0, registro['valor'])
        if registro.get('fecha_toma'):
            self.lab_fecha_toma.delete(0, tk.END)
            self.lab_fecha_toma.insert(0, _mostrar_fecha(registro['fecha_toma']))
        self.lab_resultado_lbl.config(
            text=f"Editando registro ID {rid} — {registro['tipo_prueba']} ({registro['resultado_clasificacion']}). "
                 "Modifique los campos y presione 'Evaluar y Guardar' para actualizar."
        )
        self.status_var.set(f"Editando laboratorio ID: {rid} — presione Evaluar y Guardar.")

    def _lab_cancelar_edicion(self):
        self.lab_editando_id = None
        self.lab_resultado_lbl.config(text="Sin evaluar.")
        self.status_var.set("Edición de laboratorio cancelada.")

    def _ant_cargar_paciente(self):
        pid = self.patient_mgr.resolver_id_a_database_id(self.ant_paciente_id.get())
        if pid is None:
            messagebox.showerror("Error", "Ingrese un ID válido (ej: 1 o 1.2).")
            return
        paciente = self.patient_mgr.obtener_paciente(pid)
        if not paciente:
            messagebox.showerror("Error", "Paciente no encontrado.")
            return

        self._ant_paciente_actual = pid

        self.ant_nombre.config(state='normal')
        self.ant_nombre.delete(0, tk.END)
        self.ant_nombre.insert(0, paciente['nombre'])
        self.ant_nombre.config(state='readonly')

        self.ant_fecha_nac.config(state='normal')
        self.ant_fecha_nac.delete(0, tk.END)
        self.ant_fecha_nac.insert(0, _mostrar_fecha(paciente['fecha_nacimiento']))
        self.ant_fecha_nac.config(state='readonly')

        self.ant_sexo.config(state='normal')
        self.ant_sexo.delete(0, tk.END)
        self.ant_sexo.insert(0, paciente['sexo'])
        self.ant_sexo.config(state='readonly')

        from datetime import date as date_cls
        try:
            fn = date_cls.fromisoformat(paciente['fecha_nacimiento'])
            edad_txt = calcular_edad_texto(fn, date_cls.today())
        except ValueError:
            edad_txt = ""
        self.ant_edad.config(state='normal')
        self.ant_edad.delete(0, tk.END)
        self.ant_edad.insert(0, edad_txt)
        self.ant_edad.config(state='readonly')

        if paciente['peso_kg']:
            self.ant_peso.delete(0, tk.END)
            self.ant_peso.insert(0, str(paciente['peso_kg']))
        if paciente['talla_cm']:
            self.ant_talla.delete(0, tk.END)
            self.ant_talla.insert(0, str(paciente['talla_cm']))

        self.status_var.set(f"Paciente {paciente['nombre']} cargado en Antropometría")

    def _ant_leer_campos(self):
        peso = None
        if self.ant_peso.get().strip():
            peso = float(self.ant_peso.get().strip())
        talla = None
        if self.ant_talla.get().strip():
            talla = float(self.ant_talla.get().strip())
        tipo_med = "L" if "Dec" in self.ant_tipo_med.get() else "H"
        edema = self.ant_edema.get() == "si"
        pc = None
        if self.ant_pc.get().strip():
            pc = float(self.ant_pc.get().strip())
        muac = None
        if self.ant_muac.get().strip():
            muac = float(self.ant_muac.get().strip())
        pliegue = None
        if self.ant_pliegue.get().strip():
            pliegue = float(self.ant_pliegue.get().strip())
        pliegue_sub = None
        if self.ant_pliegue_sub.get().strip():
            pliegue_sub = float(self.ant_pliegue_sub.get().strip())
        return peso, talla, tipo_med, edema, pc, muac, pliegue, pliegue_sub

    def _ant_evaluar(self):
        from datetime import date as date_cls
        from src.modules.who_anthro_calc import evaluar_antropometria

        try:
            pid = int(self.ant_paciente_id.get().strip())
        except (ValueError, TypeError):
            messagebox.showerror("Error", "Ingrese un ID de paciente válido.")
            return
        paciente = self.patient_mgr.obtener_paciente(pid)
        if not paciente:
            messagebox.showerror("Error", "Paciente no encontrado.")
            return

        try:
            fecha_nac = date_cls.fromisoformat(paciente['fecha_nacimiento'])
        except ValueError:
            messagebox.showerror("Error", "Fecha de nacimiento inválida.")
            return

        try:
            fecha_visita = _parsear_fecha(self.ant_fecha_visita.get().strip())
        except ValueError:
            messagebox.showerror("Error", "Fecha de visita inválida (DD-MM-AAAA).")
            return

        try:
            peso, talla, tipo_med, edema, pc, muac, pliegue, pliegue_sub = self._ant_leer_campos()
        except ValueError:
            messagebox.showerror("Error", "Los valores deben ser numéricos.")
            return

        if peso is None and talla is None:
            messagebox.showerror("Error", "Ingrese al menos peso o talla.")
            return

        resultado = evaluar_antropometria(
            sexo=paciente['sexo'],
            fecha_nacimiento=fecha_nac,
            fecha_visita=fecha_visita,
            peso_kg=peso,
            talla_cm=talla,
            tipo_medicion=tipo_med,
            edema=edema,
            pc_cm=pc,
            muac_mm=muac,
            pliegue_triceps_mm=pliegue,
            pliegue_subescapular_mm=pliegue_sub,
        )

        if resultado['errores']:
            messagebox.showerror("Error", "\n".join(resultado['errores']))
            return

        self._resultado_actual = resultado
        self._ant_mostrar_indicador()
        if resultado.get('edad_meses_decimal') is not None and resultado['edad_meses_decimal'] >= 60:
            ref = "Referencia 2007 (AnthroPlus)"
        else:
            ref = "Estándares OMS 0-5 años"
        self.status_var.set(f"Evaluación antropométrica completada — {ref}")

    def _ant_guardar(self):
        """Guarda la evaluación antropométrica actual del paciente en la BD."""
        from datetime import date as date_cls
        r = self._resultado_actual
        pid = self._ant_paciente_actual
        if pid is None:
            try:
                pid = int(self.ant_paciente_id.get().strip())
            except (ValueError, TypeError):
                messagebox.showerror("Error", "Cargue primero un paciente para guardar.")
                return
        if r is None:
            messagebox.showwarning("Aviso", "Primero presione 'Evaluar' para generar resultados.")
            return

        try:
            fecha_visita = _parsear_fecha(self.ant_fecha_visita.get().strip())
        except ValueError:
            messagebox.showerror("Error", "Fecha de visita inválida (DD-MM-AAAA).")
            return

        tipo_med = "L" if "Dec" in self.ant_tipo_med.get() else "H"
        campos = {
            "peso_kg": r.get("peso_kg"),
            "talla_cm": r.get("talla_original_cm"),
            "tipo_medicion": tipo_med,
            "edema": 1 if r.get("edema") else 0,
            "pc_cm": r.get("pc_cm"),
            "muac_mm": r.get("muac_mm"),
            "pliegue_triceps_mm": r.get("pliegue_triceps_mm"),
            "pliegue_subescapular_mm": r.get("pliegue_subescapular_mm"),
            "edad_dias": r.get("edad_dias"),
            "edad_meses_completos": r.get("edad_meses_completos"),
            "edad_meses_decimal": r.get("edad_meses_decimal"),
        }
        for key in self.INDICADORES_MAP:
            zk, pk, ck, fk = self.INDICADORES_MAP[key]
            campos[zk] = r.get(zk)
            campos[pk] = r.get(pk)
            campos[ck] = r.get(ck)
            if fk:
                campos[fk] = r.get(fk)

        try:
            evaluacion_id = self.antropometria_mgr.guardar(
                pid, fecha_visita, "", campos)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar: {e}")
            return
        messagebox.showinfo("Guardado",
                            f"Evaluación guardada (ID {evaluacion_id}) para el paciente {pid}.")
        self.status_var.set(f"Evaluación guardada (ID {evaluacion_id})")

    def _ant_cargar_evaluacion(self):
        """Permite seleccionar y cargar una evaluación previa del paciente para editarla."""
        try:
            pid = int(self.ant_paciente_id.get().strip())
        except (ValueError, TypeError):
            messagebox.showerror("Error", "Ingrese/cargue primero un ID de paciente.")
            return
        lista = self.antropometria_mgr.listar_por_paciente(pid)
        if not lista:
            try:
                pid = self._ant_paciente_actual
            except Exception:
                pass
            lista = self.antropometria_mgr.listar_por_paciente(pid) if pid else []
            if not lista:
                messagebox.showinfo("Sin registros", "No hay evaluaciones guardadas para este paciente.")
                return

        ventana = tk.Toplevel(self.root)
        ventana.title(f"Evaluaciones del paciente {pid}")
        ventana.geometry("640x380")
        ventana.transient(self.root)

        ttk.Label(ventana, text="Seleccione una evaluación para cargar y editar:",
                  font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W, padx=10, pady=8)

        tree = ttk.Treeview(ventana, columns=("fecha", "edad", "peso", "talla", "pc", "z"),
                            show="headings", height=10)
        tree.heading("fecha", text="Fecha visita")
        tree.heading("edad", text="Edad (meses)")
        tree.heading("peso", text="Peso (kg)")
        tree.heading("talla", text="Talla (cm)")
        tree.heading("pc", text="PC (cm)")
        tree.heading("z", text="Z lhfa")
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        tree.column("fecha", width=100, anchor=tk.W)
        tree.column("edad", width=80, anchor=tk.CENTER)
        tree.column("peso", width=80, anchor=tk.CENTER)
        tree.column("talla", width=80, anchor=tk.CENTER)
        tree.column("pc", width=80, anchor=tk.CENTER)
        tree.column("z", width=80, anchor=tk.CENTER)

        for ev in lista:
            zval = ev.get("z_lhfa")
            ztxt = f"{zval:+.2f}" if zval is not None else "N/A"
            tree.insert("", tk.END, iid=str(ev["id"]), values=(
                _mostrar_fecha(ev["fecha_visita"]),
                ev.get("edad_meses_decimal") or "",
                ev.get("peso_kg") or "",
                ev.get("talla_cm") or "",
                ev.get("pc_cm") or "",
                ztxt,
            ))

        def _cargar_seleccionada():
            sel = tree.selection()
            if not sel:
                messagebox.showwarning("Aviso", "Seleccione una evaluación.")
                return
            ev_id = int(sel[0])
            ev = self.antropometria_mgr.obtener(ev_id)
            if not ev:
                messagebox.showerror("Error", "No se encontró la evaluación.")
                return
            self._ant_paciente_actual = pid
            self.ant_paciente_id.delete(0, tk.END)
            self.ant_paciente_id.insert(0, str(pid))
            self._ant_cargar_paciente()

            self.ant_fecha_visita.delete(0, tk.END)
            self.ant_fecha_visita.insert(0, _mostrar_fecha(ev["fecha_visita"]))

            def _set(entry, val):
                entry.delete(0, tk.END)
                if val is not None:
                    entry.insert(0, str(val))
            _set(self.ant_peso, ev.get("peso_kg"))
            _set(self.ant_talla, ev.get("talla_cm"))
            _set(self.ant_pc, ev.get("pc_cm"))
            _set(self.ant_muac, ev.get("muac_mm"))
            _set(self.ant_pliegue, ev.get("pliegue_triceps_mm"))
            _set(self.ant_pliegue_sub, ev.get("pliegue_subescapular_mm"))

            tipo = ev.get("tipo_medicion") or "L"
            self.ant_tipo_med.set("Decúbito (L)" if tipo == "L" else "Bipedestación (H)")
            self.ant_edema.set("si" if ev.get("edema") else "no")

            ventana.destroy()
            messagebox.showinfo("Cargado",
                                "Evaluación cargada. Edite los campos y presione 'Evaluar' y luego 'Guardar'.")

        btn_row = ttk.Frame(ventana)
        btn_row.pack(fill=tk.X, padx=10, pady=5)
        ttk.Button(btn_row, text="Cargar seleccionada", style='Primary.TButton',
                   command=_cargar_seleccionada).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_row, text="Cancelar", command=ventana.destroy).pack(side=tk.LEFT, padx=5)

    INDICADORES_MAP = {
        "lhfa": ("z_lhfa", "perc_lhfa", "clasif_lhfa", "flag_lhfa"),
        "wfa": ("z_wfa", "perc_wfa", "clasif_wfa", "flag_wfa"),
        "wflh": ("z_wflh", "perc_wflh", "clasif_wflh", "flag_wflh"),
        "bmi": ("z_bmi", "perc_bmi", "clasif_bmi", "flag_bmi"),
        "hcfa": ("z_pc", "perc_pc", "clasif_pc", None),
        "acfa": ("z_acfa", "perc_acfa", "clasif_muac", "flag_acfa"),
        "tsfa": ("z_tsfa", "perc_tsfa", "clasif_tsfa", None),
        "ssfa": ("z_ssfa", "perc_ssfa", "clasif_ssfa", None),
    }

    INDICADOR_CAMPOS = {
        "lhfa": ["ant_talla", "ant_tipo_med"],
        "wfa": ["ant_peso"],
        "wflh": ["ant_peso", "ant_talla", "ant_tipo_med"],
        "bmi": ["ant_peso", "ant_talla", "ant_tipo_med"],
        "hcfa": ["ant_pc"],
        "acfa": ["ant_muac"],
        "tsfa": ["ant_pliegue"],
        "ssfa": ["ant_pliegue_sub"],
    }

    INDICADOR_NOMBRES = {
        "lhfa": "Longitud/Altura-Edad",
        "wfa": "Peso-Edad",
        "wflh": "Peso-Longitud/Altura",
        "bmi": "IMC-Edad",
        "hcfa": "Perímetro Cefálico-Edad",
        "acfa": "MUAC-Edad",
        "tsfa": "Pliegue Tríceps-Edad",
        "ssfa": "Pliegue Subescapular-Edad",
    }

    INDICADORES_RADIO = [
        ("lhfa", "Longitud/Altura-Edad"),
        ("wfa", "Peso-Edad"),
        ("wflh", "Peso-Longitud/Altura"),
        ("bmi", "IMC-Edad"),
        ("hcfa", "Perímetro Cefálico-Edad"),
        ("acfa", "MUAC-Edad"),
        ("tsfa", "Pliegue Tríceps-Edad"),
        ("ssfa", "Pliegue Subescapular-Edad"),
    ]

    def _ant_cambiar_indicador(self):
        codigo = self.ant_indicador_var.get()
        campos_requeridos = self.INDICADOR_CAMPOS.get(codigo, [])
        for attr_name in ["ant_peso", "ant_talla", "ant_tipo_med", "ant_pc",
                          "ant_muac", "ant_pliegue", "ant_pliegue_sub"]:
            widget = getattr(self, attr_name, None)
            if widget is None:
                continue
            parent_frame = widget.master
            if attr_name in campos_requeridos:
                try:
                    parent_frame.pack(fill=tk.X, pady=2)
                except Exception:
                    pass
            else:
                try:
                    parent_frame.pack_forget()
                except Exception:
                    pass
        if self._resultado_actual is not None:
            self._ant_mostrar_indicador()

    def _ant_mostrar_indicador(self, event=None):
        r = self._resultado_actual
        if r is None:
            return

        codigo = self.ant_indicador_var.get()
        nombre = self.INDICADOR_NOMBRES.get(codigo, codigo)
        z_key, perc_key, clasif_key, flag_key = self.INDICADORES_MAP.get(codigo, (None, None, None, None))

        z_val = r.get(z_key) if z_key else None
        perc_val = r.get(perc_key) if perc_key else None
        clasif_val = r.get(clasif_key, "N/A") if clasif_key else "N/A"
        flag_val = r.get(flag_key, 0) if flag_key else 0

        t = self.ant_resultado_text
        t.config(state='normal')
        t.delete("1.0", tk.END)

        t.insert("1.0", f"\n  {nombre}\n")
        t.insert(tk.END, f"\n  {'=' * 48}\n")

        if codigo == "lhfa":
            med_val = f"{r.get('talla_cm', r.get('talla_original_cm', ''))} cm"
        elif codigo == "wfa":
            med_val = f"{r.get('peso_kg', '')} kg"
        elif codigo == "wflh":
            med_val = f"{r.get('peso_kg', '')} kg / {r.get('talla_cm', r.get('talla_original_cm', ''))} cm"
        elif codigo == "bmi":
            med_val = f"{r.get('imc', '')} kg/m²"
        elif codigo == "hcfa":
            med_val = f"{r.get('pc_cm', '')} cm"
        elif codigo == "acfa":
            med_val = f"{r.get('muac_mm', '')} mm"
        elif codigo == "tsfa":
            med_val = f"{r.get('pliegue_triceps_mm', '')} mm"
        elif codigo == "ssfa":
            med_val = f"{r.get('pliegue_subescapular_mm', '')} mm"
        else:
            med_val = ""
        t.insert(tk.END, f"\n  Valor medido:   {med_val}\n")

        if z_val is not None:
            color_z = "▼" if z_val < -2 else ("▲" if z_val > 2 else "●")
            t.insert(tk.END, f"\n  Z-score:        {z_val:+.2f}  {color_z}\n")
        else:
            t.insert(tk.END, "\n  Z-score:        N/A\n")

        if perc_val is not None:
            t.insert(tk.END, f"\n  Percentil (P):  {perc_val:.1f}%\n")
        else:
            t.insert(tk.END, "\n  Percentil (P):  N/A\n")

        t.insert(tk.END, f"\n  Clasificación:  {clasif_val}\n")

        if flag_val and flag_val != 0:
            t.insert(tk.END, f"\n  Bandera:        ±{abs(flag_val)} (fuera de rango)\n")

        t.insert(tk.END, f"\n  {'=' * 48}\n")
        t.insert(tk.END, f"\n  Todos los indicadores:\n\n")

        for ind_code in self.INDICADORES_MAP:
            zk, pk, ck, fk = self.INDICADORES_MAP[ind_code]
            ind_nombre = self.INDICADOR_NOMBRES.get(ind_code, ind_code)
            zv = r.get(zk)
            pv = r.get(pk)
            cv = r.get(ck, "N/A")
            z_str = f"{zv:+.2f}" if zv is not None else "  N/A"
            p_str = f"P{pv:.0f}" if pv is not None else " N/A"
            marker = " ◄" if ind_code == codigo else ""
            t.insert(tk.END, f"  {ind_nombre:.<32s} Z={z_str:>7s}  {p_str:>5s}  {cv}{marker}\n")

        t.config(state=tk.DISABLED)

    def _ant_ubicar_grafica(self):
        from datetime import date as date_cls
        from src.modules.who_anthro_calc import evaluar_antropometria
        from src.modules.who_growth_charts import CHART_MAP

        try:
            pid = int(self.ant_paciente_id.get().strip())
        except (ValueError, TypeError):
            messagebox.showerror("Error", "Ingrese un ID de paciente válido.")
            return
        paciente = self.patient_mgr.obtener_paciente(pid)
        if not paciente:
            messagebox.showerror("Error", "Paciente no encontrado.")
            return

        try:
            peso, talla, tipo_med, edema, pc, muac, pliegue, pliegue_sub = self._ant_leer_campos()
        except ValueError:
            messagebox.showerror("Error", "Los valores deben ser numéricos.")
            return

        indicador = self.ant_indicador_var.get()

        if indicador in ("lhfa", "wflh", "bmi") and talla is None:
            messagebox.showerror("Error", f"Ingrese talla/longitud para graficar {self.INDICADOR_NOMBRES.get(indicador, indicador)}.")
            return
        if indicador == "wfa" and peso is None:
            messagebox.showerror("Error", "Ingrese peso para graficar Peso-Edad.")
            return
        if indicador == "hcfa" and pc is None:
            messagebox.showerror("Error", "Ingrese perímetro cefálico para graficar PC-Edad.")
            return
        if indicador == "acfa" and muac is None:
            messagebox.showerror("Error", "Ingrese MUAC para graficar MUAC-Edad.")
            return
        if indicador == "tsfa" and pliegue is None:
            messagebox.showerror("Error", "Ingrese pliegue tríceps para graficar.")
            return
        if indicador == "ssfa" and pliegue_sub is None:
            messagebox.showerror("Error", "Ingrese pliegue subescapular para graficar.")
            return

        try:
            fecha_nac = date_cls.fromisoformat(paciente['fecha_nacimiento'])
            fecha_visita = _parsear_fecha(self.ant_fecha_visita.get().strip())
        except ValueError:
            messagebox.showerror("Error", "Fechas inválidas.")
            return

        resultado = evaluar_antropometria(
            sexo=paciente['sexo'],
            fecha_nacimiento=fecha_nac,
            fecha_visita=fecha_visita,
            peso_kg=peso,
            talla_cm=talla,
            tipo_medicion=tipo_med,
            edema=edema,
            pc_cm=pc,
            muac_mm=muac,
            pliegue_triceps_mm=pliegue,
            pliegue_subescapular_mm=pliegue_sub,
        )

        if resultado['errores']:
            messagebox.showerror("Error", "\n".join(resultado['errores']))
            return

        chart_func = CHART_MAP.get(indicador)
        if chart_func is None:
            messagebox.showerror("Error", f"No hay gráfica disponible para {self.INDICADOR_NOMBRES.get(indicador, indicador)}.")
            return

        ventana = tk.Toplevel(self.root)
        ventana.title(f"Gráfica OMS — {self.INDICADOR_NOMBRES.get(indicador, indicador)}")
        ventana.geometry("920x680")
        ventana.transient(self.root)

        info_frame = ttk.Frame(ventana)
        info_frame.pack(fill=tk.X, padx=10, pady=5)
        sexo_txt = "Niño" if paciente['sexo'] == 'M' else "Niña"
        info = f"{paciente['nombre']} | {sexo_txt} | {resultado['edad_meses_completos']} meses"
        if peso:
            info += f" | Peso: {peso} kg"
        if talla:
            info += f" | Talla: {talla} cm"
        if pc:
            info += f" | PC: {pc} cm"
        if muac:
            info += f" | MUAC: {muac} mm"
        ttk.Label(info_frame, text=info, font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W)

        mode_var = tk.StringVar(value="zscore")
        mode_frame = ttk.Frame(ventana)
        mode_frame.pack(fill=tk.X, padx=10, pady=2)
        ttk.Label(mode_frame, text="Modo:").pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(mode_frame, text="Z-Scores (SD)", variable=mode_var, value="zscore",
                       bg=COLOR_BG, font=('Segoe UI', 10)).pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(mode_frame, text="Percentiles (P3-P97)", variable=mode_var, value="percentil",
                       bg=COLOR_BG, font=('Segoe UI', 10)).pack(side=tk.LEFT, padx=5)

        chart_frame = ttk.Frame(ventana)
        chart_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        def refrescar_grafica(*args):
            for w in chart_frame.winfo_children():
                w.destroy()
            modo = mode_var.get()
            edad_d = resultado['edad_dias']
            kwargs = {"modo": modo}
            if indicador == "lhfa":
                chart = chart_func(chart_frame, paciente['sexo'],
                                   resultado['edad_meses_decimal'], talla,
                                   paciente['nombre'], edad_dias=edad_d,
                                   tipo_medicion=tipo_med, **kwargs)
            elif indicador == "wfa":
                chart = chart_func(chart_frame, paciente['sexo'],
                                   resultado['edad_meses_decimal'], peso,
                                   paciente['nombre'], edad_dias=edad_d, **kwargs)
            elif indicador == "wflh":
                chart = chart_func(chart_frame, paciente['sexo'],
                                   talla, peso, paciente['nombre'],
                                   tipo_med=tipo_med, **kwargs)
            elif indicador == "bmi":
                chart = chart_func(chart_frame, paciente['sexo'],
                                   resultado['edad_meses_decimal'],
                                   resultado['imc'] or 0, paciente['nombre'],
                                   edad_dias=edad_d, **kwargs)
            elif indicador == "hcfa":
                chart = chart_func(chart_frame, paciente['sexo'],
                                   resultado['edad_meses_decimal'], pc,
                                   paciente['nombre'], edad_dias=edad_d, **kwargs)
            elif indicador == "acfa":
                chart = chart_func(chart_frame, paciente['sexo'],
                                   resultado['edad_meses_decimal'], muac,
                                   paciente['nombre'], edad_dias=edad_d, **kwargs)
            elif indicador == "tsfa":
                chart = chart_func(chart_frame, paciente['sexo'],
                                   resultado['edad_meses_decimal'], pliegue,
                                   paciente['nombre'], **kwargs)
            elif indicador == "ssfa":
                chart = chart_func(chart_frame, paciente['sexo'],
                                   resultado['edad_meses_decimal'], pliegue_sub,
                                   paciente['nombre'], **kwargs)
            chart.pack(fill=tk.BOTH, expand=True)

        mode_var.trace_add("write", refrescar_grafica)
        refrescar_grafica()

        res_frame = ttk.LabelFrame(ventana, text=" Z-Scores ", padding=5)
        res_frame.pack(fill=tk.X, padx=10, pady=5)

        z_lineas = []
        for z_name, z_val in [
            ("L/Alt-edad", resultado['z_lhfa']),
            ("Peso-edad", resultado['z_wfa']),
            ("Peso-L/Alt", resultado['z_wflh']),
            ("IMC-edad", resultado['z_bmi']),
            ("PC-edad", resultado['z_pc']),
            ("MUAC-edad", resultado['z_acfa']),
        ]:
            if z_val is not None:
                z_lineas.append(f"{z_name}: {z_val:+.2f}")

        ttk.Label(res_frame, text="  |  ".join(z_lineas), font=('Consolas', 10)).pack(anchor=tk.W, padx=5)

        self.status_var.set(
            f"Gráfica {self.INDICADOR_NOMBRES.get(indicador, indicador)} — {paciente['nombre']}"
        )

    def _ant_limpiar(self):
        for e in [self.ant_paciente_id, self.ant_peso, self.ant_talla, self.ant_pc,
                  self.ant_muac, self.ant_pliegue, self.ant_pliegue_sub]:
            e.delete(0, tk.END)
        for w in [self.ant_nombre, self.ant_fecha_nac, self.ant_sexo, self.ant_edad]:
            w.config(state='normal')
            w.delete(0, tk.END)
            w.config(state='readonly')
        self.ant_edema.set("no")
        self.ant_tipo_med.set("Decúbito (L)")
        self.ant_fecha_visita.delete(0, tk.END)
        self.ant_fecha_visita.insert(0, date.today().strftime("%d-%m-%Y"))
        self._resultado_actual = None
        self._ant_paciente_actual = None
        self.ant_resultado_text.config(state='normal')
        self.ant_resultado_text.delete("1.0", tk.END)
        self.ant_resultado_text.insert("1.0", "Ingrese datos y presione 'Evaluar' para ver resultados.")
        self.ant_resultado_text.config(state='disabled')
        self._ant_cambiar_indicador()

    # ==================================================================
    # MÉTODOS: PACIENTES
    # ==================================================================
    def _guardar_paciente(self):
        nombre = self.entry_nombre.get().strip()
        fecha_nac = self.entry_fecha_nac.get().strip()
        sexo = self.combo_sexo.get()
        peso = self.entry_peso.get().strip()
        talla = self.entry_talla.get().strip()

        if not nombre or not fecha_nac:
            messagebox.showwarning("Campos requeridos", "Nombre y fecha de nacimiento son obligatorios.")
            return

        try:
            fecha_dt = _parsear_fecha(fecha_nac)
        except ValueError:
            messagebox.showerror("Error", "Formato de fecha inválido. Use DD-MM-AAAA.")
            return

        peso_f = float(peso) if peso else 0.0
        talla_f = float(talla) if talla else 0.0

        # Si hay un paciente seleccionado, ACTUALIZA; si no, INSERT nuevo
        if getattr(self, 'paciente_seleccionado', None):
            pid = self.paciente_seleccionado
            self.patient_mgr.actualizar_paciente(pid, nombre, fecha_dt, sexo, peso_f, talla_f)
            msg = f"Paciente {nombre} (ID {self.patient_mgr.obtener_display_id(pid)}) actualizado correctamente."
        else:
            pid = self.patient_mgr.agregar_paciente(nombre, fecha_dt, sexo, peso_f, talla_f)
            msg = f"Paciente {nombre} registrado con ID {self.patient_mgr.obtener_display_id(pid)}"
        self.status_var.set(msg)
        messagebox.showinfo("Éxito", msg)
        self.paciente_seleccionado = None
        self._limpiar_formulario()
        self._cargar_pacientes()

    def _seguir_paciente(self):
        nombre = self.entry_nombre.get().strip()
        fecha_nac = self.entry_fecha_nac.get().strip()
        sexo = self.combo_sexo.get()
        peso = self.entry_peso.get().strip()
        talla = self.entry_talla.get().strip()
        fecha_actual = self.entry_fecha_actual.get().strip() or date.today().strftime("%d-%m-%Y")

        if not nombre or not fecha_nac:
            messagebox.showwarning("Campos requeridos", "Completa nombre y fecha de nacimiento antes de crear un seguimiento.")
            return

        try:
            fecha_dt = _parsear_fecha(fecha_nac)
            fecha_hoy = _parsear_fecha(fecha_actual)
        except ValueError:
            messagebox.showerror("Error", "Formato de fecha inválido. Use DD-MM-AAAA.")
            return

        base_id = getattr(self, 'paciente_seleccionado', None)
        if not base_id:
            base_id = self.patient_mgr.agregar_paciente(nombre, fecha_dt, sexo, float(peso) if peso else 0.0, float(talla) if talla else 0.0)
            self.paciente_seleccionado = base_id

        follow_id = self.patient_mgr.agregar_seguimiento(
            base_id,
            nombre,
            fecha_dt,
            sexo,
            float(peso) if peso else 0.0,
            float(talla) if talla else 0.0,
        )
        display_id = self.patient_mgr.obtener_display_id(follow_id)
        self.status_var.set(f"Seguimiento creado para {nombre} con ID {display_id}")
        messagebox.showinfo("Seguimiento", f"Se creó la ficha de seguimiento {display_id} para {nombre}.")
        self.paciente_seleccionado = follow_id
        self._limpiar_formulario()
        self._cargar_pacientes()
        self.entry_fecha_actual.delete(0, tk.END)
        self.entry_fecha_actual.insert(0, fecha_hoy.strftime("%d-%m-%Y"))
        self.entry_nombre.insert(0, nombre)
        self.entry_fecha_nac.insert(0, fecha_nac)
        self.combo_sexo.set(sexo)

    def _limpiar_formulario(self):
        for e in [self.entry_nombre, self.entry_fecha_nac, self.entry_peso, self.entry_talla, self.entry_fecha_actual]:
            e.delete(0, tk.END)
        self.combo_sexo.set("M")
        self.entry_fecha_actual.insert(0, date.today().strftime("%d-%m-%Y"))
        self.paciente_seleccionado = None

    def _cargar_pacientes(self):
        for item in self.tree_pacientes.get_children():
            self.tree_pacientes.delete(item)
        self._paciente_row_ids = {}
        pacientes = self.patient_mgr.listar_pacientes()
        for p in pacientes:
            display_id = self.patient_mgr.obtener_display_id(p['id'])
            item = self.tree_pacientes.insert("", tk.END, values=(
                display_id, p['nombre'],
                _mostrar_fecha(p['fecha_nacimiento']), p['sexo'], p['peso_kg'], p['talla_cm'],
                "Seguir"
            ))
            self._paciente_row_ids[item] = p['id']
        self.status_var.set(f"{len(pacientes)} paciente(s) registrado(s)")

    def _buscar_pacientes(self):
        termino = self.entry_buscar.get().strip()
        if not termino:
            self._cargar_pacientes()
            return
        for item in self.tree_pacientes.get_children():
            self.tree_pacientes.delete(item)
        self._paciente_row_ids = {}
        pacientes = self.patient_mgr.buscar_pacientes(termino)
        for p in pacientes:
            display_id = self.patient_mgr.obtener_display_id(p['id'])
            item = self.tree_pacientes.insert("", tk.END, values=(
                display_id, p['nombre'],
                _mostrar_fecha(p['fecha_nacimiento']), p['sexo'], p['peso_kg'], p['talla_cm'],
                "Seguir"
            ))
            self._paciente_row_ids[item] = p['id']

    def _seleccionar_paciente(self, event):
        sel = self.tree_pacientes.selection()
        if sel:
            actual_id = self._paciente_row_ids.get(sel[0])
            if actual_id is None:
                return
            self.paciente_seleccionado = actual_id
            self._habilitar_pestanas()
            self._llenar_historia_desde_paciente(self.paciente_seleccionado)

    def _clic_pacientes(self, event):
        """Detecta clic en la columna 'Seguir' (7ª) de la lista de pacientes."""
        col = self.tree_pacientes.identify_column(event.x)
        row_id = self.tree_pacientes.identify_row(event.y)
        if not row_id or col != "#7":
            return
        paciente_id = self._paciente_row_ids.get(row_id)
        if paciente_id is None:
            return
        self._seguir_desde_lista(paciente_id)

    def _seguir_desde_lista(self, paciente_id: int):
        """Crea una nueva consulta (seguimiento) del paciente seleccionado en la lista."""
        paciente = self.patient_mgr.obtener_paciente(paciente_id)
        if not paciente:
            messagebox.showerror("Error", "Paciente no encontrado.")
            return
        base_id = paciente['parent_id'] if paciente.get('parent_id') is not None else paciente['id']
        fecha_nac = date.fromisoformat(paciente['fecha_nacimiento'])
        follow_id = self.patient_mgr.agregar_seguimiento(
            base_id, paciente['nombre'], fecha_nac, paciente['sexo'],
            paciente['peso_kg'] or 0.0, paciente['talla_cm'] or 0.0,
        )
        display_id = self.patient_mgr.obtener_display_id(follow_id)
        self.paciente_seleccionado = follow_id
        self._habilitar_pestanas()
        self._llenar_historia_desde_paciente(follow_id)
        self._cargar_pacientes()
        self.status_var.set(f"Consulta {display_id} creada para {paciente['nombre']}")
        messagebox.showinfo("Seguimiento",
                            f"Se abrió una nueva consulta {display_id} para {paciente['nombre']}.\n"
                            "A partir de ahora registre el nuevo historial, antropometría y laboratorios en las pestañas.")

    def _llenar_historia_desde_paciente(self, paciente_id: int):
        """Llena los campos de Historia Alimentaria desde un paciente seleccionado."""
        paciente = self.patient_mgr.obtener_paciente(paciente_id)
        if not paciente:
            return

        # Llena el formulario de Pacientes (para edición)
        self.entry_nombre.delete(0, tk.END)
        self.entry_nombre.insert(0, paciente['nombre'])
        self.entry_fecha_nac.delete(0, tk.END)
        self.entry_fecha_nac.insert(0, _mostrar_fecha(paciente['fecha_nacimiento']))
        self.combo_sexo.set(paciente['sexo'])
        self.entry_peso.delete(0, tk.END)
        if paciente['peso_kg'] is not None:
            self.entry_peso.insert(0, str(paciente['peso_kg']))
        self.entry_talla.delete(0, tk.END)
        if paciente['talla_cm'] is not None:
            self.entry_talla.insert(0, str(paciente['talla_cm']))

        self.ha_paciente_id.delete(0, tk.END)
        self.ha_paciente_id.insert(0, str(paciente_id))

        self.ha_nombre.delete(0, tk.END)
        self.ha_nombre.insert(0, paciente['nombre'])

        self.ha_fecha_nac.delete(0, tk.END)
        self.ha_fecha_nac.insert(0, _mostrar_fecha(paciente['fecha_nacimiento']))

        self.ha_edad.delete(0, tk.END)
        from datetime import date as date_cls
        try:
            fecha_nac = date_cls.fromisoformat(paciente['fecha_nacimiento'])
            edad_dias = (date_cls.today() - fecha_nac).days
            if edad_dias < 30:
                self.ha_edad.insert(0, f"{edad_dias} días")
            elif edad_dias < 365:
                meses = round(edad_dias / 30.44)
                self.ha_edad.insert(0, f"{meses} meses")
            else:
                anios = round(edad_dias / 365.25, 1)
                self.ha_edad.insert(0, f"{anios} años")
        except ValueError:
            pass

        self.ha_sexo.set(paciente['sexo'])

        # También llena Historia Médica
        self.hm_paciente_id.delete(0, tk.END)
        self.hm_paciente_id.insert(0, str(paciente_id))
        self.hm_nombre.config(state='normal')
        self.hm_nombre.delete(0, tk.END)
        self.hm_nombre.insert(0, paciente['nombre'])
        self.hm_nombre.config(state='readonly')

        # Llena Antropometría
        self.ant_paciente_id.delete(0, tk.END)
        self.ant_paciente_id.insert(0, str(paciente_id))
        self._ant_cargar_paciente()

        # Llena Laboratorios
        self.lab_paciente_id.delete(0, tk.END)
        self.lab_paciente_id.insert(0, str(paciente_id))
        self._lab_cargar_paciente()

        self.status_var.set(f"Paciente {paciente['nombre']} cargado en todas las pestañas")

    def _eliminar_paciente(self):
        if not self.paciente_seleccionado:
            messagebox.showwarning("Seleccionar", "Seleccione un paciente de la lista.")
            return
        if messagebox.askyesno("Confirmar", "¿Eliminar paciente seleccionado?"):
            self.patient_mgr.eliminar_paciente(self.paciente_seleccionado)
            self.status_var.set("Paciente eliminado")
            self.paciente_seleccionado = None
            self._cargar_pacientes()

    # ==================================================================
    # MÉTODOS: EVALUACIÓN
    # ==================================================================
    def _realizar_evaluacion(self):
        try:
            pid = int(self.entry_eval_paciente_id.get().strip())
        except (ValueError, TypeError):
            messagebox.showerror("Error", "Ingrese un ID de paciente válido.")
            return

        paciente = self.patient_mgr.obtener_paciente(pid)
        if not paciente:
            messagebox.showerror("Error", "Paciente no encontrado.")
            return

        try:
            fecha_eval = _parsear_fecha(self.entry_eval_fecha.get())
        except ValueError:
            messagebox.showerror("Error", "Fecha de evaluación inválida.")
            return

        fecha_nac = date.fromisoformat(paciente['fecha_nacimiento'])
        peso = paciente['peso_kg'] if paciente['peso_kg'] else 0
        talla = paciente['talla_cm'] if paciente['talla_cm'] else 0

        if peso == 0 or talla == 0:
            messagebox.showwarning("Datos incompletos", "El paciente no tiene peso/talla registrados.")
            return

        reporte = generar_reporte_evaluacion(
            paciente['nombre'],
            fecha_nac, paciente['sexo'], peso, talla, fecha_eval
        )

        self.text_evaluacion.delete("1.0", tk.END)
        self.text_evaluacion.insert("1.0", self._formatear_reporte(reporte))
        self.status_var.set(f"Evaluación completada: {reporte['clasificacion_peso']}")

    def _formatear_reporte(self, r: dict) -> str:
        req = r['requerimientos']
        return (
            "=" * 60 + "\n"
            "  REPORTE DE EVALUACIÓN NUTRICIONAL\n" +
            "=" * 60 + "\n\n"
            f"  Paciente:      {r['paciente']}\n"
            f"  Edad:          {r['edad_meses']} meses\n"
            f"  Peso:          {r['peso_kg']} kg\n"
            f"  Talla:         {r['talla_cm']} cm\n"
            f"  IMC:           {r['imc']} kg/m²\n\n"
            "  --- Z-SCORES (Tabla OMS) ---\n"
            f"  Peso/Edad:     {r['z_score_peso_edad']}  →  {r['clasificacion_peso']}\n"
            f"  Talla/Edad:    {r['z_score_talla_edad']}  →  {r['clasificacion_talla']}\n"
            f"  Peso/Talla:    {r['z_score_peso_talla']}\n"
            f"  IMC/Edad:      {r['z_score_imc_edad']}\n\n"
            "  --- REQUERIMIENTOS DIARIOS ---\n"
            f"  Calorías:      {req['calorias_kcal']} kcal\n"
            f"  Proteínas:     {req['proteinas_g']} g\n"
            f"  Grasas:        {req['grasas_g']} g\n"
            f"  Carbohidratos: {req['carbohidratos_g']} g\n"
            f"  Fibra:         {req['fibra_g']} g\n"
            f"  Hierro:        {req['hierro_mg']} mg\n"
            f"  Calcio:        {req['calcio_mg']} mg\n"
            f"  Vitamina A:    {req['vitamina_a_ui']} UI\n"
            f"  Vitamina C:    {req['vitamina_c_mg']} mg\n"
            f"  Zinc:          {req['zinc_mg']} mg\n" +
            "=" * 60
        )

    # ==================================================================
    # MÉTODOS: REQUERIMIENTOS
    # ==================================================================
    def _calcular_requerimientos(self):
        try:
            edad = float(self.entry_req_edad.get().strip())
            peso = float(self.entry_req_peso.get().strip())
            talla = float(self.entry_req_talla.get().strip())
        except ValueError:
            messagebox.showerror("Error", "Ingrese valores numéricos válidos.")
            return

        req = calcular_requerimientos_caloricos(edad, peso, talla)
        self.text_requerimientos.delete("1.0", tk.END)
        self.text_requerimientos.insert("1.0", (
            "=" * 50 + "\n"
            "  REQUERIMIENTOS NUTRICIONALES DIARIOS\n" +
            "=" * 50 + "\n\n"
            f"  Edad: {edad} meses | Peso: {peso} kg | Talla: {talla} cm\n\n"
            f"  Energía:        {req['calorias_kcal']} kcal\n"
            f"  Proteínas:      {req['proteinas_g']} g\n"
            f"  Grasas:         {req['grasas_g']} g\n"
            f"  Carbohidratos:  {req['carbohidratos_g']} g\n"
            f"  Fibra:          {req['fibra_g']} g\n\n"
            "  --- Micronutrientes ---\n"
            f"  Hierro:         {req['hierro_mg']} mg\n"
            f"  Calcio:         {req['calcio_mg']} mg\n"
            f"  Vitamina A:     {req['vitamina_a_ui']} UI\n"
            f"  Vitamina C:     {req['vitamina_c_mg']} mg\n"
            f"  Zinc:           {req['zinc_mg']} mg\n" +
            "=" * 50
        ))

    # ==================================================================
    # MÉTODOS: HISTORIA ALIMENTARIA
    # ==================================================================
    def _cargar_paciente_en_historia(self):
        """Carga los datos del paciente en el formulario de historia alimentaria."""
        try:
            pid = int(self.ha_paciente_id.get().strip())
        except (ValueError, TypeError):
            messagebox.showerror("Error", "Ingrese un ID de paciente válido.")
            return

        paciente = self.patient_mgr.obtener_paciente(pid)
        if not paciente:
            messagebox.showerror("Error", "Paciente no encontrado.")
            return

        self.ha_nombre.delete(0, tk.END)
        self.ha_nombre.insert(0, paciente['nombre'])

        self.ha_fecha_nac.delete(0, tk.END)
        self.ha_fecha_nac.insert(0, _mostrar_fecha(paciente['fecha_nacimiento']))

        self.ha_edad.delete(0, tk.END)
        from datetime import date as date_cls
        try:
            fecha_nac = date_cls.fromisoformat(paciente['fecha_nacimiento'])
            edad_dias = (date_cls.today() - fecha_nac).days
            if edad_dias < 30:
                self.ha_edad.insert(0, f"{edad_dias} días")
            elif edad_dias < 365:
                meses = round(edad_dias / 30.44)
                self.ha_edad.insert(0, f"{meses} meses")
            else:
                anios = round(edad_dias / 365.25, 1)
                self.ha_edad.insert(0, f"{anios} años")
        except ValueError:
            pass

        self.ha_sexo.set(paciente['sexo'])
        self.status_var.set(f"Paciente {paciente['nombre']} cargado en Historia Alimentaria")
    def _recopilar_datos_historia(self) -> dict:
        """Recopila todos los campos del formulario de historia alimentaria."""
        tipo = self.ha_tipo_alimentacion.get()
        tipo_map = {"lactancia materna exclusiva": "lactancia_exclusiva",
                    "fórmula infantil exclusiva": "formula_exclusiva",
                    "alimentación mixta (ambas)": "mixta"}

        patron_keys = {
            "desayuno": "desayuno",
            "merienda_manana": "merienda_manana",
            "almuerzo": "almuerzo",
            "merienda_tarde": "merienda_tarde",
            "cena": "cena",
            "otra_merienda": "otra_merienda",
        }
        patron_data = {}
        for key, var_name in patron_keys.items():
            entries = self.ha_patron_entries.get(var_name)
            if entries:
                patron_data[f"patron_{var_name}_hora"] = entries[0].get().strip()
                patron_data[f"patron_{var_name}_alimentos"] = entries[1].get().strip()

        apetito_map = {"Excelente": "excelente", "Bueno": "bueno", "Regular": "regular", "Pobre": "pobre"}
        snacks_map = {
            "Nunca": "nunca", "Ocasionalmente (1-2 veces/sem)": "ocasionalmente",
            "Frecuentemente (diario)": "frecuentemente", "Varias veces al día": "varias_veces_dia"
        }
        alergias_map = {"Sí": "si", "No": "no", "En estudio": "en_estudio"}

        si_no_map = {"Sí": "si", "No": "no"}
        familia_map = {"Sí, siempre": "siempre", "A veces": "a_veces", "Rara vez": "rara_vez", "No": "no"}
        ambiente_map = {"Sí": "si", "A veces": "a_veces", "No": "no"}

        datos = {
            'tipo_alimentacion': tipo_map.get(tipo, tipo),
            'lm_frecuencia': self.ha_lm_frecuencia.get().strip(),
            'lm_duracion_minutos': self.ha_lm_duracion.get().strip(),
            'lm_posicion_tecnica': self.ha_lm_posicion.get().strip(),
            'lm_suplementos': si_no_map.get(self.ha_lm_suplementos.get(), 'no') == 'si',
            'lm_suplementos_detalle': self.ha_lm_suplementos_detalle.get().strip(),
            'fi_tipo_formula': self.ha_fi_tipo.get().strip(),
            'fi_preparacion': self.ha_fi_preparacion.get().strip(),
            'fi_kcal_100ml': self.ha_fi_kcal.get().strip(),
            'fi_preparacion_fresca': self.ha_fi_preparacion_fresca.get(),
            'fi_tomas_24h': self.ha_fi_tomas_24h.get().strip(),
            'fi_frecuencia': self.ha_fi_frecuencia.get().strip(),
            'fi_volumen_ofrecido': self.ha_fi_vol_ofrecido.get().strip(),
            'fi_volumen_real': self.ha_fi_vol_real.get().strip(),
            'fi_duracion_toma': self.ha_fi_duracion.get().strip(),
            'fi_adicional': si_no_map.get(self.ha_fi_adicional.get(), 'no') == 'si',
            'fi_adicional_detalle': self.ha_fi_adicional_detalle.get().strip(),
            'comidas_snacks_dia': self.ha_comidas_snacks.get().strip(),
            'lugar_comidas': self.ha_lugar_comidas.get().strip(),
            'apetito': apetito_map.get(self.ha_apetito.get(), 'bueno'),
            'apetito_comentarios': self.ha_apetito_comentarios.get().strip(),
            'comidas_familia': familia_map.get(self.ha_comidas_familia.get(), 'a_veces'),
            'ambiente_agradable': ambiente_map.get(self.ha_ambiente.get(), 'si'),
            'ambiente_dificultades': self.ha_ambiente_dificultades.get().strip(),
            'leche_cantidad': self.ha_leche_cantidad.get().strip(),
            'leche_tipo': self.ha_leche_tipo.get().strip(),
            'jugo_cantidad': self.ha_jugo_cantidad.get().strip(),
            'snacks_frecuencia': snacks_map.get(self.ha_snacks_freq.get(), 'nunca'),
            'snacks_tipo': self.ha_snacks_tipo.get().strip(),
            'alergias': alergias_map.get(self.ha_alergias.get(), 'no'),
            'alergias_detalle': self.ha_alergias_detalle.get().strip(),
            'suplemento_vitaminico': self.ha_suplemento.get().strip(),
            'otros_comentarios': self.ha_otros_comentarios.get().strip(),
        }
        datos.update(patron_data)
        return datos

    def _guardar_historia(self):
        try:
            pid = int(self.ha_paciente_id.get().strip())
        except (ValueError, TypeError):
            messagebox.showerror("Error", "Ingrese un ID de paciente válido.")
            return

        paciente = self.patient_mgr.obtener_paciente(pid)
        if not paciente:
            messagebox.showerror("Error", "Paciente no encontrado.")
            return

        try:
            fecha_eval = _parsear_fecha(self.ha_fecha_eval.get())
        except ValueError:
            messagebox.showerror("Error", "Fecha de evaluación inválida (DD-MM-AAAA).")
            return

        evaluador = self.ha_evaluador.get().strip()
        datos = self._recopilar_datos_historia()

        if self.ha_editando_id is not None:
            self.historia_mgr.actualizar(self.ha_editando_id, fecha_eval, evaluador, datos)
            self.status_var.set(f"Historia alimentaria actualizada (ID: {self.ha_editando_id})")
            messagebox.showinfo("Éxito", "Historia alimentaria actualizada correctamente.")
            self.ha_editando_id = None
            return

        hid = self.historia_mgr.guardar(pid, fecha_eval, evaluador, datos)
        self.status_var.set(f"Historia alimentaria guardada (ID: {hid})")
        messagebox.showinfo("Éxito", f"Historia alimentaria guardada correctamente.\nID Registro: {hid}")

    # ==================================================================
    # EDICIÓN DE HISTORIA ALIMENTARIA
    # ==================================================================
    def _editar_alimento_seleccionado(self, hid: int, fila: int):
        """Carga un registro en el formulario para su edición."""
        registro = self.historia_mgr.obtener(hid)
        if not registro:
            messagebox.showerror("Error", "Registro no encontrado.")
            return
        self.ha_editando_id = hid
        self.ha_paciente_id.delete(0, tk.END)
        self.ha_paciente_id.insert(0, str(registro['paciente_id']))
        self._cargar_paciente_en_historia()
        self._llenar_historia_formulario(registro)
        self.status_var.set(f"Editando historia alimentaria ID: {hid} (fila {fila}) — presione Guardar para actualizar.")

    def _seleccionar_historia_a_editar(self):
        """Muestra una lista de registros del paciente para elegir uno y editarlo."""
        try:
            pid = int(self.ha_paciente_id.get().strip())
        except (ValueError, TypeError):
            messagebox.showerror("Error", "Ingrese un ID de paciente válido.")
            return
        historiales = self.historia_mgr.listar_por_paciente(pid)
        if not historiales:
            messagebox.showinfo("Sin registros", "No hay historias alimentarias para este paciente.")
            return

        ventana = tk.Toplevel(self.root)
        ventana.title(f"Seleccionar Historia Alimentaria a editar — Paciente {pid}")
        ventana.geometry("720x400")

        tree = ttk.Treeview(ventana, columns=("id", "fecha", "evaluador"), show='headings', height=12)
        tree.heading("id", text="ID")
        tree.heading("fecha", text="Fecha Evaluación")
        tree.heading("evaluador", text="Evaluador")
        tree.column("id", width=60, anchor=tk.CENTER)
        tree.column("fecha", width=150, anchor=tk.CENTER)
        tree.column("evaluador", width=200, anchor=tk.W)
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        for h in historiales:
            tree.insert("", tk.END, values=(h['id'], h['fecha_evaluacion'], h['evaluador']))

        def _editar_seleccion():
            sel = tree.selection()
            if not sel:
                messagebox.showwarning("Aviso", "Seleccione un registro de la lista.")
                return
            vals = tree.item(sel[0], "values")
            hid = int(vals[0])
            fila = int(vals[0])
            ventana.destroy()
            self._editar_alimento_seleccionado(hid, fila)

        botones = ttk.Frame(ventana)
        botones.pack(fill=tk.X, padx=10, pady=10)
        ttk.Button(botones, text="Editar Seleccionado", style='Primary.TButton',
                   command=_editar_seleccion).pack(side=tk.LEFT, padx=5)
        ttk.Button(botones, text="Eliminar Seleccionado",
                   command=lambda: self._eliminar_historia_seleccionada(tree)).pack(side=tk.LEFT, padx=5)
        ttk.Button(botones, text="Cerrar", command=ventana.destroy).pack(side=tk.LEFT, padx=5)

    def _eliminar_historia_seleccionada(self, tree):
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Seleccione un registro de la lista.")
            return
        vals = tree.item(sel[0], "values")
        hid = int(vals[0])
        if messagebox.askyesno("Confirmar", f"¿Eliminar la historia alimentaria ID {hid}?"):
            self.historia_mgr.eliminar(hid)
            if self.ha_editando_id == hid:
                self.ha_editando_id = None
            messagebox.showinfo("Eliminado", "Registro eliminado.")
            tree.delete(sel[0])

    def _cancelar_edicion_historia(self):
        self.ha_editando_id = None
        self.status_var.set("Edición de historia alimentaria cancelada.")

    def _llenar_historia_formulario(self, registro: dict):
        """Llena los campos del formulario desde un registro de la BD."""
        inv_apetito = {"excelente": "Excelente", "bueno": "Bueno", "regular": "Regular", "pobre": "Pobre"}
        inv_snacks = {"nunca": "Nunca", "ocasionalmente": "Ocasionalmente (1-2 veces/sem)",
                      "frecuentemente": "Frecuentemente (diario)", "varias_veces_dia": "Varias veces al día"}
        inv_alergias = {"si": "Sí", "no": "No", "en_estudio": "En estudio"}
        inv_familia = {"siempre": "Sí, siempre", "a_veces": "A veces", "rara_vez": "Rara vez", "no": "No"}
        inv_ambiente = {"si": "Sí", "a_veces": "A veces", "no": "No"}

        self._limpiar_historia()

        tipo_val = registro.get('tipo_alimentacion', '')
        if tipo_val not in ('lactancia_exclusiva', 'formula_exclusiva', 'mixta'):
            tipo_val = 'lactancia_exclusiva'
        self.ha_tipo_alimentacion.set(tipo_val)
        self.ha_fecha_eval.delete(0, tk.END)
        self.ha_fecha_eval.insert(0, _mostrar_fecha(registro.get('fecha_evaluacion', '')))
        self.ha_evaluador.insert(0, registro.get('evaluador', '') or '')

        self.ha_lm_frecuencia.insert(0, registro.get('lm_frecuencia', '') or '')
        self.ha_lm_duracion.insert(0, registro.get('lm_duracion_minutos', '') or '')
        self.ha_lm_posicion.insert(0, registro.get('lm_posicion_tecnica', '') or '')
        self.ha_lm_suplementos.set("si" if registro.get('lm_suplementos') else "no")
        self.ha_lm_suplementos_detalle.insert(0, registro.get('lm_suplementos_detalle', '') or '')

        self.ha_fi_tipo.insert(0, registro.get('fi_tipo_formula', '') or '')
        self.ha_fi_preparacion.insert(0, registro.get('fi_preparacion', '') or '')
        self.ha_fi_kcal.insert(0, registro.get('fi_kcal_100ml', '') or '')
        self.ha_fi_tomas_24h.insert(0, registro.get('fi_tomas_24h', '') or '')
        self.ha_fi_frecuencia.insert(0, registro.get('fi_frecuencia', '') or '')
        self.ha_fi_vol_ofrecido.insert(0, registro.get('fi_volumen_ofrecido', '') or '')
        self.ha_fi_vol_real.insert(0, registro.get('fi_volumen_real', '') or '')
        self.ha_fi_duracion.insert(0, registro.get('fi_duracion_toma', '') or '')
        self.ha_fi_adicional.set("si" if registro.get('fi_adicional') else "no")
        self.ha_fi_adicional_detalle.insert(0, registro.get('fi_adicional_detalle', '') or '')

        self.ha_comidas_snacks.insert(0, registro.get('comidas_snacks_dia', '') or '')
        self.ha_lugar_comidas.insert(0, registro.get('lugar_comidas', '') or '')

        patron_keys = {
            "desayuno": "desayuno", "merienda_manana": "merienda_manana",
            "almuerzo": "almuerzo", "merienda_tarde": "merienda_tarde",
            "cena": "cena", "otra_merienda": "otra_merienda",
        }
        for var_name in patron_keys:
            entries = self.ha_patron_entries.get(var_name)
            if not entries:
                continue
            hora = registro.get(f"patron_{var_name}_hora", '') or ''
            alim = registro.get(f"patron_{var_name}_alimentos", '') or ''
            entries[0].insert(0, hora)
            entries[1].insert(0, alim)

        self.ha_apetito.set(inv_apetito.get(registro.get('apetito', ''), 'Bueno'))
        self.ha_apetito_comentarios.insert(0, registro.get('apetito_comentarios', '') or '')
        self.ha_comidas_familia.set(inv_familia.get(registro.get('comidas_familia', ''), 'A veces'))
        self.ha_ambiente.set(inv_ambiente.get(registro.get('ambiente_agradable', ''), 'Sí'))
        self.ha_ambiente_dificultades.insert(0, registro.get('ambiente_dificultades', '') or '')

        self.ha_leche_cantidad.insert(0, registro.get('leche_cantidad', '') or '')
        self.ha_leche_tipo.insert(0, registro.get('leche_tipo', '') or '')
        self.ha_jugo_cantidad.insert(0, registro.get('jugo_cantidad', '') or '')
        self.ha_snacks_freq.set(inv_snacks.get(registro.get('snacks_frecuencia', ''), 'Nunca'))
        self.ha_snacks_tipo.insert(0, registro.get('snacks_tipo', '') or '')

        self.ha_alergias.set(inv_alergias.get(registro.get('alergias', ''), 'No'))
        self.ha_alergias_detalle.insert(0, registro.get('alergias_detalle', '') or '')
        self.ha_suplemento.insert(0, registro.get('suplemento_vitaminico', '') or '')
        self.ha_otros_comentarios.insert(0, registro.get('otros_comentarios', '') or '')

    def _cargar_historia_alimentaria(self):
        try:
            pid = int(self.ha_paciente_id.get().strip())
        except (ValueError, TypeError):
            messagebox.showerror("Error", "Ingrese un ID de paciente válido.")
            return

        historiales = self.historia_mgr.listar_por_paciente(pid)
        if not historiales:
            messagebox.showinfo("Sin registros", "No hay historias alimentarias para este paciente.")
            return

        ultimo = historiales[0]
        texto = self.historia_mgr.generar_texto_reporte(ultimo)

        win = tk.Toplevel(self.root)
        win.title(f"Historia Alimentaria — Paciente {pid}")
        win.geometry("750x700")
        text = scrolledtext.ScrolledText(win, font=('Consolas', 10), bg=COLOR_WHITE)
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text.insert("1.0", texto)
        text.config(state=tk.DISABLED)

    def _ver_ultima_historia(self):
        self._cargar_historia_alimentaria()

    def _limpiar_historia(self):
        campos = [
            self.ha_nombre, self.ha_fecha_nac, self.ha_edad, self.ha_evaluador,
            self.ha_lm_frecuencia, self.ha_lm_duracion, self.ha_lm_posicion,
            self.ha_lm_suplementos_detalle,
            self.ha_fi_tipo, self.ha_fi_preparacion, self.ha_fi_kcal,
            self.ha_fi_tomas_24h, self.ha_fi_frecuencia, self.ha_fi_vol_ofrecido,
            self.ha_fi_vol_real, self.ha_fi_duracion, self.ha_fi_adicional_detalle,
            self.ha_comidas_snacks, self.ha_lugar_comidas,
            self.ha_apetito_comentarios, self.ha_ambiente_dificultades,
            self.ha_leche_cantidad, self.ha_leche_tipo, self.ha_jugo_cantidad,
            self.ha_snacks_tipo, self.ha_alergias_detalle,
            self.ha_suplemento, self.ha_otros_comentarios,
        ]
        for c in campos:
            c.delete(0, tk.END)
        for entries in self.ha_patron_entries.values():
            for e in entries:
                e.delete(0, tk.END)

    # ==================================================================
    # UTILIDADES
    # ==================================================================
    def _acerca_de(self):
        messagebox.showinfo(
            "Acerca de",
            "Nutrición Pediátrica v1.0\n\n"
            "Dashboard de Evaluación y Seguimiento Nutricional Infantil\n"
            "Cálculos basados en tablas OMS\n"
            "Base de datos SQLite\n\n"
            "Incluye:\n"
            "• Gestión de pacientes\n"
            "• Evaluación nutricional (Z-scores, IMC)\n"
            "• Seguimiento de crecimiento\n"
            "• Requerimientos nutricionales\n"
            "• Historia alimentaria completa\n"
            "• Laboratorios con clasificación por edad"
        )

    def _on_close(self):
        self.db.close()
        self.root.destroy()
