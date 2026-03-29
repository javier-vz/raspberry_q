#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GraphRAG v4.0 Offline — Versión para Raspberry Pi 5
====================================================
Reemplaza Groq API por Ollama (LLM local).
Sin dependencias externas de red. 100% offline.

Uso:
    Requiere Ollama corriendo en localhost:11434
    Modelo recomendado: llama3.2:3b o gemma2:2b

Compatibilidad:
    - Drop-in replacement de graphrag_v4_api.py
    - Misma interfaz pública: responder(), responder_con_api()
    - app.py solo necesita cambiar la importación
"""

import time
import urllib.request
import urllib.error
import json
from typing import List

# Importar GraphRAG v2.0 como base
from graphrag_v2 import GraphRAG_v2

# Importar configuración optimizada para modelos offline
# Usa config_graphrag_offline.py si existe, si no cae al original
try:
    from config_graphrag_offline import (
        SYSTEM_PROMPT,
        USER_PROMPT_TEMPLATE,
        mapear_relacion,
        Config
    )
except ImportError:
    from config_graphrag import (
        SYSTEM_PROMPT,
        USER_PROMPT_TEMPLATE,
        mapear_relacion,
        Config
    )


def limpiar_markdown(texto: str) -> str:
    """
    Elimina markdown que los modelos pequeños generan
    aunque se les pida no hacerlo.
    - **negrita** → negrita
    - *italica* → italica  
    - bullets al final (• Está en: X) → se eliminan
    """
    import re
    # Quitar **negrita**
    texto = re.sub(r'\*\*([^*]+)\*\*', r'\1', texto)
    # Quitar *italica*
    texto = re.sub(r'\*([^*]+)\*', r'\1', texto)
    # Quitar bullets sueltos al final (• Está en: X • Altitud: Y)
    # Estos son restos del contexto que el modelo copia literalmente
    texto = re.sub(r'\s*[•·]\s*(Está en|Altitud|Contiene|Realizado|Duración|Fecha)[^•\n]*', '', texto)
    # Limpiar espacios extra
    texto = re.sub(r'  +', ' ', texto).strip()
    return texto


# ============================================================================
# CONFIGURACIÓN OFFLINE
# ============================================================================

class ConfigOffline:
    """Parámetros específicos para modelos locales pequeños."""

    # Ollama server — cambiar si corre en otro puerto
    OLLAMA_URL = "http://localhost:11434"

    # Modelos recomendados en orden de preferencia (se usará el primero disponible)
    # Latencia estimada en RPi5 con 8GB RAM:
    #   qwen2.5:1.5b  → ~3-5s   (más rápido, calidad ok)
    #   llama3.2:3b   → ~5-10s  (balance calidad/velocidad)
    #   gemma2:2b     → ~4-7s   (buena comprensión de español)
    #   phi3.5:mini   → ~6-10s  (mejor calidad general)
    MODELOS_PREFERIDOS = [
        "llama3.2:3b",
        "gemma2:2b",
        "qwen2.5:1.5b",
        "phi3.5:mini",
        "llama3.2:1b",  # fallback mínimo
    ]

    # Límites ajustados para modelos pequeños
    MAX_TOKENS = 300          # Modelos pequeños se pierden con respuestas largas
    TEMPERATURE = 0.1         # Ligeramente más alto que Groq para variabilidad
    TOP_P = 0.9

    # Timeouts
    TIMEOUT_SEGUNDOS = 60     # RPi5 puede tardar en modelos 3B


# ============================================================================
# SISTEMA PROMPT SIMPLIFICADO PARA MODELOS PEQUEÑOS
# ============================================================================

# Los modelos de 1-3B siguen mejor instrucciones cortas y directas.
# Si el modelo elegido es >= 3B, se usa el prompt completo de config_graphrag.
SYSTEM_PROMPT_SIMPLE = """Eres un asistente especializado en la festividad andina Qoyllur Rit'i (Cusco, Perú).

