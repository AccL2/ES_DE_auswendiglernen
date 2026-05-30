import streamlit as st
import pandas as pd
import os
import re
import random
import base64
import urllib.parse
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

# URL de tu Google Sheet (Modificada internamente para exportar como CSV)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1hpP0J5qRrbx5p9W2nHWsoTDBA9hhvLZYblaU12Ln3w4/export?format=csv"

# Cargar los datos desde Google Sheets en la nube
@st.cache_data(ttl=5) # ttl bajo para captar rápido los cambios de estado entre móvil/pc
def cargar_datos_web():
    # Añadimos un parámetro aleatorio al final para romper la cache del navegador al recargar
    url = f"{SHEET_URL}&nocache={random.randint(1, 100000)}"
    df = pd.read_csv(url)
    df.columns = df.columns.str.strip()
    return df

try:
    df_total = cargar_datos_web()
except Exception as e:
    st.error(f"No se pudo conectar con el Google Sheet. Asegúrate de tener conexión a internet. Detalles: {e}")
    st.stop()

# --- BARRA LATERAL ---
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
# Separar frases jubiladas (Azul) de las activas/pendientes
df_activas_y_pendientes = df_isla_completa[df_isla_completa['Estado'] != 'Azul'].copy()
df_jubiladas = df_isla_completa[df_isla_completa['Estado'] == 'Azul']
total_jubiladas = len(df_jubiladas)

# ¿Está la isla completada al 100%?
if total_jubiladas == total_frases_isla and total_frases_isla > 0:
    st.title("🇩🇪 Método de Chunks & Islas")
    st.balloons()
    st.success(f"🎉 ¡ESPECTACULAR! Has completado la isla '{isla_seleccionada}' al 100%.")
    st.info(f"Has jubilado con éxito los {total_frases_isla} monólogos en color Azul 🔵. ¡Están listos en tu disco duro profundo!")
    
    if st.button("♻️ Reiniciar toda la isla a Rojo (Empezar de cero)", use_container_width=True):
        st.warning("Para reiniciar, cambia manualmente la columna Estado a 'Rojo' en tu Google Sheet y recarga la app.")
    st.stop()

# Si no está completada, construimos la Rueda de 15 activas
df_en_rueda = df_activas_y_pendientes[df_activas_y_pendientes['Estado'].isin(['Rojo', 'Naranja', 'Verde'])].copy()

# Si en la rueda no se llega a 15, rellenamos el hueco con las siguientes "Pendientes"
if len(df_en_rueda) < 15 and len(df_activas_y_pendientes) > len(df_en_rueda):
    df_en_rueda = df_activas_y_pendientes.head(15).copy()

# Guardamos el total de monólogos que van a competir en esta rueda (máximo 15)
total_rueda_actual = len(df_en_rueda)

if st.session_state.indice_actual >= total_rueda_actual:
    st.session_state.indice_actual = total_rueda_actual - 1 if total_rueda_actual > 0 else 0

# --- CONTENIDO PRINCIPAL ---
st.title("🇩🇪 Método de Chunks & Islas")

# Marcadores superiores de control del sistema de memoria
col_ind1, col_ind2, col_ind3 = st.columns(3)
with col_ind1:
    st.metric("🏝️ Total Isla", f"{total_frases_isla} chunks")
with col_ind2:
    st.metric("🔄 En Rueda Activa", f"{total_rueda_actual} / 15")
with col_ind3:
    st.metric("🔵 Jubilados (Azul)", f"{total_jubiladas} / {total_frases_isla}")

st.write("---")

# Extraer datos de la frase en rueda que toca estudiar
fila_actual = df_en_rueda.iloc[st.session_state.indice_actual]
castellano_texto = str(fila_actual['Castellano'])
aleman_texto = str(fila_actual['Aleman'])
estado_actual = str(fila_actual['Estado'])

# Averiguar el índice real en la hoja de cálculo de Google (Panda index + 2 por encabezados)
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

