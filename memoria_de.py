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

# Inyectar la tipografía Montserrat y estilos adaptables
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght=400;600&display=swap');
    
    /* Forzar Montserrat de forma nativa y limpia en las tarjetas principales */
    .texto-isla, .texto-isla *, .texto-isla p, .texto-isla b {
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 400 !important;
        line-height: 1.6 !important;
        font-size: 1.15rem !important;
    }
    
    .titulo-situacion {
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 600 !important;
        font-size: 1rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: #718096;
        margin-bottom: 0.5rem;
    }
    
    /* Bloque Azul (Castellano) */
    .bloque-azul {
        background-color: rgba(28, 131, 225, 0.15);
        border-left: 5px solid rgb(28, 131, 225);
        padding: 1.2rem 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    
    /* Bloque Verde (Alemán) */
    .bloque-verde {
        background-color: rgba(33, 195, 84, 0.15);
        border-left: 5px solid rgb(33, 195, 84);
        padding: 1.2rem 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    
    /* Bloque Rojo Claro (Gramática) */
    .bloque-gramatica {
        background-color: rgba(239, 68, 68, 0.15);
        border-left: 5px solid #ef4444;
        padding: 1.2rem 1.5rem;
        border-radius: 0.5rem;
        margin-top: 1rem;
        margin-bottom: 1rem;
    }
    
    .texto-gramatica {
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 400 !important;
        line-height: 1.6;
        font-size: 1.15rem;
        margin: 0;
        padding: 0;
    }
    
    /* Nota de porcentaje de coincidencia */
    .resultado-porcentaje {
        font-family: 'Montserrat', sans-serif;
        font-size: 1.3rem;
        font-weight: 600;
        text-align: center;
        padding: 12px;
        border-radius: 8px;
        margin-top: 10px;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# FUNCIÓN: Comparación por ventanas de igual longitud
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

def formatear_lineas(texto):
    frases = re.split(r'(?<=[.!?])\s+', texto.strip())
    return "<br>".join(frases)

# URL de tu Google Sheet (Exportación dinámica en formato CSV)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1hpP0J5qRrbx5p9W2nHWsoTDBA9hhvLZYblaU12Ln3w4/export?format=csv"

# Cargar los datos desde Google Sheets en la nube
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

# --- BARRA LATERAL (PANEL IZQUIERDO) ---
st.sidebar.title("Configuración")
islas_disponibles = df_total['Isla'].unique()
isla_seleccionada = st.sidebar.selectbox("🏝️ Selecciona la Isla:", islas_disponibles)

# Filtrar las frases pertenecientes a la isla seleccionada
df_isla_completa = df_total[df_total['Isla'] == isla_seleccionada].copy()
total_frases_isla = len(df_isla_completa)

# Control de reinicio de estado al cambiar de isla
if 'isla_anterior' not in st.session_state or st.session_state.isla_anterior != isla_seleccionada:
    st.session_state.indice_actual = 0
    st.session_state.isla_anterior = isla_seleccionada
    st.session_state.ver_solucion = False
    st.session_state.ver_gramatica = False

# --- LOGICA DE LA RUEDA DE LOS 15 ---
df_activas_y_pendientes = df_isla_completa[df_isla_completa['Estado'] != 'Azul'].copy()
df_azul = df_isla_completa[df_isla_completa['Estado'] == 'Azul']
total_aprendidos = len(df_azul)

# Construimos la Rueda tomando estrictamente un máximo de 15 del bloque activo/pendiente
df_en_rueda = df_activas_y_pendientes.head(15).copy()
total_rueda_actual = len(df_en_rueda)

# Contar cuántos hay de cada color ESTRICTAMENTE dentro de los 15 máximos de la rueda en pantalla
estados_rueda = df_en_rueda['Estado'].fillna('Rojo').tolist()
n_rojos = estados_rueda.count('Rojo')
n_naranjas = estados_rueda.count('Naranja')
n_verdes = estados_rueda.count('Verde')

# --- RESUMEN EN EL PANEL IZQUIERDO ---
st.sidebar.write("---")
st.sidebar.markdown("### 📊 Estado de la Isla")

# Tarjeta sin puntos negros, estilizada, límitada a 15 y acumulado real global en azul
st.sidebar.markdown(f"""
<div style="font-family: 'Montserrat', sans-serif; background: rgba(255,255,255,0.05); padding: 14px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.1);">
    <p style="margin: 0 0 10px 0; font-size: 0.95rem; color: #cbd5e1; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">🔄 LOADING... ({total_rueda_actual}):</p>
    <div style="font-size: 1rem; margin-bottom: 6px;">🔴 {n_rojos} Malas / Nuevas</div>
    <div style="font-size: 1rem; margin-bottom: 6px;">🟠 {n_naranjas} A medias</div>
    <div style="font-size: 1rem; margin-bottom: 0px;">🟢 {n_verdes} Casi listas</div>
    <hr style="margin: 12px 0; border: 0; border-top: 1px solid rgba(255,255,255,0.15);">
    <p style="margin: 0; font-size: 1rem; font-weight: 600;">🔵 Aprendidos: <span style="color: #3b82f6;">{total_aprendidos}</span> / {total_frases_isla}</p>
</div>
""", unsafe_allow_html=True)


# ¿Está la isla completada al 100%?
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

# Extraer datos de la frase actual en la rueda
fila_actual = df_en_rueda.iloc[st.session_state.indice_actual]
castellano_texto = str(fila_actual['Castellano'])
aleman_texto = str(fila_actual['Aleman'])
estado_actual = str(fila_actual['Estado'])

# Encontrar la fila real de Google Sheets (Pandas index + 2)
indice_fila_google_sheet = int(df_isla_completa.index[df_isla_completa['Castellano'] == castellano_texto].tolist()[0]) + 2

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

st.progress((st.session_state.indice_actual + 1) / total_rueda_actual)

if situacion_texto:
    st.markdown(f'<div class="titulo-situacion">📍 {situacion_texto}</div>', unsafe_allow_html=True)


# --- 🔄 BARRA DE NAV / CONTROL ---
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
    if st.button("⬅️ Anterior", use_container_width=True, key="btn_anterior_arriba"):
        if st.session_state.indice_actual > 0:
            st.session_state.indice_actual -= 1
            st.session_state.ver_solucion = False
            st.session_state.ver_gramatica = False
            st.rerun()

with col_nav_sig:
    if st.button("Siguiente ➡️", use_container_width=True, key="btn_siguiente_arriba"):
        if st.session_state.indice_actual < total_rueda_actual - 1:
            st.session_state.indice_actual += 1
            st.session_state.ver_solucion = False
            st.session_state.ver_gramatica = False
            st.rerun()

with col_nav_gram:
    if st.button("💡 Gramática", use_container_width=True, key="btn_gramatica_arriba"):
        st.session_state.ver_gramatica = not st.session_state.ver_gramatica
        st.rerun()

st.write("")

# Renderizado de la Tarjeta con la estructura de divs original para asegurar la fuente Montserrat limpia
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


# --- 🎛️ BOTONES DE COLORES ULTRA LIMPIOS 🎛️ ---
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
    # URL de tu Web App de Google Apps Script
    WEB_APP_URL = "https://script.google.com/macros/s/AKfycbzxuhVMl8swR7fJHyd5dXt0WCXTpHoSWUrLxxKpRF3Bcwt2lo09vSvkDiAeWymV3F7l/exec"
    
    try:
        requests.post(WEB_APP_URL, params={"row": indice_fila_google_sheet, "status": nuevo_estado})
    except Exception:
        pass
    
    st.cache_data.clear()
    
    if nuevo_estado != "Azul" and st.session_state.indice_actual < total_rueda_actual - 1:
        st.session_state.indice_actual += 1
        
    st.session_state.ver_solucion = False
    st.session_state.ver_gramatica = False
    st.rerun()


# --- 🎧 REPRODUCTOR CON ONDA + VELOCIDAD POR DÉCIMAS 🎧 ---
ruta_audio = f"Audios/{audio_id}.mp3"
if os.path.exists(ruta_audio):
    st.write("🎧 **Onda de audio interactiva:**")
    
    with open(ruta_audio, "rb") as f:
        audio_bytes = f.read()
    b64_audio = base64.b64encode(audio_bytes).decode()
    
    html_reproductor = f"""
    <div style="font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.15); padding: 12px; border-radius: 12px; color: #ffffff; box-sizing: border-box;">
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
            container: '#waveform',
            waveColor: '#64748b',
            progressColor: '#3b82f6',
            cursorColor: '#f43f5e',
            barWidth: 2,
            barGap: 2,
            barRadius: 2,
            height: 65,
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
            btnPlay.innerHTML = "⏸️ Pausa";
            btnPlay.style.background = "#22c55e"; 
        }});
        wavesurfer.on('pause', () => {{
            btnPlay.innerHTML = "▶️ Play";
            btnPlay.style.background = "#1c83e1"; 
        }});

        document.getElementById('btnBack').addEventListener('click', () => {{ wavesurfer.skip(-5); }});
        document.getElementById('btnForward').addEventListener('click', () => {{ wavesurfer.skip(5); }});

        const speedSlider = document.getElementById('speedSlider');
        const speedValue = document.getElementById('speedValue');

        speedSlider.addEventListener('input', (e) => {{
            const currentSpeed = parseFloat(e.target.value);
            wavesurfer.setPlaybackRate(currentSpeed);
            speedValue.innerHTML = currentSpeed.toFixed(1) + "x";
        }});
        wavesurfer.on('ready', () => {{ wavesurfer.setPlaybackRate(parseFloat(speedSlider.value)); }});
    </script>
    """
    st.components.v1.html(html_reproductor, height=215)
else:
    st.warning(f"⚠️ Audio no encontrado en: `{ruta_audio}`")


# --- DESPLEGABLE DE DICTADO ---
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


# --- 💡 EXPLICACIÓN ---
if st.session_state.ver_gramatica:
    if 'Explicacion' in fila_actual and pd.notna(fila_actual['Explicacion']) and str(fila_actual['Explicacion']).strip() != "":
        explicacion_formateada = formatear_lineas(str(fila_actual['Explicacion']))
        st.markdown(f"""
        <div class="bloque-gramatica">
            <div class="texto-gramatica">
                <b>💡 Explicación Gramatical:</b><br><br>
                {explicacion_formateada}
            </div>
        </div>
        """, unsafe_allow_html=True)
