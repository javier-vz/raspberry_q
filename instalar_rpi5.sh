#!/usr/bin/env bash
# =============================================================================
# instalar_rpi5.sh — Setup completo de Qoyllur Rit'i Explorer (Offline)
# Raspberry Pi 5 · 8GB RAM · Ubuntu/Raspberry Pi OS 64-bit
#
# Uso:
#   chmod +x instalar_rpi5.sh
#   ./instalar_rpi5.sh
#
# Qué hace:
#   1. Instala dependencias del sistema
#   2. Crea entorno virtual Python
#   3. Instala paquetes Python (sin groq)
#   4. Instala Ollama y descarga modelo recomendado
#   5. Genera script de inicio
#   6. (Opcional) Configura servicio systemd para autoarranque
# =============================================================================

set -e  # Salir si algún comando falla

# ── Colores ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; NC='\033[0m'

log()  { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[⚠]${NC} $1"; }
info() { echo -e "${BLUE}[→]${NC} $1"; }
err()  { echo -e "${RED}[✗]${NC} $1"; exit 1; }
sep()  { echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"; }

# ── Banner ───────────────────────────────────────────────────────────────────
clear
echo ""
echo -e "${CYAN}🏔️  Qoyllur Rit'i Explorer — Instalación Offline${NC}"
echo -e "${CYAN}    Raspberry Pi 5 · 8GB RAM${NC}"
sep
echo ""

# ── Directorio del proyecto ───────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"
VENV_DIR="$PROJECT_DIR/.venv"

info "Directorio del proyecto: $PROJECT_DIR"
echo ""

# ── 1. Dependencias del sistema ───────────────────────────────────────────────
sep
echo -e "  ${BLUE}PASO 1${NC} · Dependencias del sistema"
sep

info "Actualizando lista de paquetes..."
sudo apt-get update -qq

info "Instalando dependencias del sistema..."
sudo apt-get install -y \
    python3 python3-pip python3-venv python3-dev \
    libopenblas-dev liblapack-dev \
    curl wget git \
    build-essential \
    2>/dev/null || warn "Algunos paquetes pueden ya estar instalados"

log "Dependencias del sistema listas"
echo ""

# ── 2. Entorno virtual Python ─────────────────────────────────────────────────
sep
echo -e "  ${BLUE}PASO 2${NC} · Entorno virtual Python"
sep

if [ -d "$VENV_DIR" ]; then
    warn "Ya existe un entorno virtual en $VENV_DIR"
    read -p "  ¿Recrearlo? (s/N): " resp
    if [[ "$resp" =~ ^[sS]$ ]]; then
        rm -rf "$VENV_DIR"
        info "Eliminado entorno anterior"
    fi
fi

if [ ! -d "$VENV_DIR" ]; then
    info "Creando entorno virtual..."
    python3 -m venv "$VENV_DIR"
    log "Entorno virtual creado en $VENV_DIR"
fi

# Activar venv
source "$VENV_DIR/bin/activate"
info "Actualizando pip..."
pip install --upgrade pip --quiet
echo ""

# ── 3. Paquetes Python ────────────────────────────────────────────────────────
sep
echo -e "  ${BLUE}PASO 3${NC} · Paquetes Python (modo offline)"
sep

info "Instalando paquetes (puede tardar 5-10 min en RPi5)..."

# Instalar paquetes uno a uno para mejor diagnóstico de errores
PAQUETES=(
    "streamlit>=1.32.0"
    "rdflib>=7.0.0"
    "sentence-transformers>=2.2.0"
    "numpy>=1.24.0"
    "rank-bm25>=0.2.2"
    "python-dotenv>=1.0.0"
    "reportlab>=4.0.0"
    "scikit-learn>=1.0.0"
)

for pkg in "${PAQUETES[@]}"; do
    info "Instalando $pkg..."
    pip install "$pkg" --quiet || warn "Error instalando $pkg — continuando..."
done

# sentence-transformers necesita torch — versión CPU para ARM
info "Instalando PyTorch (versión CPU para ARM)..."
pip install torch torchvision torchaudio \
    --index-url https://download.pytorch.org/whl/cpu \
    --quiet 2>/dev/null || \
pip install torch --quiet 2>/dev/null || \
    warn "PyTorch no se pudo instalar automáticamente. Instálalo manualmente."

log "Paquetes Python instalados"
echo ""

# ── 4. Predescargar modelo de embeddings ─────────────────────────────────────
sep
echo -e "  ${BLUE}PASO 4${NC} · Modelo de embeddings (sentence-transformers)"
sep

info "Descargando paraphrase-multilingual-MiniLM-L12-v2 (~80MB)..."
info "Este modelo se usará para búsqueda semántica (sin GPU, solo CPU)"

python3 -c "
from sentence_transformers import SentenceTransformer
print('  Descargando modelo...')
m = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
print('  Modelo listo. Dimensiones:', m.get_sentence_embedding_dimension())
" 2>/dev/null && log "Modelo de embeddings descargado" || warn "El modelo se descargará al primer uso"
echo ""

# ── 5. Instalar Ollama ────────────────────────────────────────────────────────
sep
echo -e "  ${BLUE}PASO 5${NC} · Ollama (LLM local)"
sep

if command -v ollama &>/dev/null; then
    log "Ollama ya está instalado: $(ollama --version 2>/dev/null || echo 'versión desconocida')"
else
    info "Instalando Ollama..."
    curl -fsSL https://ollama.ai/install.sh | sh || err "No se pudo instalar Ollama"
    log "Ollama instalado"
fi

# Iniciar servicio Ollama si no está corriendo
if ! pgrep -x "ollama" > /dev/null; then
    info "Iniciando Ollama en background..."
    ollama serve &>/dev/null &
    OLLAMA_PID=$!
    sleep 3
    info "Ollama PID: $OLLAMA_PID"
fi

# ── Elegir y descargar modelo ─────────────────────────────────────────────────
echo ""
echo -e "  ${YELLOW}Elige el modelo a descargar:${NC}"
echo ""
echo -e "  ${CYAN}1)${NC} llama3.2:3b   (~2GB) · ${GREEN}Recomendado${NC} · 5-10s/respuesta · Mejor calidad"
echo -e "  ${CYAN}2)${NC} gemma2:2b     (~1.6GB) · 4-7s/respuesta · Buena comprensión español"
echo -e "  ${CYAN}3)${NC} qwen2.5:1.5b  (~1GB)  · 3-5s/respuesta · Más rápido, menos calidad"
echo -e "  ${CYAN}4)${NC} Omitir (instalaré el modelo después manualmente)"
echo ""
read -p "  Opción [1-4]: " MODEL_CHOICE

case "$MODEL_CHOICE" in
    1) OLLAMA_MODEL="llama3.2:3b" ;;
    2) OLLAMA_MODEL="gemma2:2b" ;;
    3) OLLAMA_MODEL="qwen2.5:1.5b" ;;
    4) OLLAMA_MODEL="" ; warn "Recuerda instalar un modelo: ollama pull llama3.2:3b" ;;
    *) OLLAMA_MODEL="llama3.2:3b" ; warn "Opción inválida, usando llama3.2:3b" ;;
