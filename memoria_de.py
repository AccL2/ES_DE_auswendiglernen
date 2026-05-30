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

# --- 🌐 ENLACES DE TU CONFIGURACIÓN ---
# Tu Google Sheet exportado dinámicamente como CSV para leerlo al instante
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1hpP0J5qRrbx5p9W2nHWsoTDBA9hhvLZYblaU12Ln3w4/export?format=csv&gid=0"
# Tu Web App de Google para guardar los estados y el contador diario
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbxT5tzluJTlMl8dW0Ps-v93F672sG4Fn8ajDBrdoeitbQBFyqqrW_udtjwuD47glvUX/exec"

# Inyectar la tipografía Montserrat y estilos premium adaptables
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght=300;400;500;600;700&display=swap');
    
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

    .titulo-situacion {
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 500 !important;
        font-size: 0.75rem !important;
        text-transform: uppercase;
        letter-spacing: 2px;
        color: #8a9ab5;
        margin-bottom: 0.75rem;
    }
    
    .texto-isla {
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 400 !important;
        line-height: 1.8 !important;
        font-size: 1.25rem !important;
    }

    .bloque-azul {
        background: var(--azul-bg);
        border: 1px solid var(--azul-borde);
        border-left: 4px solid var(--azul);
        padding: 1.4rem 1.6rem;
        border-radius: var(--radio);
        margin-bottom: 1rem;
    }
    
    .bloque-verde {
        background: var(--verde-bg);
        border: 1px solid var(--verde-borde);
        border-left: 4px solid var(--verde);
        padding: 1.4rem 1.6rem;
        border-radius: var(--radio);
        margin-bottom: 1rem;
    }
    
    .bloque-gramatica {
        background: var(--rojo-bg);
        border: 1px solid var(--rojo-borde);
        border-left: 4px solid var(--rojo);
        padding: 1.4rem 1.6rem;
        border-radius: var(--radio);
        margin-top: 0.75rem;
        margin-bottom: 1rem;
    }
    
    .resultado-porcentaje {
        font-family: 'Montserrat', sans-serif;
        font-size: 1.3rem;
        font-weight: 600;
        text-align: center;
        padding: 12px;
        border-radius: var(--radio);
        margin-top: 10px;
        margin-bottom: 10px;
    }

    .progreso-contador {
        font-family: 'Montserrat', sans-serif;
        font-size: 0.72rem;
        font-weight: 500;
        color: #8a9ab5;
        text-align: right;
        margin-bottom: 4px;
    }

    .flash-aprendida {
        border-radius: var(--radio);
        padding: 1rem 1.4rem;
        text-align: center;
        font-family: 'Montserrat', sans-serif;
        color: #22a66e;
        border: 1px solid rgba(34, 166, 110, 0.35);
        margin-bottom: 1rem;
        background: rgba(34, 166, 110, 0.05);
    }
    </style>
