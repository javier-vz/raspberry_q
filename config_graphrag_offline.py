"""
config_graphrag_offline.py
==========================
Configuración optimizada para modelos locales pequeños (1B-3B).
Reemplaza config_graphrag.py cuando se usa Ollama en RPi5.

Diferencias vs config_graphrag.py original:
- SYSTEM_PROMPT mucho más corto (modelos 3B pierden instrucciones largas)
- Prohibición explícita de inventar información
- USER_PROMPT más directo
- Sin ejemplos en el prompt (ahorran tokens, el modelo los ignora igual)
"""

# ============================================================================
# PROMPTS OPTIMIZADOS PARA MODELOS 3B
# ============================================================================

SYSTEM_PROMPT = """Eres un asistente sobre la festividad andina Qoyllur Rit'i (Cusco, Perú).

REGLAS ESTRICTAS:
1. Usa SOLO la información del contexto. NUNCA inventes datos.
2. Si el contexto dice "Está en: X" → di "está en X". Úsalo directamente.
3. Responde en 2-3 oraciones en español. Sin listas con bullets al final.
4. No uses asteriscos ni markdown. Solo texto plano.
5. Si no hay información relevante, di: "El contexto no contiene esa información."

PROHIBIDO inventar: rituales, motivaciones, prácticas, simbolismos no mencionados en el contexto."""

USER_PROMPT_TEMPLATE = """Contexto:
{contexto}

Pregunta: {pregunta}

Responde en 2-3 oraciones usando solo el contexto. Sin asteriscos, sin bullets al final:"""

# ============================================================================
# MAPEOS DE RELACIONES (sin cambios — compatibilidad total)
# ============================================================================

MAPEOS_RELACIONES = {
    'realizadoPor': 'Realizado por',
    'realizado': 'Realizado por',
    'realizaPrincipalmente': 'Realizado principalmente por',
    'esResponsableDe': 'Responsable de',
    'estaEn': 'Está en',
    'contiene': 'Contiene',
    'esParteDelApu': 'Parte del apu',
    'estaEnLadera': 'En ladera de',
    'tieneLugar': 'Tiene lugar en',
    'ocurre': 'Ocurre en',
    'ocurreEnLugar': 'Ocurre en',
    'defineMarcoTemporal': 'Parte de',
    'tieneDuracionHoras': 'Duración (hrs)',
    'tieneFecha': 'Fecha',
    'tieneHoraInicio': 'Hora',
    'esPeriodicoCon': 'Periodicidad',
    'participan': 'Participan',
    'participa': 'Participa en',
    'participaEn': 'Participa en',
    'requiereIntermediario': 'Requiere intermediario',
    'perteneceA': 'Pertenece a',
    'esParte': 'Incluye',
    'esParteDeFestividad': 'Parte de la festividad',
    'aloja': 'Aloja en',
    'utiliza': 'Utiliza',
    'desde': 'Desde',
    'hacia': 'Hacia',
    'pasaPor': 'Pasa por',
    'conduceA': 'Conduce a',
    'esDestinoRitualDe': 'Destino ritual de',
    'esLugarDeRitual': 'Lugar de ritual',
    'esVeneradoEn': 'Venerado en',
    'requiereRol': 'Requiere rol',
    'desempeniaRol': 'Desempeña rol',
    'ejecutaDanza': 'Ejecuta danza',
    'utilizaObjeto': 'Utiliza',
    'portaObjeto': 'Porta',
    'usaObjetoRitual': 'Usa objeto',
    'usaVestimenta': 'Usa vestimenta',
    'tieneParte': 'Tiene parte',
    'esParteDe': 'Es parte de',
    'hechoDeRitual': 'Hecho de',
    'tieneNombreLocal': 'Nombre local',
    'tieneAltitudMetros': 'Altitud',
    'tieneImportancia': 'Importancia',
    'cantidadAproximada': 'Cantidad aprox.',
}


def mapear_relacion(rel_tipo: str, obj_nombre: str) -> str:
    for key, value in MAPEOS_RELACIONES.items():
        if key.lower() in rel_tipo.lower():
            if 'Altitud' in value:
                return f"{value}: {obj_nombre} msnm"
            elif 'Duración' in value:
                return f"{value}: {obj_nombre}"
            elif 'Fecha' in value or 'Hora' in value:
                return f"{value}: {obj_nombre}"
            return f"{value}: {obj_nombre}"
    return f"Relacionado con: {obj_nombre}"


def obtener_relaciones_naturales(entidad: dict, max_relaciones: int = 4, max_objetos: int = 3) -> list:
    return []


# ============================================================================
# CONFIGURACIÓN
# ============================================================================

class Config:
    # Búsqueda
    TOP_K_BUSQUEDA = 10
    TOP_K_CONTEXTO = 5

    # Contexto — ligeramente reducido para modelos 3B
    MAX_CHARS_CONTEXTO = 1800
    MAX_CHARS_DESC = 200
    MAX_RELACIONES = 4
    MAX_OBJETOS_POR_REL = 3

    # LLM — ajustado para Ollama local
    MODELO_GROQ = "llama3.2:3b"   # referencia, no se usa directamente
    MAX_TOKENS = 250               # respuestas más cortas = menos alucinaciones
    TEMPERATURE = 0.05             # casi determinístico
    TOP_P = 0.9

    # Frases que indican alucinación
    FRASES_PROHIBIDAS = [
        'purificar', 'alma', 'almas', 'fe', 'renovar',
        'conectar con', 'experiencia espiritual', 'oportunidad',
        'les permite', 'importante para', 'simboliza',
        'desafío espiritual', 'prácticas simbólicas',
        'vinculados a', 'relacionadas con el hielo',
    ]


# ============================================================================
# METADATA
# ============================================================================

CONFIG_VERSION = "2.0.0-offline"
CONFIG_DATE = "2026-03-29"
CONFIG_DESCRIPTION = "Config optimizada para modelos locales 1B-3B en Raspberry Pi 5"
