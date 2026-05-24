import streamlit as st
import pandas as pd
import os
import re
import random
import base64
from difflib import SequenceMatcher

# Configuración inicial
st.set_page_config(page_title="Entrenador de Idiomas", layout="centered")

# Estilos
st.markdown("""
    <style>
    .bloque-azul { background: rgba(28, 131, 225, 0.15); border-left: 5px solid #1c83e1; padding: 1.2rem; border-radius: 0.5rem; margin-bottom: 1rem; }
    .bloque-verde { background: rgba(33, 195, 84, 0.15); border-left: 5px solid #21c354; padding: 1.2rem; border-radius: 0.5rem; margin-bottom: 1rem; }
    </style>
""", unsafe_allow_html=True)

def sim(u, o): return SequenceMatcher(None, re.sub(r'[^\w\s]', '', u.lower()), re.sub(r'[^\w\s]', '', o.lower())).ratio() * 100

@st.cache_data(ttl=10)
def cargar_datos():
    df = pd.read_excel("frases.xlsx")
    df.columns = df.columns.str.strip()
    return df

df_total = cargar_datos()

# Sidebar: Configuración e Isla
st.sidebar.title("Configuración")
isla = st.sidebar.selectbox("🏝️ Isla:", df_total['Isla'].unique())
df_isla = df_total[df_total['Isla'] == isla].reset_index(drop=True)

if 'ind' not in st.session_state: st.session_state.ind = 0
if 'sol' not in st.session_state: st.session_state.sol = False

# Orden aleatorio
modo_ale = st.sidebar.toggle("🔀 Orden aleatorio")
if modo_ale and 'orden' not in st.session_state:
    st.session_state.orden = list(range(len(df_isla)))
    random.shuffle(st.session_state.orden)
elif not modo_ale and 'orden' in st.session_state:
    del st.session_state.orden

idx_list = st.session_state.get('orden', list(range(len(df_isla))))
df_view = df_isla.iloc[idx_list].reset_index(drop=True)

# Navegación por selector
nav = st.sidebar.selectbox("🎯 Ir a frase:", [f"Frase {i+1}" for i in range(len(df_view))])
if int(nav.split()[1]) - 1 != st.session_state.ind:
    st.session_state.ind = int(nav.split()[1]) - 1
    st.session_state.sol = False
    st.rerun()

# Lógica de navegación
st.subheader(f"Progreso: {st.session_state.ind + 1} de {len(df_view)}")
st.progress((st.session_state.ind + 1) / len(df_view))

col1, col2, col3 = st.columns(3)
if col1.button("👁️/🔄 Solución"): st.session_state.sol = not st.session_state.sol
if col2.button("⬅️ Anterior"): st.session_state.ind = max(0, st.session_state.ind - 1); st.session_state.sol = False
if col3.button("Siguiente ➡️"): st.session_state.ind = min(len(df_view)-1, st.session_state.ind + 1); st.session_state.sol = False

# Visualización
fila = df_view.iloc[st.session_state.ind]
if not st.session_state.sol:
    st.markdown(f'<div class="bloque-azul"><b>Castellano:</b><br>{fila["Castellano"]}</div>', unsafe_allow_html=True)
else:
    st.markdown(f'<div class="bloque-verde"><b>Solución:</b><br>{fila["Aleman"]}</div>', unsafe_allow_html=True)

# Audio
val_audio = fila['Audio_ID']
audio_id = str(int(float(val_audio))) if pd.notna(val_audio) and str(val_audio).strip() else "sin_audio"
ruta = f"Audios/{audio_id}.mp3"

if os.path.exists(ruta):
    with open(ruta, "rb") as f: b64 = base64.b64encode(f.read()).decode()
    st.components.v1.html(f"""
    <div id="waveform"></div>
    <div style="display:flex; gap:10px; margin-top:10px;">
        <button id="p" style="padding:10px; flex-grow:1;">▶️ Play</button>
        <button id="r" style="padding:10px;">Reset</button>
    </div>
    <input type="range" id="s" min="0.5" max="2.0" step="0.1" value="1.0" style="width:100%">
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
    """, height=200)

# Dictado
with st.expander("📝 Modo Dictado"):
    txt = st.text_area("Escribe lo que oyes:")
    if st.button("Comprobar dictado"):
        score = sim(txt, str(fila["Aleman"]))
        st.write(f"### Precisión: {score:.1f}%")
