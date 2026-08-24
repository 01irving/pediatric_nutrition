"""
Datos de referencia de laboratorio para evaluación nutricional pediátrica.
Basado en: Himes RW, Shulman RJ. "Use of Laboratory Measurements in
Nutritional Assessment", en Koletzko B, et al. (eds): Pediatric Nutrition
in Practice. World Rev Nutr Diet. Basel, Karger, 2015, vol 113, pp 23-28.

Cada prueba define rangos de referencia según edad (en meses) y, cuando
aplica, sexo. Los valores están simplificados con fines de apoyo clínico
y no sustituyen el criterio médico ni los valores de referencia propios
del laboratorio que procese la muestra.
"""
from typing import Optional, Dict, Any, List

# Cada rango: (edad_min_meses, edad_max_meses o None, low o None, high o None, sexo o None, etiqueta)
LAB_TESTS: Dict[str, Dict[str, Any]] = {
    "albumina": {
        "nombre": "Albúmina (suero)",
        "unidad": "g/l",
        "unidad_alterna": {"label": "g/dl", "factor": 10},
        "tipo": "numerico",
        "rangos": [
            (0, 12, 29, 55, None, "Lactante"),
            (12, None, 37, 55, None, "Niño"),
        ],
        "descripcion": "Proteína sérica más abundante, vida media 20 días. Reactante de fase aguda negativo.",
        "deficiencia": "↓ con disfunción hepática sintética.",
        "pitfalls": "Cambia con estado de hidratación y desplazamientos de líquidos.",
    },
    "fosfatasa_alcalina": {
        "nombre": "Fosfatasa alcalina (suero)",
        "unidad": "U/l",
        "tipo": "numerico",
        "rangos": [
            (0, 12, 150, 420, None, "Lactante"),
            (24, 120, 100, 320, None, "2-10 años"),
            (120, 228, 100, 390, "M", "Adolescente varón"),
            (120, 228, 100, 320, "F", "Adolescente mujer"),
            (228, None, 30, 120, None, "Adulto"),
        ],
        "descripcion": "Metaloenzima dependiente de zinc, presente en hígado, hueso, vía biliar, riñón e intestino.",
        "deficiencia": "Fosfatasa alcalina baja obliga a considerar deficiencia de zinc.",
        "pitfalls": "",
    },
    "alfa1_antitripsina": {
        "nombre": "α1-Antitripsina (heces)",
        "unidad": "mg/g de heces",
        "tipo": "numerico",
        "rangos": [
            (0, 6, None, 4.5, None, "<6 meses"),
            (6, None, None, 3, None, ">6 meses"),
        ],
        "descripcion": "Medida de pérdida proteica intestinal.",
        "deficiencia": "Elevada en enteropatía perdedora de proteínas.",
        "pitfalls": "Inestable a pH <3; no es útil para evaluar pérdida proteica gástrica.",
    },
    "biotina": {
        "nombre": "Biotina (suero)",
        "unidad": "pmol/l",
        "tipo": "numerico",
        "rangos": [(0, None, 214, 246, None, "Todas las edades")],
        "descripcion": "Vitamina hidrosoluble, cofactor de carboxilasas.",
        "deficiencia": "Dermatitis, glositis, alopecia, retraso pondoestatural, ataxia, debilidad, depresión y convulsiones.",
        "pitfalls": "Anticonvulsivantes, hemodiálisis y nutrición parenteral pueden causar deficiencia.",
    },
    "calcio": {
        "nombre": "Calcio (suero)",
        "unidad": "mmol/l",
        "unidad_alterna": {"label": "mg/dl", "factor": 0.2495},
        "tipo": "numerico",
        "rangos": [
            (0, 0.33, 1.9, 2.6, None, "Nacimiento a 10 días"),
            (0.33, 24, 2.3, 2.8, None, "10 días a 2 años"),
            (24, 144, 2.2, 2.7, None, "2-12 años"),
            (144, None, 2.2, 2.5, None, "Adolescente/adulto"),
        ],
        "descripcion": "Integridad esquelética, cofactor en cascada de coagulación y función neuromuscular.",
        "deficiencia": "Fatiga, irritabilidad muscular, tetania y convulsiones.",
        "pitfalls": "Hipocalcemia facticia por albúmina baja (50% está unido a albúmina).",
    },
    "ceruloplasmina": {
        "nombre": "Ceruloplasmina (suero)",
        "unidad": "mg/l",
        "unidad_alterna": {"label": "mg/dl", "factor": 10},
        "tipo": "numerico",
        "rangos": [
            (0, 3, 40, 160, None, "Nacimiento a 3 meses"),
            (3, 12, 290, 380, None, "3-12 meses"),
            (12, 180, 230, 490, None, "1-15 años"),
        ],
        "descripcion": "Transporta el 90% del cobre sérico.",
        "deficiencia": "Reactante de fase aguda positivo.",
        "pitfalls": "",
    },
    "cobre": {
        "nombre": "Cobre (suero)",
        "unidad": "µmol/l",
        "unidad_alterna": {"label": "µg/dl", "factor": 0.1574},
        "tipo": "numerico",
        "rangos": [(0, None, 11, 22, None, "Todas las edades pediátricas")],
        "descripcion": "Cofactor mineral para superóxido dismutasa y enzimas de síntesis del tejido conectivo.",
        "deficiencia": "Anemia, neutropenia, despigmentación, cambios característicos del cabello, hueso y tejido conectivo debilitados.",
        "pitfalls": "Dosis supra-fisiológicas de hierro o zinc pueden alterar la absorción de cobre.",
    },
    "creatinina": {
        "nombre": "Creatinina (suero)",
        "unidad": "µmol/l",
        "unidad_alterna": {"label": "mg/dl", "factor": 88.4},
        "tipo": "numerico",
        "rangos": [
            (0, 1, 27, 88, None, "Neonato"),
            (1, 12, 18, 35, None, "Lactante"),
            (12, 144, 27, 62, None, "Niño"),
            (144, 228, 44, 88, None, "Adolescente"),
        ],
        "descripcion": "Producto del metabolismo de creatina-fosfato muscular; su nivel refleja la masa muscular.",
        "deficiencia": "",
        "pitfalls": "Disminución de la filtración glomerular, cimetidina, cefalosporinas y trimetoprim pueden aumentar la creatinina sérica.",
    },
    "elastasa_fecal": {
        "nombre": "Elastasa (heces)",
        "unidad": "µg/g de heces",
        "tipo": "numerico",
        "rangos": [(0, None, 200, None, None, "Todas las edades")],
        "descripcion": "Indicador de suficiencia exocrina pancreática.",
        "deficiencia": "",
        "pitfalls": "Sensibilidad y especificidad inciertas en insuficiencia leve.",
    },
    "grasa_fecal": {
        "nombre": "Grasa fecal (coeficiente de absorción)",
        "unidad": "%",
        "tipo": "numerico",
        "rangos": [
            (0, 36, 85, None, None, "<3 años"),
            (36, None, 95, None, None, ">3 años"),
        ],
        "descripcion": "Indicador de malabsorción de grasa.",
        "deficiencia": "",
        "pitfalls": "Clásicamente requiere recolección de heces de 72 horas con diario dietético y aporte adecuado de grasa.",
    },
    "ferritina": {
        "nombre": "Ferritina (suero)",
        "unidad": "µg/l",
        "tipo": "numerico",
        "rangos": [
            (0, 1, 25, 200, None, "Neonato"),
            (1, 2, 200, 600, None, "1 mes"),
            (2, 5, 50, 200, None, "2-5 meses"),
            (5, 180, 7, 140, None, "6 meses a 15 años"),
        ],
        "descripcion": "Principal forma de almacenamiento de hierro; sus niveles reflejan las reservas corporales.",
        "deficiencia": "Indicador temprano y sensible de anemia ferropénica.",
        "pitfalls": "Reactante de fase aguda positivo.",
    },
    "folato": {
        "nombre": "Folato (suero)",
        "unidad": "nmol/l",
        "unidad_alterna": {"label": "ng/ml", "factor": 2.266},
        "tipo": "numerico",
        "rangos": [
            (0, 1, 16, 72, None, "Neonato"),
            (1, 216, 4, 20, None, "Niño"),
            (216, None, 10, 63, None, "Adulto"),
        ],
        "descripcion": "Vitamina hidrosoluble, papel en síntesis de ADN/ARN y metabolismo de aminoácidos.",
        "deficiencia": "Anemia macrocítica, neutrófilos hipersegmentados, glositis, estomatitis, retraso del crecimiento y defectos del tubo neural fetal.",
        "pitfalls": "Metotrexato, fenitoína y sulfasalazina antagonizan la utilización de folato.",
    },
    "hemoglobina": {
        "nombre": "Hemoglobina (sangre total)",
        "unidad": "mmol/l",
        "unidad_alterna": {"label": "g/dl", "factor": 0.6206},
        "tipo": "numerico",
        "rangos": [
            (0, 0.3, 2.06, 3.79, None, "0-8 días"),
            (0.3, 3, 1.66, 3.33, None, "9 días a 3 meses"),
            (3, 12, 1.53, 2.25, None, "3 meses a 1 año"),
            (12, 36, 1.38, 2.14, None, "1-3 años"),
            (36, 132, 1.58, 2.31, None, "3-11 años"),
            (132, 216, 1.72, 2.43, None, "11-18 años"),
            (216, None, 1.86, 2.48, "M", "Adulto varón"),
            (216, None, 2.17, 2.79, "F", "Adulta mujer"),
        ],
        "descripcion": "Molécula transportadora de oxígeno en el eritrocito.",
        "deficiencia": "Microcítica: deficiencia de hierro, enfermedad crónica. Normocítica: enfermedad crónica, sangrado agudo. Macrocítica: deficiencia de B12/folato.",
        "pitfalls": "Influenciada por estado de hidratación, nutrición y embarazo.",
    },
    "hierro": {
        "nombre": "Hierro (suero)",
        "unidad": "µmol/l",
        "unidad_alterna": {"label": "µg/dl", "factor": 0.1791},
        "tipo": "numerico",
        "rangos": [
            (0, 1, 17.9, 44.8, None, "Neonato"),
            (1, 12, 7.2, 17.9, None, "Lactante"),
            (12, 216, 9, 21.5, None, "Niño"),
            (216, None, 11.6, 31.3, "M", "Adulto varón"),
            (216, None, 9, 30.4, "F", "Adulta mujer"),
        ],
        "descripcion": "Componente de proteínas hemo y citocromos.",
        "deficiencia": "Anemia microcítica, palidez, debilidad y disnea.",
        "pitfalls": "La transferrina es una medida más sensible de reservas de hierro corporal, pero es una proteína de fase aguda negativa.",
    },
    "linfocitos": {
        "nombre": "Linfocitos totales (sangre total)",
        "unidad": "/mm3",
        "tipo": "numerico",
        "rangos": [(0, None, 1500, None, None, "Todas las edades")],
        "descripcion": "El recuento total de linfocitos se correlaciona inversamente con el grado de desnutrición.",
        "deficiencia": "",
        "pitfalls": "",
    },
    "magnesio": {
        "nombre": "Magnesio (suero)",
        "unidad": "mmol/l",
        "unidad_alterna": {"label": "mg/dl", "factor": 0.4115},
        "tipo": "numerico",
        "rangos": [(0, None, 0.63, 1.00, None, "Todas las edades")],
        "descripcion": "Importante para la conducción neuromuscular; cofactor enzimático.",
        "deficiencia": "Arritmia, tetania, hipocalcemia e hipokalemia.",
        "pitfalls": "↓ por albúmina sérica baja; ↑ en muestras hemolizadas.",
    },
    "ph_fecal": {
        "nombre": "pH fecal",
        "unidad": "pH",
        "tipo": "numerico",
        "rangos": [(0, None, 5.5, None, None, "Todas las edades")],
        "descripcion": "Un pH fecal bajo generalmente implica malabsorción de carbohidratos.",
        "deficiencia": "",
        "pitfalls": "El procesamiento inadecuado de la muestra puede dar valores falsamente bajos.",
    },
    "fosforo": {
        "nombre": "Fósforo (suero)",
        "unidad": "mmol/l",
        "unidad_alterna": {"label": "mg/dl", "factor": 0.3229},
        "tipo": "numerico",
        "rangos": [
            (0, 1, 1.45, 2.91, None, "Neonato"),
            (0.33, 24, 1.29, 2.1, None, "10 días a 2 años"),
            (24, 108, 1.03, 1.87, None, "3-9 años"),
            (108, 180, 1.07, 1.74, None, "10-15 años"),
            (180, None, 0.78, 1.42, None, ">15 años"),
        ],
        "descripcion": "Vital para la transferencia de energía a nivel celular.",
        "deficiencia": "Confusión, dificultad respiratoria, hipoxia tisular, anomalías óseas y ↑ fosfatasa alcalina.",
        "pitfalls": "El 'síndrome de realimentación' es hipofosfatemia e hipokalemia que complica la rehabilitación nutricional del paciente gravemente desnutrido.",
    },
    "prealbumina": {
        "nombre": "Prealbúmina / transtiretina (suero)",
        "unidad": "mg/l",
        "unidad_alterna": {"label": "mg/dl", "factor": 10},
        "tipo": "numerico",
        "rangos": [
            (0, 1, 70, 390, None, "Neonato"),
            (1, 6, 80, 340, None, "1-6 meses"),
            (6, 48, 120, 360, None, "6 meses a 4 años"),
            (48, 72, 120, 300, None, "4-6 años"),
            (72, 228, 120, 420, None, "6-19 años"),
        ],
        "descripcion": "Medida de reservas de proteína visceral; vida media de 2 días.",
        "deficiencia": "Reactante de fase aguda negativo.",
        "pitfalls": "",
    },
    "tiempo_protrombina": {
        "nombre": "Tiempo de protrombina (plasma)",
        "unidad": "s",
        "tipo": "numerico",
        "rangos": [(0, None, 11, 15, None, "Todas las edades")],
        "descripcion": "Usado para evaluar suficiencia de vitamina K, aunque se evalúa mejor con protrombina descarboxilada (PIVKA-II).",
        "deficiencia": "",
        "pitfalls": "También se prolonga en disfunción hepática, síndromes de malabsorción, uso prolongado de antibióticos y terapia con warfarina.",
    },
    "sustancias_reductoras": {
        "nombre": "Sustancias reductoras (heces)",
        "unidad": "",
        "tipo": "cualitativo",
        "valor_normal": "negativo",
        "descripcion": "Su presencia sugiere malabsorción de carbohidratos.",
        "deficiencia": "",
        "pitfalls": "El procesamiento inadecuado de la muestra puede dar valores falsamente normales.",
    },
    "proteina_ligadora_retinol": {
        "nombre": "Proteína ligadora de retinol (suero)",
        "unidad": "mg/l",
        "unidad_alterna": {"label": "mg/dl", "factor": 10},
        "tipo": "numerico",
        "rangos": [
            (0, 108, 10, 78, None, "<9 años"),
            (108, None, 13, 99, None, "≥9 años"),
        ],
        "descripcion": "Medida de reservas de proteína visceral; vida media de 12 h.",
        "deficiencia": "↓ en deficiencia de vitamina A y disfunción hepática. Reactante de fase aguda negativo.",
        "pitfalls": "↑ en insuficiencia renal.",
    },
    "selenio": {
        "nombre": "Selenio (suero)",
        "unidad": "µmol/l",
        "unidad_alterna": {"label": "µg/l", "factor": 0.0127},
        "tipo": "numerico",
        "rangos": [
            (0, 12, 0.8, 1.1, None, "Término (0-12 meses)"),
            (12, 60, 1.4, 1.7, None, "1-5 años"),
            (60, 108, 1.4, 1.8, None, "6-9 años"),
            (108, None, 1.6, 2.1, None, "≥10 años"),
        ],
        "descripcion": "Mineral traza esencial para la glutatión peroxidasa.",
        "deficiencia": "Cardiomiopatía (enfermedad de Keshan), miositis y distrofia ungueal.",
        "pitfalls": "",
    },
    "nitrogeno_ureico": {
        "nombre": "Nitrógeno ureico (suero)",
        "unidad": "mmol/l",
        "unidad_alterna": {"label": "mg/dl", "factor": 0.357},
        "tipo": "numerico",
        "rangos": [
            (0, 1, 0.7, 6.7, None, "Neonato"),
            (1, 216, 1.8, 6.4, None, "Lactante/niño"),
            (216, None, 2.1, 7.1, None, "Adulto"),
        ],
        "descripcion": "Producido en el hígado a partir de la degradación de proteínas y excretado por vía renal.",
        "deficiencia": "↓ en estados de bajo aporte proteico.",
        "pitfalls": "↑ en dietas hiperproteicas, pero también en enfermedad renal.",
    },
    "vitamina_a": {
        "nombre": "Vitamina A (suero)",
        "unidad": "µmol/l",
        "tipo": "numerico",
        "rangos": [
            (0, 12, 0.63, 1.75, None, "Término (0-12 meses)"),
            (12, 72, 0.7, 1.5, None, "1-6 años"),
            (72, 144, 0.9, 1.7, None, "7-12 años"),
            (144, 228, 0.9, 2.5, None, "13-19 años"),
        ],
        "descripcion": "Vitamina liposoluble, función en visión, mantenimiento del epitelio e inmunidad; 90% almacenada en hígado.",
        "deficiencia": "Ceguera nocturna reversible (primera manifestación clínica), que sin corregir puede progresar a cicatrización corneal.",
        "pitfalls": "↓ en enfermedad hepática, deficiencia de zinc. ↑ con uso de anticonceptivos orales.",
    },
    "vitamina_b1": {
        "nombre": "Vitamina B1 — tiamina (sangre total)",
        "unidad": "% actividad transcetolasa eritrocitaria",
        "tipo": "numerico_invertido",
        "rangos": [(0, None, None, 15, None, "Todas las edades")],
        "descripcion": "Vitamina hidrosoluble con rol en fosforilación oxidativa y vía de las pentosas fosfato.",
        "deficiencia": "Beriberi: falla cardiaca, neuropatía periférica ± edema. Encefalopatía de Wernicke, síndrome de Korsakoff.",
        "pitfalls": "",
    },
    "vitamina_b2": {
        "nombre": "Vitamina B2 — riboflavina (sangre total)",
        "unidad": "% actividad glutatión reductasa eritrocitaria",
        "tipo": "numerico_invertido",
        "rangos": [(0, None, None, 20, None, "Todas las edades")],
        "descripcion": "Vitamina hidrosoluble que facilita reacciones redox.",
        "deficiencia": "Dermatitis, queilitis, glositis y alteración visual.",
        "pitfalls": "",
    },
    "vitamina_b6": {
        "nombre": "Vitamina B6 — piridoxina (plasma)",
        "unidad": "nmol/l",
        "tipo": "numerico",
        "rangos": [(0, None, 14.6, 72.8, None, "Todas las edades")],
        "descripcion": "Cofactor para enzimas de reacciones de aminotransferencia.",
        "deficiencia": "Anemia microcítica-hipocrómica, dermatitis, queilosis, estomatitis, neuropatía periférica, convulsiones y ↓ AST/ALT.",
        "pitfalls": "↓ nivel con tratamiento con isoniazida.",
    },
    "vitamina_b12": {
        "nombre": "Vitamina B12 — cobalamina (suero)",
        "unidad": "pmol/l",
        "unidad_alterna": {"label": "pg/ml", "factor": 0.738},
        "tipo": "numerico",
        "rangos": [
            (0, 1, 118, 959, None, "Neonato"),
            (1, 216, 148, 616, None, "Lactante/niño"),
        ],
        "descripcion": "Vitamina hidrosoluble activa en síntesis de ADN y metabolismo de aminoácidos de cadena ramificada.",
        "deficiencia": "Anemia megaloblástica, neutrófilos hipersegmentados, glositis, estomatitis, debilidad, homocisteína y ácido metilmalónico elevados.",
        "pitfalls": "↓ por fenitoína, inhibidores de bomba de protones, neomicina y deficiencia de folato.",
    },
    "vitamina_c": {
        "nombre": "Vitamina C — ascorbato (plasma)",
        "unidad": "µmol/l",
        "unidad_alterna": {"label": "mg/dl", "factor": 56.78},
        "tipo": "numerico",
        "rangos": [(0, None, 23, 114, None, "Todas las edades")],
        "descripcion": "Antioxidante hidrosoluble importante en la síntesis de colágeno.",
        "deficiencia": "Escorbuto: hemorragia petequial y gingival, gingivitis y mala cicatrización de heridas.",
        "pitfalls": "",
    },
    "vitamina_d": {
        "nombre": "Vitamina D — 25-hidroxi (plasma)",
        "unidad": "µg/l",
        "tipo": "numerico",
        "rangos": [(0, None, 14, 80, None, "Todas las edades (varía según temporada: verano 15-80, invierno 14-42)")],
        "descripcion": "Vitamina liposoluble implicada en la homeostasis de calcio y fósforo.",
        "deficiencia": "La deficiencia afecta principalmente el hueso y se denomina 'raquitismo'; ↓ calcio y fósforo séricos, ↑ fosfatasa alcalina.",
        "pitfalls": "↓ con terapia anticonvulsivante y colestiramina.",
    },
    "vitamina_e": {
        "nombre": "Vitamina E (suero)",
        "unidad": "µmol/l",
        "tipo": "numerico",
        "rangos": [
            (0, 12, 2, 8, None, "Término (0-12 meses)"),
            (12, 144, 7, 21, None, "1-12 años"),
            (144, 228, 14, 23, None, "13-19 años"),
        ],
        "descripcion": "Antioxidante liposoluble que protege las membranas celulares.",
        "deficiencia": "Disminución de reflejos tendinosos profundos, alteración del equilibrio y la marcha.",
        "pitfalls": "Transportada en suero unida a lípidos; la hiperlipidemia puede enmascarar la deficiencia; el índice vitamina E/lípidos es útil en estas circunstancias.",
    },
    "zinc": {
        "nombre": "Zinc (plasma)",
        "unidad": "µmol/l",
        "unidad_alterna": {"label": "µg/dl", "factor": 0.153},
        "tipo": "numerico",
        "rangos": [(0, None, 10.7, 18.4, None, "Todas las edades")],
        "descripcion": "Cofactor de más de 200 enzimas, notablemente fosfatasa alcalina, ARN/ADN polimerasa y superóxido dismutasa.",
        "deficiencia": "Acrodermatitis enteropática, retraso en cicatrización de heridas, alteración del gusto, falla de crecimiento, retraso puberal y diarrea.",
        "pitfalls": "↑ en muestras hemolizadas. ↓ en pacientes con drepanocitosis, hipoalbuminemia.",
    },
}