# Mostrar indicador del color del monólogo actual en la rueda
dict_colores_emoji = {"Rojo": "🔴 Crudo / Nuevo", "Naranja": "🟠 En progreso", "Verde": "🟢 Repasillo / Dominado"}
color_badge = dict_colores_emoji.get(estado_actual, "🔴 Rojo")

st.subheader(f"Monólogo en rueda: {st.session_state.indice_actual + 1} de {total_rueda_actual} (Estado: {color_badge})")
st.progress((st.session_state.indice_actual + 1) / total_rueda_actual)

if situacion_texto:
    st.markdown(f'<div class="titulo-situacion">📍 Situación: {situacion_texto}</div>', unsafe_allow_html=True)


# --- 🔄 BARRA DE NAV / CONTROL ORIGINAL ---
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

# Renderizado de la Tarjeta (Castellano / Alemán)
if not st.session_state.ver_solucion:
    castellano_formateado = formatear_lineas(castellano_texto)
    st.markdown(f"""
    <div class="bloque-azul">
        <div class="texto-isla">
            <b>Castellano (Haz el 'Tapa y Escupe'):</b><br><br>
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


# --- 🎛️ BARRA DE GESTIÓN DE LA MEMORIA (TUS COLORES) 🎛️ ---
st.write("### 🧮 Califica tu evocación mental para este monólogo:")
col_c1, col_c2, col_c3, col_c4 = st.columns(4)

nuevo_estado_solicitado = None

with col_c1:
    if st.button("🔴 Mantener Rojo", use_container_width=True, help="Te ha costado mucho o es nuevo"):
        nuevo_estado_solicitado = "Rojo"
with col_c2:
    if st.button("🟠 Pasar Naranja", use_container_width=True, help="Lo vas pillando pero aún dudas"):
        nuevo_estado_solicitado = "Naranja"
with col_c3:
    if st.button("🟢 Pasar Verde", use_container_width=True, help="Te lo sabes, listo para repasar rápido"):
        nuevo_estado_solicitado = "Verde"
with col_c4:
    if st.button("🔵 Jubilar Azul", use_container_width=True, help="¡Dominado! Sacar de la rueda y meter uno nuevo"):
        nuevo_estado_solicitado = "Azul"

# Si el usuario hace clic en cambiar un color, mandamos la actualización a Google Sheets
if nuevo_estado_solicitado:
    # URL de la Web App de Google que has creado e implementado en tu cuenta
    WEB_APP_URL = "https://script.google.com/macros/s/AKfycbzxuhVMl8swR7fJHyd5dXt0WCXTpHoSWUrLxxKpRF3Bcwt2lo09vSvkDiAeWymV3F7l/exec" 
    
    params = urllib.parse.urlencode({
        "row": indice_fila_google_sheet,
        "status": nuevo_estado_solicitado
    })
    
    url_final_update = f"{WEB_APP_URL}?{params}"
    
    # Inyectamos el componente de recarga instantánea
    st.components.v1.html(f"""
        <script>
            fetch("{url_final_update}", {{ method: "POST", mode: "no-cors" }})
            .then(() => {{
                parent.window.location.reload();
            }});
        </script>
    """, height=0, width=0)
    
    st.cache_data.clear()
    st.success(f"¡Estado actualizado a {nuevo_estado_solicitado}! Sincronizando en la nube...")
    st.rerun()


# --- 🎧 REPRODUCTOR CON ONDA + VELOCIDAD POR DÉCIMAS 🎧 ---
ruta_audio = f"Audios/{audio_id}.mp3"
if os.path.exists(ruta_audio):
    st.write("🎧 **Arrastra sobre la onda para bucle. Haz un clic normal fuera de la selección o pulsa el botón Reset para volver a escuchar todo:**")
    
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
        }});

        wavesurfer.on('pause', () => {{
            btnPlay.innerHTML = "▶️ Play";
            btnPlay.style.background = "#1c83e1"; 
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


# --- 💡 EXPLICACIÓN ABAJO DEL TODO ---
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
    else:
        st.info("ℹ️ No hay ninguna explicación cargada para esta frase en el archivo Excel.")
