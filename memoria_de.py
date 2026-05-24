import streamlit as st
import pandas as pd
import os
import re
import random
import base64
from difflib import SequenceMatcher

# Configuración de la página
st.set_page_config(page_title="Entrenador de Idiomas por Islas", page_icon="🇩🇪", layout="centered")

# Inyectar la tipografía Montserrat y estilos adaptables
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght=400;600&display=swap');
    
    .texto-isla {
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 400 !important;
        line-height: 1.6;
        font-size: 1.15rem;
        margin: 0;
        padding: 0;
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

# Cargar la base de datos de Excel
@st.cache_data(ttl=10)
def cargar_datos():
    df = pd.read_excel("frases.xlsx")
    df.columns = df.columns.str.strip()
    return df

try:
    df_total = cargar_datos()
except Exception as e:
    st.error(f"No se pudo cargar el archivo 'frases.xlsx'. Error: {e}")
    st.stop()

# --- BARRA LATERAL ---
st.sidebar.title("Configuración")
islas_disponibles = df_total['Isla'].unique()
isla_seleccionada = st.sidebar.selectbox("🏝️ Selecciona la Isla:", islas_disponibles)

df_isla_original = df_total[df_total['Isla'] == isla_seleccionada].reset_index(drop=True)
total_frases = len(df_isla_original)

if 'isla_anterior' not in st.session_state or st.session_state.isla_anterior != isla_seleccionada:
    st.session_state.indice_actual = 0
    st.session_state.isla_anterior = isla_seleccionada
    st.session_state.ver_solucion = False
    st.session_state.completado = False
    if 'orden_aleatorio' in st.session_state:
        del st.session_state.orden_aleatorio

modo_aleatorio = st.sidebar.toggle("🔀 Activar orden aleatorio")

if modo_aleatorio:
    if 'orden_aleatorio' not in st.session_state:
        indices_mezclados = list(range(total_frases))
        random.shuffle(indices_mezclados)
        st.session_state.orden_aleatorio = indices_mezclados
        st.session_state.indice_actual = 0  
        st.session_state.ver_solucion = False
    df_isla = df_isla_original.iloc[st.session_state.orden_aleatorio].reset_index(drop=True)
else:
    if 'orden_aleatorio' in st.session_state:
        del st.session_state.orden_aleatorio
        st.session_state.indice_actual = 0  
        st.session_state.ver_solucion = False
    df_isla = df_isla_original

if 'indice_actual' not in st.session_state:
    st.session_state.indice_actual = 0

if 'ver_solucion' not in st.session_state:
    st.session_state.ver_solucion = False

if st.session_state.indice_actual >= total_frases:
    st.session_state.indice_actual = total_frases - 1 if total_frases > 0 else 0

opciones_frases = [f"Frase {i+1}" for i in range(total_frases)]
frase_seleccionada_nav = st.sidebar.selectbox(
    "🎯 Ir a frase específica:", 
    options=opciones_frases, 
    index=int(st.session_state.indice_actual),
    key=f"nav_selector_{st.session_state.indice_actual}"
)

nuevo_indice = opciones_frases.index(frase_seleccionada_nav)
if nuevo_indice != st.session_state.indice_actual:
    st.session_state.indice_actual = nuevo_indice
    st.session_state.ver_solucion = False
    st.rerun()

# --- CONTENIDO PRINCIPAL ---
st.title("🇩🇪 Método de Chunks & Islas")

if st.session_state.indice_actual >= total_frases - 1 and st.session_state.get('completado', False):
    st.success("🎉 ¡Enhorabuena! Has completado todas las frases de esta isla.")
    if st.button("Repetir Isla (Volver a empezar)", use_container_width=True):
        st.session_state.indice_actual = 0
        st.session_state.ver_solucion = False
        st.session_state.completado = False
        if 'orden_aleatorio' in st.session_state:
            del st.session_state.orden_aleatorio
        st.rerun()
    st.stop()

fila_actual = df_isla.iloc[st.session_state.indice_actual]
castellano_texto = str(fila_actual['Castellano'])
aleman_texto = str(fila_actual['Aleman'])

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

def formatear_lineas(texto):
    frases = re.split(r'(?<=[.!?])\s+', texto.strip())
    return "<br>".join(frases)

st.subheader(f"Progreso: Frase {st.session_state.indice_actual + 1} de {total_frases}")
st.progress((st.session_state.indice_actual + 1) / total_frases)

if situacion_texto:
    st.markdown(f'<div class="titulo-situacion">📍 Situación: {situacion_texto}</div>', unsafe_allow_html=True)


# --- 🔄 FILA COMPARTIDA DE BOTONES INTERNOS (Para Streamlit) ---
# Creamos únicamente las columnas de solución, anterior y siguiente para Streamlit, dejando el espacio para el audio síncrono.
col_nav_play, col_nav_sol, col_nav_ant, col_nav_sig, col_vacio = st.columns([0.20, 0.20, 0.20, 0.20, 0.20])

# El botón de play físico real de Streamlit se omite arriba y se inyecta nativamente abajo
# para que no refresque la app al pausar y reanudar.

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
        if st.session_state.indice_actual < total_frases - 1:
            st.session_state.indice_actual += 1
            st.session_state.ver_solucion = False
        else:
            st.session_state.completado = True
        st.rerun()

st.write("")

# Renderizado de la Tarjeta de texto
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


# --- 🎧 REPRODUCTOR AVANZADO CON INTEGRACIÓN DE BOTÓN SUPERIOR FLUIDO 🎧 ---
ruta_audio = f"Audios/{audio_id}.mp3"
if os.path.exists(ruta_audio):
    st.write("🎧 **Arrastra sobre la onda para bucle. Haz un clic normal fuera de la selección o pulsa el botón Reset para volver a escuchar todo:**")
    
    with open(ruta_audio, "rb") as f:
        audio_bytes = f.read()
    b64_audio = base64.b64encode(audio_bytes).decode()
    
    # Inyectamos mediante JavaScript un espejo del botón en la parte superior exacta donde estaba
    html_reproductor = f"""
    <div id="control-superior-audio" style="position: fixed; top: -1000px;"></div>
    
    <script>
        // Clonamos dinámicamente el botón de Play/Pause en la barra superior de Streamlit en tiempo real
        window.addEventListener('DOMContentLoaded', () => {{
            setTimeout(() => {{
                // Buscamos la columna vacía que Streamlit preparó arriba para el audio (la primera columna)
                const colBotones = window.parent.document.querySelectorAll('[data-testid="stHorizontalBlock"] button');
                // Encontramos el contenedor del primer botón para inyectar nuestro disparador síncrono justo ahí
                const primerColumna = window.parent.document.querySelector('[data-testid="stHorizontalBlock"] [data-testid="column"]');
                
                if (primerColumna && !window.parent.document.getElementById('btn-play-nativo-arriba')) {{
                    const btnArriba = window.parent.document.createElement('button');
                    btnArriba.id = 'btn-play-nativo-arriba';
                    btnArriba.innerHTML = '▶️/⏸️ Audio';
                    btnArriba.style.width = '100%';
                    btnArriba.style.padding = '6px 0px';
                    btnArriba.style.backgroundColor = '#262730';
                    btnArriba.style.color = 'white';
                    btnArriba.style.border = '1px solid rgba(49, 51, 63, 0.2)';
                    btnArriba.style.borderRadius = '4px';
                    btnArriba.style.cursor = 'pointer';
                    btnArriba.style.fontSize = '14px';
                    btnArriba.style.height = '38px';
                    btnArriba.style.boxSizing = 'border-box';
                    
                    btnArriba.onclick = () => {{
                        document.getElementById('btnPlay').click();
                    }};
                    
                    // Reemplazamos visualmente o añadimos en la primera posición
                    primerColumna.insertBefore(btnArriba, primerColumna.firstChild);
                }}
            }}, 150);
        }});
    </script>

    <div style="font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.15); padding: 12px; border-radius: 12px; color: #ffffff; box-sizing: border-box;">
        <div id="waveform" style="margin-bottom: 12px; background: rgba(0, 0, 0, 0.2); border-radius: 6px; padding: 4px; cursor: pointer;"></div>
        
        <div style="display: flex; justify-content: center; align-items: center; gap: 10px; flex-wrap: wrap; margin-bottom: 12px;">
            <button id="btnBack" style="padding: 6px 12px; background: #475569; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: bold; font-size: 0.85rem;">⏮️ -5s</button>
            <button id="btnPlay" style="padding: 8px 20px; background: #1c83e1; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: bold; font-size: 0.95rem; min-width: 90px;">▶️ Play</button>
            <button id="btnForward" style="padding: 6px 12px; background: #475569; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: bold; font-size: 0.85rem;">+5s ⏭️</button>
            <button id="btnResetRegion" style="padding: 6px 12px; background: #dc2626; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: bold; font-size: 0.85rem;">Reset 🔄</button>
        </div>

        <div style="display: flex; align-items: center; justify-content: center; gap: 12px; background: rgba(0,0,0,0.15); padding: 6px 12px; border-radius: 8px;">
            <label for="speedSlider" style="font-size: 0.8rem; font-weight: bold; color: #cbd5e1; min-width: 120px;">⚡ Velocidad de audio:</label>
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

        wsRegions.enableDragSelection({{
            color: 'rgba(59, 130, 246, 0.3)'
        }});

        wsRegions.on('region-created', (region) => {{
            wsRegions.getRegions().forEach(r => {{
                if (r !== region) r.remove();
            }});
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

        document.getElementById('btnResetRegion').addEventListener('click', () => {{
            wsRegions.clearRegions();
        }});

        const btnPlay = document.getElementById('btnPlay');
        btnPlay.addEventListener('click', () => {{
            wavesurfer.playPause();
        }});

        wavesurfer.on('play', () => {{
            btnPlay.innerHTML = "⏸️ Pausa";
            btnPlay.style.background = "#22c55e"; 
            // Sincronizamos el botón espejo de arriba si existe
            const btnSup = window.parent.document.getElementById('btn-play-nativo-arriba');
            if (btnSup) btnSup.innerHTML = "⏸️ Pausa";
        }});

        wavesurfer.on('pause', () => {{
            btnPlay.innerHTML = "▶️ Play";
            btnPlay.style.background = "#1c83e1"; 
            // Sincronizamos el botón espejo de arriba si existe
            const btnSup = window.parent.document.getElementById('btn-play-nativo-arriba');
            if (btnSup) btnSup.innerHTML = "▶️/⏸️ Audio";
        }});

        document.getElementById('btnBack').addEventListener('click', () => {{
            wavesurfer.skip(-5);
        }});

        document.getElementById('btnForward').addEventListener('click', () => {{
            wavesurfer.skip(5);
        }});

        const speedSlider = document.getElementById('speedSlider');
        const speedValue = document.getElementById('speedValue');

        speedSlider.addEventListener('input', (e) => {{
            const currentSpeed = parseFloat(e.target.value);
            wavesurfer.setPlaybackRate(currentSpeed);
            speedValue.innerHTML = currentSpeed.toFixed(1) + "x";
        }});
        
        wavesurfer.on('ready', () => {{
            wavesurfer.setPlaybackRate(parseFloat(speedSlider.value));
        }});
    </script>
    """
    st.components.v1.html(html_reproductor, height=215)
else:
    st.warning(f"⚠️ Audio no encontrado en la ruta: `{ruta_audio}`")


# --- DESPLEGABLE DE DICTADO ---
with st.expander("📝 Modo Dictado: Haz clic aquí para escribir lo que oyes"):
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
        else:
            st.warning("Escribe algo en el cuadro antes de comprobar.")