def listar_pruebas() -> List[str]:
    """Devuelve los códigos de todas las pruebas disponibles, ordenados por nombre."""
    return sorted(LAB_TESTS.keys(), key=lambda k: LAB_TESTS[k]["nombre"])


def obtener_prueba(codigo: str) -> Optional[Dict[str, Any]]:
    return LAB_TESTS.get(codigo)


def unidades_disponibles(codigo: str) -> List[str]:
    """Devuelve las unidades en las que se puede capturar el valor de una prueba.

    La primera es siempre la unidad base usada en los rangos de referencia.
    Solo se ofrece una unidad convencional alterna (mg/dl, g/dl, etc.) cuando
    existe un factor de conversión inequívoco; las pruebas expresadas en UI
    o en porcentaje de actividad no tienen unidad alterna.
    """
    prueba = obtener_prueba(codigo)
    if not prueba:
        return []
    unidades = [prueba.get("unidad", "")]
    alterna = prueba.get("unidad_alterna")
    if alterna:
        unidades.append(alterna["label"])
    return unidades


def convertir_a_base(codigo: str, valor: float, unidad: Optional[str]) -> float:
    """Convierte un valor a la unidad base de la prueba (la usada en los rangos).

    Si `unidad` coincide con la unidad base, o no se reconoce, el valor se
    devuelve sin modificar.
    """
    prueba = obtener_prueba(codigo)
    if not prueba:
        return valor
    if unidad is None or unidad == prueba.get("unidad", ""):
        return valor
    alterna = prueba.get("unidad_alterna")
    if alterna and unidad == alterna["label"]:
        return valor * alterna["factor"]
    return valor