REGLAS:
1. Responde SOLO con información del contexto dado
2. Sé directo y conciso (2-4 oraciones máximo)
3. Si hay información de ubicación (está en, altitud), úsala
4. No inventes información que no esté en el contexto
5. Responde en español

Si no hay información relevante, di: "El contexto no contiene información sobre eso."
"""

USER_PROMPT_SIMPLE = """Contexto sobre Qoyllur Rit'i:
{contexto}

Pregunta: {pregunta}

Respuesta (basada solo en el contexto, 2-4 oraciones):"""


# ============================================================================
# CLIENTE OLLAMA (sin dependencias externas)
# ============================================================================

def _llamar_ollama(
    modelo: str,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 300,
    temperature: float = 0.1,
    timeout: int = 60,
    base_url: str = "http://localhost:11434"
) -> str:
    """
    Llama a Ollama usando solo urllib (sin openai, sin requests).
    Retorna el texto generado o lanza excepción.
    """
    url = f"{base_url}/api/chat"

    payload = {
        "model": modelo,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
        "stream": False,
        "options": {
            "temperature": temperature,
            "top_p": 0.9,
            "num_predict": max_tokens,
        }
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read().decode("utf-8")
        result = json.loads(body)
        # Ollama /api/chat response
        return result["message"]["content"].strip()


def verificar_ollama(base_url: str = "http://localhost:11434") -> bool:
    """Comprueba si Ollama está corriendo."""
    try:
        req = urllib.request.Request(f"{base_url}/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=3):
            return True
    except Exception:
        return False


def listar_modelos_disponibles(base_url: str = "http://localhost:11434") -> list:
    """Retorna lista de modelos instalados en Ollama."""
    try:
        req = urllib.request.Request(f"{base_url}/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return [m["name"] for m in data.get("models", [])]
    except Exception:
        return []


def seleccionar_mejor_modelo(base_url: str = "http://localhost:11434") -> str | None:
    """
    Elige el mejor modelo disponible según lista de preferencia.
    Retorna None si Ollama no está disponible o no hay modelos.
    """
    disponibles = listar_modelos_disponibles(base_url)
    if not disponibles:
        return None

    disponibles_lower = [m.lower() for m in disponibles]

    for preferido in ConfigOffline.MODELOS_PREFERIDOS:
        for nombre_real in disponibles:
            if preferido.split(":")[0] in nombre_real.lower():
                return nombre_real

    # Si ninguno de la lista, usar el primero disponible
    return disponibles[0] if disponibles else None


# ============================================================================
# CLASE PRINCIPAL
# ============================================================================

class GraphRAG_v4_Offline(GraphRAG_v2):
    """
    GraphRAG v4.0 Offline para Raspberry Pi 5.

    Arquitectura:
    - Búsqueda: Embeddings semánticos + BM25 (idéntico a v4 API)
    - Generación: Ollama LLM local (reemplaza Groq)

    Interfaz pública idéntica a GraphRAG_v4_API para compatibilidad
    con app.py sin cambios adicionales.
    """

    def __init__(
        self,
        ttl_path: str,
        ollama_url: str = None,
        modelo: str = None,
        verbose: bool = False
    ):
        """
        Args:
            ttl_path:   Ruta al archivo TTL
            ollama_url: URL de Ollama (default: http://localhost:11434)
            modelo:     Forzar un modelo específico (default: auto-detectar)
            verbose:    Mostrar mensajes de debug
        """
        # Inicializar base (carga grafo + embeddings)
        super().__init__(ttl_path)

        self.verbose_mode = verbose
        self.ollama_url = ollama_url or ConfigOffline.OLLAMA_URL

        # ── Detectar Ollama y modelo ─────────────────────────────────────────
        self._ollama_disponible = verificar_ollama(self.ollama_url)

        if self._ollama_disponible:
            if modelo:
                self.modelo = modelo
            else:
                self.modelo = seleccionar_mejor_modelo(self.ollama_url)

            if not self.modelo:
                self._ollama_disponible = False
                print("⚠️  Ollama disponible pero sin modelos instalados.")
                print("   Instala un modelo: ollama pull llama3.2:3b")
        else:
            self.modelo = None
            print("⚠️  Ollama no detectado en", self.ollama_url)
            print("   El sistema usará respuestas basadas en plantillas (v2).")

        # Elegir prompt según tamaño de modelo
        self._usar_prompt_simple = self._es_modelo_pequeno()

        if verbose:
            print("\n" + "=" * 60)
            if self._ollama_disponible:
                print(f"✅ Ollama conectado: {self.ollama_url}")
                print(f"   Modelo: {self.modelo}")
                print(f"   Prompt: {'simplificado' if self._usar_prompt_simple else 'completo'}")
            else:
                print("⚠️  Modo fallback: respuestas por plantilla (sin LLM)")
            print("=" * 60 + "\n")

    def _es_modelo_pequeno(self) -> bool:
        """True si el modelo tiene <= 2B parámetros (usa prompt simplificado)."""
        if not self.modelo:
            return True
        nombre = self.modelo.lower()
        indicadores_pequeno = ["1b", "1.5b", "2b", "0.5b", "tiny", "mini"]
        return any(ind in nombre for ind in indicadores_pequeno)

    # ── Método heredado de v4_api ────────────────────────────────────────────

    def expandir_partes(self, entidad: dict, max_partes: int = 10) -> str:
        """Expande las partes de un objeto compuesto (idéntico a v4_api)."""
        relaciones = entidad.get('relaciones', {})
        if 'tieneParte' not in relaciones:
            return ""

        partes_info = []
        for parte_id in relaciones['tieneParte'][:max_partes]:
            parte = self.entidades.get(parte_id)
            if not parte:
                continue

            parte_labels = parte.get('labels', [])
            nombre = parte_labels[0] if parte_labels else parte_id

            parte_comments = parte.get('comments', [])
            desc = parte_comments[0][:100] if parte_comments else ""

            material = None
            parte_props = parte.get('propiedades', {})
            if 'hechoDeRitual' in parte_props:
                material = parte_props['hechoDeRitual']

            if material and desc:
                partes_info.append(f"{nombre} ({desc}, hecho de {material})")
            elif desc:
                partes_info.append(f"{nombre} ({desc})")
            elif material:
                partes_info.append(f"{nombre} (hecho de {material})")
            else:
                partes_info.append(nombre)

        if partes_info:
            return f"\n  Partes: {'; '.join(partes_info)}"
        return ""

    def construir_contexto(
        self,
        entidades_ids: List[str],
        max_chars: int = None
    ) -> str:
        """
        Construye contexto para el LLM local.
        Idéntico a v4_api pero con límite de chars reducido
        para modelos pequeños.
        """
        # Modelos pequeños necesitan contextos más cortos
        if self._usar_prompt_simple:
            max_chars = max_chars or min(Config.MAX_CHARS_CONTEXTO, 1500)
        else:
            max_chars = max_chars or Config.MAX_CHARS_CONTEXTO

        partes = []
        chars_usados = 0

        for ent_id in entidades_ids[:Config.TOP_K_CONTEXTO]:
            if chars_usados > max_chars:
                break

            ent = self.entidades.get(ent_id, {})
            if not ent:
                continue

            labels = ent.get('labels', [])
            nombre = labels[0] if labels else ent_id

            comments = ent.get('comments', [])
            desc = comments[0] if comments else ""

            info = f"• {nombre}"
            if desc:
                info += f"\n  {desc[:Config.MAX_CHARS_DESC]}"

            relaciones = ent.get('relaciones', {})
            rels_naturales = []

            for rel_tipo, objetos in list(relaciones.items())[:Config.MAX_RELACIONES]:
                if rel_tipo == 'tieneParte':
                    continue
                for obj_id in objetos[:Config.MAX_OBJETOS_POR_REL]:
                    obj_ent = self.entidades.get(obj_id, {})
                    if obj_ent:
                        obj_labels = obj_ent.get('labels', [])
                        obj_nombre = obj_labels[0] if obj_labels else obj_id
                        rel_natural = mapear_relacion(rel_tipo, obj_nombre)
                        rels_naturales.append(rel_natural)

            if rels_naturales:
                info += f"\n  {'; '.join(rels_naturales[:3])}"

            partes_expansion = self.expandir_partes(ent)
            if partes_expansion:
                info += partes_expansion

            parte_len = len(info)
            if chars_usados + parte_len < max_chars:
                partes.append(info)
                chars_usados += parte_len

        if not partes:
            return "No se encontró información relevante en el grafo de conocimiento."

        return "\n\n".join(partes)

    def responder_con_api(
        self,
        pregunta: str,
        modo: str = "hibrido",
        verbose: bool = False
    ) -> str:
        """
        Responde usando Ollama local (misma firma que v4_api).

        Si Ollama no está disponible, hace fallback a respuesta
        basada en plantillas (v2).
        """
        if verbose:
            print(f"\n{'='*60}")
            print(f"🔍 Procesando: '{pregunta}'")

        # ── Fase 1: Búsqueda ────────────────────────────────────────────────
        start_busqueda = time.time()

        if modo == "semantico":
            resultados = self.buscar_semantico(pregunta, top_k=Config.TOP_K_BUSQUEDA)
        elif modo == "lexico":
            resultados = self.buscar_lexico(pregunta, top_k=Config.TOP_K_BUSQUEDA)
        else:
            resultados = self.buscar_hibrido(pregunta, top_k=Config.TOP_K_BUSQUEDA)

        t_busqueda = time.time() - start_busqueda

        if not resultados:
            return "No encontré información relacionada en el grafo."

        # ── Boost: vestimenta ────────────────────────────────────────────────
        if any(p in pregunta.lower() for p in ['vestimenta', 'traje', 'ropa', 'viste', 'visten', 'porta']):
            traje_id = None
            for ent_id, ent in self.entidades.items():
                if 'Traje de Ukumari' in ent.get('labels', []):
                    traje_id = ent_id
                    break
            if traje_id and traje_id not in [r[0] for r in resultados[:2]]:
                resultados.insert(0, (traje_id, 0.98))

        # ── Boost: ubicaciones ───────────────────────────────────────────────
        if any(p in pregunta.lower() for p in ['dónde', 'donde', 'ubicado', 'ubicación', 'está', 'esta']):
            entidades_con_ubicacion = []
            for ent_id, score in resultados[:5]:
                ent = self.entidades.get(ent_id, {})
                relaciones = ent.get('relaciones', {})
                if 'estaEn' in relaciones:
                    for ubicacion_id in relaciones['estaEn']:
                        if ubicacion_id not in [r[0] for r in resultados[:5]]:
                            entidades_con_ubicacion.append((ubicacion_id, score * 0.9))
            for i, (ent_id, score) in enumerate(entidades_con_ubicacion[:2], 2):
                resultados.insert(i, (ent_id, score))

        entidades_ids = [ent_id for ent_id, _ in resultados[:Config.TOP_K_CONTEXTO]]

        if verbose:
            print(f"   ✅ Búsqueda: {len(resultados)} resultados en {t_busqueda*1000:.0f}ms")

        # ── Fase 2: Contexto ─────────────────────────────────────────────────
        contexto = self.construir_contexto(entidades_ids)

        if verbose:
            print(f"   ✅ Contexto: {len(contexto)} chars")

        # ── Fase 3: LLM local (Ollama) ───────────────────────────────────────
        if not self._ollama_disponible or not self.modelo:
            # Fallback: usar respuesta por plantilla de v2
            if verbose:
                print("   ⚠️  Sin Ollama — usando respuesta por plantilla")
            return self._respuesta_plantilla(pregunta, entidades_ids, contexto)

        if verbose:
            print(f"   🤖 Generando con {self.modelo}...")

        # Elegir prompt según capacidad del modelo
        if self._usar_prompt_simple:
            system = SYSTEM_PROMPT_SIMPLE
            user   = USER_PROMPT_SIMPLE.format(contexto=contexto, pregunta=pregunta)
        else:
            system = SYSTEM_PROMPT
            user   = USER_PROMPT_TEMPLATE.format(contexto=contexto, pregunta=pregunta)

        start_llm = time.time()
        try:
            respuesta = _llamar_ollama(
                modelo      = self.modelo,
                system_prompt = system,
                user_prompt   = user,
                max_tokens  = ConfigOffline.MAX_TOKENS,
                temperature = ConfigOffline.TEMPERATURE,
                timeout     = ConfigOffline.TIMEOUT_SEGUNDOS,
                base_url    = self.ollama_url,
            )
            t_llm = time.time() - start_llm

            respuesta = limpiar_markdown(respuesta)

            if verbose:
                print(f"   ✅ LLM: {t_llm:.1f}s · {len(respuesta)} chars")

            return respuesta

        except urllib.error.URLError:
            # Ollama se cayó durante la sesión
            self._ollama_disponible = False
            if verbose:
                print("   ❌ Ollama desconectado — usando plantilla")
            return self._respuesta_plantilla(pregunta, entidades_ids, contexto)

        except Exception as e:
            if verbose:
                print(f"   ❌ Error LLM: {e}")
            return self._respuesta_plantilla(pregunta, entidades_ids, contexto)

    def _respuesta_plantilla(
        self,
        pregunta: str,
        entidades_ids: List[str],
        contexto: str
    ) -> str:
        """
        Respuesta de emergencia cuando no hay LLM disponible.
        Devuelve el contexto estructurado del grafo directamente.
        Más legible que el fallback v2 bruto.
        """
        if not entidades_ids:
            return "No encontré información relacionada en el grafo."

        ent_id = entidades_ids[0]
        ent = self.entidades.get(ent_id, {})
        labels = ent.get('labels', [])
        nombre = labels[0] if labels else ent_id
        comments = ent.get('comments', [])

        lineas = [f"**{nombre}**"]
        if comments:
            lineas.append(comments[0])

        # Relaciones clave
        relaciones = ent.get('relaciones', {})
        for rel_tipo in ['estaEn', 'contiene', 'realizadoPor', 'participan', 'tieneParte']:
            if rel_tipo in relaciones:
                for obj_id in relaciones[rel_tipo][:3]:
                    obj_ent = self.entidades.get(obj_id, {})
                    obj_labels = obj_ent.get('labels', [])
                    obj_nombre = obj_labels[0] if obj_labels else obj_id
                    rel_natural = mapear_relacion(rel_tipo, obj_nombre)
                    lineas.append(f"  • {rel_natural}")

        # Propiedades
        props = ent.get('propiedades', {})
        for prop in ['tieneAltitudMetros', 'tieneFecha', 'tieneDuracionHoras']:
            if prop in props:
                lineas.append(f"  • {mapear_relacion(prop, props[prop])}")

        return "\n".join(lineas)

    def responder(
        self,
        pregunta: str,
        use_api: bool = True,
        modo: str = "hibrido",
        verbose: bool = False
    ) -> str:
        """
        Wrapper principal — misma firma que GraphRAG_v4_API.responder().
        Compatibilidad total con app.py.
        """
        if use_api:
            return self.responder_con_api(pregunta, modo, verbose)
        else:
            return super().responder(pregunta, modo, verbose)

    def estado_ollama(self) -> dict:
        """Retorna estado del sistema para diagnóstico."""
        return {
            "ollama_url":        self.ollama_url,
            "ollama_disponible": self._ollama_disponible,
            "modelo":            self.modelo,
            "prompt_simple":     self._usar_prompt_simple,
            "modelos_instalados": listar_modelos_disponibles(self.ollama_url),
        }
