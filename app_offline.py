#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Qoyllur Rit'i Explorer — v2.2 Offline
Dark mode · Mobile-first · GraphRAG v4.0 · Raspberry Pi 5

Cambios respecto a app.py original:
  - Sin Groq API key
  - Usa graphrag_v4_offline.py (Ollama local)
  - Banner de estado de Ollama en sidebar
  - Fichas patrimoniales generadas localmente con plantilla
"""

import os
import re
import io
from datetime import datetime
import streamlit as st

st.set_page_config(
    page_title="Qoyllur Rit'i Explorer",
    page_icon="🏔️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

.stApp { background: #0d1117 !important; font-family: 'Inter', sans-serif !important; }

.block-container {
    max-width: 700px !important;
    margin: 0 auto !important;
    padding: 0 1.25rem 4rem 1.25rem !important;
    background: transparent !important;
}

#MainMenu, footer, header { visibility: hidden !important; }
.stDeployButton { display: none !important; }

p, span, label, div, li { color: #e6edf3; }
h1,h2,h3,h4,h5,h6 { color: #e6edf3 !important; }
code { background: #21262d !important; color: #79c0ff !important; border-radius: 4px; padding: 0 4px; }

.app-header {
    background: #161b22;
    border-bottom: 1px solid #30363d;
    padding: 0.8rem 1.25rem;
    margin: 0 -1.25rem 1.75rem -1.25rem;
    display: flex;
    align-items: center;
}
.app-header-title { font-size: 1.05rem; font-weight: 700; color: #e6edf3; margin: 0; }
.app-header-sub   { font-size: 0.72rem; color: #8b949e; margin-left: auto; }

/* TABS */
.stTabs [data-baseweb="tab-list"] {
    background: #161b22 !important;
    border-radius: 8px !important;
    padding: 3px !important;
    border: 1px solid #30363d !important;
    gap: 2px !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: #8b949e !important;
    border-radius: 6px !important;
    border: none !important;
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    padding: 0.45rem 1.1rem !important;
}
.stTabs [data-baseweb="tab"][aria-selected="true"] {
    background: #21262d !important;
    color: #e6edf3 !important;
}
.stTabs [data-baseweb="tab-highlight"],
.stTabs [data-baseweb="tab-border"] { display: none !important; }

/* INPUTS */
.stTextInput > div > div > input {
    background: #21262d !important;
    border: 1px solid #30363d !important;
    border-radius: 8px !important;
    color: #e6edf3 !important;
    font-size: 0.9rem !important;
}
.stTextInput > div > div > input:focus {
    border-color: #d4a017 !important;
    box-shadow: 0 0 0 2px rgba(212,160,23,.2) !important;
}
.stTextInput > div > div > input::placeholder { color: #8b949e !important; }
.stTextInput label { color: #8b949e !important; font-size: 0.8rem !important; }

/* TEXTAREA */
.stTextArea > div > div > textarea {
    background: #21262d !important;
    border: 1px solid #30363d !important;
    border-radius: 8px !important;
    color: #e6edf3 !important;
    font-size: 0.88rem !important;
    line-height: 1.7 !important;
}

/* SELECTBOX */
.stSelectbox > div > div {
    background: #21262d !important;
    border: 1px solid #30363d !important;
    border-radius: 8px !important;
    color: #e6edf3 !important;
}
.stSelectbox label { color: #8b949e !important; font-size: 0.8rem !important; }
.stSelectbox > div > div > div { color: #e6edf3 !important; }
[data-baseweb="popover"],
[data-baseweb="popover"] > div,
[data-baseweb="popover"] > div > div { background: #21262d !important; border: 1px solid #30363d !important; border-radius: 8px !important; }
[data-baseweb="menu"] { background: #21262d !important; border: 1px solid #30363d !important; border-radius: 8px !important; }
[data-baseweb="menu"] ul, [data-baseweb="menu"] li { background: #21262d !important; color: #e6edf3 !important; }
[role="listbox"], [role="listbox"] > div, [role="listbox"] li, [role="option"] { background: #21262d !important; color: #e6edf3 !important; font-size: 0.88rem !important; }
[role="option"]:hover { background: #30363d !important; }
[aria-selected="true"][role="option"] { background: #30363d !important; color: #e6edf3 !important; }
[data-baseweb="popover"] * { color: #e6edf3 !important; }
[data-baseweb="popover"] div { background: #21262d !important; }

/* RADIO */
.stRadio > div {
    background: #161b22 !important;
    border: 1px solid #30363d !important;
    border-radius: 8px !important;
    padding: 0.5rem 0.75rem !important;
    gap: 1.5rem !important;
}
.stRadio label { color: #adbac7 !important; font-size: 0.85rem !important; }

/* BOTONES */
.stButton > button {
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    border: none !important;
    transition: all .15s !important;
}
.stButton > button[kind="primary"] {
    background: #d4a017 !important;
    color: #000 !important;
    width: 100% !important;
    padding: 0.6rem !important;
    box-shadow: 0 2px 8px rgba(212,160,23,.3) !important;
}
.stButton > button[kind="primary"]:hover { background: #b8891a !important; }
.stButton > button[kind="secondary"] {
    background: #21262d !important;
    color: #8b949e !important;
    border: 1px solid #30363d !important;
    width: 100% !important;
}

/* EXPANDER */
.streamlit-expanderHeader {
    background: #161b22 !important;
    border: 1px solid #30363d !important;
    border-radius: 8px !important;
    color: #8b949e !important;
    font-size: 0.83rem !important;
}
.streamlit-expanderContent {
    background: #161b22 !important;
    border: 1px solid #30363d !important;
    border-top: none !important;
}

/* INFO/ALERT */
.stAlert > div {
    background: #161b22 !important;
    border: 1px solid #30363d !important;
    border-radius: 8px !important;
    color: #8b949e !important;
}

/* METRICS */
[data-testid="metric-container"] {
    background: #161b22 !important;
    border: 1px solid #30363d !important;
    border-radius: 10px !important;
    padding: 0.85rem 1rem !important;
}
[data-testid="stMetricValue"] { color: #d4a017 !important; font-weight: 700 !important; }
[data-testid="stMetricLabel"] { color: #8b949e !important; font-size: 0.72rem !important; }

/* DIVIDER */
hr { border-color: #30363d !important; margin: 1rem 0 !important; }

/* CHAT */
.msg-user {
    background: rgba(31,111,235,.1);
    border: 1px solid rgba(56,139,253,.25);
    border-radius: 10px 10px 4px 10px;
    padding: 0.8rem 1rem;
    margin: 0.6rem 0;
}
.msg-user .lbl { font-size:0.68rem; font-weight:700; color:#58a6ff; text-transform:uppercase; letter-spacing:.5px; margin-bottom:5px; }
.msg-user .txt { font-size:0.88rem; color:#e6edf3; }

.msg-bot {
    background: #161b22;
    border: 1px solid #30363d;
    border-left: 3px solid #d4a017;
    border-radius: 4px 10px 10px 10px;
    padding: 0.8rem 1rem;
    margin: 0.6rem 0;
}
.msg-bot .lbl { font-size:0.68rem; font-weight:700; color:#d4a017; text-transform:uppercase; letter-spacing:.5px; margin-bottom:5px; }
.msg-bot .txt { font-size:0.88rem; color:#adbac7; line-height:1.7; }

/* STATUS BADGE */
.status-online  { color: #3fb950; font-size: 0.75rem; font-weight: 600; }
.status-offline { color: #f85149; font-size: 0.75rem; font-weight: 600; }
.status-warn    { color: #d29922; font-size: 0.75rem; font-weight: 600; }

/* ABOUT */
.about-sec {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 10px;
    padding: 1rem 1.1rem;
    margin-bottom: 0.85rem;
}
.about-sec h4 { font-size:0.72rem; font-weight:700; text-transform:uppercase; letter-spacing:.5px; color:#d4a017; margin:0 0 0.6rem 0; }
.about-sec p  { font-size:0.84rem; line-height:1.72; color:#adbac7; margin:0; }
.about-sec p+p { margin-top:0.5rem; }

.chips { display:flex; flex-wrap:wrap; gap:0.3rem; margin-top:0.6rem; }
.chip  { font-size:0.67rem; padding:0.18rem 0.5rem; border-radius:4px; font-family:monospace; border:1px solid #30363d; background:rgba(255,255,255,.04); color:#adbac7; }
.chip.b{ background:rgba(56,139,253,.1); border-color:rgba(56,139,253,.3); color:#79c0ff; }
.chip.g{ background:rgba(212,160,23,.1);  border-color:rgba(212,160,23,.3);  color:#d4a017; }

/* FICHA */
.ficha-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-bottom: 1rem;
}
.ficha-tag {
    font-size: 0.68rem;
    padding: 0.2rem 0.6rem;
    border-radius: 20px;
    border: 1px solid #30363d;
    background: rgba(212,160,23,.08);
    color: #d4a017;
    font-weight: 600;
}

/* FOOTER */
.tfooter { text-align:center; padding:1.5rem 0 0.5rem; border-top:1px solid #30363d; margin-top:2rem; }
.tfooter p { font-size:0.72rem; color:#8b949e; margin:0.2rem 0; }
.empty-state { text-align:center; padding:2.5rem 1rem; color:#8b949e; font-size:0.85rem; }
</style>
""", unsafe_allow_html=True)