esac

if [ -n "$OLLAMA_MODEL" ]; then
    info "Descargando $OLLAMA_MODEL (puede tardar 5-15 min según tu internet)..."
    ollama pull "$OLLAMA_MODEL" && log "Modelo $OLLAMA_MODEL descargado" || \
        warn "No se pudo descargar el modelo. Intenta: ollama pull $OLLAMA_MODEL"
fi
echo ""

# ── 6. Verificar archivos del proyecto ───────────────────────────────────────
sep
echo -e "  ${BLUE}PASO 6${NC} · Verificación de archivos"
sep

ARCHIVOS_REQUERIDOS=(
    "qoyllurity.ttl"
    "graphrag_v2.py"
    "graphrag_v4_offline.py"
    "config_graphrag.py"
    "app_offline.py"
)

TODOS_OK=true
for archivo in "${ARCHIVOS_REQUERIDOS[@]}"; do
    if [ -f "$PROJECT_DIR/$archivo" ]; then
        log "$archivo ✓"
    else
        warn "$archivo — NO ENCONTRADO"
        TODOS_OK=false
    fi
done

if [ "$TODOS_OK" = false ]; then
    warn "Algunos archivos faltan. Asegúrate de copiarlos al directorio del proyecto."
fi
echo ""

# ── 7. Script de inicio ───────────────────────────────────────────────────────
sep
echo -e "  ${BLUE}PASO 7${NC} · Script de inicio"
sep

