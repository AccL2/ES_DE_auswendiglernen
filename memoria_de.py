import streamlit as st
import pandas as pd
import os
import re
import random
import base64
import requests
from datetime import datetime
from difflib import SequenceMatcher

st.set_page_config(page_title="Entrenador de Idiomas por Islas", page_icon="🇩🇪", layout="centered")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600;700&display=swap');

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

    html, body, [class*="css"], .stMarkdown, .stTextArea, .stExpander,
    .stButton button, .stSelectbox, .stSidebar, p, label, input, textarea {
        font-family: 'Montserrat', sans-serif !important;
    }

    h1 {
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 700 !important;
        font-size: 1.85rem !important;
        letter-spacing: -0.5px !important;
        margin-bottom: 0.25rem !important;
    }
    h2, h3 { font-family: 'Montserrat', sans-serif !important; font-weight: 600 !important; }

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
        transition: box-shadow 0.2s;
    }
    .bloque-azul:hover { box-shadow: 0 4px 20px rgba(59,125,216,0.14); }

    .bloque-verde {
        background: var(--verde-bg);
        border: 1px solid var(--verde-borde);
        border-left: 4px solid var(--verde);
        padding: 1.4rem 1.6rem;
        border-radius: var(--radio);
        margin-bottom: 1rem;
        box-shadow: 0 2px 12px rgba(34,166,110,0.07);
        transition: box-shadow 0.2s;
    }
    .bloque-verde:hover { box-shadow: 0 4px 20px rgba(34,166,110,0.14); }

    .bloque-gramatica {
        background: var(--rojo-bg);
        border: 1px solid var(--rojo-borde);
        border-left: 4px solid var(--rojo);
        padding: 1.4rem 1.6rem;
        border-radius: var(--radio);
        margin-top: 0.75rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 12px rgba(224,84,84,0.07);
    }
    .texto-gramatica {
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 400 !important;
        line-height: 1.8;
        font-size: 1.2rem;
        margin: 0; padding: 0;
    }

    .resultado-porcentaje {
        font-family: 'Montserrat', sans-serif;
        font-size: 1.5rem;
        font-weight: 400;
        text-align: center;
        padding: 14px 20px;
        border-radius: var(--radio);
        margin-top: 10px;
        margin-bottom: 10px;
        letter-spacing: -0.3px;
    }

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
    .palabra-ok    { color: #22a66e; font-weight: 500; }
    .palabra-mal   { color: #e05454; font-weight: 500; text-decoration: underline wavy #e05454; }
    .palabra-extra { color: #f5a623; font-weight: 500; font-style: italic; }

    .stProgress > div > div { height: 5px !important; border-radius: 99px !important; }

    .progreso-contador {
        font-family: 'Montserrat', sans-serif;
        font-size: 0.72rem;
        font-weight: 500;
        color: #8a9ab5;
        text-align: right;
        letter-spacing: 1px;
        margin-bottom: 4px;
    }

    @keyframes flash-aprendida {
        0%   { background: rgba(34,166,110,0.0); }
        30%  { background: rgba(34,166,110,0.25); }
        100% { background: rgba(34,166,110,0.0); }
    }
    .flash-aprendida {
        animation: flash-aprendida 1.2s ease-out forwards;
        border-radius: var(--radio);
        padding: 1rem 1.4rem;
        text-align: center;
        font-family: 'Montserrat', sans-serif;
        font-size: 1.1rem;
        font-weight: 600;
        color: #22a66e;
        border: 1px solid rgba(34,166,110,0.35);
        margin-bottom: 1rem;
    }

    .stButton button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 0.82rem !important;
        letter-spacing: 0.4px !important;
        padding: 0.45rem 0.9rem !important;
        transition: all 0.15s ease !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
    }
    .stButton button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 14px rgba(0,0,0,0.18) !important;
    }
    .stButton button:active { transform: translateY(0px) !important; }

    section[data-testid="stSidebar"] { border-right: 1px solid rgba(255,255,255,0.06); }
    section[data-testid="stSidebar"] .stSelectbox label,
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 { font-family: 'Montserrat', sans-serif !important; }

    .streamlit-expanderHeader {
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 500 !important;
        font-size: 0.95rem !important;
        border-radius: 8px !important;
    }

    hr { opacity: 0.15; }
    </style>
""", unsafe_allow_html=True)

# ── URLs ──
WEB_APP_URL    = "https://script.google.com/macros/s/AKfycbyMpUxnYWLCceZpCIsILNWTywzT0MGnrctLFK0DKVkRBr0t1JDj3TagKVfi70zZHQzb/exec"
SHEET_BASE_URL = "https://docs.google.com/spreadsheets/d/1hpP0J5qRrbx5p9W2nHWsoTDBA9hhvLZYblaU12Ln3w4/export?format=xlsx"


# ── CARGA DE DATOS ──
@st.cache_data(ttl=2)
def cargar_frases():
    url = f"{SHEET_BASE_URL}&nocache={random.randint(1, 999999)}"
    xls = pd.ExcelFile(url)
    df = xls.parse(xls.sheet_names[0])
    df.columns = df.columns.str.strip()
    return df


@st.cache_data(ttl=2)
def cargar_progreso():
    url = f"{SHEET_BASE_URL}&sheet=Progreso&nocache={random.randint(1, 999999)}"
    df = pd.read_excel(url, sheet_name="Progreso")
    df.columns = df.columns.str.strip()
    return df


def obtener_contador_diario():
    try:
        hoy = datetime.now().strftime("%Y-%m-%d")
        df = cargar_progreso().copy()
        df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
        fila = df[df['Fecha'].dt.strftime('%Y-%m-%d') == hoy]
        if not fila.empty:
            return int(fila.iloc[0]['Cantidad'])
    except Exception:
        pass
    return 0


# ── FUNCIONES AUXILIARES ──
def calcular_similitud_parcial(texto_usuario, texto_original):
    def limpiar(t):
        t = t.strip().lower()
        return re.sub(r'[.,!?¿¡"\'\s\n\r\t]', '', t)
    u = limpiar(texto_usuario)
    o = limpiar(texto_original)
    if not u or not o:
        return 0
    if len(u) <= len(o):
        mejor = 0.0
        for i in range(len(o) - len(u) + 1):
            r = SequenceMatcher(None, u, o[i:i+len(u)]).ratio()
            if r > mejor:
                mejor = r
        return mejor * 100
    return SequenceMatcher(None, u, o).ratio() * 100


def comparar_palabras(texto_usuario, texto_original):
    def tok(t): return re.findall(r'\w+', t.lower())
    pu, po = tok(texto_usuario), tok(texto_original)
    matcher = SequenceMatcher(None, pu, po)
    hu, ho = [], []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            for w in pu[i1:i2]: hu.append(f'<span class="palabra-ok">{w}</span>')
            for w in po[j1:j2]: ho.append(f'<span class="palabra-ok">{w}</span>')
        elif tag == 'replace':
            for w in pu[i1:i2]: hu.append(f'<span class="palabra-mal">{w}</span>')
            for w in po[j1:j2]: ho.append(f'<span class="palabra-mal">{w}</span>')
        elif tag == 'delete':
            for w in pu[i1:i2]: hu.append(f'<span class="palabra-extra">{w}</span>')
        elif tag == 'insert':
            for w in po[j1:j2]: ho.append(f'<span class="palabra-mal">▢ {w}</span>')
    return ' '.join(hu), ' '.join(ho)


def formatear_lineas(texto):
    return "<br>".join(re.split(r'(?<=[.!?])\s+', texto.strip()))


# ── CARGA INICIAL ──
try:
    df_total = cargar_frases()
except Exception as e:
    st.error(f"No se pudo conectar con el Google Sheet. Detalles: {e}")
    st.stop()

frases_vistas_hoy = obtener_contador_diario()


# ── SIDEBAR ──
st.sidebar.title("Configuración")
islas_disponibles = df_total['Isla'].unique()
isla_seleccionada = st.sidebar.selectbox("🏝️ Selecciona la Isla:", islas_disponibles)

df_isla_completa  = df_total[df_total['Isla'] == isla_seleccionada].copy()
total_frases_isla = len(df_isla_completa)

if 'isla_anterior' not in st.session_state or st.session_state.isla_anterior != isla_seleccionada:
    st.session_state.indice_actual   = 0
    st.session_state.isla_anterior   = isla_seleccionada
    st.session_state.ver_solucion    = False
    st.session_state.ver_gramatica   = False
    st.session_state.flash_aprendida = False

df_activas_y_pendientes = df_isla_completa[df_isla_completa['Estado'] != 'Azul'].copy()
df_azul                 = df_isla_completa[df_isla_completa['Estado'] == 'Azul']
total_aprendidos        = len(df_azul)
df_en_rueda             = df_activas_y_pendientes.head(15).copy()
total_rueda_actual      = len(df_en_rueda)

estados_rueda = df_en_rueda['Estado'].fillna('Rojo').astype(str).str.strip().tolist()
n_rojos    = estados_rueda.count('Rojo')
n_naranjas = estados_rueda.count('Naranja')
n_verdes   = estados_rueda.count('Verde')

porcentaje_isla = round((total_aprendidos / total_frases_isla * 100)) if total_frases_isla > 0 else 0

st.sidebar.write("---")
st.sidebar.markdown("### 📊 Estado de la Isla")
st.sidebar.markdown(f"""
<div style="font-family:'Montserrat',sans-serif; background:rgba(255,255,255,0.04); padding:16px 18px; border-radius:12px; border:1px solid rgba(255,255,255,0.09); margin-bottom:15px;">
    <p style="margin:0 0 12px 0; font-size:0.7rem; color:#8a9ab5; font-weight:500; text-transform:uppercase; letter-spacing:2px;">🔄 En rueda &nbsp;·&nbsp; {total_rueda_actual}</p>
    <div style="display:flex; flex-direction:column; gap:8px;">
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
    <div style="margin:14px 0 0 0; padding-top:12px; border-top:1px solid rgba(255,255,255,0.08); display:flex; align-items:center; justify-content:space-between;">
        <div style="display:flex; align-items:center; gap:8px; font-size:0.9rem;">
            <span style="width:10px;height:10px;border-radius:50%;background:#3b7dd8;display:inline-block;flex-shrink:0;"></span>
            <span style="color:#8a9ab5; font-size:0.8rem;">Aprendidas</span>
        </div>
        <span style="font-size:1rem; font-weight:600; color:#3b7dd8;">{total_aprendidos}<span style="color:#8a9ab5; font-weight:400; font-size:0.82rem;"> / {total_frases_isla}</span></span>
    </div>
    <div style="margin-top:12px;">
        <div style="height:5px; background:rgba(255,255,255,0.08); border-radius:99px; overflow:hidden;">
            <div style="height:100%; width:{porcentaje_isla}%; background:#3b7dd8; border-radius:99px; transition:width 0.4s ease;"></div>
        </div>
        <p style="margin:5px 0 0 0; font-size:0.72rem; color:#8a9ab5; text-align:right;">{porcentaje_isla}% completada</p>
    </div>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown(f"""
<div style="font-family:'Montserrat',sans-serif; background:rgba(34,166,110,0.08); padding:14px 16px; border-radius:12px; border:1px solid rgba(34,166,110,0.3); text-align:center;">
    <span style="font-size:1.4rem; display:block; margin-bottom:2px;">🎯</span>
    <span style="font-size:0.72rem; color:#8a9ab5; font-weight:600; text-transform:uppercase; letter-spacing:1px; display:block;">Frases Calificadas Hoy</span>
    <span style="font-size:2rem; font-weight:700; color:#22a66e; line-height:1.2; display:block; margin-top:2px;">{frases_vistas_hoy}</span>
</div>
""", unsafe_allow_html=True)


# ── Isla completada ──
if total_aprendidos == total_frases_isla and total_frases_isla > 0:
    st.title("🇩🇪 Método de Chunks & Islas")
    st.balloons()
    st.success(f"🎉 ¡ESPECTACULAR! Has completado la isla '{isla_seleccionada}' al 100%.")
    st.info(f"Has pasado a Aprendidos los {total_frases_isla} monólogos en color Azul 🔵.")
    st.stop()

if st.session_state.indice_actual >= total_rueda_actual:
    st.session_state.indice_actual = total_rueda_actual - 1 if total_rueda_actual > 0 else 0


# ── CONTENIDO PRINCIPAL ──
st.title("🇩🇪 Método de Chunks & Islas")

if total_rueda_actual == 0:
    st.info("No quedan frases activas en esta rueda.")
    st.stop()

fila_actual      = df_en_rueda.iloc[st.session_state.indice_actual]
castellano_texto = str(fila_actual['Castellano'])
aleman_texto     = str(fila_actual['Aleman'])
estado_actual    = str(fila_actual['Estado']).strip()

indice_fila_google_sheet = int(
    df_total.index[df_total['Castellano'] == castellano_texto].tolist()[0]
) + 2

audio_id_raw = fila_actual['Audio_ID']
if pd.isna(audio_id_raw):
    audio_id = "sin_audio"
elif isinstance(audio_id_raw, float):
    audio_id = str(int(audio_id_raw))
else:
    audio_id = str(audio_id_raw).strip()

situacion_texto = ""
if 'Situacion' in fila_actual and pd.notna(fila_actual['Situacion']):
    situacion_texto = str(fila_actual['Situacion']).strip()

# ── Progreso ──
pos_actual = st.session_state.indice_actual + 1
st.markdown(f'<div class="progreso-contador">{pos_actual} / {total_rueda_actual}</div>', unsafe_allow_html=True)
st.progress(pos_actual / total_rueda_actual)

if situacion_texto:
    st.markdown(f'<div class="titulo-situacion">📍 {situacion_texto}</div>', unsafe_allow_html=True)

# ── Navegación ──
col_nav_sol, col_nav_ant, col_nav_sig, col_nav_gram = st.columns([0.25, 0.25, 0.25, 0.25])

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
    if st.button("⬅️ Anterior", use_container_width=True, key="btn_anterior"):
        if st.session_state.indice_actual > 0:
            st.session_state.indice_actual  -= 1
            st.session_state.ver_solucion    = False
            st.session_state.ver_gramatica   = False
            st.session_state.flash_aprendida = False
            st.rerun()

with col_nav_sig:
    if st.button("Siguiente ➡️", use_container_width=True, key="btn_siguiente"):
        if st.session_state.indice_actual < total_rueda_actual - 1:
            st.session_state.indice_actual  += 1
            st.session_state.ver_solucion    = False
            st.session_state.ver_gramatica   = False
            st.session_state.flash_aprendida = False
            st.rerun()

with col_nav_gram:
    if st.button("💡 Gramática", use_container_width=True, key="btn_gramatica"):
        st.session_state.ver_gramatica = not st.session_state.ver_gramatica
        st.rerun()

st.write("")

# ── Flash aprendida ──
if st.session_state.get('flash_aprendida'):
    st.markdown('<div class="flash-aprendida">✦ ¡Frase aprendida! 🔵</div>', unsafe_allow_html=True)
    st.session_state.flash_aprendida = False

# ── Badge estado actual ──
bg_tira, color_tira = "rgba(59,125,216,0.15)", "#3b7dd8"
if estado_actual == "Rojo":
    bg_tira, color_tira = "rgba(224,84,84,0.15)", "#e05454"
elif estado_actual == "Naranja":
    bg_tira, color_tira = "rgba(245,158,11,0.15)", "#f59e0b"
elif estado_actual == "Verde":
    bg_tira, color_tira = "rgba(34,166,110,0.15)", "#22a66e"

st.markdown(f'<div class="tira-historial" style="background-color:{bg_tira}; color:{color_tira}; border:1px solid {color_tira}44;">ESTADO ACTUAL</div>', unsafe_allow_html=True)

# ── Tarjeta principal ──
if not st.session_state.ver_solucion:
    st.markdown(f'<div class="bloque-azul"><div class="texto-isla"><b>Castellano (Lee y piensa):</b><br><br>{formatear_lineas(castellano_texto)}</div></div>', unsafe_allow_html=True)
else:
    st.markdown(f'<div class="bloque-verde"><div class="texto-isla"><b>Solución en Alemán:</b><br><br>{formatear_lineas(aleman_texto)}</div></div>', unsafe_allow_html=True)

# ── Gramática ──
if st.session_state.ver_gramatica:
    if 'Explicacion' in fila_actual and pd.notna(fila_actual['Explicacion']) and str(fila_actual['Explicacion']).strip():
        st.markdown(f'<div class="bloque-gramatica"><div class="texto-gramatica"><b>💡 Explicación Gramatical:</b><br><br>{formatear_lineas(str(fila_actual["Explicacion"]))}</div></div>', unsafe_allow_html=True)

# ── Botones de color ──
col_c1, col_c2, col_c3, col_c4 = st.columns(4)
nuevo_estado = None

with col_c1:
    if st.button("🔴", use_container_width=True, key="btn_rojo"):    nuevo_estado = "Rojo"
with col_c2:
    if st.button("🟠", use_container_width=True, key="btn_naranja"): nuevo_estado = "Naranja"
with col_c3:
    if st.button("🟢", use_container_width=True, key="btn_verde"):   nuevo_estado = "Verde"
with col_c4:
    if st.button("🔵", use_container_width=True, key="btn_azul"):    nuevo_estado = "Azul"

if nuevo_estado:
    try:
        requests.post(WEB_APP_URL, params={
            "row": indice_fila_google_sheet,
            "status": nuevo_estado,
            "sumarContador": "true"
        })
    except Exception:
        pass
    st.cache_data.clear()
    if nuevo_estado == "Azul":
        st.session_state.flash_aprendida = True
    elif st.session_state.indice_actual < total_rueda_actual - 1:
        st.session_state.indice_actual += 1
    st.session_state.ver_solucion  = False
    st.session_state.ver_gramatica = False
    st.rerun()


# ── Reproductor de audio avanzado ──
ruta_audio = f"Audios/{audio_id}.mp3"
if os.path.exists(ruta_audio):
    st.write("🎧 **Onda de audio interactiva:**")
    with open(ruta_audio, "rb") as f:
        b64_audio = base64.b64encode(f.read()).decode()

    html_reproductor = f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600&display=swap');
        .audio-player {{
            font-family: 'Montserrat', sans-serif;
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,255,255,0.1);
            padding: 16px;
            border-radius: 14px;
            color: #e8ecf2;
            box-sizing: border-box;
        }}
        .waveform-wrap {{
            margin-bottom: 14px;
            background: rgba(0,0,0,0.25);
            border-radius: 8px;
            padding: 6px 6px 2px;
            cursor: pointer;
        }}
        .audio-controls {{
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 8px;
            flex-wrap: wrap;
            margin-bottom: 12px;
        }}
        .audio-btn {{
            padding: 7px 15px;
            background: rgba(255,255,255,0.08);
            color: #e8ecf2;
            border: 1px solid rgba(255,255,255,0.12);
            border-radius: 8px;
            cursor: pointer;
            font-weight: 500;
            font-size: 0.83rem;
            font-family: 'Montserrat', sans-serif;
            transition: all 0.15s ease;
        }}
        .audio-btn:hover {{ background: rgba(255,255,255,0.14); transform: translateY(-1px); }}
        .audio-btn-play {{
            padding: 8px 22px;
            background: #3b7dd8;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            font-size: 0.9rem;
            font-family: 'Montserrat', sans-serif;
            min-width: 96px;
            transition: all 0.15s ease;
        }}
        .audio-btn-play:hover {{ background: #2d6ac4; transform: translateY(-1px); }}
        .audio-btn-reset {{
            padding: 7px 15px;
            background: rgba(224,84,84,0.15);
            color: #e05454;
            border: 1px solid rgba(224,84,84,0.3);
            border-radius: 8px;
            cursor: pointer;
            font-weight: 500;
            font-size: 0.83rem;
            font-family: 'Montserrat', sans-serif;
            transition: all 0.15s ease;
        }}
        .audio-btn-reset:hover {{ background: rgba(224,84,84,0.25); }}
        .speed-row {{
            display: flex;
            align-items: center;
            gap: 12px;
            background: rgba(0,0,0,0.18);
            padding: 8px 14px;
            border-radius: 10px;
        }}
        .speed-label {{
            font-size: 0.78rem;
            font-weight: 500;
            color: #8a9ab5;
            white-space: nowrap;
            min-width: 90px;
        }}
        .speed-val {{
            font-size: 0.88rem;
            font-weight: 600;
            color: #3b7dd8;
            min-width: 38px;
            text-align: right;
        }}
    </style>
    <div class="audio-player">
        <div class="waveform-wrap"><div id="waveform"></div></div>
        <div class="audio-controls">
            <button id="btnBack" class="audio-btn">⏮ −5s</button>
            <button id="btnPlay" class="audio-btn-play">▶ Play</button>
            <button id="btnForward" class="audio-btn">+5s ⏭</button>
            <button id="btnResetRegion" class="audio-btn-reset">✕ Reset</button>
        </div>
        <div class="speed-row">
            <span class="speed-label">⚡ Velocidad</span>
            <input type="range" id="speedSlider" min="0.5" max="2.0" step="0.1" value="1.0"
                   style="flex-grow:1; cursor:pointer; accent-color:#3b7dd8; margin:0;">
            <span id="speedValue" class="speed-val">1.0×</span>
        </div>
    </div>

    <script src="https://unpkg.com/wavesurfer.js@7"></script>
    <script src="https://unpkg.com/wavesurfer.js@7/dist/plugins/regions.min.js"></script>
    <script>
        const wavesurfer = WaveSurfer.create({{
            container: '#waveform',
            waveColor: '#4a5568',
            progressColor: '#3b7dd8',
            cursorColor: '#e05454',
            barWidth: 2, barGap: 2, barRadius: 3,
            height: 60,
            url: 'data:audio/mp3;base64,{b64_audio}'
        }});

        const wsRegions = wavesurfer.registerPlugin(WaveSurfer.Regions.create());
        wsRegions.enableDragSelection({{ color: 'rgba(59,130,246,0.3)' }});
        wsRegions.on('region-created', (region) => {{
            wsRegions.getRegions().forEach(r => {{ if (r !== region) r.remove(); }});
        }});
        wavesurfer.on('timeupdate', (currentTime) => {{
            const regions = wsRegions.getRegions();
            if (regions.length > 0) {{
                const r = regions[0];
                if (currentTime >= r.end || currentTime < r.start) {{
                    wavesurfer.setTime(r.start);
                }}
            }}
        }});
        wavesurfer.on('interaction', () => {{
            setTimeout(() => {{
                const regions = wsRegions.getRegions();
                if (regions.length > 0) {{
                    const ct = wavesurfer.getCurrentTime();
                    const r  = regions[0];
                    if (ct < r.start || ct > r.end) wsRegions.clearRegions();
                }}
            }}, 50);
        }});

        document.getElementById('btnResetRegion').addEventListener('click', () => wsRegions.clearRegions());

        const btnPlay = document.getElementById('btnPlay');
        btnPlay.addEventListener('click', () => wavesurfer.playPause());
        wavesurfer.on('play',  () => {{ btnPlay.innerHTML = "⏸ Pausa"; btnPlay.style.background = "#22a66e"; }});
        wavesurfer.on('pause', () => {{ btnPlay.innerHTML = "▶ Play";  btnPlay.style.background = "#3b7dd8"; }});

        document.getElementById('btnBack').addEventListener('click',    () => wavesurfer.skip(-5));
        document.getElementById('btnForward').addEventListener('click', () => wavesurfer.skip(5));

        const speedSlider = document.getElementById('speedSlider');
        const speedValue  = document.getElementById('speedValue');
        speedSlider.addEventListener('input', (e) => {{
            const v = parseFloat(e.target.value);
            wavesurfer.setPlaybackRate(v);
            speedValue.innerHTML = v.toFixed(1) + "×";
        }});
        wavesurfer.on('ready', () => wavesurfer.setPlaybackRate(parseFloat(speedSlider.value)));
    </script>
    """
    st.components.v1.html(html_reproductor, height=215)
else:
    st.warning(f"⚠️ Audio no encontrado: `{ruta_audio}`")


# ── Modo Dictado ──
with st.expander("📝 Modo Dictado"):
    texto_usuario = st.text_area(
        "Escribe el texto en alemán:",
        key=f"input_dictado_{st.session_state.indice_actual}",
        height=250
    )
    if st.button("🔍 Comprobar Dictado", use_container_width=True):
        if texto_usuario:
            pct = calcular_similitud_parcial(texto_usuario, aleman_texto)
            cf, ct = ("rgba(16,185,129,0.15)", "#10b981") if pct >= 90 else \
                     ("rgba(245,158,11,0.15)",  "#f59e0b") if pct >= 50 else \
                     ("rgba(239,68,68,0.15)",   "#ef4444")
            st.markdown(f'<div class="resultado-porcentaje" style="background-color:{cf}; color:{ct}; border:1px solid {ct};">De lo que has escrito: {pct:.0f}% bien</div>', unsafe_allow_html=True)
            hu, ho = comparar_palabras(texto_usuario, aleman_texto)
            st.markdown(f"""
            <div class="dictado-comparacion">
                <div style="font-size:0.7rem;font-weight:600;text-transform:uppercase;letter-spacing:1.5px;color:#8a9ab5;margin-bottom:8px;">Tu versión</div>
                <div style="margin-bottom:14px;">{hu}</div>
                <div style="font-size:0.7rem;font-weight:600;text-transform:uppercase;letter-spacing:1.5px;color:#8a9ab5;margin-bottom:8px;">Versión correcta</div>
                <div>{ho}</div>
            </div>
            <div style="font-family:'Montserrat',sans-serif;font-size:0.75rem;color:#8a9ab5;margin-top:8px;display:flex;gap:16px;">
                <span><span style="color:#22a66e;">■</span> Correcto</span>
                <span><span style="color:#e05454;">■</span> Error / Faltante</span>
                <span><span style="color:#f5a623;">■</span> Sobrante</span>
            </div>
            """, unsafe_allow_html=True)


# ── Anotaciones ──
anotacion_inicial = str(fila_actual['Explicacion']) if 'Explicacion' in fila_actual and pd.notna(fila_actual['Explicacion']) else ""
st.markdown('<div style="font-family:\'Montserrat\';font-size:0.85rem;font-weight:700;text-transform:uppercase;letter-spacing:1.5px;color:#8a9ab5;margin-top:1.5rem;margin-bottom:8px;">ANOTACIONES</div>', unsafe_allow_html=True)
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