""", unsafe_allow_html=True)

# FUNCIÓN: Comparación por ventanas de igual longitud para el dictado
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

def formatear_lineas(texto):
    frases = re.split(r'(?<=[.!?])\s+', texto.strip())
    return "<br>".join(frases)

# Cargar los datos desde Google Sheets en tiempo real de forma segura
@st.cache_data(ttl=1)
def cargar_datos_sistema():
    try:
        # Carga directa de la nube sin depender de archivos locales
        df = pd.read_csv(SHEET_CSV_URL)
    except Exception as e:
        # Respaldo si falla la conexión a internet
        if os.path.exists("frases.xlsx"):
            df = pd.read_excel("frases.xlsx")
        else:
            df = pd.DataFrame(columns=['Isla', 'Castellano', 'Aleman', 'Audio_ID', 'Situacion', 'Explicacion', 'Estado'])
        
    df.columns = df.columns.str.strip()
    
    # Blindar las columnas requeridas para evitar KeyErrors accidentales
    columnas_requeridas = ['Isla', 'Castellano', 'Aleman', 'Audio_ID', 'Situacion', 'Explicacion', 'Estado']
    for col in columnas_requeridas:
        if col not in df.columns:
            df[col] = 'Rojo' if col == 'Estado' else ""

    # Obtener el progreso del objetivo diario desde la Web App
    try:
        respuesta = requests.get(WEB_APP_URL, params={"getContador": "true"}, timeout=4)
        contador = respuesta.json().get("contador", 0)
    except Exception:
        contador = 0
        
    return df, contador

try:
    df_total, contador_diario = cargar_datos_sistema()
except Exception as e:
    st.error(f"No se pudo inicializar la base de datos remota. Error: {e}")
    st.stop()

# --- BARRA LATERAL ---
st.sidebar.title("Configuración")
islas_disponibles = df_total['Isla'].dropna().unique() if len(df_total['Isla'].dropna().unique()) > 0 else ["Sin Islas"]
isla_seleccionada = st.sidebar.selectbox("🏝️ Selecciona la Isla:", islas_disponibles)

df_isla_completa = df_total[df_total['Isla'] == isla_seleccionada].copy()
total_frases_isla = len(df_isla_completa)

if 'isla_anterior' not in st.session_state or st.session_state.isla_anterior != isla_seleccionada:
    st.session_state.indice_actual = 0
    st.session_state.isla_anterior = isla_seleccionada
    st.session_state.ver_solucion = False
    st.session_state.ver_gramatica = False
    st.session_state.flash_aprendida = False

# --- LÓGICA DE LA RUEDA DINÁMICA DE LOS 15 CHUNKS ---
df_activas_y_pendientes = df_isla_completa[df_isla_completa['Estado'].astype(str).str.strip() != 'Azul'].copy()
df_azul = df_isla_completa[df_isla_completa['Estado'].astype(str).str.strip() == 'Azul']
total_aprendidos = len(df_azul)

df_en_rueda = df_activas_y_pendientes.head(15).copy()
total_rueda_actual = len(df_en_rueda)

if total_rueda_actual > 0:
    estados_rueda = df_en_rueda['Estado'].fillna('Rojo').astype(str).str.strip().tolist()
    n_rojos   = estados_rueda.count('Rojo')
    n_naranjas = estados_rueda.count('Naranja')
    n_verdes  = estados_rueda.count('Verde')
else:
    n_rojos = n_naranjas = n_verdes = 0

# --- 🎯 OBJETIVO DIARIO ---
st.sidebar.write("---")
st.sidebar.markdown("### 🎯 Objetivo Diario")
progreso_diario = min(contador_diario / 15, 1.0)
color_diario = "#22a66e" if contador_diario >= 15 else "#f5a623"

st.sidebar.markdown(f"""
<div style="background: rgba(255,255,255,0.04); padding: 14px 16px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.09); margin-bottom: 10px;">
    <p style="margin: 0 0 4px 0; font-size: 0.7rem; color: #8a9ab5; font-weight: 500; text-transform: uppercase; letter-spacing: 2px;">📅 HOY: {contador_diario} / 15 frases</p>
    <div style="height: 5px; background: rgba(255,255,255,0.08); border-radius: 99px; overflow: hidden; margin-top: 8px;">
        <div style="height: 100%; width: {progreso_diario * 100}%; background: {color_diario}; border-radius: 99px;"></div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- RESUMEN DE LA ISLA ---
st.sidebar.markdown("### 📊 Estado de la Isla")
porcentaje_isla = round((total_aprendidos / total_frases_isla * 100)) if total_frases_isla > 0 else 0