cat > "$PROJECT_DIR/iniciar.sh" << EOF
#!/usr/bin/env bash
# Script de inicio — Qoyllur Rit'i Explorer Offline
# Generado por instalar_rpi5.sh

SCRIPT_DIR="\$(cd "\$(dirname "\${BASH_SOURCE[0]}")" && pwd)"
cd "\$SCRIPT_DIR"

# Activar entorno virtual
source "\$SCRIPT_DIR/.venv/bin/activate"

# Iniciar Ollama si no está corriendo
if ! pgrep -x "ollama" > /dev/null; then
    echo "Iniciando Ollama..."
    ollama serve &>/dev/null &
    sleep 2
fi

# Iniciar Streamlit
echo "Iniciando Qoyllur Rit'i Explorer..."
echo "Abre tu navegador en: http://localhost:8501"
echo "(En red local: http://\$(hostname -I | awk '{print \$1}'):8501)"
echo ""
streamlit run app_offline.py \
    --server.port 8501 \
    --server.address 0.0.0.0 \
    --server.headless true \
    --browser.gatherUsageStats false
EOF

chmod +x "$PROJECT_DIR/iniciar.sh"
log "Script de inicio creado: iniciar.sh"
echo ""

# ── 8. Servicio systemd (opcional) ───────────────────────────────────────────
sep
echo -e "  ${BLUE}PASO 8${NC} · Servicio systemd (autoarranque)"
sep

read -p "  ¿Instalar como servicio systemd (autoarranque al iniciar)? (s/N): " INSTALL_SERVICE

if [[ "$INSTALL_SERVICE" =~ ^[sS]$ ]]; then
    CURRENT_USER=$(whoami)
    SERVICE_FILE="/etc/systemd/system/qoyllurity.service"

    sudo tee "$SERVICE_FILE" > /dev/null << EOF
[Unit]
Description=Qoyllur Rit'i Explorer Offline
After=network.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$PROJECT_DIR
ExecStartPre=/bin/bash -c 'ollama serve &>/dev/null & sleep 2'
ExecStart=$PROJECT_DIR/.venv/bin/streamlit run $PROJECT_DIR/app_offline.py --server.port 8501 --server.address 0.0.0.0 --server.headless true --browser.gatherUsageStats false
Restart=on-failure
RestartSec=5
Environment=HOME=/home/$CURRENT_USER

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable qoyllurity.service
    sudo systemctl start qoyllurity.service
    log "Servicio systemd instalado y activo"
    info "Comandos: sudo systemctl {start|stop|status|restart} qoyllurity"
else
    info "Servicio systemd omitido. Usa ./iniciar.sh para arrancar manualmente."
fi
echo ""

# ── Resumen final ─────────────────────────────────────────────────────────────
sep
echo ""
echo -e "${GREEN}🎉 Instalación completada${NC}"
echo ""
echo -e "  Para iniciar la aplicación:"
echo -e "  ${CYAN}  cd $PROJECT_DIR && ./iniciar.sh${NC}"
echo ""
echo -e "  Acceso local:    ${CYAN}http://localhost:8501${NC}"
IP=$(hostname -I 2>/dev/null | awk '{print $1}')
if [ -n "$IP" ]; then
echo -e "  Acceso en red:   ${CYAN}http://$IP:8501${NC}"
fi
echo ""
echo -e "  Comandos Ollama útiles:"
echo -e "  ${CYAN}  ollama list${NC}          — ver modelos instalados"
echo -e "  ${CYAN}  ollama pull MODEL${NC}    — descargar otro modelo"
echo -e "  ${CYAN}  ollama rm MODEL${NC}      — eliminar modelo"
echo ""
sep
echo ""
