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
    
    /* Bloque Azul (Modo Pregunta - Solo Castellano) */
    .bloque-azul {
        background-color: rgba(28, 131, 225, 0.15);
        border-left: 5px solid rgb(28, 131, 225);
        padding: 1.2rem 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    
    /* Bloque Combinado (Modo Solución - Frase a Frase) */
    .bloque-solucion-combinada {
        background-color: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 1.2rem 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    
    .par-frase {
        margin-bottom: 1.2rem;
        padding-bottom: 1.2rem;
        border-bottom: 1px dashed rgba(255, 255, 255, 0.1);
    }
    
    .par-frase:last-child {
        margin-bottom: 0;
        padding-bottom: 0;
        border-bottom: none;
    }
    
    .sub-castellano {
        color: #a0aec0;
        font-size: 1rem;
        font-style: italic;
        margin-bottom: 0.3rem;
    }
    
    .sub-aleman {
        color: #22c55e;
        font-size: 1.2rem;
        font-weight: 600;
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

# AUXILIAR: Segmenta el texto respetando los puntos finales de las frases
def segmentar_frases(texto):
    frases = re.split(r'(?<=[.!?])\s+', texto.strip())
    return [f.strip() for f in frases if f.strip()]

st.subheader(f"Progreso: Frase {st.session_state.indice_actual + 1} de {total_frases}")
st.progress((st.session_state.indice_actual + 1) / total_frases)

if situacion_texto:
    st.markdown(f'<div class="titulo-situacion">📍 Situación: {situacion_texto}</div>', unsafe_allow_html=True)

# --- PANEL VISUAL CORREGIDO CON EXPLICITACIÓN DE HTML ---
if not st.session_state.ver_solucion:
    listado_cas = segmentar_frases(castellano_texto)
    castellano_html = "<br>".join(listado_cas)
    st.markdown(f"""
    <div class="bloque-azul">
        <div class="texto-isla">
            <b>Castellano (Lee y piensa tu traducción):</b><br><br>
            {castellano_html}
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    lista_cas = segmentar_frases(castellano_texto)
    lista_ale = segmentar_frases(aleman_texto)
    
    html_pares = ""
    max_lineas = max(len(lista_cas), len(lista_ale))
    
    for idx in range(max_lineas):
        f_cas = lista_cas[idx] if idx < len(lista_cas) else ""
        f_ale = lista_ale[idx] if idx < len(lista_ale) else ""
        
        # Generamos la estructura de los pares frase por frase sin romper las f-strings
        html_pares += f'<div class="par-frase"><div class="sub-castellano">🇪🇸 {f_cas}</div><div class="sub-aleman">🇩🇪 {f_ale}</div></div>'
        
    # Usamos st.markdown con unsafe_allow_html=True forzado para renderizar los bloques
    st.markdown(f"""
    <div class="bloque-solucion-combinada">
        <div class="texto-isla">
            <b>Comparativa estructurada de la solución:</b><br><br>
            {html_pares}
        </div>
    </div>
    """, unsafe_allow_html=True)


# --- 🎧 REPRODUCTOR CON ONDA + BUCLE POR REGIONES 🎧 ---
ruta_audio = f"Audios/{audio_id}.mp3"
if os.path.exists(ruta_audio):
    st.write("🎧 **Arrastra sobre la onda para bucle. Haz un clic normal fuera de la selección o pulsa el botón Reset para volver a escuchar todo:**")
    
    with open(ruta_audio, "rb") as f:
        audio_bytes = f.read()
    b64_audio = base64.b64encode(audio_bytes).decode()
    
    html_reproductor = f"""
    <div style="font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.15); padding: 15px; border-radius: 12px; color: #ffffff;">
        <div id="waveform" style="margin-bottom: 15px; background: rgba(0, 0, 0, 0.2); border-radius: 6px; padding: 4px; cursor: pointer;"></div>
        
        <div style="display: flex; justify-content: center; align-items: center; gap: 10px; flex-wrap: wrap;">
            <button id="btnBack" style="padding: 8px 14px; background: #475569; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: bold; font-size: 0.9rem;">⏮️ -5s</button>
            <button id="btnPlay" style="padding: 10px 22px; background: #1c83e1; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: bold; font-size: 1rem; min-width: 90px;">▶️ Play</button>
            <button id="btnForward" style="padding: 8px 14px; background: #475569; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: bold; font-size: 0.9rem;">+5s ⏭️</button>
            <button id="btnResetRegion" style="padding: 8px 14px; background: #dc2626; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: bold; font-size: 0.9rem;">Reset 🔄</button>
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
            height: 70,
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
    </script>
    """
    st.components.v1.html(html_reproductor, height=155)
else:
    st.warning(f"⚠️ Audio no encontrado en la ruta: `{ruta_audio}`")


# --- DESPLEGABLE DE DICTADO CON AMPLITUD ASEGURADA ---
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


st.write("---")

# --- BOTONES DE NAVEGACIÓN ---
col1, col2 = st.columns(2)

with col1:
    if not st.session_state.ver_solucion:
        if st.button("👁️ Mostrar solución alemán", use_container_width=True):
            st.session_state.ver_solucion = True
            st.rerun()
    else:
        if st.button("🔄 Volver a Castellano", use_container_width=True):
            st.session_state.ver_solucion = False
            st.rerun()

with col2:
    if st.button("Siguiente Frase ➡️", use_container_width=True):
        if st.session_state.indice_actual < total_frases - 1:
            st.session_state.indice_actual += 1
            st.session_state.ver_solucion = False
        else:
            st.session_state.completado = True
        st.rerun()
