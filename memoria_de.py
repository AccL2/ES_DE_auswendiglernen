import streamlit as st
import pandas as pd
import os
import re
import random
import base64
from difflib import SequenceMatcher

# Configuración de la página
st.set_page_config(page_title="Entrenador de Idiomas por Islas", page_icon="🇩🇪", layout="centered")

# Estilos CSS Integrados
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght=400;600&display=swap');
    .texto-isla { font-family: 'Montserrat', sans-serif !important; font-size: 1.15rem; line-height: 1.6; }
    .bloque-azul { background-color: rgba(28, 131, 225, 0.15); border-left: 5px solid #1c83e1; padding: 1.2rem; border-radius: 0.5rem; margin-bottom: 1rem; }
    .bloque-verde { background-color: rgba(33, 195, 84, 0.15); border-left: 5px solid #21c354; padding: 1.2rem; border-radius: 0.5rem; margin-bottom: 1rem; }
    .bloque-gramatica { background-color: rgba(239, 68, 68, 0.1); border: 1px solid #f87171; padding: 1rem; border-radius: 0.5rem; margin-top: 1rem; color: #991b1b; font-family: 'Montserrat', sans-serif; }
    .resultado-porcentaje { font-family: 'Montserrat', sans-serif; font-size: 1.3rem; font-weight: 600; text-align: center; padding: 12px; border-radius: 8px; margin: 10px 0; border: 1px solid #ddd; }
    </style>
""", unsafe_allow_html=True)

# Lógica de comparación
def sim(u, o): return SequenceMatcher(None, re.sub(r'[^\w\s]', '', u.lower()), re.sub(r'[^\w\s]', '', o.lower())).ratio() * 100

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

# Estado de sesión
if 'ind' not in st.session_state: st.session_state.ind = 0
if 'sol' not in st.session_state: st.session_state.sol = False
if 'gram' not in st.session_state: st.session_state.gram = False

# Sidebar
st.sidebar.title("Configuración")
isla = st.sidebar.selectbox("🏝️ Isla:", df_total['Isla'].unique())
df_isla = df_total[df_total['Isla'] == isla].reset_index(drop=True)

modo_ale = st.sidebar.toggle("🔀 Orden aleatorio")
if modo_ale and 'orden' not in st.session_state:
    st.session_state.orden = random.sample(range(len(df_isla)), len(df_isla))
elif not modo_ale and 'orden' in st.session_state:
    del st.session_state.orden

idx_list = st.session_state.get('orden', list(range(len(df_isla))))
df_view = df_isla.iloc[idx_list].reset_index(drop=True)

# Navegación por selector (Sincronizado)
nav_idx = st.sidebar.selectbox("🎯 Ir a frase:", range(len(df_view)), format_func=lambda i: f"Frase {i+1}")
if nav_idx != st.session_state.ind:
    st.session_state.ind = nav_idx
    st.session_state.sol = False
    st.session_state.gram = False
    st.rerun()

# Controles Superiores
col1, col2, col3, col4 = st.columns(4)
if col1.button("👁️/🔄 Solución"): st.session_state.sol = not st.session_state.sol
if col4.button("💡 Gramática"): st.session_state.gram = not st.session_state.gram
if col2.button("⬅️ Anterior"): 
    st.session_state.ind = max(0, st.session_state.ind - 1); st.session_state.sol = False; st.session_state.gram = False; st.rerun()
if col3.button("Siguiente ➡️"): 
    st.session_state.ind = min(len(df_view)-1, st.session_state.ind + 1); st.session_state.sol = False; st.session_state.gram = False; st.rerun()

# Progreso y Visualización
fila = df_view.iloc[st.session_state.ind]
st.progress((st.session_state.ind + 1) / len(df_view))

if not st.session_state.sol:
    st.markdown(f'<div class="bloque-azul"><b>Castellano:</b><br>{fila["Castellano"]}</div>', unsafe_allow_html=True)
else:
    st.markdown(f'<div class="bloque-verde"><b>Solución:</b><br>{fila["Aleman"]}</div>', unsafe_allow_html=True)
    if st.session_state.gram and 'Explicacion' in fila and pd.notna(fila['Explicacion']):
        st.markdown(f'<div class="bloque-gramatica"><b>Nota Gramatical:</b><br>{fila["Explicacion"]}</div>', unsafe_allow_html=True)

# Audio (ID blindado)
val = fila.get('Audio_ID')
audio_id = str(int(float(val))) if pd.notna(val) and str(val).strip() != "nan" else "sin_audio"
ruta = f"Audios/{audio_id}.mp3"

if os.path.exists(ruta):
    with open(ruta, "rb") as f: b64 = base64.b64encode(f.read()).decode()
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
        const ws = WaveSurfer.create({{container:'#waveform', waveColor:'#64748b', progressColor:'#3b82f6', url:'data:audio/mp3;base64,{b64}'}});
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

# Dictado
with st.expander("📝 Modo Dictado"):
    txt = st.text_area("Escribe lo que oyes:", key="input_dict")
    if st.button("Comprobar dictado"):
        st.markdown(f'<div class="resultado-porcentaje">Precisión: {sim(txt, str(fila["Aleman"])):.1f}%</div>', unsafe_allow_html=True)
