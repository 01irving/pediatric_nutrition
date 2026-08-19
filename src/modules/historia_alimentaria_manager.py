"""
Gestor de Historia Alimentaria.
Operaciones CRUD para el formulario de historia alimentaria del niño/a.
"""
import json
from typing import List, Optional, Dict, Any
from datetime import date
from src.database.db_manager import DatabaseManager


class HistoriaAlimentariaManager:
    """Maneja las operaciones CRUD de historia alimentaria."""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def guardar(self, paciente_id: int, fecha_evaluacion: date, evaluador: str,
                datos: Dict[str, Any]) -> int:
        """Guarda un registro completo de historia alimentaria."""
        campos = [
            'tipo_alimentacion',
            'lm_frecuencia', 'lm_duracion_minutos', 'lm_posicion_tecnica',
            'lm_suplementos', 'lm_suplementos_detalle',
            'fi_tipo_formula', 'fi_preparacion', 'fi_kcal_100ml',
            'fi_preparacion_fresca', 'fi_tomas_24h', 'fi_frecuencia',
            'fi_volumen_ofrecido', 'fi_volumen_real', 'fi_duracion_toma',
            'fi_adicional', 'fi_adicional_detalle',
            'comidas_snacks_dia', 'lugar_comidas',
            'patron_desayuno_hora', 'patron_desayuno_alimentos',
            'patron_merienda_manana_hora', 'patron_merienda_manana_alimentos',
            'patron_almuerzo_hora', 'patron_almuerzo_alimentos',
            'patron_merienda_tarde_hora', 'patron_merienda_tarde_alimentos',
            'patron_cena_hora', 'patron_cena_alimentos',
            'patron_otra_merienda_hora', 'patron_otra_merienda_alimentos',
            'apetito', 'apetito_comentarios',
            'comidas_familia', 'ambiente_agradable', 'ambiente_dificultades',
            'leche_cantidad', 'leche_tipo', 'jugo_cantidad',
            'snacks_frecuencia', 'snacks_tipo',
            'alergias', 'alergias_detalle', 'suplemento_vitaminico', 'otros_comentarios'
        ]

        placeholders = ', '.join(['?'] * (len(campos) + 3))
        columnas = ', '.join(['paciente_id', 'fecha_evaluacion', 'evaluador'] + campos)

        valores = [paciente_id, fecha_evaluacion.isoformat(), evaluador]
        for c in campos:
            v = datos.get(c, '')
            if isinstance(v, bool):
                v = 1 if v else 0
            valores.append(v)

        cursor = self.db.execute(
            f"INSERT INTO historia_alimentaria ({columnas}) VALUES ({placeholders})",
            tuple(valores)
        )
        self.db.commit()
        return cursor.lastrowid

    def obtener(self, historial_id: int) -> Optional[Dict[str, Any]]:
        """Obtiene un registro de historia alimentaria por ID."""
        row = self.db.fetchone(
            "SELECT * FROM historia_alimentaria WHERE id = ?", (historial_id,)
        )
        return dict(row) if row else None

    def listar_por_paciente(self, paciente_id: int) -> List[Dict[str, Any]]:
        """Lista todas las historias alimentarias de un paciente."""
        rows = self.db.fetchall(
            "SELECT * FROM historia_alimentaria WHERE paciente_id = ? ORDER BY fecha_evaluacion DESC",
            (paciente_id,)
        )
        return [dict(r) for r in rows]

    def eliminar(self, historial_id: int):
        """Elimina un registro de historia alimentaria."""
        self.db.execute("DELETE FROM historia_alimentaria WHERE id = ?", (historial_id,))
        self.db.commit()

    def generar_texto_reporte(self, datos: Dict[str, Any]) -> str:
        """Genera un reporte en texto plano de la historia alimentaria."""
        tipo_map = {
            'lactancia_exclusiva': 'Lactancia materna exclusiva',
            'formula_exclusiva': 'Fórmula infantil exclusiva',
            'mixta': 'Alimentación mixta (ambas)',
        }
        apetito_map = {'excelente': 'Excelente', 'bueno': 'Bueno', 'regular': 'Regular', 'pobre': 'Pobre'}
        snacks_map = {
            'nunca': 'Nunca', 'ocasionalmente': 'Ocasionalmente (1-2 veces/sem)',
            'frecuentemente': 'Frecuentemente (diario)', 'varias_veces_dia': 'Varias veces al día'
        }
        alergias_map = {'si': 'Sí', 'no': 'No', 'en_estudio': 'En estudio'}
        si_no_map = {'si': 'Sí', 'a_veces': 'A veces', 'no': 'No'}
        familia_map = {'siempre': 'Sí, siempre', 'a_veces': 'A veces', 'rara_vez': 'Rara vez', 'no': 'No'}

        lineas = [
            "=" * 70,
            "   FORMULARIO DE HISTORIA ALIMENTARIA — EVALUACIÓN NUTRICIONAL PEDIÁTRICA",
            "=" * 70,
            "",
            f"  Fecha de evaluación:   {datos.get('fecha_evaluacion', '')}",
            f"  Evaluador:             {datos.get('evaluador', '')}",
            "",
            "-" * 70,
            "  SECCIÓN 1: TIPO DE ALIMENTACIÓN DEL LACTANTE",
            "-" * 70,
            f"  Tipo de alimentación:  {tipo_map.get(datos.get('tipo_alimentacion', ''), 'No especificado')}",
            "",
            "-" * 70,
            "  SECCIÓN 2: LACTANCIA MATERNA",
            "-" * 70,
            f"  Frecuencia de alimentación:    {datos.get('lm_frecuencia', '')}",
            f"  Duración por pecho (min):       {datos.get('lm_duracion_minutos', '')}",
            f"  Posición y técnica:             {datos.get('lm_posicion_tecnica', '')}",
            f"  Ofrece suplementos:             {'Sí' if datos.get('lm_suplementos') else 'No'}",
            f"  Detalle suplementos:            {datos.get('lm_suplementos_detalle', '')}",
            "",
            "-" * 70,
            "  SECCIÓN 3: ALIMENTACIÓN CON FÓRMULA INFANTIL",
            "-" * 70,
            f"  Tipo de fórmula:                {datos.get('fi_tipo_formula', '')}",
            f"  Preparación:                    {datos.get('fi_preparacion', '')}",
            f"  Contenido energético (kcal/100ml): {datos.get('fi_kcal_100ml', '')}",
            f"  Preparación fresca:             {datos.get('fi_preparacion_fresca', '')}",
            f"  Tomas en 24 horas:              {datos.get('fi_tomas_24h', '')}",
            f"  Frecuencia:                     {datos.get('fi_frecuencia', '')}",
            f"  Volumen ofrecido (ml):          {datos.get('fi_volumen_ofrecido', '')}",
            f"  Volumen real consumido (ml):     {datos.get('fi_volumen_real', '')}",
            f"  Duración de cada toma (min):     {datos.get('fi_duracion_toma', '')}",
            f"  Añade algo adicional:            {'Sí' if datos.get('fi_adicional') else 'No'}",
            f"  Detalle adicional:              {datos.get('fi_adicional_detalle', '')}",
            "",
            "-" * 70,
            "  SECCIÓN 4: ALIMENTACIÓN EN NIÑOS MAYORES",
            "-" * 70,
            f"  Comidas y snacks al día:         {datos.get('comidas_snacks_dia', '')}",
            f"  Lugar de comidas:                {datos.get('lugar_comidas', '')}",
            "",
            "  Patrón de comidas del día:",
            f"    Desayuno:       Hora: {datos.get('patron_desayuno_hora', '')}  |  Alimentos: {datos.get('patron_desayuno_alimentos', '')}",
            f"    Merienda mañana: Hora: {datos.get('patron_merienda_manana_hora', '')}  |  Alimentos: {datos.get('patron_merienda_manana_alimentos', '')}",
            f"    Almuerzo:       Hora: {datos.get('patron_almuerzo_hora', '')}  |  Alimentos: {datos.get('patron_almuerzo_alimentos', '')}",
            f"    Merienda tarde:  Hora: {datos.get('patron_merienda_tarde_hora', '')}  |  Alimentos: {datos.get('patron_merienda_tarde_alimentos', '')}",
            f"    Cena:           Hora: {datos.get('patron_cena_hora', '')}  |  Alimentos: {datos.get('patron_cena_alimentos', '')}",
            f"    Otra merienda:   Hora: {datos.get('patron_otra_merienda_hora', '')}  |  Alimentos: {datos.get('patron_otra_merienda_alimentos', '')}",
            "",
            "-" * 70,
            "  APETITO Y AMBIENTE DURANTE LAS COMIDAS",
            "-" * 70,
            f"  Apetito:                        {apetito_map.get(datos.get('apetito', ''), 'No especificado')}",
            f"  Comentarios sobre el apetito:   {datos.get('apetito_comentarios', '')}",
            f"  Comidas en familia:             {familia_map.get(datos.get('comidas_familia'), 'No especificado')}",
            f"  Situaciones agradables:         {si_no_map.get(datos.get('ambiente_agradable'), 'No especificado')}",
            f"  Dificultades en comidas:        {datos.get('ambiente_dificultades', '')}",
            "",
            "-" * 70,
            "  CONSUMO DE LECHE Y JUGOS",
            "-" * 70,
            f"  Leche al día:                   {datos.get('leche_cantidad', '')}",
            f"  Tipo de leche:                  {datos.get('leche_tipo', '')}",
            f"  Jugo al día:                    {datos.get('jugo_cantidad', '')}",
            f"  Snacks/empaquetados:            {snacks_map.get(datos.get('snacks_frecuencia'), 'No especificado')}",
            f"  Tipo de snacks:                 {datos.get('snacks_tipo', '')}",
            "",
            "-" * 70,
            "  OBSERVACIONES ADICIONALES",
            "-" * 70,
            f"  Alergias/intolerancias:         {alergias_map.get(datos.get('alergias'), 'No especificado')}",
            f"  Detalle alergias:               {datos.get('alergias_detalle', '')}",
            f"  Suplemento vitamínico/mineral:  {datos.get('suplemento_vitaminico', '')}",
            f"  Otros comentarios padres:       {datos.get('otros_comentarios', '')}",
            "",
            "=" * 70,
        ]
        return "\n".join(lineas)
