import streamlit as st
import pandas as pd
import os
import re
import base64
import requests
from difflib import SequenceMatcher

# Configuración de la página
st.set_page_config(page_title="Entrenador de Idiomas por Islas", page_icon="🇩🇪", layout="centered")

# --- 🌐 ENLACES DE TU CONFIGURACIÓN ---
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1hpP0J5qRrbx5p9W2nHWsoTDBA9hhvLZYblaU12Ln3w4/export?format=csv&gid=0"
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbxT5tzluJTlMl8dW0Ps-v93F672sG4Fn8ajDBrdoeitbQBFyqqrW_udtjwuD47glvUX/exec"

# Estilos visuales con colores dinámicos adaptados al estado de la frase
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght=300;400;500;600;700&display=swap');
    
    :root {
        --azul:        #3b7dd8; --azul-bg:     rgba(59, 125, 216, 0.08); --azul-borde:  rgba(59, 125, 216, 0.4);
        --verde:       #22a66e; --verde-bg:    rgba(34, 166, 110, 0.08); --verde-borde: rgba(34, 166, 110, 0.4);
        --rojo:        #e05454; --rojo-bg:     rgba(224, 84, 84, 0.08);  --rojo-borde:  rgba(224, 84, 84, 0.4);
        --naranja:     #f5a623; --naranja-bg:  rgba(245, 166, 35, 0.08); --naranja-borde: rgba(245, 166, 35, 0.4);
        --radio:       12px;
    }

    html, body, [class*="css"], .stMarkdown, .stTextArea, .stExpander,
    .stButton button, .stSelectbox, .stSidebar, p, label, input, textarea {
        font-family: 'Montserrat', sans-serif !important;
    }

    h1 { font-family: 'Montserrat', sans-serif !important; font-weight: 700 !important; font-size: 1.85rem !important; }
    .titulo-situacion { font-size: 0.75rem !important; text-transform: uppercase; letter-spacing: 2px; color: #8a9ab5; margin-bottom: 0.75rem; }
    .texto-isla { font-weight: 400 !important; line-height: 1.8 !important; font-size: 1.25rem !important; }
    
    /* Cajas con bordes inteligentes según el estado real de la frase */
    .caja-dinamica-Rojo { background: var(--rojo-bg); border: 1px solid var(--rojo-borde); border-left: 5px solid var(--rojo); padding: 1.4rem 1.6rem; border-radius: var(--radio); margin-bottom: 1rem; }
    .caja-dinamica-Naranja { background: var(--naranja-bg); border: 1px solid var(--naranja-borde); border-left: 5px solid var(--naranja); padding: 1.4rem 1.6rem; border-radius: var(--radio); margin-bottom: 1rem; }
    .caja-dinamica-Verde { background: var(--verde-bg); border: 1px solid var(--verde-borde); border-left: 5px solid var(--verde); padding: 1.4rem 1.6rem; border-radius: var(--radio); margin-bottom: 1rem; }
    .caja-dinamica- { background: var(--azul-bg); border: 1px solid var(--azul-borde); border-left: 5px solid var(--azul); padding: 1.4rem 1.6rem; border-radius: var(--radio); margin-bottom: 1rem; }
    .caja-dinamica-nan { background: var(--azul-bg); border: 1px solid var(--azul-borde); border-left: 5px solid var(--azul); padding: 1.4rem 1.6rem; border-radius: var(--radio); margin-bottom: 1rem; }

    .bloque-verde { background: var(--verde-bg); border: 1px solid var(--verde-borde); border-left: 5px solid var(--verde); padding: 1.4rem 1.6rem; border-radius: var(--radio); margin-bottom: 1rem; }
    .bloque-gramatica { background: var(--rojo-bg); border: 1px solid var(--rojo-borde); border-left: 4px solid var(--rojo); padding: 1.4rem 1.6rem; border-radius: var(--radio); margin-top: 0.75rem; }
    .resultado-porcentaje { font-size: 1.2rem; font-weight: 600; text-align: center; padding: 10px; border-radius: var(--radio); margin-top: 10px; }
    .progreso-contador { font-size: 0.72rem; font-weight: 500; color: #8a9ab5; text-align: right; margin-bottom: 4px; }
    </style>
""", unsafe_allow_html=True)

def calcular_similitud_parcial(texto_usuario, texto_original):
    def limpiar(t): return re.sub(r'[.,!?¿¡"\'\s\n\r\t]', '', t.strip().lower())
    u_limpio, o_limpio = limpiar(texto_usuario), limpiar(texto_original)
    if not u_limpio or not o_limpio: return 0
    len_u, len_o = len(u_limpio), len(o_limpio)
    if len_u <= len_o:
        mejor_ratio = 0.0
        for i in range(len_o - len_u + 1):
            ratio_actual = SequenceMatcher(None, u_limpio, o_limpio[i : i + len_u]).ratio()
            if ratio_actual > mejor_ratio: mejor_ratio = ratio_actual
        return mejor_ratio * 100
    return SequenceMatcher(None, u_limpio, o_limpio).ratio() * 100

def formatear_lineas(texto):
    return "<br>".join(re.split(r'(?<=[.!?])\s+', texto.strip()))

# Cargar los datos respetando estrictamente las mayúsculas de tu Google Sheet
@st.cache_data(ttl=1)
def cargar_datos_sistema():
    try: 
        df = pd.read_csv(SHEET_CSV_URL)
    except Exception:
        if os.path.exists("frases.xlsx"): 
            df = pd.read_excel("frases.xlsx")
        else: 
            df = pd.DataFrame(columns=['Isla', 'Castellano', 'Aleman', 'Audio_ID', 'Situacion', 'Explicacion', 'Estado'])
    
    # Limpiar solo espacios en blanco de las cabeceras, sin alterar las letras
    df.columns = df.columns.str.strip()
        
    for col in df.columns:
        if df[col].dtype == 'object': 
            df[col] = df[col].astype(str).str.strip()
            
    # Asegurar que existan las columnas clave de forma exacta
    if 'Estado' not in df.columns: df['Estado'] = ""
    if 'Isla' not in df.columns: df['Isla'] = "Sin Isla"
    if 'Castellano' not in df.columns: df['Castellano'] = ""
    if 'Aleman' not in df.columns: df['Aleman'] = ""
        
    return df

df_total = cargar_datos_sistema()

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

# Filtrar Rueda desactivando las Aprendidas (Azul)
df_activas = df_isla_completa[df_isla_completa['Estado'].astype(str).str.strip() != 'Azul'].copy()
total_aprendidos = len(df_isla_completa[df_isla_completa['Estado'].astype(str).str.strip() == 'Azul'])
df_en_rueda = df_activas.head(15).copy()
total_rueda_actual = len(df_en_rueda)

# Contadores de la barra lateral
if total_rueda_actual > 0:
    estados_rueda = df_en_rueda['Estado'].fillna('Rojo').astype(str).str.strip().tolist()
    n_rojos, n_naranjas, n_verdes = estados_rueda.count('Rojo'), estados_rueda.count('Naranja'), estados_rueda.count('Verde')
else:
    n_rojos = n_naranjas = n_verdes = 0

st.sidebar.markdown(f"""
### 📊 Estado de la Isla
<div style="background: rgba(255,255,255,0.04); padding: 16px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.09);">
    <p style="margin: 0 0 12px 0; font-size: 0.7rem; color: #8a9ab5; letter-spacing: 2px;">🔄 EN RUEDA ACTUAL: {total_rueda_actual}</p>
    <p style="margin:4px 0; font-size:0.9rem;">🔴 Rojas: <b>{n_rojos}</b></p>
    <p style="margin:4px 0; font-size:0.9rem;">🟠 Naranjas: <b>{n_naranjas}</b></p>
    <p style="margin:4px 0; font-size:0.9rem;">🟢 Verdes: <b>{n_verdes}</b></p>
    <div style="margin-top:12px; padding-top:12px; border-top:1px solid rgba(255,255,255,0.08); display:flex; justify-content:between;">
        <span style="color:#8a9ab5;font-size:0.8rem;">🔵 Aprendidas:</span>
        <span style="font-weight:600; color:#3b7dd8;">{total_aprendidos} / {total_frases_isla}</span>
    </div>
</div>
""", unsafe_allow_html=True)

if total_frases_isla > 0 and total_aprendidos == total_frases_isla:
    st.title("🇩🇪 Método de Chunks")
    st.balloons()
    st.success("🎉 ¡Felicidades! Completaste esta isla de estudio.")
    st.stop()

if st.session_state.indice_actual >= total_rueda_actual:
    st.session_state.indice_actual = 0

# --- CONTENIDO PRINCIPAL ---
st.title("🇩🇪 Método de Chunks & Islas")

if total_rueda_actual == 0:
    st.info("🏝️ No hay más frases pendientes en esta isla.")
    st.stop()

fila_actual = df_en_rueda.iloc[st.session_state.indice_actual]
castash_raw = fila_actual['Castellano']
castellano_texto = str(castash_raw)
aleman_texto     = str(fila_actual['Aleman'])
estado_actual    = str(fila_actual['Estado']).strip()

if estado_actual == "nan" or not estado_actual:
    estado_actual = ""

# Encontrar fila del Excel real para realizar la edición remota de forma exacta
indices_match = df_total[df_total['Castellano'] == castash_raw].index
indice_fila_excel = int(indices_match[0]) + 2 if len(indices_match) > 0 else 2

audio_id_raw = fila_actual['Audio_ID'] if 'Audio_ID' in fila_actual else "sin_audio"
audio_id = "sin_audio" if pd.isna(audio_id_raw) else str(int(audio_id_raw)) if isinstance(audio_id_raw, float) else str(audio_id_raw).strip()
situacion_texto = str(fila_actual['Situacion']).strip() if 'Situacion' in fila_actual and pd.notna(fila_actual['Situacion']) else ""

st.markdown(f'<div class="progreso-contador">{st.session_state.indice_actual + 1} / {total_rueda_actual}</div>', unsafe_allow_html=True)
st.progress((st.session_state.indice_actual + 1) / total_rueda_actual)

if situacion_texto:
    st.markdown(f'<div class="titulo-situacion">📍 {situacion_texto}</div>', unsafe_allow_html=True)

# --- BOTONES DE NAVEGACIÓN ---
col_nav_sol, col_nav_ant, col_nav_sig, col_nav_gram = st.columns(4)
with col_nav_sol:
    if st.button("👁️ Solución", use_container_width=True): st.session_state.ver_solucion = not st.session_state.ver_solucion; st.rerun()
with col_nav_ant:
    if st.button("⬅️ Anterior", use_container_width=True) and st.session_state.indice_actual > 0:
        st.session_state.indice_actual -= 1; st.session_state.ver_solucion = False; st.session_state.ver_gramatica = False; st.rerun()
with col_nav_sig:
    if st.button("Siguiente ➡️", use_container_width=True) and st.session_state.indice_actual < total_rueda_actual - 1:
        st.session_state.indice_actual += 1; st.session_state.ver_solucion = False; st.session_state.ver_gramatica = False; st.rerun()
with col_nav_gram:
    if st.button("💡 Gramática", use_container_width=True): st.session_state.ver_gramatica = not st.session_state.ver_gramatica; st.rerun()

# --- MUESTRA DE BLOQUE DE TEXTO CON COLOR DE BORDE SEGÚN SU ESTADO ---
if not st.session_state.ver_solucion:
    st.markdown(f'<div class="caja-dinamica-{estado_actual}"><div class="texto-isla"><b>Castellano (Estado actual: {estado_actual if estado_actual else "Nuevo / Sin color"}):</b><br><br>{formatear_lineas(castellano_texto)}</div></div>', unsafe_allow_html=True)
else:
    st.markdown(f'<div class="bloque-verde"><div class="texto-isla"><b>Solución en Alemán:</b><br><br>{formatear_lineas(aleman_texto)}</div></div>', unsafe_allow_html=True)

# --- BOTONES DE CAMBIO DE COLOR ---
col_c1, col_c2, col_c3, col_c4 = st.columns(4)
nuevo_estado = None
with col_c1:
    if st.button("🔴 Rojo", use_container_width=True): nuevo_estado = "Rojo"
with col_c2:
    if st.button("🟠 Naranja", use_container_width=True): nuevo_estado = "Naranja"
with col_c3:
    if st.button("🟢 Verde", use_container_width=True): nuevo_estado = "Verde"
with col_c4:
    if st.button("🔵 Azul", use_container_width=True): nuevo_estado = "Azul"

if nuevo_estado:
    try:
        # Envío directo tradicional
        requests.post(WEB_APP_URL, params={"row": indice_fila_excel, "status": nuevo_estado}, timeout=5)
    except Exception: pass
    
    st.cache_data.clear()
    if st.session_state.indice_actual < total_rueda_actual - 1: st.session_state.indice_actual += 1
    else: st.session_state.indice_actual = 0
    st.session_state.ver_solucion = False
    st.session_state.ver_gramatica = False
    st.rerun()

# --- AUDIO REPRODUCTOR ---
ruta_audio = f"Audios/{audio_id}.mp3"
if os.path.exists(ruta_audio):
    with open(ruta_audio, "rb") as f: b64_audio = base64.b64encode(f.read()).decode()
    html_reproductor = f"""
    <div style="background: rgba(255, 255, 255, 0.04); border: 1px solid rgba(255, 255, 255, 0.1); padding: 12px; border-radius: 12px;">
        <div id="waveform" style="background: rgba(0, 0, 0, 0.2); border-radius: 6px; padding: 4px;"></div>
        <div style="display: flex; justify-content: center; gap: 10px; margin-top: 10px;">
            <button id="btnPlay" style="padding: 6px 16px; background: #1c83e1; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: bold;">▶️ Play / Pausa</button>
            <button id="btnResetRegion" style="padding: 6px 12px; background: #dc2626; color: white; border: none; border-radius: 6px; cursor: pointer;">Borrar Bucle 🔄</button>
        </div>
    </div>
    <script src="https://unpkg.com/wavesurfer.js@7"></script>
    <script src="https://unpkg.com/wavesurfer.js@7/dist/plugins/regions.min.js"></script>
    <script>
        const wavesurfer = WaveSurfer.create({{ container: '#waveform', waveColor: '#64748b', progressColor: '#3b82f6', height: 50, url: 'data:audio/mp3;base64,{b64_audio}' }});
        const wsRegions = wavesurfer.registerPlugin(WaveSurfer.Regions.create());
        wsRegions.enableDragSelection({{ color: 'rgba(59, 130, 246, 0.3)' }});
        wsRegions.on('region-created', (r) => {{ wsRegions.getRegions().forEach(x => {{ if (x !== r) x.remove(); }}); }});
        wavesurfer.on('timeupdate', (t) => {{ const rg = wsRegions.getRegions(); if (rg.length > 0 && (t >= rg[0].end || t < rg[0].start)) wavesurfer.setTime(rg[0].start); }});
        document.getElementById('btnResetRegion').addEventListener('click', () => wsRegions.clearRegions());
        document.getElementById('btnPlay').addEventListener('click', () => wavesurfer.playPause());
    </script>
    """
    st.components.v1.html(html_reproductor, height=130)

# --- DICTADO Y GRAMÁTICA ---
with st.expander("📝 Modo Dictado"):
    texto_usuario = st.text_area("Escribe lo que oyes:", key=f"dict_{st.session_state.indice_actual}")
    if st.button("🔍 Comprobar", use_container_width=True) and texto_usuario:
        p = calcular_similitud_parcial(texto_usuario, aleman_texto)
        st.markdown(f'<div class="resultado-porcentaje" style="background: rgba(255,255,255,0.05); border: 1px solid #3b7dd8; color: white;">Resultado: {p:.0f}% correcto</div>', unsafe_allow_html=True)

if st.session_state.ver_gramatica:
    exp = str(fila_actual['Explicacion']).strip() if 'Explicacion' in fila_actual and pd.notna(fila_actual['Explicacion']) else ""
    st.markdown(f'<div class="bloque-gramatica"><b>💡 Nota gramatical:</b><br><br>{formatear_lineas(exp) if exp else "Sin notas."}</div>', unsafe_allow_html=True)

# --- 🔍 VISUALIZADOR MAPA DE LA ISLA ---
st.write("---")
with st.expander("🔍 Ver toda la Isla (Mapa de colores de tus frases)"):
    st.write("Aquí tienes la lista completa de frases de esta isla con el color que guardaste para cada una:")
    columnas_visibles = [col for col in ['Castellano', 'Aleman', 'Estado'] if col in df_isla_completa.columns]
    tabla_bonita = df_isla_completa[columnas_visibles].copy()
    tabla_bonita['Estado'] = tabla_bonita['Estado'].replace({"": "Nuevo (Sin color)", "nan": "Nuevo (Sin color)"})
    st.dataframe(tabla_bonita, use_container_width=True, hide_index=True)
