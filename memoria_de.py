import streamlit as st
import pandas as pd
import os
import re
import random
import base64
import requests
from difflib import SequenceMatcher

# Configuración de la página
st.set_page_config(page_title="Entrenador de Idiomas por Islas", page_icon="🇩🇪", layout="centered")

# Inyectar tipografías y estilos premium
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600;700&display=swap');

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

    /* ── Fuente base GLOBAL — cubre todos los elementos nativos de Streamlit ── */
    html, body, * {
        font-family: 'Montserrat', sans-serif !important;
    }

    /* Selectbox, radio, checkbox, slider, number_input, date_input */
    .stSelectbox > div, .stSelectbox label,
    .stRadio > div, .stRadio label,
    .stCheckbox > div, .stCheckbox label,
    .stSlider > div, .stSlider label,
    .stNumberInput > div, .stNumberInput label,
    .stDateInput > div, .stDateInput label,
    .stTextInput > div, .stTextInput label,
    .stTextArea > div, .stTextArea label,
    div[data-testid="stSelectbox"] *,
    div[data-testid="stTextInput"] *,
    div[data-testid="stTextArea"] *,
    div[data-testid="stNumberInput"] *,
    div[data-testid="stDateInput"] * {
        font-family: 'Montserrat', sans-serif !important;
    }

    /* Métricas */
    div[data-testid="stMetric"] *,
    div[data-testid="stMetricLabel"] *,
    div[data-testid="stMetricValue"] *,
    div[data-testid="stMetricDelta"] * {
        font-family: 'Montserrat', sans-serif !important;
    }

    /* Tablas / dataframes */
    .stDataFrame *, table, th, td {
        font-family: 'Montserrat', sans-serif !important;
    }

    /* Alertas: info, success, warning, error */
    div[data-testid="stAlert"] *,
    div[role="alert"] * {
        font-family: 'Montserrat', sans-serif !important;
    }

    /* Expander */
    details > summary,
    .streamlit-expanderHeader,
    .streamlit-expanderHeader * {
        font-family: 'Montserrat', sans-serif !important;
    }

    /* Sidebar completa */
    section[data-testid="stSidebar"] *,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] input {
        font-family: 'Montserrat', sans-serif !important;
    }

    /* Toast / notificaciones */
    div[data-testid="stToast"] * {
        font-family: 'Montserrat', sans-serif !important;
    }

    /* Botones */
    button, .stButton button, button * {
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

    h2, h3 {
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 600 !important;
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

    /* Estilo para el contenedor de Anotaciones */
    .bloque-anotaciones {
        background: var(--rojo-bg) !important;
        border: 1px solid var(--rojo-borde) !important;
        border-left: 4px solid var(--rojo) !important;
        padding: 1.4rem 1.6rem !important;
        border-radius: var(--radio) !important;
        margin-top: 1.5rem !important;
        margin-bottom: 0.5rem !important;
        box-shadow: 0 2px 12px rgba(224,84,84,0.07) !important;
    }

    /* Forzar que el text_area interno de Streamlit sea transparente para que luzca integrado */
    .bloque-anotaciones div[data-testid="stTextArea"] textarea {
        background-color: transparent !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        color: #e8ecf2 !important;
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
        letter-spacing: -0.3px;
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

    /* ── Barra de progreso más fina y elegante ── */
    .stProgress > div > div {
        height: 5px !important;
        border-radius: 99px !important;
    }

    /* ── Contador de progreso ── */
    .progreso-contador {
        font-family: 'Montserrat', sans-serif;
        font-size: 0.72rem;
        font-weight: 500;
        color: #8a9ab5;
        text-align: right;
        letter-spacing: 1px;
        margin-bottom: 4px;
    }

    /* ── Botones de navegación ── */
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
    .stButton button:active {
        transform: translateY(0px) !important;
    }

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {
        border-right: 1px solid rgba(255,255,255,0.06);
    }
    section[data-testid="stSidebar"] .stSelectbox label,
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        font-family: 'Montserrat', sans-serif !important;
    }

    /* ── Expander ── */
    .streamlit-expanderHeader {
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 500 !important;
        font-size: 0.95rem !important;
        border-radius: 8px !important;
    }

    /* ── Separador sidebar ── */
    hr { opacity: 0.15; }
    </style>
""", unsafe_allow_html=True)

# ── FUNCIÓN: Comparación por ventanas de igual longitud ──
def calcular_similitud_parcial(texto_usuario, texto_original):
    def limpiar(t):
        t = t.strip().lower()
        return re.sub(r'[.,!?¿¡"\'\s\n\r\t]', '', t)
    u_limpio = limpiar(texto_usuario)
    o_limpio = limpiar(texto_original)
    if not u_limpio or not o_limpio:
        return 0
    len_u = len(u_limpio)
    len_o = len(o_limpio)
    if len_u <= len_o:
        mejor_ratio = 0.0
        for i in range(len_o - len_u + 1):
            subcadena_original = o_limpio[i : i + len_u]
            ratio_actual = SequenceMatcher(None, u_limpio, subcadena_original).ratio()
            if ratio_actual > mejor_ratio:
                mejor_ratio = ratio_actual
        return mejor_ratio * 100
    else:
        return SequenceMatcher(None, u_limpio, o_limpio).ratio() * 100


# ── FUNCIÓN: Comparación palabra a palabra para resaltado ──
def comparar_palabras(texto_usuario, texto_original):
    def tokenizar(t):
        return re.findall(r'\w+', t.lower())

    palabras_usuario  = tokenizar(texto_usuario)
    palabras_original = tokenizar(texto_original)

    matcher = SequenceMatcher(None, palabras_usuario, palabras_original)
    html_usuario  = []
    html_original = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            for w in palabras_usuario[i1:i2]:
                html_usuario.append(f'<span class="palabra-ok">{w}</span>')
            for w in palabras_original[j1:j2]:
                html_original.append(f'<span class="palabra-ok">{w}</span>')
        elif tag == 'replace':
            for w in palabras_usuario[i1:i2]:
                html_usuario.append(f'<span class="palabra-mal">{w}</span>')
            for w in palabras_original[j1:j2]:
                html_original.append(f'<span class="palabra-mal">{w}</span>')
        elif tag == 'delete':
            for w in palabras_usuario[i1:i2]:
                html_usuario.append(f'<span class="palabra-extra">{w}</span>')
        elif tag == 'insert':
            for w in palabras_original[j1:j2]:
                html_original.append(f'<span class="palabra-mal">▢ {w}</span>')

    return ' '.join(html_usuario), ' '.join(html_original)


def formatear_lineas(texto):
    frases = re.split(r'(?<=[.!?])\s+', texto.strip())
    return "<br>".join(frases)

# URLs
SHEET_URL   = "https://docs.google.com/spreadsheets/d/1hpP0J5qRrbx5p9W2nHWsoTDBA9hhvLZYblaU12Ln3w4/export?format=csv"
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbzUjhiwydEHUGfYaEJOXpvJf-00D1Yx3jHltLgGPpCXXc_08dL_4fugUmmY7u7EmXgM/exec"

@st.cache_data(ttl=2)
def cargar_datos_web():
    url = f"{SHEET_URL}&nocache={random.randint(1, 100000)}"
    df = pd.read_csv(url)
    df.columns = df.columns.str.strip()
    return df

try:
    df_total = cargar_datos_web()
except Exception as e:
    st.error(f"No se pudo conectar con el Google Sheet. Detalles: {e}")
    st.stop()

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

# --- CÁLCULO ESTABLE DE LA RUEDA DE 15 ---
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
<div style="font-family: 'Montserrat', sans-serif; background: rgba(255,255,255,0.04); padding: 16px 18px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.09);">
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
            <div style="height: 100%; width: {porcentaje_isla}%; background: #3b7dd8; border-radius: 99px; transition: width 0.4s ease;"></div>
        </div>
        <p style="margin: 5px 0 0 0; font-size: 0.72rem; color: #8a9ab5; text-align: right; letter-spacing: 0.5px;">{porcentaje_isla}% completada</p>
    </div>
</div>
""", unsafe_allow_html=True)


# ¿Isla completada al 100%?
if total_aprendidos == total_frases_isla and total_frases_isla > 0:
    st.title("🇩🇪 Método de Chunks & Islas")
    st.balloons()
    st.success(f"🎉 ¡ESPECTACULAR! Has completado la isla '{isla_seleccionada}' al 100%.")
    st.info(f"Has pasado a Aprendidos los {total_frases_isla} monólogos en color Azul 🔵.")
    st.stop()

if st.session_state.indice_actual >= total_rueda_actual:
    st.session_state.indice_actual = total_rueda_actual - 1 if total_rueda_actual > 0 else 0

# --- CONTENIDO PRINCIPAL ---
st.title("🇩🇪 Método de Chunks & Islas")

fila_actual = df_en_rueda.iloc[st.session_state.indice_actual]
castellano_texto = str(fila_actual['Castellano'])
aleman_texto     = str(fila_actual['Aleman'])
estado_actual    = str(fila_actual['Estado']).strip()

indice_fila_google_sheet = int(df_total.index[df_total['Castellano'] == castellano_texto].tolist()[0]) + 2

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

# ── Contador + barra de progreso ──
pos_actual = st.session_state.indice_actual + 1
st.markdown(f'<div class="progreso-contador">{pos_actual} / {total_rueda_actual}</div>', unsafe_allow_html=True)
st.progress(pos_actual / total_rueda_actual)

if situacion_texto:
    st.markdown(f'<div class="titulo-situacion">📍 {situacion_texto}</div>', unsafe_allow_html=True)


# --- BARRA DE NAV / CONTROL (Botón Gramática eliminado) ---
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
    if st.button("⬅️ Anterior", use_container_width=True, key="btn_anterior_arriba"):
        if st.session_state.indice_actual > 0:
            st.session_state.indice_actual -= 1
            st.session_state.ver_solucion = False
            st.rerun()

with col_nav_sig:
    if st.button("Siguiente ➡️", use_container_width=True, key="btn_siguiente_arriba"):
        if st.session_state.indice_actual < total_rueda_actual - 1:
            st.session_state.indice_actual += 1
            st.session_state.ver_solucion = False
            st.rerun()

st.write("")


# ── LÓGICA DE LA TIRA DE COLOR PASTEL SUPERIOR ──
bg_tira = "rgba(59, 125, 216, 0.15)"
color_texto_tira = "#3b7dd8" 

if estado_actual == "Rojo":
    bg_tira = "rgba(224, 84, 84, 0.15)"
    color_texto_tira = "#e05454"
elif estado_actual == "Naranja":
    bg_tira = "rgba(245, 158, 11, 0.15)"
    color_texto_tira = "#f59e0b"
elif estado_actual == "Verde":
    bg_tira = "rgba(34, 166, 110, 0.15)"
    color_texto_tira = "#22a66e"

st.markdown(f"""
    <div class="tira-historial" style="background-color: {bg_tira}; color: {color_texto_tira}; border: 1px solid {color_texto_tira}44;">
        ESTADO ACTUAL
    </div>
""", unsafe_allow_html=True)


# ── Tarjeta principal ──
if not st.session_state.ver_solucion:
    castellano_formateado = formatear_lineas(castellano_texto)
    st.markdown(f"""
    <div class="bloque-azul">
        <div class="texto-isla">
            <b>Castellano (Lee y piensa):</b><br><br>
            {castellano_formateado}
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    aleman_formateado = formatear_lineas(aleman_texto)
    st.markdown(f"""
    <div class="bloque-verde">
        <div class="texto-isla">
            <b>Solución en Alemán:</b><br><br>
            {aleman_formateado}
        </div>
    </div>
    """, unsafe_allow_html=True)


# --- BOTONES DE COLORES ---
col_c1, col_c2, col_c3, col_c4 = st.columns(4)
nuevo_estado = None

with col_c1:
    if st.button("🔴", use_container_width=True, key="btn_color_rojo"):
        nuevo_estado = "Rojo"
with col_c2:
    if st.button("🟠", use_container_width=True, key="btn_color_naranja"):
        nuevo_estado = "Naranja"
with col_c3:
    if st.button("🟢", use_container_width=True, key="btn_color_verde"):
        nuevo_estado = "Verde"
with col_c4:
    if st.button("🔵", use_container_width=True, key="btn_color_azul"):
        nuevo_estado = "Azul"

if nuevo_estado:

    try:

        # Asegúrate de limpiar el texto antes de enviarlo
castellano_limpio = " ".join(castellano_texto.split())

r = requests.post(
    WEB_APP_URL,
    params={
        "castellano": castellano_limpio, # Usa la versión limpia
        "status": nuevo_estado,
        "sumarContador": "true"
    },
    timeout=10
)

        if r.status_code == 200:

            st.toast(f"Estado cambiado a {nuevo_estado}")

            st.cache_data.clear()

            if st.session_state.indice_actual < total_rueda_actual - 1:
                st.session_state.indice_actual += 1

            st.session_state.ver_solucion = False

            st.rerun()

        else:

            st.error(f"Error del servidor: {r.status_code}")
            st.write(r.text)

    except Exception as e:

        st.error(f"No se pudo conectar con Google Script: {e}")


# --- REPRODUCTOR DE AUDIO ---
ruta_audio = f"Audios/{audio_id}.mp3"
if os.path.exists(ruta_audio):
    st.markdown('<p style="font-family:\'Montserrat\',sans-serif; font-weight:600; font-size:0.95rem; margin-bottom:8px;">🎧 Onda de audio interactiva:</p>', unsafe_allow_html=True)

    with open(ruta_audio, "rb") as f:
        audio_bytes = f.read()
    b64_audio = base64.b64encode(audio_bytes).decode()

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
        .audio-player .waveform-wrap {{
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
            barWidth: 2,
            barGap: 2,
            barRadius: 3,
            height: 60,
            url: 'data:audio/mp3;base64,{b64_audio}'
        }});

        const wsRegions = wavesurfer.registerPlugin(WaveSurfer.Regions.create());
        wsRegions.enableDragSelection({{ color: 'rgba(59, 130, 246, 0.3)' }});

        wsRegions.on('region-created', (region) => {{
            wsRegions.getRegions().forEach(r => {{ if (r !== region) r.remove(); }});
        }});

        wavesurfer.on('timeupdate', (currentTime) => {{
            const regions = wsRegions.getRegions();
            if (regions.length > 0) {{
                const activeRegion = regions[0];
                if (currentTime >= activeRegion.end || currentTime < activeRegion.start) {{
                    wavesurfer.setTime(activeRegion.start);
                }}
            }}
        }});

        wavesurfer.on('interaction', () => {{
            setTimeout(() => {{
                const regions = wsRegions.getRegions();
                if (regions.length > 0) {{
                    const currentTime = wavesurfer.getCurrentTime();
                    const activeRegion = regions[0];
                    if (currentTime < activeRegion.start || currentTime > activeRegion.end) {{
                        wsRegions.clearRegions();
                    }}
                }}
            }}, 50);
        }});

        document.getElementById('btnResetRegion').addEventListener('click', () => {{ wsRegions.clearRegions(); }});
        const btnPlay = document.getElementById('btnPlay');
        btnPlay.addEventListener('click', () => {{ wavesurfer.playPause(); }});

        wavesurfer.on('play', () => {{
            btnPlay.innerHTML = "⏸ Pausa";
            btnPlay.style.background = "#22a66e";
        }});
        wavesurfer.on('pause', () => {{
            btnPlay.innerHTML = "▶ Play";
            btnPlay.style.background = "#3b7dd8";
        }});

        document.getElementById('btnBack').addEventListener('click', () => {{ wavesurfer.skip(-5); }});
        document.getElementById('btnForward').addEventListener('click', () => {{ wavesurfer.skip(5); }});

        const speedSlider = document.getElementById('speedSlider');
        const speedValue  = document.getElementById('speedValue');

        speedSlider.addEventListener('input', (e) => {{
            const currentSpeed = parseFloat(e.target.value);
            wavesurfer.setPlaybackRate(currentSpeed);
            speedValue.innerHTML = currentSpeed.toFixed(1) + "×";
        }});
        wavesurfer.on('ready', () => {{ wavesurfer.setPlaybackRate(parseFloat(speedSlider.value)); }});
    </script>
    """
    st.components.v1.html(html_reproductor, height=215)
else:
    st.warning(f"⚠️ Audio no encontrado en: `{ruta_audio}`")


# --- MODO DICTADO ---
with st.expander("📝 Modo Dictado"):
    texto_usuario = st.text_area(
        "Escribe el texto en alemán:",
        key=f"input_dictado_{st.session_state.indice_actual}",
        height=250
    )

    if st.button("🔍 Comprobar Dictado", use_container_width=True):
        if texto_usuario:
            porcentaje_acierto = calcular_similitud_parcial(texto_usuario, aleman_texto)

            if porcentaje_acierto >= 90:
                color_fondo, color_texto = "rgba(16, 185, 129, 0.15)", "#10b981"
            elif porcentaje_acierto >= 50:
                color_fondo, color_texto = "rgba(245, 158, 11, 0.15)", "#f59e0b"
            else:
                color_fondo, color_texto = "rgba(239, 68, 68, 0.15)", "#ef4444"

            st.markdown(f"""
            <div class="resultado-porcentaje" style="background-color: {color_fondo}; color: {color_texto}; border: 1px solid {color_texto};">
                De lo que has escrito: {porcentaje_acierto:.0f}% bien
            </div>
            """, unsafe_allow_html=True)

            # ── Resaltado palabra a palabra ──
            html_usuario, html_original = comparar_palabras(texto_usuario, aleman_texto)

            st.markdown(f"""
            <div class="dictado-comparacion">
                <div style="font-size:0.7rem; font-weight:600; text-transform:uppercase; letter-spacing:1.5px; color:#8a9ab5; margin-bottom:8px;">Tu versión</div>
                <div style="margin-bottom:14px;">{html_usuario}</div>
                <div style="font-size:0.7rem; font-weight:600; text-transform:uppercase; letter-spacing:1.5px; color:#8a9ab5; margin-bottom:8px;">Versión correcta</div>
                <div>{html_original}</div>
            </div>
            <div style="font-family:'Montserrat',sans-serif; font-size:0.75rem; color:#8a9ab5; margin-top:8px; display:flex; gap:16px;">
                <span><span class="palabra-ok" style="color:#22a66e;">■</span> Correcto</span>
                <span><span class="palabra-mal" style="color:#e05454;">■</span> Error / Faltante</span>
                <span><span class="palabra-extra" style="color:#f5a623;">■</span> Sobrante</span>
            </div>
            """, unsafe_allow_html=True)


# --- BLOQUE FIJO: ANOTACIONES (Diseño ultra limpio en mayúsculas) ---
anotacion_inicial = str(fila_actual['Explicacion']) if 'Explicacion' in fila_actual and pd.notna(fila_actual['Explicacion']) else ""

# Título simple en mayúsculas sin marcos ni cajas de color
st.markdown("""
    <div style="font-family: 'Montserrat', sans-serif; font-size: 0.85rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px; color: #8a9ab5; margin-top: 1.5rem; margin-bottom: 8px;">
        ANOTACIONES
    </div>
""", unsafe_allow_html=True)

texto_anotaciones = st.text_area(
    "Anotaciones", 
    value=anotacion_inicial,
    key=f"input_anotaciones_{st.session_state.indice_actual}",
    height=150,
    label_visibility="collapsed" # Oculta el texto duplicado automático de Streamlit
)

if st.button("💾 Guardar Anotaciones", use_container_width=True, key="btn_guardar_anotaciones"):
    try:
        res = requests.post(WEB_APP_URL, params={"castellano": castellano_texto, "explanation": texto_anotaciones})
        if res.status_code == 200:
            st.success("¡Anotaciones guardadas correctamente en Google Sheets! 🚀")
            st.cache_data.clear()
            st.rerun()
        else:
            st.error("Error al guardar en el servidor remoto.")
    except Exception as e:
        st.error(f"No se pudo conectar con el servidor: {e}")
