import streamlit as st
import pandas as pd
import os
import re
import random
import base64
import requests
from datetime import date
from difflib import SequenceMatcher

# Configuración de la página
st.set_page_config(page_title="Entrenador de Idiomas por Islas", page_icon="🇩🇪", layout="centered")

# Inyectar tipografías y estilos premium
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
    .bloque-azul:hover { box-shadow: 0 4px 20px rgba(59,125,216,0.14); }

    .bloque-verde {
        background: var(--verde-bg);
        border: 1px solid var(--verde-borde);
        border-left: 4px solid var(--verde);
        padding: 1.4rem 1.6rem;
        border-radius: var(--radio);
        margin-bottom: 1rem;
        box-shadow: 0 2px 12px rgba(34,166,110,0.07);
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
    }

    .texto-gramatica {
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 400 !important;
        line-height: 1.8;
        font-size: 1.2rem;
    }

    .resultado-porcentaje {
        font-family: 'Montserrat', sans-serif;
        font-size: 1.5rem;
        text-align: center;
        padding: 14px 20px;
        border-radius: var(--radio);
        margin-top: 10px;
        margin-bottom: 10px;
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
    .palabra-ok   { color: #22a66e; font-weight: 500; }
    .palabra-mal  { color: #e05454; font-weight: 500; text-decoration: underline wavy #e05454; }
    .palabra-extra { color: #f5a623; font-weight: 500; font-style: italic; }

    .stProgress > div > div { height: 5px !important; border-radius: 99px !important; }
    .progreso-contador {
        font-family: 'Montserrat', sans-serif;
        font-size: 0.72rem;
        font-weight: 500;
        color: #8a9ab5;
        text-align: right;
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
        color: #22a66e;
        border: 1px solid rgba(34,166,110,0.35);
        margin-bottom: 1rem;
    }

    .stButton button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 0.82rem !important;
        padding: 0.45rem 0.9rem !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
    }
    .stButton button:hover { transform: translateY(-1px) !important; }

    section[data-testid="stSidebar"] { border-right: 1px solid rgba(255,255,255,0.06); }
    .streamlit-expanderHeader { border-radius: 8px !important; }
    hr { opacity: 0.15; }
    </style>
""", unsafe_allow_html=True)


# ── COMPARADORES DE TEXTO ──
def calcular_similitud_parcial(texto_usuario, texto_original):
    def limpiar(t):
        t = t.strip().lower()
        return re.sub(r'[.,!?¿¡"\'\s\n\r\t]', '', t)
    u_limpio = limpiar(texto_usuario)
    o_limpio = limpiar(texto_original)
    if not u_limpio or not o_limpio: return 0
    len_u = len(u_limpio)
    len_o = len(o_limpio)
    if len_u <= len_o:
        mejor_ratio = 0.0
        for i in range(len_o - len_u + 1):
            subcadena_original = o_limpio[i : i + len_u]
            ratio_actual = SequenceMatcher(None, u_limpio, subcadena_original).ratio()
            if ratio_actual > mejor_ratio: mejor_ratio = ratio_actual
        return mejor_ratio * 100
    else:
        return SequenceMatcher(None, u_limpio, o_limpio).ratio() * 100

def comparar_palabras(texto_usuario, texto_original):
    def tokenizar(t): return re.findall(r'\w+', t.lower())
    palabras_usuario  = tokenizar(texto_usuario)
    palabras_original = tokenizar(texto_original)
    matcher = SequenceMatcher(None, palabras_usuario, palabras_original)
    html_usuario, html_original = [], []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            for w in palabras_usuario[i1:i2]: html_usuario.append(f'<span class="palabra-ok">{w}</span>')
            for w in palabras_original[j1:j2]: html_original.append(f'<span class="palabra-ok">{w}</span>')
        elif tag == 'replace':
            for w in palabras_usuario[i1:i2]: html_usuario.append(f'<span class="palabra-mal">{w}</span>')
            for w in palabras_original[j1:j2]: html_original.append(f'<span class="palabra-mal">{w}</span>')
        elif tag == 'delete':
            for w in palabras_usuario[i1:i2]: html_usuario.append(f'<span class="palabra-extra">{w}</span>')
        elif tag == 'insert':
            for w in palabras_original[j1:j2]: html_original.append(f'<span class="palabra-mal">▢ {w}</span>')
    return ' '.join(html_usuario), ' '.join(html_original)

def formatear_lineas(texto):
    frases = re.split(r'(?<=[.!?])\s+', texto.strip())
    return "<br>".join(frases)


# ── URL DE GOOGLE SHEET (Estructura de dos pestañas) ──
SHEET_FRASES_URL = "https://docs.google.com/spreadsheets/d/1hpP0J5qRrbx5p9W2nHWsoTDBA9hhvLZYblaU12Ln3w4/export?format=csv&gid=0"
SHEET_PROGRESO_URL = "https://docs.google.com/spreadsheets/d/1hpP0J5qRrbx5p9W2nHWsoTDBA9hhvLZYblaU12Ln3w4/gviz/tq?tqx=out:csv&sheet=Progreso"

@st.cache_data(ttl=1)
def cargar_datos_web():
    seed = random.randint(1, 100000)
    # Cargar Frases
    df_f = pd.read_csv(f"{SHEET_FRASES_URL}&nocache={seed}")
    df_f.columns = df_f.columns.str.strip()
    
    # Cargar Contador de Progreso Diario
    try:
        df_p = pd.read_csv(f"{SHEET_PROGRESO_URL}&nocache={seed}")
        df_p.columns = df_p.columns.str.strip()
    except Exception:
        df_p = pd.DataFrame(columns=['Fecha', 'Cantidad'])
        
    return df_f, df_p

try:
    df_total, df_progreso = cargar_datos_web()
except Exception as e:
    st.error(f"No se pudo conectar con el Google Sheet. Detalles: {e}")
    st.stop()


# ── CÁLCULO DEL CONTADOR GLOBAL DESDE EL EXCEL ──
hoy_str = str(date.today())
fila_hoy = df_progreso[df_progreso['Fecha'] == hoy_str]

if not fila_hoy.empty:
    contador_diario_excel = int(fila_hoy.iloc[0]['Cantidad'])
    if 'ultimo_contador_visto' in st.session_state and contador_diario_excel < st.session_state.ultimo_contador_visto:
        st.session_state.aviso_15_lanzado = False
    st.session_state.ultimo_contador_visto = contador_diario_excel
else:
    contador_diario_excel = 0
    st.session_state.aviso_15_lanzado = False


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
    st.session_state.ver_gramatica = False
    st.session_state.flash_aprendida = False

# --- LÓGICA DE LA RUEDA DE LOS 15 ---
df_activas_y_pendientes = df_isla_completa[df_isla_completa['Estado'] != 'Azul'].copy()
df_azul = df_isla_completa[df_isla_completa['Estado'] == 'Azul']
total_aprendidos = len(df_azul)

df_en_rueda = df_activas_y_pendientes.head(15).copy()
total_rueda_actual = len(df_en_rueda)

estados_rueda = df_en_rueda['Estado'].fillna('Rojo').tolist()
n_rojos   = estados_rueda.count('Rojo')
n_naranjas = estados_rueda.count('Naranja')
n_verdes  = estados_rueda.count('Verde')


# --- 🎯 OBJETIVO DIARIO (SINCRONIZADO MULTI-DISPOSITIVO) ---
st.sidebar.write("---")
st.sidebar.markdown("### 🎯 Objetivo Diario")

progreso_diario = min(contador_diario_excel / 15, 1.0)
color_diario = "#22a66e" if contador_diario_excel >= 15 else "#f5a623"

st.sidebar.markdown(f"""
<div style="font-family: 'Montserrat', sans-serif; background: rgba(255,255,255,0.04); padding: 14px 16px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.09); margin-bottom: 10px;">
    <p style="margin: 0 0 4px 0; font-size: 0.7rem; color: #8a9ab5; font-weight: 500; text-transform: uppercase; letter-spacing: 2px;">📅 HOY: {contador_diario_excel} / 15 frases</p>
    <div style="height: 5px; background: rgba(255,255,255,0.08); border-radius: 99px; overflow: hidden; margin-top: 8px;">
        <div style="height: 100%; width: {progreso_diario * 100}%; background: {color_diario}; border-radius: 99px; transition: width 0.4s ease;"></div>
    </div>
</div>
""", unsafe_allow_html=True)

if contador_diario_excel >= 15:
    st.sidebar.caption("✅ ¡Meta diaria cumplida en la nube!")


# --- RESUMEN SIDEBAR ---
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
            <div style="height: 100%; width: {porcentaje_isla}%; background: #3b7dd8; border-radius: 99px;"></div>
        </div>
        <p style="margin: 5px 0 0 0; font-size: 0.72rem; color: #8a9ab5; text-align: right;">{porcentaje_isla}% completada</p>
    </div>
</div>
""", unsafe_allow_html=True)


if total_aprendidos == total_frases_isla and total_frases_isla > 0:
    st.title("🇩🇪 Método de Chunks & Islas")
    st.balloons()
    st.success(f"🎉 ¡ESPECTACULAR! Has completado la isla '{isla_seleccionada}' al 100%.")
    st.stop()

if st.session_state.indice_actual >= total_rueda_actual:
    st.session_state.indice_actual = total_rueda_actual - 1 if total_rueda_actual > 0 else 0

# --- CONTENIDO PRINCIPAL ---
st.title("🇩🇪 Método de Chunks & Islas")

if 'aviso_15_lanzado' not in st.session_state:
    st.session_state.aviso_15_lanzado = False

if contador_diario_excel >= 15 and not st.session_state.aviso_15_lanzado:
    st.balloons()
    st.success("🎯 ¡Objetivo Diario Alcanzado! Has estudiado 15 frases hoy. ¡Gran trabajo!")
    st.session_state.aviso_15_lanzado = True

fila_actual = df_en_rueda.iloc[st.session_state.indice_actual]
castellano_texto = str(fila_actual['Castellano'])
aleman_texto     = str(fila_actual['Aleman'])

indice_fila_google_sheet = int(df_isla_completa.index[df_isla_completa['Castellano'] == castellano_texto].tolist()[0]) + 2

audio_id_raw = fila_actual['Audio_ID']
audio_id = "sin_audio" if pd.isna(audio_id_raw) else str(int(audio_id_raw)) if isinstance(audio_id_raw, float) else str(audio_id_raw).strip()

situacion_texto = str(fila_actual['Situacion']).strip() if 'Situacion' in fila_actual and pd.notna(fila_actual['Situacion']) else ""

pos_actual = st.session_state.indice_actual + 1
st.markdown(f'<div class="progreso-contador">{pos_actual} / {total_rueda_actual}</div>', unsafe_allow_html=True)
st.progress(pos_actual / total_rueda_actual)

if situacion_texto:
    st.markdown(f'<div class="titulo-situacion">📍 {situacion_texto}</div>', unsafe_allow_html=True)


# --- BOTONES DE CONTROL ---
col_nav_sol, col_nav_ant, col_nav_sig, col_nav_gram = st.columns([0.25, 0.25, 0.25, 0.25])
with col_nav_sol:
    if not st.session_state.ver_solucion:
        if st.button("👁️ Solución", use_container_width=True, key="sol"): st.session_state.ver_solucion = True; st.rerun()
    else:
        if st.button("🔄 Ocultar", use_container_width=True, key="ocultar"): st.session_state.ver_solucion = False; st.rerun()
with col_nav_ant:
    if st.button("⬅️ Anterior", use_container_width=True):
        if st.session_state.indice_actual > 0: st.session_state.indice_actual -= 1; st.session_state.ver_solucion = False; st.rerun()
with col_nav_sig:
    if st.button("Siguiente ➡️", use_container_width=True):
        if st.session_state.indice_actual < total_rueda_actual - 1: st.session_state.indice_actual += 1; st.session_state.ver_solucion = False; st.rerun()
with col_nav_gram:
    if st.button("💡 Gramática", use_container_width=True): st.session_state.ver_gramatica = not st.session_state.ver_gramatica; st.rerun()

if st.session_state.get('flash_aprendida'):
    st.markdown('<div class="flash-aprendida">✦ ¡Frase aprendida! 🔵</div>', unsafe_allow_html=True)
    st.session_state.flash_aprendida = False

if not st.session_state.ver_solucion:
    st.markdown(f'<div class="bloque-azul"><div class="texto-isla"><b>Castellano:</b><br><br>{formatear_lineas(castellano_texto)}</div></div>', unsafe_allow_html=True)
else:
    st.markdown(f'<div class="bloque-verde"><div class="texto-isla"><b>Solución en Alemán:</b><br><br>{formatear_lineas(aleman_texto)}</div></div>', unsafe_allow_html=True)


# --- BOTONES DE COLORES CON URL INTEGRADA ---
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
    # URL ÚNICA DE TU DESPLIEGUE GOOGLE APPS SCRIPT
    WEB_APP_URL = "https://script.google.com/macros/s/AKfycbyFp4YlESm0lgRW2-NPR-qQ45Shuns_cFHci01SnTskqBaaWbJWATXWNWqiJyoB0PxK/exec"
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

    st.session_state.ver_solucion = False
    st.session_state.ver_gramatica = False
    st.rerun()


# --- REPRODUCTOR DE AUDIO ---
ruta_audio = f"Audios/{audio_id}.mp3"
if os.path.exists(ruta_audio):
    st.write("🎧 **Onda de audio interactiva:**")
    with open(ruta_audio, "rb") as f: b64_audio = base64.b64encode(f.read()).decode()
    html_reproductor = f"""
    <div id="waveform"></div>
    <button id="btnPlay" style="background:#3b7dd8; color:white; border:none; padding:8px 20px; border-radius:6px; margin-top:10px; cursor:pointer;">▶ Play</button>
    <script src="https://unpkg.com/wavesurfer.js@7"></script>
    <script>
        const wavesurfer = WaveSurfer.create({{ container: '#waveform', waveColor: '#4a5568', progressColor: '#3b7dd8', height: 50, url: 'data:audio/mp3;base64,{b64_audio}' }});
        const btn = document.getElementById('btnPlay');
        btn.addEventListener('click', () => wavesurfer.playPause());
        wavesurfer.on('play', () => btn.innerHTML = "⏸ Pausa");
        wavesurfer.on('pause', () => btn.innerHTML = "▶ Play");
    </script>
    """
    st.components.v1.html(html_reproductor, height=130)
else:
    st.warning(f"⚠️ Audio no encontrado en: `{ruta_audio}`")


# --- MODO DICTADO Y GRAMÁTICA ---
with st.expander("📝 Modo Dictado"):
    texto_usuario = st.text_area("Escribe el texto en alemán:", key=f"dict_{st.session_state.indice_actual}", height=120)
    if st.button("🔍 Comprobar Dictado", use_container_width=True) and texto_usuario:
        porcentaje_acierto = calcular_similitud_parcial(texto_usuario, aleman_texto)
        st.metric("Acierto", f"{porcentaje_acierto:.0f}%")
        html_u, html_o = comparar_palabras(texto_usuario, aleman_texto)
        st.markdown(f"<div class='dictado-comparacion'><b>Tuyo:</b> {html_u}<br><b>Correcto:</b> {html_o}</div>", unsafe_allow_html=True)

if st.session_state.ver_gramatica and 'Explicacion' in fila_actual and pd.notna(fila_actual['Explicacion']):
    st.markdown(f"<div class='bloque-gramatica'><b>💡 Gramática:</b><br>{formatear_lineas(str(fila_actual['Explicacion']))}</div>", unsafe_allow_html=True)