def _buscar_rango(prueba: Dict[str, Any], edad_meses: Optional[float], sexo: Optional[str]):
    """Encuentra el rango de referencia aplicable según edad y sexo."""
    if edad_meses is None:
        return None
    candidatos = []
    for r in prueba.get("rangos", []):
        min_m, max_m, low, high, sexo_r, label = r
        if edad_meses < min_m:
            continue
        if max_m is not None and edad_meses >= max_m:
            continue
        if sexo_r is not None and sexo is not None and sexo_r != sexo:
            continue
        candidatos.append(r)
    if not candidatos:
        return None
    # Preferir el rango específico de sexo si existe
    especificos = [c for c in candidatos if c[4] is not None]
    return especificos[0] if especificos else candidatos[0]


def clasificar_resultado(codigo: str, valor: Any, edad_meses: Optional[float] = None,
                          sexo: Optional[str] = None, unidad: Optional[str] = None) -> Dict[str, Any]:
    """
    Clasifica un valor de laboratorio comparándolo con el rango de referencia
    según la edad (y sexo, cuando aplica).

    Si `unidad` corresponde a la unidad convencional alterna de la prueba
    (p. ej. mg/dl, g/dl), el valor se convierte primero a la unidad base
    (p. ej. mmol/l, g/l) antes de compararlo con el rango de referencia.

    Devuelve un diccionario con: prueba, unidad, valor, valor_original,
    unidad_original, rango_texto, clasificacion ('Normal', 'Bajo', 'Alto',
    'Anormal', 'Sin rango'), etiqueta_rango.
    """
    prueba = obtener_prueba(codigo)
    if not prueba:
        return {"error": "Prueba no reconocida"}

    resultado = {
        "prueba": prueba["nombre"],
        "unidad": prueba.get("unidad", ""),
        "valor": valor,
        "valor_original": valor,
        "unidad_original": unidad or prueba.get("unidad", ""),
    }

    if prueba["tipo"] == "cualitativo":
        valor_norm = str(valor).strip().lower()
        esperado = prueba.get("valor_normal", "negativo").lower()
        resultado["rango_texto"] = f"Esperado: {prueba.get('valor_normal', '')}"
        resultado["etiqueta_rango"] = "Todas las edades"
        resultado["clasificacion"] = "Normal" if valor_norm == esperado else "Anormal"
        return resultado

    try:
        valor_num = convertir_a_base(codigo, float(valor), unidad)
        resultado["valor"] = valor_num
    except (TypeError, ValueError):
        resultado["clasificacion"] = "Sin rango"
        resultado["rango_texto"] = "Valor no numérico"
        resultado["etiqueta_rango"] = ""
        return resultado

    rango = _buscar_rango(prueba, edad_meses, sexo)
    if rango is None:
        resultado["clasificacion"] = "Sin rango"
        resultado["rango_texto"] = "Sin rango de referencia definido para esta edad"
        resultado["etiqueta_rango"] = ""
        return resultado

    _, _, low, high, _, label = rango
    if low is not None and high is not None:
        rango_texto = f"{low} - {high} {prueba.get('unidad', '')}".strip()
    elif low is not None:
        rango_texto = f"> {low} {prueba.get('unidad', '')}".strip()
    else:
        rango_texto = f"< {high} {prueba.get('unidad', '')}".strip()

    resultado["rango_texto"] = rango_texto
    resultado["etiqueta_rango"] = label

    if low is not None and valor_num < low:
        resultado["clasificacion"] = "Bajo"
    elif high is not None and valor_num > high:
        resultado["clasificacion"] = "Alto"
    else:
        resultado["clasificacion"] = "Normal"

    return resultado