st.sidebar.markdown(f"""
<div style="background: rgba(255,255,255,0.04); padding: 16px 18px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.09);">
    <p style="margin: 0 0 12px 0; font-size: 0.7rem; color: #8a9ab5; font-weight: 500; text-transform: uppercase; letter-spacing: 2px;">🔄 En rueda &nbsp;·&nbsp; {total_rueda_actual}</p>
    <div style="display: flex; flex-direction: column; gap: 8px;">
        <div style="display:flex; align-items:center; gap:10px; font-size:0.9rem;">
            <span style="width:10px;height:10px;border-radius:50%;background:#e05454;display:inline-block;"></span>
            <span>{n_rojos} &nbsp;<span style="color:#8a9ab5;font-size:0.8rem;">Malas / Nuevas</span></span>
        </div>
        <div style="display:flex; align-items:center; gap:10px; font-size:0.9rem;">
            <span style="width:10px;height:10px;border-radius:50%;background:#f5a623;display:inline-block;"></span>
            <span>{n_naranjas} &nbsp;<span style="color:#8a9ab5;font-size:0.8rem;">A medias</span></span>
        </div>
        <div style="display:flex; align-items:center; gap:10px; font-size:0.9rem;">
            <span style="width:10px;height:10px;border-radius:50%;background:#22a66e;display:inline-block;"></span>
            <span>{n_verdes} &nbsp;<span style="color:#8a9ab5;font-size:0.8rem;">Casi listas</span></span>
        </div>
    </div>
    <div style="margin: 14px 0 0 0; padding-top: 12px; border-top: 1px solid rgba(255,255,255,0.08); display:flex; align-items:center; justify-content:space-between;">
        <span style="color:#8a9ab5; font-size:0.8rem;">🔵 Aprendidas</span>
        <span style="font-size:1rem; font-weight:600; color:#3b7dd8;">{total_aprendidos}<span style="color:#8a9ab5; font-weight:400; font-size:0.82rem;"> / {total_frases_isla}</span></span>
    </div>
</div>
""", unsafe_allow_html=True)

if total_frases_isla > 0 and total_aprendidos == total_frases_isla:
    st.title("🇩🇪 Método de Chunks & Islas")
    st.balloons()
    st.success(f"🎉 ¡ESPECTACULAR! Has completado la isla '{isla_seleccionada}' al 100%.")
    st.stop()

if st.session_state.indice_actual >= total_rueda_actual:
    st.session_state.indice_actual = total_rueda_actual - 1 if total_rueda_actual > 0 else 0

# --- CONTENIDO PRINCIPAL ---
st.title("🇩🇪 Método de Chunks & Islas")

if total_rueda_actual == 0:
    st.info("🏝️ No hay frases disponibles o todas han sido marcadas como Aprendidas (Azul). ¡Excelente trabajo!")
    st.stop()

if contador_diario >= 15 and not st.session_state.get('aviso_diario_mostrado', False):
    st.balloons()
    st.success("🎯 ¡Objetivo Diario Alcanzado en la nube! Completaste tus 15 frases de hoy.")
    st.session_state.aviso_diario_mostrado = True

fila_actual = df_en_rueda.iloc[st.session_state.indice_actual]
castellano_texto = str(fila_actual['Castellano'])
aleman_texto     = str(fila_actual['Aleman'])

# Calcular de forma precisa la fila real de Google Sheets (Contando cabecera y desfase 2)
indices_match = df_total[df_total['Castellano'] == castellano_texto].index
indice_fila_excel = int(indices_match[0]) + 2 if len(indices_match) > 0 else 2

audio_id_raw = fila_actual['Audio_ID']
audio_id = "sin_audio" if pd.isna(audio_id_raw) else str(int(audio_id_raw)) if isinstance(audio_id_raw, float) else str(audio_id_raw).strip()

situacion_texto = str(fila_actual['Situacion']).strip() if 'Situacion' in fila_actual and pd.notna(fila_actual['Situacion']) else ""

pos_actual = st.session_state.indice_actual + 1
st.markdown(f'<div class="progreso-contador">{pos_actual} / {total_rueda_actual}</div>', unsafe_allow_html=True)
st.progress(pos_actual / total_rueda_actual)

if situacion_texto:
    st.markdown(f'<div class="titulo-situacion">📍 {situacion_texto}</div>', unsafe_allow_html=True)

# --- 🔄 MANDOS DE NAVEGACIÓN ---
col_nav_sol, col_nav_ant, col_nav_sig, col_nav_gram = st.columns([0.25, 0.25, 0.25, 0.25])
with col_nav_sol:
    if not st.session_state.ver_solucion:
        if st.button("👁️ Solución", use_container_width=True, key="sol"): st.session_state.ver_solucion = True; st.rerun()
    else:
        if st.button("🔄 Ocultar", use_container_width=True, key="ocultar"): st.session_state.ver_solucion = False; st.rerun()
with col_nav_ant:
    if st.button("⬅️ Anterior", use_container_width=True):
        if st.session_state.indice_actual > 0: st.session_state.indice_actual -= 1; st.session_state.ver_solucion = False; st.session_state.ver_gramatica = False; st.rerun()
