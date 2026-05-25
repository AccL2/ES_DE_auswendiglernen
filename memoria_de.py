import streamlit as st
import pandas as pd
import os
import re
import random
import base64
from difflib import SequenceMatcher

# Configuración de la página
st.set_page_config(page_title="Entrenador de Idiomas por Islas", page_icon="🇩🇪", layout="centered")

# Estilos CSS
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght=400;600&display=swap');
    .texto-isla { font-family: 'Montserrat', sans-serif !important; font-weight: 400 !important; line-height: 1.6; font-size: 1.15rem; }
    .titulo-situacion { font-family: 'Montserrat', sans-serif !important; font-weight: 600; text-transform: uppercase; color: #718096; margin-bottom: 0.5rem; }
    .bloque-azul { background-color: rgba(28, 131, 225, 0.15); border-left: 5px solid rgb(28, 131, 225); padding: 1.2rem; border-radius: 0.5rem; margin-bottom: 1rem; }
    .bloque-verde { background-color: rgba(33, 195, 84, 0.15); border-left: 5px solid rgb(33, 195, 84); padding: 1.2rem; border-radius: 0.5rem; margin-bottom: 1rem; }
    .bloque-gramatica { background-color: rgba(239, 68, 68, 0.1); border: 1px solid #f87171; padding: 1rem; border-radius: 0.5rem; margin-top: 1rem; color: #991b1b; font-family: 'Montserrat', sans-serif; }
    .resultado-porcentaje { font-family: 'Montserrat', sans-serif; font-size: 1.3rem; font-weight: 600; text-align: center; padding: 12px; border-radius: 8px; margin: 10px 0; border: 1px solid #ddd; }
    </style>
""", unsafe_allow_html=True)

def calcular_similitud_parcial(texto_usuario, texto_original):
    def limpiar(t): return re.sub(r'[.,!?¿¡"\'\s\n\r\t]', '', t.strip().lower())
    u_limpio, o_limpio = limpiar(texto_usuario), limpiar(texto_original)
    if not u_limpio or not o_limpio: return 0
    if len(u_limpio) <= len(o_limpio):
        mejor = 0.0
        for i in range(len(o_limpio) - len(u_limpio) + 1):
            ratio = SequenceMatcher(None, u_limpio, o_limpio[i : i + len(u_limpio)]).ratio()
            if ratio > mejor: mejor = ratio
        return mejor * 100
    return SequenceMatcher(None, u_limpio, o_limpio).ratio() * 100

@st.cache_data(ttl=10)
def cargar_datos():
    df = pd.read_excel("frases.xlsx")
    df.columns = df.columns.str.strip()
    return df

try:
    df_total = cargar_datos()
except Exception as e:
    st.error(f"Error cargando Excel: {e}")
    st.stop()

# --- ESTADO Y NAVEGACIÓN ---
if 'indice_actual' not in st.session_state: st.session_state.indice_actual = 0
if 'ver_solucion' not in st.session_state: st.session_state.ver_solucion = False
if 'ver_gramatica' not in st.session_state: st.session_state.ver_gramatica = False

islas = df_total['Isla'].unique()
isla_seleccionada = st.sidebar.selectbox("🏝️ Selecciona la Isla:", islas)
df_isla = df_total[df_total['Isla'] == isla_seleccionada].reset_index(drop=True)

modo_ale = st.sidebar.toggle("🔀 Orden aleatorio")
if modo_ale and 'orden_aleatorio' not in st.session_state:
    st.session_state.orden_aleatorio = random.sample(range(len(df_isla)), len(df_isla))
elif not modo_ale and 'orden_aleatorio' in st.session_state:
    del st.session_state.orden_aleatorio

if modo_ale: df_isla = df_isla.iloc[st.session_state.orden_aleatorio].reset_index(drop=True)

total_frases = len(df_isla)
st.subheader(f"Progreso: Frase {st.session_state.indice_actual + 1} de {total_frases}")
st.progress((st.session_state.indice_actual + 1) / total_frases)

# --- CONTROLES SUPERIORES ---
col1, col2, col3, col4 = st.columns(4)
if col1.button("👁️/🔄 Solución"): st.session_state.ver_solucion = not st.session_state.ver_solucion
if col4.button("💡 Gramática"): st.session_state.ver_gramatica = not st.session_state.ver_gramatica
if col2.button("⬅️ Anterior"): st.session_state.indice_actual = max(0, st.session_state.indice_actual - 1); st.session_state.ver_solucion = False; st.session_state.ver_gramatica = False; st.rerun()
if col3.button("Siguiente ➡️"): st.session_state.indice_actual = min(total_frases - 1, st.session_state.indice_actual + 1); st.session_state.ver_solucion = False; st.session_state.ver_gramatica = False; st.rerun()

# --- RENDERIZADO ---
fila = df_isla.iloc[st.session_state.indice_actual]
if not st.session_state.ver_solucion:
    st.markdown(f'<div class="bloque-azul"><b>Castellano:</b><br>{fila["Castellano"]}</div>', unsafe_allow_html=True)
else:
    st.markdown(f'<div class="bloque-verde"><b>Solución:</b><br>{fila["Aleman"]}</div>', unsafe_allow_html=True)

# --- REPRODUCTOR (Blindado contra errores) ---
val_audio = fila.get('Audio_ID')
audio_id = str(val_audio).strip() if pd.notna(val_audio) and str(val_audio).strip() != "nan" else "sin_audio"
ruta_audio = f"Audios/{audio_id}.mp3"

if os.path.exists(ruta_audio):
    with open(ruta_audio, "rb") as f: b64 = base64.b64encode(f.read()).decode()
    st.components.v1.html(f"""
    <div id="waveform" style="background:rgba(0,0,0,0.1); border-radius:8px;"></div>
    <div style="display:flex; gap:10px; margin-top:10px;">
        <button id="p" style="padding:10px; flex-grow:1; cursor:pointer;">▶️ Play</button>
        <button id="r" style="padding:10px; cursor:pointer;">Reset</button>
    </div>
    <input type="range" id="s" min="0.5" max="2.0" step="0.1" value="1.0" style="width:100%; margin-top:10px;">
    <script src="https://unpkg.com/wavesurfer.js@7"></script>
    <script src="https://unpkg.com/wavesurfer.js@7/dist/plugins/regions.min.js"></script>
    <script>
        const ws = WaveSurfer.create({{container:'#waveform', url:'data:audio/mp3;base64,{b64}'}});
        const reg = ws.registerPlugin(WaveSurfer.Regions.create());
        ws.on('audioprocess', () => {{
            const rs = reg.getRegions();
            if (rs.length > 0 && ws.getCurrentTime() >= rs[0].end) ws.setTime(rs[0].start);
        }});
        document.getElementById('p').onclick = () => ws.playPause();
        document.getElementById('r').onclick = () => reg.clearRegions();
        document.getElementById('s').oninput = (e) => ws.setPlaybackRate(e.target.value);
        ws.on('play', () => document.getElementById('p').innerText = "⏸️ Pausa");
        ws.on('pause', () => document.getElementById('p').innerText = "▶️ Play");
    </script>
    """, height=180)

# --- DICTADO ---
with st.expander("📝 Modo Dictado"):
    txt = st.text_area("Escribe lo que oyes:")
    if st.button("Comprobar dictado"):
        p = calcular_similitud_parcial(txt, str(fila["Aleman"]))
        st.markdown(f'<div class="resultado-porcentaje">Precisión: {p:.0f}%</div>', unsafe_allow_html=True)

# --- EXPLICACIÓN ABAJO DEL TODO ---
if st.session_state.ver_gramatica and 'Explicacion' in fila and pd.notna(fila['Explicacion']):
    st.markdown(f'<div class="bloque-gramatica"><b>💡 Explicación Gramatical:</b><br>{fila["Explicacion"]}</div>', unsafe_allow_html=True)
