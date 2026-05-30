import streamlit as st
import pandas as pd
import os
import re
import random
import base64
import requests
from datetime import datetime
from difflib import SequenceMatcher

# Configuración de la página
st.set_page_config(page_title="Entrenador de Idiomas por Islas", page_icon="🇩🇪", layout="centered")

# Inyectar tipografías y estilos premium
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght=300;400;500;600;700&display=swap');

    /* ── Variables de color ── */
    :root {
        --azul:        #3b7dd8;
        --azul-bg:     rgba(59, 125, 216, 0.10);
        --azul-borde:  rgba(59, 125, 216, 0.55);
        --verde:       #22a66e;
        --verde-bg:    rgba(34, 166, 110, 0.10);
        --verde-borde: rgba(34, 166, 110, 0.55);
        --rojo:        #e05454;
        --rojo-bg:     rgba(224, 84, 84, 0.10);
        --rojo-borde:  rgba(224, 84, 84, 0.55);
        --naranja:     #f5a623;
        --radio:       12px;
    }

    /* ── Fuente base para toda la app ── */
    html, body, [class*="css"], .stMarkdown, .stTextArea, .stExpander,
    .stButton button, .stSelectbox, .stSidebar, p, label, input, textarea {
        font-family: 'Montserrat', sans-serif !important;
    }

    /* ── Título principal ── */
    h1 {
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 700 !important;
        font-size: 1.85rem !important;
        letter-spacing: -0.5px !important;
        margin-bottom: 0.25rem !important;
    }

    /* ── Etiqueta de situación ── */
    .titulo-situacion {
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 500 !important;
        font-size: 0.75rem !important;
        text-transform: uppercase;
        letter-spacing: 2px;
        color: #8a9ab5;
        margin-bottom: 0.75rem;
        display: flex;
        align-items: center;
        gap: 6px;
    }

    /* ── Tarjetas y Tiras de Historial Pastel ── */
    .tira-historial {
        width: 100%;
        padding: 5px 12px;
        border-radius: 8px;
        font-size: 0.70rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        text-align: center;
        margin-bottom: 12px;
    }

    .texto-isla, .texto-isla *, .texto-isla p, .texto-isla b {
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 400 !important;
        line-height: 1.8 !important;
        font-size: 1.25rem !important;
    }
    .texto-isla b {
        font-weight: 600 !important;
        font-size: 0.72rem !important;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        opacity: 0.65;
    }

    .bloque-azul {
        background: var(--azul-bg);
        border: 1px solid var(--azul-borde);
        border-left: 4px solid var(--azul);
        padding: 1.4rem 1.6rem;
        border-radius: var(--radio);
        margin-bottom: 1rem;
        box-shadow: 0 2px 12px rgba(59,125,216,0.07);
    }
    .bloque-verde {
        background: var(--verde-bg);
        border: 1px solid var(--verde-borde);
        border-left: 4px solid var(--verde);
        padding: 1.4rem 1.6rem;
        border-radius: var(--radio);
        margin-bottom: 1rem;
        box-shadow: 0 2px 12px rgba(34,166,110,0.07);
    }

    /* ── Resultado dictado ── */
    .resultado-porcentaje {
        font-family: 'Montserrat', sans-serif;
        font-size: 1.5rem;
        font-weight: 400;
        text-align: center;
        padding: 14px 20px;
        border-radius: var(--radio);
        margin-top: 10px;
        margin-bottom: 10px;
    }

    /* ── Resaltado dictado palabra a palabra ── */
    .dictado-comparacion {
        font-family: 'Montserrat', sans-serif;
        font-size: 1.1rem;
        line-height: 1.9;
        padding: 1.2rem 1.4rem;
        border-radius: var(--radio);
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.08);
        margin-top: 12px;
    }
    .palabra-ok   { color: #22a66e; font-weight: 500; }
    .palabra-mal  { color: #e05454; font-weight: 500; text-decoration: underline wavy #e05454; }
    .palabra-extra { color: #f5a623; font-weight: 500; font-style: italic; }

    /* ── Barra de progreso ── */
    .stProgress > div > div {
        height: 5px !important;
        border-radius: 99px !important;
    }

    /* ── Contador de progreso de la rueda ── */
    .progreso-contador {
        font-family: 'Montserrat', sans-serif;
        font-size: 0.72rem;
        font-weight: 500;
        color: #8a9ab5;
        text-align: right;
        letter-spacing: 1px;
        margin-bottom: 4px;
    }

    /* ── Botones ── */
    .stButton button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 0.82rem !important;
        letter-spacing: 0.4px !important;
        padding: 0.45rem 0.9rem !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
    }
    section[data-testid="stSidebar"] {
        border-right: 1px solid rgba(255,255,255,0.06);
    }
    hr { opacity: 0.15; }
    </style>
""", unsafe_allow_html=True)

# URL de tu Google Apps Script (Tu motor de escritura)
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbyMpUxnYWLCceZpCIsILNWTywzT0MGnrctLFK0DKVkRBr0t1JDj3TagKVfi70zZHQzb/exec"

# URLs de descarga de CSV para ambas pestañas
URL_FRASES   = "https://docs.google.com/spreadsheets/d/1hpP0J5qRrbx5p9W2nHWsoTDBA9hhvLZYblaU12Ln3w4/export?format=csv&gid=0"
URL_PROGRESO = "https://docs.google.com/spreadsheets/d/1hpP0J5qRrbx5p9W2nHWsoTDBA9hhvLZYblaU12Ln3w4/export?format=csv&gid=1513540695"

# ── FUNCIONES DE CARGA ──
@st.cache_data(ttl=2)
def cargar_frases():
    url = f"{URL_FRASES}&nocache={random.randint(1, 100000)}"
    df = pd.read_csv(url)
    df.columns = df.columns.str.strip()
    return df

@st.cache_data(ttl=2)
def obtener_contador_diario():
    try:
        url = f"{URL_PROGRESO}&nocache={random.randint(1, 100000)}"
        df_prog = pd.read_csv(url)
        df_prog.columns = df_prog.columns.str.strip()
        
        # Fecha de hoy formateada exactamente como la guarda Google (YYYY-MM-DD)
        hoy = datetime.now().strftime("%Y-%m-%d")
        
        # Convertimos la columna Fecha a texto limpio para comparar sin fallos de tipo
        df_prog['Fecha'] = df_prog['Fecha'].astype(str).str.strip()
        
        fila_hoy = df_prog[df_prog['Fecha'] == hoy]
        if not fila_hoy.empty:
            return int(fila_hoy.iloc[0]['Cantidad'])
    except Exception:
        pass
    return 0

# Carga inicial de las frases
try:
    df_total = cargar_frases()
except Exception as e:
    st.error(f"No se pudo conectar con el Google Sheet. Detalles: {e}")
    st.stop()

# Obtener contador del día actual
frases_vistas_hoy = obtener_contador_diario()

# --- BARRA LATERAL ---
st.sidebar.title("Configuración")
islas_disponibles = df_total['Isla'].unique()
isla_seleccionada = st.sidebar.selectbox("🏝️ Selecciona la Isla:", islas_disponibles)

df_isla_completa = df_total[df_total['Isla'] == isla_seleccionada].copy()
total_frases_isla = len(df_isla_completa)

if 'isla_anterior' not in st.session_state or st.session_state.isla_anterior != isla_seleccionada:
    st.session_state.indice_actual = 0
    st.session_state.isla_anterior = isla_seleccionada
    st.session_state.ver_solucion = False

# Cálculo de la rueda de 15
df_activas_y_pendientes = df_isla_completa[df_isla_completa['Estado'] != 'Azul'].copy()
df_azul = df_isla_completa[df_isla_completa['Estado'] == 'Azul']
total_aprendidos = len(df_azul)

df_en_rueda = df_activas_y_pendientes.head(15).copy()
total_rueda_actual = len(df_en_rueda)

estados_rueda = df_en_rueda['Estado'].fillna('Rojo').astype(str).str.strip().tolist()
n_rojos   = estados_rueda.count('Rojo')
n_naranjas = estados_rueda.count('Naranja')
n_verdes  = estados_rueda.count('Verde')

# --- RESUMEN SIDEBAR ---
st.sidebar.write("---")
st.sidebar.markdown("### 📊 Estado de la Isla")

porcentaje_isla = round((total_aprendidos / total_frases_isla * 100)) if total_frases_isla > 0 else 0

st.sidebar.markdown(f"""
<div style="font-family: 'Montserrat', sans-serif; background: rgba(255,255,255,0.04); padding: 16px 18px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.09); margin-bottom: 15px;">
    <p style="margin: 0 0 12px 0; font-size: 0.7rem; color: #8a9ab5; font-weight: 500; text-transform: uppercase; letter-spacing: 2px;">🔄 En rueda &nbsp;·&nbsp; {total_rueda_actual}</p>
    <div style="display: flex; flex-direction: column; gap: 8px;">
        <div style="display:flex; align-items:center; gap:10px; font-size:0.9rem;">
            <span style="width:10px;height:10px;border-radius:50%;background:#e05454;display:inline-block;flex-shrink:0;"></span>
            <span style="color:#e8ecf2;">{n_rojos} &nbsp;<span style="color:#8a9ab5;font-size:0.8rem;">Nuevas / Malas</span></span>
        </div>
        <div style="display:flex; align-items:center; gap:10px; font-size:0.9rem;">
            <span style="width:10px;height:10px;border-radius:50%;background:#f5a623;display:inline-block;flex-shrink:0;"></span>
            <span style="color:#e8ecf2;">{n_naranjas} &nbsp;<span style="color:#8a9ab5;font-size:0.8rem;">A medias</span></span>
        </div>
        <div style="display:flex; align-items:center; gap:10px; font-size:0.9rem;">
            <span style="width:10px;height:10px;border-radius:50%;background:#22a66e;display:inline-block;flex-shrink:0;"></span>
            <span style="color:#e8ecf2;">{n_verdes} &nbsp;<span style="color:#8a9ab5;font-size:0.8rem;">Casi listas</span></span>
        </div>
    </div>
    <div style="margin: 14px 0 0 0; padding-top: 12px; border-top: 1px solid rgba(255,255,255,0.08); display:flex; align-items:center; justify-content:space-between;">
        <div style="display:flex; align-items:center; gap:8px; font-size:0.9rem;">
            <span style="width:10px;height:10px;border-radius:50%;background:#3b7dd8;display:inline-block;flex-shrink:0;"></span>
            <span style="color:#8a9ab5; font-size:0.8rem;">Aprendidas</span>
        </div>
        <span style="font-size:1rem; font-weight:600; color:#3b7dd8;">{total_aprendidos}<span style="color:#8a9ab5; font-weight:400; font-size:0.82rem;"> / {total_frases_isla}</span></span>
    </div>
    <div style="margin-top: 12px;">
        <div style="height: 5px; background: rgba(255,255,255,0.08); border-radius: 99px; overflow: hidden;">
            <div style="height: 100%; width: {porcentaje_isla}%; background: #3b7dd8; border-radius: 99px;"></div>
        </div>
        <p style="margin: 5px 0 0 0; font-size: 0.72rem; color: #8a9ab5; text-align: right;">{porcentaje_isla}% completada</p>
    </div>
</div>
""", unsafe_allow_html=True)

# ── NUEVA SECCIÓN VISUAL: RENDIMIENTO DIARIO EN LA APP ──
st.sidebar.markdown(f"""
<div style="font-family: 'Montserrat', sans-serif; background: rgba(34, 166, 110, 0.08); padding: 14px 16px; border-radius: 12px; border: 1px solid rgba(34, 166, 110, 0.3); text-align: center;">
    <span style="font-size: 1.4rem; display: block; margin-bottom: 2px;">🎯</span>
    <span style="font-size: 0.72rem; color: #8a9ab5; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; display: block;">Frases Calificadas Hoy</span>
    <span style="font-size: 2rem; font-weight: 700; color: #22a66e; line-height: 1.2; display: block; margin-top: 2px;">{frases_vistas_hoy}</span>
</div>
""", unsafe_allow_html=True)


# Validación isla completa
if total_aprendidos == total_frases_isla and total_frases_isla > 0:
    st.title("🇩🇪 Método de Chunks & Islas")
    st.balloons()
    st.success(f"🎉 ¡ESPECTACULAR! Has completado la isla '{isla_seleccionada}' al 100%.")
    st.stop()

if st.session_state.indice_actual >= total_rueda_actual:
    st.session_state.indice_actual = total_rueda_actual - 1 if total_rueda_actual > 0 else 0

# --- CONTENIDO PRINCIPAL ---
st.title("🇩🇪 Método de Chunks & Islas")

fila_actual = df_en_rueda.iloc[st.session_state.indice_actual]
castellano_texto = str(fila_actual['Castellano'])
aleman_texto     = str(fila_actual['Aleman'])
estado_actual    = str(fila_actual['Estado']).strip()

indice_fila_google_sheet = int(df_isla_completa.index[df_isla_completa['Castellano'] == castellano_texto].tolist()[0]) + 2

audio_id_raw = fila_actual['Audio_ID']
audio_id = str(int(audio_id_raw)) if isinstance(audio_id_raw, float) else str(audio_id_raw).strip()

situacion_texto = str(fila_actual['Situacion']).strip() if 'Situacion' in fila_actual and pd.notna(fila_actual['Situacion']) else ""

pos_actual = st.session_state.indice_actual + 1
st.markdown(f'<div class="progreso-contador">{pos_actual} / {total_rueda_actual}</div>', unsafe_allow_html=True)
st.progress(pos_actual / total_rueda_actual)

if situacion_texto:
    st.markdown(f'<div class="titulo-situacion">📍 {situacion_texto}</div>', unsafe_allow_html=True)

# Controles de navegación
col_nav_sol, col_nav_ant, col_nav_sig = st.columns([0.34, 0.33, 0.33])
with col_nav_sol:
    if not st.session_state.ver_solucion:
        if st.button("👁️ Solución", use_container_width=True, key="btn_ver_aleman"):
            st.session_state.ver_solucion = True
            st.rerun()
    else:
        if st.button("🔄 Ocultar", use_container_width=True, key="btn_ver_castellano"):
            st.session_state.ver_solucion = False
            st.rerun()
with col_nav_ant:
    if st.button("⬅️ Anterior", use_container_width=True):
        if st.session_state.indice_actual > 0:
            st.session_state.indice_actual -= 1
            st.session_state.ver_solucion = False
            st.rerun()
with col_nav_sig:
    if st.button("Siguiente ➡️", use_container_width=True):
        if st.session_state.indice_actual < total_rueda_actual - 1:
            st.session_state.indice_actual += 1
            st.session_state.ver_solucion = False
            st.rerun()

# Historial superior
bg_tira, color_texto_tira = "rgba(59, 125, 216, 0.15)", "#3b7dd8"
if estado_actual == "Rojo":
    bg_tira, color_texto_tira = "rgba(224, 84, 84, 0.15)", "#e05454"
elif estado_actual == "Naranja":
    bg_tira, color_texto_tira = "rgba(245, 158, 11, 0.15)", "#f59e0b"
elif estado_actual == "Verde":
    bg_tira, color_texto_tira = "rgba(34, 166, 110, 0.15)", "#22a66e"

st.markdown(f'<div class="tira-historial" style="background-color: {bg_tira}; color: {color_texto_tira}; border: 1px solid {color_texto_tira}44;">ESTADO ACTUAL</div>', unsafe_allow_html=True)

if not st.session_state.ver_solucion:
    st.markdown(f'<div class="bloque-azul"><div class="texto-isla"><b>Castellano (Lee y piensa):</b><br><br>{formatear_lineas(castellano_texto)}</div></div>', unsafe_allow_html=True)
else:
    st.markdown(f'<div class="bloque-verde"><div class="texto-isla"><b>Solución en Alemán:</b><br><br>{formatear_lineas(aleman_texto)}</div></div>', unsafe_allow_html=True)

# Botones de colores
col_c1, col_c2, col_c3, col_c4 = st.columns(4)
nuevo_estado = None
with col_c1:
    if st.button("🔴", use_container_width=True): nuevo_estado = "Rojo"
with col_c2:
    if st.button("🟠", use_container_width=True): nuevo_estado = "Naranja"
with col_c3:
    if st.button("🟢", use_container_width=True): nuevo_estado = "Verde"
with col_c4:
    if st.button("🔵", use_container_width=True): nuevo_estado = "Azul"

if nuevo_estado:
    try:
        requests.post(WEB_APP_URL, params={"row": indice_fila_google_sheet, "status": nuevo_estado, "sumarContador": "true"})
    except Exception:
        pass
    st.cache_data.clear()
    if st.session_state.indice_actual < total_rueda_actual - 1:
        st.session_state.indice_actual += 1
    st.session_state.ver_solucion = False
    st.rerun()

# Reproductor de audio
ruta_audio = f"Audios/{audio_id}.mp3"
if os.path.exists(ruta_audio):
    st.write("🎧 **Onda de audio interactiva:**")
    with open(ruta_audio, "rb") as f:
        b64_audio = base64.b64encode(f.read()).decode()
    html_reproductor = f"""
    <div id="waveform" style="background:rgba(0,0,0,0.25); border-radius:8px; padding:6px; margin-bottom:14px;"></div>
    <div style="display:flex; justify-content:center; gap:8px; margin-bottom:12px;">
        <button id="btnBack" style="padding:6px 12px; background:rgba(255,255,255,0.08); color:white; border:none; border-radius:6px; cursor:pointer;">⏮ -5s</button>
        <button id="btnPlay" style="padding:8px 20px; background:#3b7dd8; color:white; border:none; border-radius:6px; font-weight:600; cursor:pointer;">▶ Play</button>
        <button id="btnForward" style="padding:6px 12px; background:rgba(255,255,255,0.08); color:white; border:none; border-radius:6px; cursor:pointer;">+5s ⏭</button>
    </div>
    <script src="https://unpkg.com/wavesurfer.js@7"></script>
    <script>
        const wavesurfer = WaveSurfer.create({{ container: '#waveform', waveColor: '#4a5568', progressColor: '#3b7dd8', height: 50, url: 'data:audio/mp3;base64,{b64_audio}' }});
        const btnPlay = document.getElementById('btnPlay');
        btnPlay.addEventListener('click', () => wavesurfer.playPause());
        wavesurfer.on('play', () => {{ btnPlay.innerHTML = "⏸ Pausa"; btnPlay.style.background = "#22a66e"; }});
        wavesurfer.on('pause', () => {{ btnPlay.innerHTML = "▶ Play"; btnPlay.style.background = "#3b7dd8"; }});
        document.getElementById('btnBack').addEventListener('click', () => wavesurfer.skip(-5));
        document.getElementById('btnForward').addEventListener('click', () => wavesurfer.skip(5));
    </script>
    """
    st.components.v1.html(html_reproductor, height=130)

# Modo dictado
with st.expander("📝 Modo Dictado"):
    texto_usuario = st.text_area("Escribe el texto en alemán:", key=f"input_dictado_{st.session_state.indice_actual}", height=120)
    if st.button("🔍 Comprobar Dictado", use_container_width=True):
        if texto_usuario:
            porcentaje = calcular_similitud_parcial(texto_usuario, aleman_texto)
            cf, ct = ("rgba(16,185,129,0.15)", "#10b981") if porcentaje >= 90 else ("rgba(245,158,11,0.15)", "#f59e0b") if porcentaje >= 50 else ("rgba(239,68,68,0.15)", "#ef4444")
            st.markdown(f'<div class="resultado-porcentaje" style="background-color:{cf}; color:{ct}; border:1px solid {ct};">De lo que has escrito: {porcentaje:.0f}% bien</div>', unsafe_allow_html=True)

# Anotaciones
anotacion_inicial = str(fila_actual['Explicacion']) if 'Explicacion' in fila_actual and pd.notna(fila_actual['Explicacion']) else ""
st.markdown('<div style="font-family:\'Montserrat\'; font-size:0.85rem; font-weight:700; text-transform:uppercase; letter-spacing:1.5px; color:#8a9ab5; margin-top:1.5rem; margin-bottom:8px;">ANOTACIONES</div>', unsafe_allow_html=True)
texto_anotaciones = st.text_area("Anotaciones", value=anotacion_inicial, key=f"input_anotaciones_{st.session_state.indice_actual}", height=100, label_visibility="collapsed")

if st.button("💾 Guardar Anotaciones", use_container_width=True):
    try:
        res = requests.post(WEB_APP_URL, params={"row": indice_fila_google_sheet, "explanation": texto_anotaciones})
        if res.status_code == 200:
            st.success("¡Anotaciones guardadas! 🚀")
            st.cache_data.clear()
            st.rerun()
    except Exception:
        pass