with col_nav_sig:
    if st.button("Siguiente ➡️", use_container_width=True):
        if st.session_state.indice_actual < total_rueda_actual - 1: st.session_state.indice_actual += 1; st.session_state.ver_solucion = False; st.session_state.ver_gramatica = False; st.rerun()
with col_nav_gram:
    if st.button("💡 Gramática", use_container_width=True): st.session_state.ver_gramatica = not st.session_state.ver_gramatica; st.rerun()

if st.session_state.get('flash_aprendida'):
    st.markdown('<div class="flash-aprendida">✦ ¡Frase guardada en tu Google Sheet! 🔵</div>', unsafe_allow_html=True)
    st.session_state.flash_aprendida = False

# Renderizado de Paneles de texto
if not st.session_state.ver_solucion:
    st.markdown(f'<div class="bloque-azul"><div class="texto-isla"><b>Castellano (Lee y piensa):</b><br><br>{formatear_lineas(castellano_texto)}</div></div>', unsafe_allow_html=True)
else:
    st.markdown(f'<div class="bloque-verde"><div class="texto-isla"><b>Solución en Alemán:</b><br><br>{formatear_lineas(aleman_texto)}</div></div>', unsafe_allow_html=True)

# --- 🎛️ BOTONES DE ACTUALIZACIÓN DE ESTADOS (NUBE) ---
col_c1, col_c2, col_c3, col_c4 = st.columns(4)
nuevo_estado = None
with col_c1:
    if st.button("🔴 Malas / Nuevas", use_container_width=True): nuevo_estado = "Rojo"
with col_c2:
    if st.button("🟠 A medias", use_container_width=True): nuevo_estado = "Naranja"
with col_c3:
    if st.button("🟢 Casi listas", use_container_width=True): nuevo_estado = "Verde"
with col_c4:
    if st.button("🔵 Aprendidas", use_container_width=True): nuevo_estado = "Azul"

if nuevo_estado:
    try:
        # Enviar cambio de estado y sumarle al contador diario en la nube al unísono
        requests.post(WEB_APP_URL, params={
            "row": indice_fila_excel, 
            "status": nuevo_estado,
            "sumarContador": "true"
        }, timeout=4)
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