# ── PDF GENERATOR (sin cambios) ───────────────────────────────────────────────
def generar_ficha_pdf(texto: str, entidad: str, tipo: str) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
        Table, TableStyle, Image, KeepTogether
    )

    PAGE_W, PAGE_H = A4
    GOLD  = colors.HexColor("#d4a017")
    DARK  = colors.HexColor("#0d1117")
    MUTED = colors.HexColor("#8b949e")
    LIGHT = colors.HexColor("#e6edf3")

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=2.2*cm, rightMargin=2.2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
        title=f"Ficha Patrimonial — {entidad}",
    )

    def sty(name, **kw): return ParagraphStyle(name, **kw)

    s_title      = sty("title",      fontSize=20, leading=24, textColor=GOLD,  fontName="Helvetica-Bold", spaceAfter=4)
    s_subtitle   = sty("subtitle",   fontSize=10, leading=13, textColor=MUTED, fontName="Helvetica",      spaceAfter=2)
    s_meta       = sty("meta",       fontSize=8,  leading=11, textColor=MUTED, fontName="Helvetica")
    s_sec_header = sty("sec_header", fontSize=8,  leading=10, textColor=GOLD,  fontName="Helvetica-Bold", spaceBefore=14, spaceAfter=4)
    s_body       = sty("body",       fontSize=9.5,leading=15, textColor=LIGHT, fontName="Helvetica",      spaceAfter=4, alignment=TA_JUSTIFY)

    def dark_background(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(DARK)
        canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
        canvas.setFillColor(GOLD)
        canvas.rect(0, 0, 0.35*cm, PAGE_H, fill=1, stroke=0)
        canvas.setStrokeColor(colors.HexColor("#30363d"))
        canvas.setLineWidth(0.5)
        canvas.line(2.2*cm, 1.6*cm, PAGE_W - 2.2*cm, 1.6*cm)
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(MUTED)
        canvas.drawString(2.2*cm, 1.1*cm, "Qoyllur Rit'i Explorer · GraphRAG v4.0 Offline · Nación Paucartambo · 2025")
        canvas.drawRightString(PAGE_W - 2.2*cm, 1.1*cm, f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        canvas.restoreState()

    story = []
    story.append(Paragraph(tipo.upper(), s_subtitle))
    story.append(Paragraph(entidad, s_title))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#30363d"), spaceAfter=6, spaceBefore=4))
    story.append(Paragraph("Festividad del Señor de Qoyllur Rit'i &nbsp;·&nbsp; Nación Paucartambo &nbsp;·&nbsp; Cusco, Perú", s_meta))
    story.append(Spacer(1, 0.5*cm))

    def strip_md(t):
        t = re.sub(r'\*\*([^*]+)\*\*', r'\1', t)
        t = re.sub(r'\*([^*]+)\*',     r'\1', t)
        t = re.sub(r'^#+\s*', '', t, flags=re.MULTILINE)
        return t

    texto = strip_md(texto)
    sections = re.split(r'\n(?=\d+\.\s+[A-ZÁÉÍÓÚÑÜ])', texto.strip())

    for sec in sections:
        sec = sec.strip()
        if not sec:
            continue
        lines = sec.split('\n', 1)
        header_line = lines[0].strip()
        body_text   = lines[1].strip() if len(lines) > 1 else ""
        header_clean = re.sub(r'^\d+\.\s*', '', header_line)

        block = []
        block.append(Paragraph(header_clean, s_sec_header))
        block.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#30363d"), spaceAfter=5, spaceBefore=0))
        if body_text:
            for line in body_text.split('\n'):
                line = line.strip()
                if not line:
                    continue
                line = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                if line.startswith('-'):
                    line = f"&nbsp;&nbsp;• {line[1:].strip()}"
                block.append(Paragraph(line, s_body))
        story.append(KeepTogether(block))

    story.append(Spacer(1, 1*cm))
    doc.build(story, onFirstPage=dark_background, onLaterPages=dark_background)
    return buf.getvalue()


# ── TTL PARSER (sin cambios) ──────────────────────────────────────────────────
@st.cache_resource
def cargar_entidades_ttl(ttl_path: str = "qoyllurity.ttl") -> dict:
    try:
        with open(ttl_path, 'r', encoding='utf-8') as f:
            ttl = f.read()
    except FileNotFoundError:
        return {}

    blocks = re.split(r'\n###[^\n]*\n', ttl)

    TYPE_PRIORITY = ['Nacion', 'LugarSagrado', 'Apu', 'Lugar', 'EventoRitual', 'Danza', 'Vestimenta', 'ObjetoRitual', 'Ukumari']
    TYPE_LABELS   = {
        'Nacion':       '🏳️ Nación',
        'LugarSagrado': '🏔️ Lugar Sagrado',
        'Apu':          '⛰️ Apu',
        'Lugar':        '📍 Lugar',
        'EventoRitual': '🎭 Evento Ritual',
        'Danza':        '💃 Danza',
        'Vestimenta':   '👘 Vestimenta',
        'ObjetoRitual': '🔮 Objeto Ritual',
        'Ukumari':      '🐻 Ukumari',
    }

    grouped = {t: [] for t in TYPE_PRIORITY}
    full = {}

    for block in blocks:
        if 'owl:NamedIndividual' not in block:
            continue
        sid = re.search(r'^:([\w_]+)\s+rdf:type', block, re.MULTILINE)
        if not sid:
            continue
        eid = sid.group(1)
        label_m = re.search(r'rdfs:label\s+"([^"@]+)"', block)
        if not label_m:
            continue
        label = label_m.group(1)
        if label[0].islower():
            continue

        tipos = re.findall(r':([A-Z][A-Za-z]+)\s*[,;]', block)
        comment_m = re.search(r'rdfs:comment\s+"([^"@]+)"', block)

        rels = []
        for pred, obj in re.findall(r':([\w]+)\s+:([\w_]+)', block):
            if pred not in ('type',) and obj != eid:
                rels.append((pred, obj))

        data_props = {}
        for pred, val in re.findall(r':([\w]+)\s+"([^"@]+)"', block):
            if pred not in ('label', 'comment'):
                data_props[pred] = val

        full[eid] = {
            'label': label, 'tipos': tipos,
            'comment': comment_m.group(1) if comment_m else '',
            'rels': rels, 'data_props': data_props,
        }

        for tipo in TYPE_PRIORITY:
            if tipo in tipos:
                grouped[tipo].append((eid, label))
                break

    for t in grouped:
        grouped[t].sort(key=lambda x: x[1])

    return {'grouped': grouped, 'labels': TYPE_LABELS, 'full': full}


def construir_contexto_ficha(eid: str, datos: dict) -> str:
    full = datos.get('full', {})
    ent  = full.get(eid)
    if not ent:
        return ""

    lines = [f"ENTIDAD: {ent['label']}", f"TIPO(S): {', '.join(ent['tipos'])}"]
    if ent['comment']:
        lines.append(f"DESCRIPCIÓN: {ent['comment']}")
    if ent['data_props']:
        lines.append("\nPROPIEDADES:")
        for k, v in ent['data_props'].items():
            lines.append(f"  - {k}: {v}")
    if ent['rels']:
        lines.append("\nRELACIONES:")
        for pred, obj in ent['rels']:
            obj_label = full.get(obj, {}).get('label', obj.replace('_', ' '))
            lines.append(f"  - {pred}: {obj_label}")
    inv = []
    for other_id, other in full.items():
        if other_id == eid:
            continue
        for pred, obj in other.get('rels', []):
            if obj == eid:
                inv.append(f"  - {other['label']} → {pred} → {ent['label']}")
    if inv:
        lines.append("\nRELACIONES INVERSAS:")
        lines.extend(inv[:10])

    return '\n'.join(lines)


def generar_ficha_local(contexto: str, entidad_label: str, tipo_label: str) -> str:
    """
    Genera una ficha patrimonial usando el LLM local (Ollama).
    Si no hay Ollama, devuelve el contexto estructurado directamente.
    """
    from graphrag_v4_offline import _llamar_ollama, verificar_ollama, seleccionar_mejor_modelo, ConfigOffline

    prompt_sistema = """Eres un experto en patrimonio cultural inmaterial peruano.
Redacta una ficha patrimonial concisa y precisa con estas secciones:
1. DENOMINACIÓN
2. ÁMBITO
3. DESCRIPCIÓN (2-3 oraciones)
4. COMUNIDAD PORTADORA
5. LOCALIZACIÓN GEOGRÁFICA
6. ELEMENTOS ASOCIADOS
7. SIGNIFICADO RITUAL

Usa SOLO la información provista. Español formal, tercera persona. Sin inventar datos."""

    prompt_usuario = f"""Datos del grafo:
{contexto}

Redacta la ficha patrimonial para: {entidad_label} ({tipo_label})"""

    ollama_ok = verificar_ollama()
    if ollama_ok:
        modelo = seleccionar_mejor_modelo()
        if modelo:
            try:
                return _llamar_ollama(
                    modelo=modelo,
                    system_prompt=prompt_sistema,
                    user_prompt=prompt_usuario,
                    max_tokens=500,
                    temperature=0.2,
                    timeout=90,
                )
            except Exception:
                pass

    # Fallback: ficha estructurada sin LLM
    lineas = [
        f"1. DENOMINACIÓN\n{entidad_label}",
        f"2. ÁMBITO\n{tipo_label} — Patrimonio Cultural Inmaterial",
        f"3. DESCRIPCIÓN\n(Generado sin LLM — instala Ollama para descripciones enriquecidas)\n{contexto[:400]}",
        "4. COMUNIDAD PORTADORA\nNación Paucartambo — Festividad del Señor de Qoyllur Rit'i",
        "5. LOCALIZACIÓN GEOGRÁFICA\nCusco, Perú — Nevado Ausangate",
        "6. ELEMENTOS ASOCIADOS\nVer relaciones en el grafo",
        "7. SIGNIFICADO RITUAL\nConsultar ontología completa",
    ]
    return "\n\n".join(lineas)


# ── ESTADO ────────────────────────────────────────────────────────────────────
if 'mensajes'       not in st.session_state: st.session_state.mensajes       = []
if 'ficha_generada' not in st.session_state: st.session_state.ficha_generada = None
if 'ficha_entidad'  not in st.session_state: st.session_state.ficha_entidad  = None

def agregar_mensaje(tipo, texto): st.session_state.mensajes.append({'tipo': tipo, 'texto': texto})
def limpiar_chat():               st.session_state.mensajes = []

# ── PREGUNTAS ─────────────────────────────────────────────────────────────────
PREGUNTAS = [
    "¿Qué es Qoyllur Rit'i?",
    "¿Dónde está el santuario?",
    "Háblame de la vestimenta de los ukukus",
    "¿Qué es el Ausangate?",
    "¿Dónde está Sinakara?",
    "¿Dónde está el glaciar Colque Punku?",
    "¿Qué hacen los ukukus?",
    "¿Qué es la lomada?",
    "¿Cuánto dura la lomada?",
    "¿Qué naciones participan?",
    "¿Cuál es el recorrido de la peregrinación?",
]


# ── MOTOR (cacheado — se carga una sola vez) ──────────────────────────────────
@st.cache_resource
def cargar_motor():
    from graphrag_v4_offline import GraphRAG_v4_Offline
    return GraphRAG_v4_Offline(ttl_path="qoyllurity.ttl", verbose=False)


# ── HEADER ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="app-header">
    <div class="app-header-title">🏔 Qoyllur Rit'i</div>
    <div class="app-header-sub">GraphRAG Explorer · Offline</div>
</div>
""", unsafe_allow_html=True)


# ── INICIALIZAR MOTOR ─────────────────────────────────────────────────────────
with st.spinner("Inicializando sistema..."):
    try:
        motor = cargar_motor()
    except Exception as e:
        st.error(f"Error al inicializar: {e}")
        st.stop()

# ── BANNER DE ESTADO DE OLLAMA ────────────────────────────────────────────────
estado = motor.estado_ollama()
if estado["ollama_disponible"]:
    st.markdown(
        f'<p class="status-online">● Ollama conectado · Modelo: {estado["modelo"]}</p>',
        unsafe_allow_html=True
    )
else:
    modelos = estado.get("modelos_instalados", [])
    if modelos:
        st.markdown('<p class="status-warn">⚠ Ollama activo pero sin modelo compatible. '
                    f'Modelos disponibles: {", ".join(modelos[:3])}</p>', unsafe_allow_html=True)
    else:
        st.markdown(
            '<p class="status-offline">● Ollama no detectado — modo plantilla activo '
            '(instala Ollama para respuestas en lenguaje natural)</p>',
            unsafe_allow_html=True
        )

# ── TABS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<p style="font-size:.82rem;color:#8b949e;line-height:1.65;margin-bottom:.75rem;margin-top:.75rem">
Explora el conocimiento documentado sobre el Señor de Qoyllur Rit'i: consulta en lenguaje
natural sobre la festividad, genera fichas patrimoniales en PDF por entidad, o revisa
los detalles del proyecto y la ontología.
</p>
""", unsafe_allow_html=True)

tab_chat, tab_fichas, tab_about = st.tabs(["💬  Consultas", "📋  Fichas", "ℹ️  Acerca de"])


# ── TAB CONSULTAS ─────────────────────────────────────────────────────────────
with tab_chat:
    modo = st.radio(
        "modo", ["📋 Preguntas sugeridas", "✍️ Pregunta libre"],
        horizontal=True, label_visibility="collapsed"
    )

    pregunta = ""
    if modo == "📋 Preguntas sugeridas":
        pregunta = st.selectbox(
            "pregunta", options=[""] + PREGUNTAS,
            format_func=lambda x: "Selecciona una pregunta..." if x == "" else x,
            label_visibility="collapsed"
        )
    else:
        pregunta = st.text_input(
            "pregunta", placeholder="¿Dónde está el glaciar Colque Punku?",
            label_visibility="collapsed"
        )
        with st.expander("💡 Ver ejemplos"):
            for p in PREGUNTAS[:6]:
                st.markdown(f"- {p}")

    if st.button("✨  Preguntar", type="primary", use_container_width=True):
        if pregunta:
            agregar_mensaje('user', pregunta)
            with st.spinner("Consultando grafo de conocimiento..."):
                try:
                    respuesta = motor.responder(pregunta, use_api=True, modo="hibrido", verbose=False)
                    agregar_mensaje('bot', respuesta)
                except Exception as e:
                    agregar_mensaje('bot', f"Error: {e}")
            st.rerun()

    if st.session_state.mensajes:
        st.markdown("---")
        for msg in reversed(st.session_state.mensajes):
            if msg['tipo'] == 'user':
                st.markdown(f'<div class="msg-user"><div class="lbl">Tú</div><div class="txt">{msg["texto"]}</div></div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="msg-bot"><div class="lbl">Asistente</div><div class="txt">{msg["texto"]}</div></div>', unsafe_allow_html=True)
        st.markdown(" ")
        if st.button("🗑️  Limpiar historial", use_container_width=True):
            limpiar_chat()
            st.rerun()
    else:
        st.markdown('<div class="empty-state">Selecciona o escribe una pregunta para comenzar</div>', unsafe_allow_html=True)


# ── TAB FICHAS ────────────────────────────────────────────────────────────────
with tab_fichas:
    datos = cargar_entidades_ttl("qoyllurity.ttl")
    if not datos:
        st.error("No se pudo cargar qoyllurity.ttl")
        st.stop()

    grouped    = datos['grouped']
    type_labels = datos['labels']

    tipos_disponibles = [t for t in grouped if grouped[t]]
    tipo_opts = {type_labels[t]: t for t in tipos_disponibles}

    tipo_sel_label = st.selectbox("Tipo de entidad", options=list(tipo_opts.keys()))
    tipo_sel       = tipo_opts[tipo_sel_label]

    entidades  = grouped[tipo_sel]
    ent_opts   = {label: eid for eid, label in entidades}
    ent_sel_label = st.selectbox("Entidad", options=list(ent_opts.keys()))
    ent_sel_id    = ent_opts[ent_sel_label]

    contexto = construir_contexto_ficha(ent_sel_id, datos)
    with st.expander("🔍 Ver datos del grafo", expanded=False):
        st.code(contexto, language=None)

    if st.button("📋  Generar ficha patrimonial", type="primary", use_container_width=True):
        spinner_msg = "Generando ficha con LLM local..." if estado["ollama_disponible"] else "Generando ficha estructurada..."
        with st.spinner(spinner_msg):
            try:
                ficha_texto = generar_ficha_local(contexto, ent_sel_label, tipo_sel_label)
                st.session_state.ficha_generada = ficha_texto
                st.session_state.ficha_entidad  = ent_sel_label
            except Exception as e:
                st.error(f"Error al generar ficha: {e}")

    if st.session_state.ficha_generada and st.session_state.ficha_entidad == ent_sel_label:
        st.markdown(f"""
<div class="ficha-meta">
  <span class="ficha-tag">📋 Ficha Patrimonial</span>
  <span class="ficha-tag">{tipo_sel_label}</span>
  <span class="ficha-tag">Qoyllur Rit'i · 2025</span>
  <span class="ficha-tag">{'🤖 LLM Local' if estado['ollama_disponible'] else '📄 Plantilla'}</span>
</div>""", unsafe_allow_html=True)

        import html as _html
        def _render_ficha_html(texto):
            import re as _re
            texto = _re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', texto)
            texto = _re.sub(r'\*([^*]+)\*', r'\1', texto)
            texto = _re.sub(r'^#+\s*', '', texto, flags=_re.MULTILINE)
            lines = texto.strip().split('\n')
            html_parts = []
            for line in lines:
                line = line.strip()
                if not line:
                    html_parts.append('<div style="height:.5rem"></div>')
                    continue
                m = _re.match(r'^(\d+\.\s+[A-ZÁÉÍÓÚÑÜ ]+)$', line.replace('<strong>','').replace('</strong>',''))
                if m:
                    clean = _re.sub(r'</?strong>', '', line)
                    html_parts.append(f'<div style="font-size:.7rem;font-weight:700;color:#d4a017;text-transform:uppercase;letter-spacing:.6px;margin-top:1.1rem;margin-bottom:.3rem;padding-bottom:.25rem;border-bottom:1px solid #30363d">{_html.escape(clean)}</div>')
                elif line.startswith('•') or line.startswith('-'):
                    txt = _html.escape(line.lstrip('•- ').strip())
                    html_parts.append(f'<div style="font-size:.86rem;color:#adbac7;line-height:1.65;padding-left:1rem">• {txt}</div>')
                else:
                    txt = _re.sub(r'<strong>(.*?)</strong>', lambda m: '<b>'+_html.escape(m.group(1))+'</b>', line)
                    txt = _html.escape(txt).replace('&lt;b&gt;', '<b>').replace('&lt;/b&gt;', '</b>')
                    html_parts.append(f'<div style="font-size:.86rem;color:#adbac7;line-height:1.7">{txt}</div>')
            return ''.join(html_parts)

        ficha_html = _render_ficha_html(st.session_state.ficha_generada)
        st.markdown(f'''<div style="background:#161b22;border:1px solid #30363d;border-radius:10px;
padding:1.25rem 1.35rem;margin-bottom:.75rem">{ficha_html}</div>''', unsafe_allow_html=True)

        try:
            pdf_bytes = generar_ficha_pdf(st.session_state.ficha_generada, entidad=ent_sel_label, tipo=tipo_sel_label)
            st.download_button(
                label="⬇️  Descargar ficha (.pdf)",
                data=pdf_bytes,
                file_name=f"ficha_{ent_sel_id}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        except Exception:
            st.download_button(
                label="⬇️  Descargar ficha (.txt)",
                data=st.session_state.ficha_generada,
                file_name=f"ficha_{ent_sel_id}.txt",
                mime="text/plain",
                use_container_width=True,
            )


# ── TAB ACERCA DE ─────────────────────────────────────────────────────────────
with tab_about:
    ollama_status = "✅ Conectado" if estado["ollama_disponible"] else "❌ No detectado"
    modelo_info   = estado.get("modelo") or "N/A"

    st.markdown(f"""
<div class="about-sec">
<h4>🏔 La festividad</h4>
<p>El Señor de Qoyllur Rit'i es una peregrinación andina que sincretiza el catolicismo
colonial con tradiciones ancestrales en torno al Apu Ausangate (6,384 msnm). Declarada
Patrimonio Cultural Inmaterial de la Humanidad por la UNESCO.</p>
</div>
<div class="about-sec">
<h4>⚙️ Estado del sistema</h4>
<p><strong>Ollama:</strong> {ollama_status} &nbsp;|&nbsp; <strong>Modelo:</strong> {modelo_info}</p>
<p>Esta versión offline no requiere conexión a internet ni API keys. El grafo de
conocimiento y los embeddings corren localmente en la Raspberry Pi.</p>
</div>
<div class="about-sec">
<h4>⚙️ Stack técnico (offline)</h4>
<div class="chips">
  <span class="chip g">GraphRAG v4.0 Offline</span>
  <span class="chip g">Knowledge Graph</span>
  <span class="chip b">OWL 2</span>
  <span class="chip b">Turtle (.ttl)</span>
  <span class="chip b">RDF / RDFS</span>
  <span class="chip">Ollama</span>
  <span class="chip">llama3.2 / gemma2</span>
  <span class="chip">sentence-transformers</span>
  <span class="chip">rdflib</span>
  <span class="chip">Streamlit</span>
</div>
</div>
<div class="about-sec">
<h4>📐 Instalar un modelo en Ollama</h4>
<p>Desde la terminal de la Raspberry Pi:</p>
</div>
""", unsafe_allow_html=True)

    st.code("""# Instalar Ollama (si no está instalado)
curl -fsSL https://ollama.ai/install.sh | sh

# Descargar modelo recomendado (balance calidad/velocidad)
ollama pull llama3.2:3b

# Alternativas más rápidas
ollama pull gemma2:2b       # ~4-7s por respuesta
ollama pull qwen2.5:1.5b    # ~3-5s por respuesta (más ligero)

# Verificar que está corriendo
ollama list""", language="bash")

    try:
        from rdflib import Graph as RDFGraph
        _g = RDFGraph()
        _g.parse("qoyllurity.ttl", format='turtle')
        c1, c2, c3 = st.columns(3)
        with c1: st.metric("Tripletas RDF", len(_g))
        with c2: st.metric("Entidades",     len(set(s for s, _, _ in _g)))
        with c3: st.metric("Propiedades",   len(set(p for _, p, _ in _g)))
    except Exception:
        pass


# ── FOOTER ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="tfooter">
    <p>🏔️ <b>Qoyllur Rit'i Explorer</b> · GraphRAG v4.0 Offline</p>
    <p>Knowledge Graph + RAG · Ollama Local · Raspberry Pi 5</p>
    <p style="color:#30363d;font-size:0.65rem;margin-top:0.3rem;">
        OWL 2 / Turtle · paraphrase-multilingual-MiniLM-L12-v2 · Sin dependencias de red
    </p>
</div>
""", unsafe_allow_html=True)
