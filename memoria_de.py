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
    .texto-isla { font-family: 'Montserrat', sans-serif !important; font-size: 1.15rem; line-height: 1.6; }
    .titulo-situacion { font-family: 'Montserrat', sans-serif !important; font-weight: 600; text-transform: uppercase; color: #718096; margin-bottom: 0.5rem; }
    .bloque-azul { background-color: rgba(28, 131, 225, 0.15); border-left: 5px solid rgb(28, 131, 225); padding: 1.2rem; border-radius: 0.5rem; margin-bottom: 1rem; }
    .bloque-verde { background-color: rgba(33, 195, 84, 0.15); border-left: 5px solid rgb(33, 195, 84); padding: 1.2rem; border-radius: 0.5rem; margin-bottom: 1rem; }
    .resultado-porcentaje { font-family: 'Montserrat', sans-serif; font-size: 1.3rem; font-weight: 600; text-align: center; padding: 12px; border-radius: 8px; margin: 10px 0; }
    </style>
""", unsafe_allow_html=True)

def calcular_similitud_parcial(texto_usuario, texto_original):
    def limpiar(t): return re.sub(r'[.,!?¿¡"\'\s\n\r\t]', '', t.strip().lower())
    u, o = limpiar(texto_usuario), limpiar(texto_original)
    if not u or not o: return 0
    if len(u) <= len(o):
        mejor = 0.0
        for i in range(len(o) - len(u) + 1):
            ratio = SequenceMatcher(None, u, o[i : i + len(u)]).ratio()
            if ratio > mejor: mejor = ratio
        return mejor * 100
    return SequenceMatcher(None, u, o).ratio() * 100

@st.cache_data(ttl=10)
def cargar_datos():
    df = pd.read_excel("frases.xlsx")
    df.columns = df.columns.str.strip()
    return df

try:
    df_total = cargar_datos()
except Exception as e:
    st.error(f"Error cargando archivo: {e}")
    st.stop()

# --- ESTADO Y NAVEGACIÓN ---
st.sidebar.title("Configuración")
isla_sel = st.sidebar.selectbox("🏝️ Selecciona la Isla:", df_total['Isla'].unique())
df_isla = df_total[df_total['Isla'] == isla_sel].reset_index(drop=True)

if 'ind' not in st.session_state: st.session_state.ind = 0
if 'sol' not in st.session_state: st.session_state.sol = False

# Navegación
col_sol, col_ant, col_sig = st.columns(3)
if col_sol.button("👁️/🔄 Solución"): st.session_state.sol = not st.session_state.sol
if col_ant.button("⬅️ Anterior"): 
    st.session_state.ind = max(0, st.session_state.ind - 1)
    st.session_state.sol = False
if col_sig.button("Siguiente ➡️"): 
    st.session_state.ind = min(len(df_isla)-1, st.session_state.ind + 1)
    st.session_state.sol = False

fila = df_isla.iloc[st.session_state.ind]
st.subheader(f"Frase {st.session_state.ind + 1} de {len(df_isla)}")
st.progress((st.session_state.ind + 1) / len(df_isla))

# Contenido
if not st.session_state.sol:
    st.markdown(f'<div class="bloque-azul"><div class="texto-isla"><b>Castellano:</b><br>{fila["Castellano"]}</div></div>', unsafe_allow_html=True)
else:
    st.markdown(f'<div class="bloque-verde"><div class="texto-isla"><b>Solución:</b><br>{fila["Aleman"]}</div></div>', unsafe_allow_html=True)

# --- REPRODUCTOR ---
audio_id = str(int(fila['Audio_ID'])) if pd.notna(fila['Audio_ID']) else "sin_audio"
ruta = f"Audios/{audio_id}.mp3"

if os.path.exists(ruta):
    with open(ruta, "rb") as f: b64 = base64.b64encode(f.read()).decode()
    
    html = f"""
    <div style="background: rgba(255,255,255,0.05); padding:15px; border-radius:12px; color:white;">
        <div id="waveform"></div>
        <div style="display:flex; gap:10px; justify-content:center; margin-top:10px;">
            <button id="btnPlay" style="padding:10px 20px; background:#1c83e1; color:white; border:none; border-radius:6px;">▶️ Play</button>
            <button id="btnReset" style="padding:10px 20px; background:#dc2626; color:white; border:none; border-radius:6px;">Reset</button>
        </div>
        <input type="range" id="speed" min="0.5" max="2.0" step="0.1" value="1.0" style="width:100%; margin-top:10px;">
        <div id="speedVal" style="text-align:center;">Velocidad: 1.0x</div>
    </div>
    <script src="https://unpkg.com/wavesurfer.js@7"></script>
    <script src="https://unpkg.com/wavesurfer.js@7/dist/plugins/regions.min.js"></script>
    <script>
        const ws = WaveSurfer.create({{container: '#waveform', waveColor: '#64748b', progressColor: '#3b82f6', url: 'data:audio/mp3;base64,{b64}'}});
        const wsRegions = ws.registerPlugin(WaveSurfer.Regions.create());
        ws.on('audioprocess', () => {{
            const regions = wsRegions.getRegions();
            if (regions.length > 0 && ws.getCurrentTime() >= regions[0].end) ws.setTime(regions[0].start);
        }});
        document.getElementById('btnPlay').onclick = () => ws.playPause();
        document.getElementById('btnReset').onclick = () => wsRegions.clearRegions();
        document.getElementById('speed').oninput = (e) => {{
            ws.setPlaybackRate(e.target.value);
            document.getElementById('speedVal').innerText = "Velocidad: " + e.target.value + "x";
        }};
        ws.on('play', () => document.getElementById('btnPlay').innerText = "⏸️ Pausa");
        ws.on('pause', () => document.getElementById('btnPlay').innerText = "▶️ Play");
    </script>
    """
    st.components.v1.html(html, height=250)
else:
    st.warning("Archivo de audio no encontrado.")

# Dictado
with st.expander("📝 Modo Dictado"):
    txt = st.text_area("Escribe lo que oyes:")
    if st.button("Comprobar"):
        p = calcular_similitud_parcial(txt, str(fila["Aleman"]))
        st.markdown(f'<div class="resultado-porcentaje" style="border:1px solid #ddd;">{p:.0f}% de acierto</div>', unsafe_allow_html=True)