# --- 🎧 REPRODUCTOR PREMIUM CON SELECCIÓN DE ONDA Y VELOCIDAD ---
ruta_audio = f"Audios/{audio_id}.mp3"
if os.path.exists(ruta_audio):
    st.write("🎧 **Arrastra sobre la onda para hacer bucles. Haz clic fuera para limpiar:**")
    with open(ruta_audio, "rb") as f: b64_audio = base64.b64encode(f.read()).decode()
    
    html_reproductor = f"""
    <div style="background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.15); padding: 12px; border-radius: 12px; color: #ffffff; box-sizing: border-box;">
        <div id="waveform" style="margin-bottom: 12px; background: rgba(0, 0, 0, 0.2); border-radius: 6px; padding: 4px; cursor: pointer;"></div>
        <div style="display: flex; justify-content: center; align-items: center; gap: 10px; flex-wrap: wrap; margin-bottom: 12px;">
            <button id="btnBack" style="padding: 6px 12px; background: #475569; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: bold; font-size: 0.85rem;">⏮️ -5s</button>
            <button id="btnPlay" style="padding: 8px 20px; background: #1c83e1; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: bold; font-size: 0.95rem; min-width: 90px;">▶️ Play</button>
            <button id="btnForward" style="padding: 6px 12px; background: #475569; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: bold; font-size: 0.85rem;">+5s ⏭️</button>
            <button id="btnResetRegion" style="padding: 6px 12px; background: #dc2626; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: bold; font-size: 0.85rem;">Reset 🔄</button>
        </div>
        <div style="display: flex; align-items: center; justify-content: center; gap: 12px; background: rgba(0,0,0,0.15); padding: 6px 12px; border-radius: 8px;">
            <label for="speedSlider" style="font-size: 0.8rem; font-weight: bold; color: #cbd5e1; min-width: 120px;">⚡ Velocidad:</label>
            <input type="range" id="speedSlider" min="0.5" max="2.0" step="0.1" value="1.0" style="flex-grow: 1; cursor: pointer; accent-color: #1c83e1; margin: 0;">
            <span id="speedValue" style="font-size: 0.85rem; font-weight: bold; color: #3b82f6; min-width: 40px; text-align: right;">1.0x</span>
        </div>
    </div>
    <script src="https://unpkg.com/wavesurfer.js@7"></script>
    <script src="https://unpkg.com/wavesurfer.js@7/dist/plugins/regions.min.js"></script>
    <script>
        const wavesurfer = WaveSurfer.create({{
            container: '#waveform', waveColor: '#64748b', progressColor: '#3b82f6',
            cursorColor: '#f43f5e', barWidth: 2, barGap: 2, barRadius: 2, height: 65,
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
                if (currentTime >= activeRegion.end || currentTime < activeRegion.start) wavesurfer.setTime(activeRegion.start);
            }}
        }});
        wavesurfer.on('interaction', () => {{
            setTimeout(() => {{
                const regions = wsRegions.getRegions();
                if (regions.length > 0) {{
                    const currentTime = wavesurfer.getCurrentTime();
                    const activeRegion = regions[0];
                    if (currentTime < activeRegion.start || currentTime > activeRegion.end) wsRegions.clearRegions();
                }}
            }}, 50);
        }});
        document.getElementById('btnResetRegion').addEventListener('click', () => wsRegions.clearRegions());
        const btnPlay = document.getElementById('btnPlay');
        btnPlay.addEventListener('click', () => wavesurfer.playPause());
        wavesurfer.on('play', () => {{ btnPlay.innerHTML = "⏸️ Pausa"; btnPlay.style.background = "#22c55e"; }});
        wavesurfer.on('pause', () => {{ btnPlay.innerHTML = "▶️ Play"; btnPlay.style.background = "#1c83e1"; }});
        document.getElementById('btnBack').addEventListener('click', () => wavesurfer.skip(-5));
        document.getElementById('btnForward').addEventListener('click', () => wavesurfer.skip(5));
        const speedSlider = document.getElementById('speedSlider');
        const speedValue = document.getElementById('speedValue');
        speedSlider.addEventListener('input', (e) => {{
            const currentSpeed = parseFloat(e.target.value);
            wavesurfer.setPlaybackRate(currentSpeed);
            speedValue.innerHTML = currentSpeed.toFixed(1) + "x";
        }});
    </script>
    """
    st.components.v1.html(html_reproductor, height=215)
else:
    st.warning(f"⚠️ Audio no encontrado para el ID: `{audio_id}`")

# --- DESPLEGABLE DE DICTADO ---
with st.expander("📝 Modo Dictado: Haz clic aquí para escribir lo que oyes"):
    texto_usuario = st.text_area("Escribe el texto en alemán:", key=f"input_dictado_{st.session_state.indice_actual}", height=120)
    if st.button("🔍 Comprobar Dictado", use_container_width=True):
        if texto_usuario:
            porcentaje_acierto = calcular_similitud_parcial(texto_usuario, aleman_texto)
            if porcentaje_acierto >= 90: color_fondo, color_texto = "rgba(16, 185, 129, 0.15)", "#10b981"
            elif porcentaje_acierto >= 50: color_fondo, color_texto = "rgba(245, 158, 11, 0.15)", "#f59e0b"
            else: color_fondo, color_texto = "rgba(239, 68, 68, 0.15)", "#ef4444"
            st.markdown(f'<div class="resultado-porcentaje" style="background-color: {color_fondo}; color: {color_texto}; border: 1px solid {color_texto};">De lo que has escrito: {porcentaje_acierto:.0f}% bien</div>', unsafe_allow_html=True)

# --- 💡 EXPLICACIÓN GRAMATICAL ---
if st.session_state.ver_gramatica:
    if 'Explicacion' in fila_actual and pd.notna(fila_actual['Explicacion']) and str(fila_actual['Explicacion']).strip() != "":
        st.markdown(f'<div class="bloque-gramatica"><div class="texto-gramatica"><b>💡 Explicación Gramatical:</b><br><br>{formatear_lineas(str(fila_actual['Explicacion']))}</div></div>', unsafe_allow_html=True)
    else:
        st.info("ℹ️ No hay ninguna explicación cargada para esta frase en el Google Sheet.")
