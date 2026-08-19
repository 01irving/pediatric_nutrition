"""
Dashboard principal — Nutrición Pediátrica.
Incluye: Pacientes, Evaluación, Seguimiento, Requerimientos, Historia Alimentaria.
"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import date
from typing import Optional
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.database.db_manager import DatabaseManager
from src.modules.patient_manager import PatientManager
from src.modules.historia_alimentaria_manager import HistoriaAlimentariaManager
from src.modules.nutrition_calcs import (
    calcular_edad_meses, calcular_imc,
    calcular_z_score_peso_edad, calcular_z_score_talla_edad,
    calcular_z_score_peso_talla, calcular_z_score_imc_edad,
    clasificar_estado_nutricional, clasificar_talla_edad,
    calcular_requerimientos_caloricos, generar_reporte_evaluacion
)

COLOR_BG = "#f0f4f8"
COLOR_PRIMARY = "#1a5276"
COLOR_ACCENT = "#2e86c1"
COLOR_SECTION = "#d6eaf8"
COLOR_WHITE = "#ffffff"
COLOR_LABEL = "#2c3e50"
COLOR_ENTRY_BG = "#fdfefe"


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

        self._configurar_estilo()
        self._crear_barra_superior()
        self._crear_barra_estado()
        self._crear_notebook()
        self._crear_pestanas()

        self.paciente_seleccionado: Optional[int] = None
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
        self._crear_pestana_evaluacion()
        self._crear_pestana_seguimiento()
        self._crear_pestana_requerimientos()
        self._crear_pestana_historia_alimentaria()

    # ==================================================================
    # PESTAÑA 1: PACIENTES
    # ==================================================================
    def _crear_pestana_pacientes(self):
        frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame, text="  Pacientes  ")
        ttk.Label(frame, text="Gestión de Pacientes", style='Title.TLabel').pack(anchor=tk.W)
        ttk.Separator(frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)

        form_frame = ttk.LabelFrame(frame, text=" Datos del Paciente ", padding=10)
        form_frame.pack(fill=tk.X, pady=5)

        row1 = ttk.Frame(form_frame)
        row1.pack(fill=tk.X, pady=2)
        ttk.Label(row1, text="Nombre:").pack(side=tk.LEFT, padx=5)
        self.entry_nombre = ttk.Entry(row1, width=25)
        self.entry_nombre.pack(side=tk.LEFT, padx=5)
        ttk.Label(row1, text="Apellido:").pack(side=tk.LEFT, padx=5)
        self.entry_apellido = ttk.Entry(row1, width=25)
        self.entry_apellido.pack(side=tk.LEFT, padx=5)

        row2 = ttk.Frame(form_frame)
        row2.pack(fill=tk.X, pady=2)
        ttk.Label(row2, text="Fecha nac. (AAAA-MM-DD):").pack(side=tk.LEFT, padx=5)
        self.entry_fecha_nac = ttk.Entry(row2, width=15)
        self.entry_fecha_nac.pack(side=tk.LEFT, padx=5)
        ttk.Label(row2, text="Sexo:").pack(side=tk.LEFT, padx=5)
        self.combo_sexo = ttk.Combobox(row2, values=["M", "F"], width=5, state="readonly")
        self.combo_sexo.pack(side=tk.LEFT, padx=5)
        self.combo_sexo.set("M")

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
        ttk.Button(btn_frame, text="Guardar Paciente", style='Primary.TButton', command=self._guardar_paciente).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Nuevo", command=self._limpiar_formulario).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Eliminar", command=self._eliminar_paciente).pack(side=tk.LEFT, padx=5)

        ttk.Separator(frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)
        ttk.Label(frame, text="Lista de Pacientes", style='Subtitle.TLabel').pack(anchor=tk.W)

        search_frame = ttk.Frame(frame)
        search_frame.pack(fill=tk.X, pady=5)
        ttk.Label(search_frame, text="Buscar:").pack(side=tk.LEFT)
        self.entry_buscar = ttk.Entry(search_frame, width=30)
        self.entry_buscar.pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="Buscar", command=self._buscar_pacientes).pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="Todos", command=self._cargar_pacientes).pack(side=tk.LEFT, padx=5)

        cols = ("ID", "Nombre", "Apellido", "Nacimiento", "Sexo", "Peso", "Talla")
        self.tree_pacientes = ttk.Treeview(frame, columns=cols, show='headings', height=8)
        for c in cols:
            self.tree_pacientes.heading(c, text=c)
            self.tree_pacientes.column(c, width=120, anchor=tk.CENTER)
        self.tree_pacientes.column("ID", width=50)
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.tree_pacientes.yview)
        self.tree_pacientes.configure(yscrollcommand=scrollbar.set)
        self.tree_pacientes.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        scrollbar.pack(fill=tk.Y, side=tk.RIGHT)
        self.tree_pacientes.bind("<<TreeviewSelect>>", self._seleccionar_paciente)
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
        ttk.Label(row, text="Fecha (AAAA-MM-DD):").pack(side=tk.LEFT, padx=5)
        self.entry_eval_fecha = ttk.Entry(row, width=15)
        self.entry_eval_fecha.insert(0, date.today().isoformat())
        self.entry_eval_fecha.pack(side=tk.LEFT, padx=5)
        ttk.Button(row, text="Evaluar", style='Primary.TButton', command=self._realizar_evaluacion).pack(side=tk.LEFT, padx=10)

        result_frame = ttk.LabelFrame(frame, text=" Resultado ", padding=10)
        result_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        self.text_evaluacion = scrolledtext.ScrolledText(result_frame, height=18, font=('Consolas', 10), bg=COLOR_WHITE)
        self.text_evaluacion.pack(fill=tk.BOTH, expand=True)

    # ==================================================================
    # PESTAÑA 3: SEGUIMIENTO
    # ==================================================================
    def _crear_pestana_seguimiento(self):
        frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame, text="  Seguimiento  ")
        ttk.Label(frame, text="Historial de Crecimiento", style='Title.TLabel').pack(anchor=tk.W)
        ttk.Separator(frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)

        input_frame = ttk.Frame(frame)
        input_frame.pack(fill=tk.X, pady=5)
        ttk.Label(input_frame, text="ID Paciente:").pack(side=tk.LEFT, padx=5)
        self.entry_seg_id = ttk.Entry(input_frame, width=10)
        self.entry_seg_id.pack(side=tk.LEFT, padx=5)
        ttk.Button(input_frame, text="Cargar Historial", command=self._cargar_historial).pack(side=tk.LEFT, padx=5)

        cols = ("Fecha", "Peso (kg)", "Talla (cm)", "IMC", "Per. Cefálico", "Observaciones")
        self.tree_seguimiento = ttk.Treeview(frame, columns=cols, show='headings', height=12)
        for c in cols:
            self.tree_seguimiento.heading(c, text=c)
            self.tree_seguimiento.column(c, width=130, anchor=tk.CENTER)
        self.tree_seguimiento.pack(fill=tk.BOTH, expand=True, pady=5)

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
        self.ha_fecha_eval.insert(0, date.today().isoformat())
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
        ttk.Button(btn_frame, text="Limpiar Formulario", command=self._limpiar_historia).pack(side=tk.LEFT, padx=5)

        ttk.Label(parent, text="ID Paciente:", style='Subtitle.TLabel').pack(side=tk.LEFT, padx=(10, 2))
        self.ha_paciente_id = ttk.Entry(parent, width=10)
        self.ha_paciente_id.pack(side=tk.LEFT, padx=5)

    # ==================================================================
    # MÉTODOS: PACIENTES
    # ==================================================================
    def _guardar_paciente(self):
        nombre = self.entry_nombre.get().strip()
        apellido = self.entry_apellido.get().strip()
        fecha_nac = self.entry_fecha_nac.get().strip()
        sexo = self.combo_sexo.get()
        peso = self.entry_peso.get().strip()
        talla = self.entry_talla.get().strip()

        if not nombre or not apellido or not fecha_nac:
            messagebox.showwarning("Campos requeridos", "Nombre, apellido y fecha de nacimiento son obligatorios.")
            return
        try:
            fecha_dt = date.fromisoformat(fecha_nac)
        except ValueError:
            messagebox.showerror("Error", "Formato de fecha inválido. Use AAAA-MM-DD.")
            return

        peso_f = float(peso) if peso else 0.0
        talla_f = float(talla) if talla else 0.0

        pid = self.patient_mgr.agregar_paciente(nombre, apellido, fecha_dt, sexo, peso_f, talla_f)
        self.status_var.set(f"Paciente {nombre} {apellido} registrado con ID {pid}")
        messagebox.showinfo("Éxito", f"Paciente registrado correctamente.\nID: {pid}")
        self._limpiar_formulario()
        self._cargar_pacientes()

    def _limpiar_formulario(self):
        for e in [self.entry_nombre, self.entry_apellido, self.entry_fecha_nac, self.entry_peso, self.entry_talla]:
            e.delete(0, tk.END)
        self.combo_sexo.set("M")

    def _cargar_pacientes(self):
        for item in self.tree_pacientes.get_children():
            self.tree_pacientes.delete(item)
        pacientes = self.patient_mgr.listar_pacientes()
        for p in pacientes:
            self.tree_pacientes.insert("", tk.END, values=(
                p['id'], p['nombre'], p['apellido'],
                p['fecha_nacimiento'], p['sexo'], p['peso_kg'], p['talla_cm']
            ))
        self.status_var.set(f"{len(pacientes)} paciente(s) registrado(s)")

    def _buscar_pacientes(self):
        termino = self.entry_buscar.get().strip()
        if not termino:
            self._cargar_pacientes()
            return
        for item in self.tree_pacientes.get_children():
            self.tree_pacientes.delete(item)
        pacientes = self.patient_mgr.buscar_pacientes(termino)
        for p in pacientes:
            self.tree_pacientes.insert("", tk.END, values=(
                p['id'], p['nombre'], p['apellido'],
                p['fecha_nacimiento'], p['sexo'], p['peso_kg'], p['talla_cm']
            ))

    def _seleccionar_paciente(self, event):
        sel = self.tree_pacientes.selection()
        if sel:
            vals = self.tree_pacientes.item(sel[0], 'values')
            self.paciente_seleccionado = int(vals[0])

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
            fecha_eval = date.fromisoformat(self.entry_eval_fecha.get().strip())
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
            paciente['nombre'], paciente['apellido'],
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
    # MÉTODOS: SEGUIMIENTO
    # ==================================================================
    def _cargar_historial(self):
        try:
            pid = int(self.entry_seg_id.get().strip())
        except (ValueError, TypeError):
            messagebox.showerror("Error", "Ingrese un ID válido.")
            return
        for item in self.tree_seguimiento.get_children():
            self.tree_seguimiento.delete(item)
        historial = self.patient_mgr.historial_crecimiento(pid)
        for h in historial:
            imc = calcular_imc(h['peso_kg'], h['talla_cm']) if h['talla_cm'] else 0
            self.tree_seguimiento.insert("", tk.END, values=(
                h['fecha'], h['peso_kg'], h['talla_cm'],
                imc, h.get('perimetro_cefalico_cm', ''), h.get('observaciones', '')
            ))
        self.status_var.set(f"{len(historial)} registro(s) de crecimiento")

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
            fecha_eval = date.fromisoformat(self.ha_fecha_eval.get().strip())
        except ValueError:
            messagebox.showerror("Error", "Fecha de evaluación inválida (AAAA-MM-DD).")
            return

        evaluador = self.ha_evaluador.get().strip()
        datos = self._recopilar_datos_historia()

        hid = self.historia_mgr.guardar(pid, fecha_eval, evaluador, datos)
        self.status_var.set(f"Historia alimentaria guardada (ID: {hid})")
        messagebox.showinfo("Éxito", f"Historia alimentaria guardada correctamente.\nID Registro: {hid}")

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
            "• Historia alimentaria completa"
        )

    def _on_close(self):
        self.db.close()
        self.root.destroy()
