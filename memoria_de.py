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

# Inyectar tipografías y estilos premium
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600;700&display=swap');

    /* ── Variables de color ── */
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
        --naranja:     #f5a623;
        --radio:       12px;
    }

    /* ── Fuente base GLOBAL ── */
    html, body,
    p, span, div, label, input, textarea, select, option,
    h1, h2, h3, h4, h5, h6,
    [class*="css"],
    .stMarkdown, .stText, .stTextArea, .stTextInput,
    .stButton button, .stSelectbox, .stSidebar {
        font-family: 'Montserrat', sans-serif !important;
    }

    /* ── Expander ── */
    div[data-testid="stExpander"] { border: 1px solid rgba(255, 255, 255, 0.1) !important; border-radius: 8px !important; }
    div[data-testid="stExpander"] summary { display: flex !important; align-items: center !important; padding: 10px 15px !important; min-height: 45px !important; }
    div[data-testid="stExpander"] summary p { margin: 0 !important; padding-right: 30px !important; font-weight: 500 !important; font-family: 'Montserrat', sans-serif !important; }

    /* ── Título principal ── */
    h1 { font-family: 'Montserrat', sans-serif !important; font-weight: 700 !important; font-size: 1.85rem !important; letter-spacing: -0.5px !important; margin-bottom: 0.25rem !important; }
    h2, h3 { font-family: 'Montserrat', sans-serif !important; font-weight: 600 !important; }

    /* ── Etiqueta de situación ── */
    .titulo-situacion { font-family: 'Montserrat', sans-serif !important; font-weight: 500 !important; font-size: 0.75rem !important; text-transform: uppercase; letter-spacing: 2px; color: #8a9ab5; margin-bottom: 0.75rem; display: flex; align-items: center; gap: 6px; }

    /* ── Tarjetas y Tiras de Historial Pastel ── */
    .tira-historial { width: 100%; padding: 5px 12px; border-radius: 8px; font-size: 0.70rem; font-weight: 600; text-transform: uppercase; letter-spacing: 1.5px; text-align: center; margin-bottom: 12px; }

    .texto-isla, .texto-isla *, .texto-isla p, .texto-isla b { font-family: 'Montserrat', sans-serif !important; font-weight: 400 !important; line-height: 1.8 !important; font-size: 1.25rem !important; }
    .texto-isla b { font-weight: 600 !important; font-size: 0.72rem !important; text-transform: uppercase; letter-spacing: 1.5px; opacity: 0.65; }

    .bloque-azul { background: var(--azul-bg); border: 1px solid var(--azul-borde); border-left: 4px solid var(--azul); padding: 1.4rem 1.6rem; border-radius: var(--radio); margin-bottom: 1rem; box-shadow: 0 2px 12px rgba(59,125,216,0.07); }
    .bloque-verde { background: var(--verde-bg); border: 1px solid var(--verde-borde); border-left: 4px solid var(--verde); padding: 1.4rem 1.6rem; border-radius: var(--radio); margin-bottom: 1rem; box-shadow: 0 2px 12px rgba(34,166,110,0.07); }

    /* ── Resultado dictado ── */
    .resultado-porcentaje { font-family: 'Montserrat', sans-serif; font-size: 1.5rem; font-weight: 400; text-align: center; padding: 14px 20px; border-radius: var(--radio); margin-top: 10px; margin-bottom: 10px; }
    .dictado-comparacion { font-family: 'Montserrat', sans-serif; font-size: 1.1rem; line-height: 1.9; padding: 1.2rem 1.4rem; border-radius: var(--radio); background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); margin-top: 12px; }
    .palabra-ok   { color: #22a66e; font-weight: 500; }
    .palabra-mal  { color: #e05454; font-weight: 500; text-decoration: underline wavy #e05454; }
    .palabra-extra { color: #f5a623; font-weight: 500; font-style: italic; }

    .stProgress > div > div { height: 5px !important; border-radius: 99px !important; }
    .progreso-contador { font-family: 'Montserrat', sans-serif; font-size: 0.72rem; font-weight: 500; color: #8a9ab5; text-align: right; letter-spacing: 1px; margin-bottom: 4px; }
    .stButton button { border-radius: 8px !important; font-weight: 600 !important; font-size: 0.82rem !important; padding: 0.45rem 0.9rem !important; border: 1px solid rgba(255,255,255,0.08) !important; }
    
    hr { opacity: 0.15; }
    </style>
""", unsafe_allow_html=True)

# ── FUNCIONES ──
def calcular_similitud_parcial(texto_usuario, texto_original):
    def limpiar(t):
        t = t.strip().lower()
        return re.sub(r'[.,!?¿¡"\'\s\n\r\t]', '', t)
    u_limpio, o_limpio = limpiar(texto_usuario), limpiar(texto_original)
    if not u_limpio or not o_limpio: return 0
    len_u = len(u_limpio)
    len_o = len(o_limpio)
    if len_u <= len_o:
        mejor_ratio = 0.0
        for i in range(len_o - len_u + 1):
            ratio_actual = SequenceMatcher(None, u_limpio, o_limpio[i : i + len_u]).ratio()
            if ratio_actual > mejor_ratio: mejor_ratio = ratio_actual
        return mejor_ratio * 100
    else:
        return SequenceMatcher(None, u_limpio, o_limpio).ratio() * 100

def comparar_palabras(texto_usuario, texto_original):
    def tokenizar(t): return re.findall(r'\w+', t.lower())
    palabras_usuario, palabras_original = tokenizar(texto_usuario), tokenizar(texto_original)
    matcher = SequenceMatcher(None, palabras_usuario, palabras_original)
    html_usuario, html_original = [], []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            for w in palabras_usuario[i1:i2]: html_usuario.append(f'<span class="palabra-ok">{w}</span>')
            for w in palabras_original[j1:j2]: html_original.append(f'<span class="palabra-ok">{w}</span>')
        elif tag == 'replace':
            for w in palabras_usuario[i1:i2]: html_usuario.append(f'<span class="palabra-mal">{w}</span>')
            for w in palabras_original[j1:j2]: html_original.append(f'<span class="palabra-mal">{w}</span>')
        elif tag == 'delete':
            for w in palabras_usuario[i1:i2]: html_usuario.append(f'<span class="palabra-extra">{w}</span>')
        elif tag == 'insert':
            for w in palabras_original[j1:j2]: html_original.append(f'<span class="palabra-mal">▢ {w}</span>')
    return ' '.join(html_usuario), ' '.join(html_original)

def formatear_lineas(texto):
    frases = re.split(r'(?<=[.!?])\s+', texto.strip())
    return "<br>".join(frases)

# URLs
SHEET_URL   = "https://docs.google.com/spreadsheets/d/1hpP0J5qRrbx5p9W2nHWsoTDBA9hhvLZYblaU12Ln3w4/export?format=csv"
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbzUjhiwydEHUGfYaEJOXpvJf-00D1Yx3jHltLgGPpCXXc_08dL_4fugUmmY7u7EmXgM/exec"

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

# --- BARRA LATERAL ---
st.sidebar.title("Configuración")
islas_disponibles = df_total['Isla'].unique()
isla_seleccionada = st.sidebar.selectbox("🏝️ Selecciona la Isla:", islas_disponibles)
df_isla_completa = df_total[df_total['Isla'] == isla_seleccionada].copy()
total_frases_isla = len(df_isla_completa)

if 'isla_anterior' not in st.session_state or st.session_state.isla_anterior != isla_seleccionada:
    st.session_state.indice_actual = 0
    st.session_state.isla_anterior = isla_seleccionada
    st.session_state.ver_solucion = False

df_activas_y_pendientes = df_isla_completa[df_isla_completa['Estado'] != 'Azul'].copy()
df_azul = df_isla_completa[df_isla_completa['Estado'] == 'Azul']
total_aprendidos = len(df_azul)
df_en_rueda = df_activas_y_pendientes.head(15).copy()
total_rueda_actual = len(df_en_rueda)
estados_rueda = df_en_rueda['Estado'].fillna('Rojo').astype(str).str.strip().tolist()
n_rojos, n_naranjas, n_verdes = estados_rueda.count('Rojo'), estados_rueda.count('Naranja'), estados_rueda.count('Verde')

# --- RESUMEN SIDEBAR ---
st.sidebar.write("---")
st.sidebar.markdown("### 📊 Estado de la Isla")
porcentaje_isla = round((total_aprendidos / total_frases_isla * 100)) if total_frases_isla > 0 else 0
st.sidebar.markdown(f"""
<div style="font-family: 'Montserrat', sans-serif; background: rgba(255,255,255,0.04); padding: 16px 18px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.09);">
    <p style="margin: 0 0 12px 0; font-size: 0.7rem; color: #8a9ab5; font-weight: 500; text-transform: uppercase; letter-spacing: 2px;">🔄 En rueda &nbsp;·&nbsp; {total_rueda_actual}</p>
    <div style="display: flex; flex-direction: column; gap: 8px;">
        <div style="display:flex; align-items:center; gap:10px; font-size:0.9rem;"><span style="width:10px;height:10px;border-radius:50%;background:#e05454;display:inline-block;flex-shrink:0;"></span><span style="color:#e8ecf2;">{n_rojos}</span></div>
        <div style="display:flex; align-items:center; gap:10px; font-size:0.9rem;"><span style="width:10px;height:10px;border-radius:50%;background:#f5a623;display:inline-block;flex-shrink:0;"></span><span style="color:#e8ecf2;">{n_naranjas}</span></div>
        <div style="display:flex; align-items:center; gap:10px; font-size:0.9rem;"><span style="width:10px;height:10px;border-radius:50%;background:#22a66e;display:inline-block;flex-shrink:0;"></span><span style="color:#e8ecf2;">{n_verdes}</span></div>
    </div>
    <div style="margin: 14px 0 0 0; padding-top: 12px; border-top: 1px solid rgba(255,255,255,0.08); display:flex; align-items:center; justify-content:space-between;">
        <span style="color:#8a9ab5; font-size:0.8rem;">Aprendidas</span>
        <span style="font-size:1rem; font-weight:600; color:#3b7dd8;">{total_aprendidos}</span>
    </div>
</div>
""", unsafe_allow_html=True)

if total_aprendidos == total_frases_isla and total_frases_isla > 0:
    st.title("🇩🇪 Método de Chunks & Islas")
    st.balloons()
    st.success(f"🎉 ¡ESPECTACULAR! Has completado la isla '{isla_seleccionada}'.")
    st.stop()

if st.session_state.indice_actual >= total_rueda_actual:
    st.session_state.indice_actual = total_rueda_actual - 1 if total_rueda_actual > 0 else 0

# --- CONTENIDO PRINCIPAL ---
st.title("🇩🇪 Método de Chunks & Islas")
fila_actual = df_en_rueda.iloc[st.session_state.indice_actual]
castellano_texto, aleman_texto = str(fila_actual['Castellano']), str(fila_actual['Aleman'])
estado_actual = str(fila_actual['Estado']).strip()
audio_id = str(int(fila_actual['Audio_ID'])) if pd.notna(fila_actual['Audio_ID']) else "sin_audio"

pos_actual = st.session_state.indice_actual + 1
st.markdown(f'<div class="progreso-contador">{pos_actual} / {total_rueda_actual}</div>', unsafe_allow_html=True)
st.progress(pos_actual / total_rueda_actual)

col_nav_sol, col_nav_ant, col_nav_sig = st.columns([0.34, 0.33, 0.33])
with col_nav_sol:
    if st.button("👁️ Solución" if not st.session_state.ver_solucion else "🔄 Ocultar", use_container_width=True):
        st.session_state.ver_solucion = not st.session_state.ver_solucion
        st.rerun()
with col_nav_ant:
    if st.button("⬅️ Anterior", use_container_width=True) and st.session_state.indice_actual > 0:
        st.session_state.indice_actual -= 1
        st.session_state.ver_solucion = False
        st.rerun()
with col_nav_sig:
    if st.button("Siguiente ➡️", use_container_width=True) and st.session_state.indice_actual < total_rueda_actual - 1:
        st.session_state.indice_actual += 1
        st.session_state.ver_solucion = False
        st.rerun()

st.write("")
st.markdown(f'<div class="tira-historial" style="background:rgba(255,255,255,0.05);">ESTADO: {estado_actual}</div>', unsafe_allow_html=True)

if not st.session_state.ver_solucion:
    st.markdown(f'<div class="bloque-azul"><div class="texto-isla"><b>Castellano:</b><br><br>{formatear_lineas(castellano_texto)}</div></div>', unsafe_allow_html=True)
else:
    st.markdown(f'<div class="bloque-verde"><div class="texto-isla"><b>Solución:</b><br><br>{formatear_lineas(aleman_texto)}</div></div>', unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)
if col1.button("🔴", use_container_width=True): nuevo = "Rojo"
elif col2.button("🟠", use_container_width=True): nuevo = "Naranja"
elif col3.button("🟢", use_container_width=True): nuevo = "Verde"
elif col4.button("🔵", use_container_width=True): nuevo = "Azul"
else: nuevo = None

if nuevo:
    requests.post(WEB_APP_URL, params={"castellano": castellano_texto, "status": nuevo, "sumarContador": "true"})
    st.cache_data.clear()
    if st.session_state.indice_actual < total_rueda_actual - 1: st.session_state.indice_actual += 1
    st.session_state.ver_solucion = False
    st.rerun()

# --- MODO DICTADO ---
with st.expander("📝 Modo Dictado"):
    texto_usuario = st.text_area("Escribe el texto en alemán:", key=f"d_{st.session_state.indice_actual}", height=200)
    if st.button("🔍 Comprobar Dictado"):
        porcentaje = calcular_similitud_parcial(texto_usuario, aleman_texto)
        st.markdown(f'<div class="resultado-porcentaje">Resultado: {porcentaje:.0f}%</div>', unsafe_allow_html=True)
        h_u, h_o = comparar_palabras(texto_usuario, aleman_texto)
        st.markdown(f'<div class="dictado-comparacion">{h_u}</div>', unsafe_allow_html=True)

# --- ANOTACIONES ---
st.markdown("### ANOTACIONES")
anot = st.text_area("Notas", value=str(fila_actual.get('Explicacion', '')), height=150, label_visibility="collapsed")
if st.button("💾 Guardar Anotaciones"):
    requests.post(WEB_APP_URL, params={"castellano": castellano_texto, "explanation": anot})
    st.success("Guardado")
    st.rerun()
