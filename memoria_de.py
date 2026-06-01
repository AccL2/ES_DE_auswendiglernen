import streamlit as st
import pandas as pd
import os
import re
import base64
import requests
from difflib import SequenceMatcher

# ── CONFIGURACIÓN DE LA PÁGINA ──
st.set_page_config(page_title="Entrenador de Idiomas por Islas", page_icon="🇩🇪", layout="centered")

# ── CONEXIÓN DIRECTA CON SUPABASE ──
SUPABASE_URL = "https://rmmkngictdwrkmnlefad.supabase.co"
SUPABASE_KEY = "sb_publishable_YMdrOSBGEUZobOsW7MUbBQ_SWPbEaHK"

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# ── INYECTAR TIPOGRAFÍAS Y ESTILOS PREMIUM ──
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght=300;400;500;600;700&display=swap');

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

    html, body, * { font-family: 'Montserrat', sans-serif !important; }

    .stSelectbox > div, .stSelectbox label, .stRadio > div, .stRadio label,
    .stTextInput > div, .stTextInput label, .stTextArea > div, .stTextArea label,
    div[data-testid="stSelectbox"] *, div[data-testid="stTextInput"] *, div[data-testid="stTextArea"] * {
        font-family: 'Montserrat', sans-serif !important;
    }

    h1 { font-family: 'Montserrat', sans-serif !important; font-weight: 700 !important; font-size: 1.85rem !important; letter-spacing: -0.5px !important; margin-bottom: 0.25rem !important; }
    h2, h3 { font-family: 'Montserrat', sans-serif !important; font-weight: 600 !important; }

    .titulo-situacion {
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 500 !important; font-size: 0.75rem !important;
        text-transform: uppercase; letter-spacing: 2px; color: #8a9ab5;
        margin-bottom: 0.75rem; display: flex; align-items: center; gap: 6px;
    }

    .tira-historial {
        width: 100%; padding: 5px 12px; border-radius: 8px; font-size: 0.70rem;
        font-weight: 600; text-transform: uppercase; letter-spacing: 1.5px;
        text-align: center; margin-bottom: 12px;
    }

    .texto-isla, .texto-isla *, .texto-isla p, .texto-isla b {
        font-family: 'Montserrat', sans-serif !important; font-weight: 400 !important;
        line-height: 1.8 !important; font-size: 1.25rem !important;
    }
    .texto-isla b { font-weight: 600 !important; font-size: 0.72rem !important; text-transform: uppercase; letter-spacing: 1.5px; opacity: 0.65; }

    .bloque-azul {
        background: var(--azul-bg); border: 1px solid var(--azul-borde); border-left: 4px solid var(--azul);
        padding: 1.4rem 1.6rem; border-radius: var(--radio); margin-bottom: 1rem;
        box-shadow: 0 2px 12px rgba(59,125,216,0.07);
    }
    .bloque-verde {
        background: var(--verde-bg); border: 1px solid var(--verde-borde); border-left: 4px solid var(--verde);
        padding: 1.4rem 1.6rem; border-radius: var(--radio); margin-bottom: 1rem;
        box-shadow: 0 2px 12px rgba(34,166,110,0.07);
    }

    .resultado-porcentaje { font-family: 'Montserrat', sans-serif; font-size: 1.5rem; font-weight: 400; text-align: center; padding: 14px 20px; border-radius: var(--radio); margin: 10px 0; }
    .dictado-comparacion { font-family: 'Montserrat', sans-serif; font-size: 1.1rem; line-height: 1.9; padding: 1.2rem 1.4rem; border-radius: var(--radio); background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); margin-top: 12px; }
    .palabra-ok   { color: #22a66e; font-weight: 500; }
    .palabra-mal  { color: #e05454; font-weight: 500; text-decoration: underline wavy #e05454; }
    .palabra-extra { color: #f5a623; font-weight: 500; font-style: italic; }

    .stProgress > div > div { height: 5px !important; border-radius: 99px !important; }
    .progreso-contador { font-family: 'Montserrat', sans-serif; font-size: 0.72rem; font-weight: 500; color: #8a9ab5; text-align: right; letter-spacing: 1px; margin-bottom: 4px; }
    
    .stButton button { border-radius: 8px !important; font-weight: 600 !important; font-size: 0.82rem !important; padding: 0.45rem 0.9rem !important; border: 1px solid rgba(255,255,255,0.08) !important; }
    section[data-testid="stSidebar"] { border-right: 1px solid rgba(255,255,255,0.06); }
    .streamlit-expanderHeader { font-family: 'Montserrat', sans-serif !important; font-weight: 500 !important; font-size: 0.95rem !important; border-radius: 8px !important; }
    hr { opacity: 0.15; }
    </style>
""", unsafe_allow_html=True)

# ── FUNCIONES AUXILIARES DE DICTADO Y TEXTO ──
def calcular_similitud_parcial(texto_usuario, texto_original):
    def limpiar(t): return re.sub(r'[.,!?¿¡"\'\s\n\r\t]', '', t.strip().lower())
    u_limpio, o_limpio = limpiar(texto_usuario), limpiar(texto_original)
    if not u_limpio or not o_limpio: return 0
    len_u, len_o = len(u_limpio), len(o_limpio)
    if len_u <= len_o:
        mejor_ratio = 0.0
        for i in range(len_o - len_u + 1):
            ratio_actual = SequenceMatcher(None, u_limpio, o_limpio[i:i + len_u]).ratio()
            if ratio_actual > mejor_ratio: mejor_ratio = ratio_actual
        return mejor_ratio * 100
    return SequenceMatcher(None, u_limpio, o_limpio).ratio() * 100

def comparar_palabras(texto_usuario, texto_original):
    def tokenizar(t): return re.findall(r'\w+', t.lower())
    p_user, p_orig = tokenizar(texto_usuario), tokenizar(texto_original)
    matcher = SequenceMatcher(None, p_user, p_orig)
    html_u, html_o = [], []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            html_u.extend([f'<span class="palabra-ok">{w}</span>' for w in p_user[i1:i2]])
            html_o.extend([f'<span class="palabra-ok">{w}</span>' for w in p_orig[j1:j2]])
        elif tag == 'replace':
            html_u.extend([f'<span class="palabra-mal">{w}</span>' for w in p_user[i1:i2]])
            html_o.extend([f'<span class="palabra-mal">{w}</span>' for w in p_orig[j1:j2]])
        elif tag == 'delete':
            html_u.extend([f'<span class="palabra-extra">{w}</span>' for w in p_user[i1:i2]])
        elif tag == 'insert':
            html_o.extend([f'<span class="palabra-mal">▢ {w}</span>' for w in p_orig[j1:j2]])
    return ' '.join(html_u), ' '.join(html_o)

def formatear_lineas(texto):
    return "<br>".join(re.split(r'(?<=[.!?])\s+', texto.strip()))

# ── LOGICA DE LLAMADAS API SUPABASE ──
def obtener_tarjetas_isla(isla):
    url = f"{SUPABASE_URL}/rest/v1/tarjetas?Isla=ilike.{isla}&order=id.asc"
    res = requests.get(url, headers=headers)
    return pd.DataFrame(res.json()) if res.status_code == 200 and res.json() else pd.DataFrame()

def obtener_islas_disponibles():
    url = f"{SUPABASE_URL}/rest/v1/tarjetas?select=Isla"
    res = requests.get(url, headers=headers)
    if res.status_code == 200 and res.json():
        return list(set([item['Isla'] for item in res.json()]))
    return ["Chunks"]

def obtener_puntero_actual():
    url = f"{SUPABASE_URL}/rest/v1/puntero?id=eq.1&select=posicion_actual"
    res = requests.get(url, headers=headers)
    if res.status_code == 200 and res.json():
        return res.json()[0]['posicion_actual']
    return 0

def actualizar_puntero_db(nueva_pos):
    url = f"{SUPABASE_URL}/rest/v1/puntero?id=eq.1"
    requests.patch(url, headers=headers, json={"posicion_actual": nueva_pos})

def actualizar_estado_tarjeta(id_tarjeta, nuevo_estado_int):
    url = f"{SUPABASE_URL}/rest/v1/tarjetas?id=eq.{id_tarjeta}"
    requests.patch(url, headers=headers, json={"Estado": nuevo_estado_int})

def actualizar_anotacion_tarjeta(id_tarjeta, texto_nota):
    url = f"{SUPABASE_URL}/rest/v1/tarjetas?id=eq.{id_tarjeta}"
    requests.patch(url, headers=headers, json={"Explicacion": texto_nota})


# ── CONFIGURACIÓN BARRA LATERAL ──
st.sidebar.title("Configuración")
islas = obtener_islas_disponibles()
isla_seleccionada = st.sidebar.selectbox("🏝️ Selecciona la Isla:", islas)

# Cargar las frases de la isla elegida desde Supabase
df_total = obtener_tarjetas_isla(isla_seleccionada)

if df_total.empty:
    st.warning(f"La isla '{isla_seleccionada}' todavía no tiene tarjetas dentro.")
    st.stop()

# TRATAMIENTO DE LOS ESTADOS COMO NÚMEROS LIMPIOS
df_total['Estado'] = pd.to_numeric(df_total['Estado'], errors='coerce').fillna(1).astype(int)

# Separar las tarjetas en rueda (1, 2, 3) de las aprendidas (4 = Azul)
df_rueda = df_total[df_total['Estado'] != 4].copy()
df_azul = df_total[df_total['Estado'] == 4].copy()

total_frases_isla = len(df_total)
total_aprendidos = len(df_azul)
total_rueda_actual = len(df_rueda)

# Sincronizar el puntero leyendo la base de datos de forma segura
if 'indice_actual' not in st.session_state:
    pos_db = obtener_puntero_actual()
    st.session_state.indice_actual = pos_db if pos_db < total_rueda_actual else 0
    st.session_state.ver_solucion = False

# 🚨 LÍNEA DE SEGURIDAD EXTRA: Si el índice en memoria es mayor o igual al total actual, lo reseteamos a 0
if st.session_state.indice_actual >= total_rueda_actual:
    st.session_state.indice_actual = 0
    
# --- RENDIMIENTO Y RESUMEN SIDEBAR ---
estados_lista = df_rueda['Estado'].tolist()
n_rojos = estados_lista.count(1)
n_naranjas = estados_lista.count(2)
n_verdes = estados_lista.count(3)
porcentaje_isla = round((total_aprendidos / total_frases_isla * 100)) if total_frases_isla > 0 else 0

st.sidebar.write("---")
st.sidebar.markdown("### 📊 Estado de la Isla")
st.sidebar.markdown(f"""
<div style="background: rgba(255,255,255,0.04); padding: 16px 18px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.09);">
    <p style="margin: 0 0 12px 0; font-size: 0.7rem; color: #8a9ab5; font-weight: 500; text-transform: uppercase; letter-spacing: 2px;">🔄 En rueda &nbsp;·&nbsp; {total_rueda_actual}</p>
    <div style="display: flex; flex-direction: column; gap: 8px;">
        <div style="display:flex; align-items:center; gap:10px; font-size:0.9rem;"><span style="width:10px;height:10px;border-radius:50%;background:#e05454;display:inline-block;"></span><span style="color:#e8ecf2;">{n_rojos} &nbsp;<span style="color:#8a9ab5;font-size:0.8rem;">Nuevas / Malas</span></span></div>
        <div style="display:flex; align-items:center; gap:10px; font-size:0.9rem;"><span style="width:10px;height:10px;border-radius:50%;background:#f5a623;display:inline-block;"></span><span style="color:#e8ecf2;">{n_naranjas} &nbsp;<span style="color:#8a9ab5;font-size:0.8rem;">A medias</span></span></div>
        <div style="display:flex; align-items:center; gap:10px; font-size:0.9rem;"><span style="width:10px;height:10px;border-radius:50%;background:#22a66e;display:inline-block;"></span><span style="color:#e8ecf2;">{n_verdes} &nbsp;<span style="color:#8a9ab5;font-size:0.8rem;">Casi listas</span></span></div>
    </div>
    <div style="margin: 14px 0 0 0; padding-top: 12px; border-top: 1px solid rgba(255,255,255,0.08); display:flex; align-items:center; justify-content:space-between;">
        <span style="color:#8a9ab5; font-size:0.8rem;">🔵 Aprendidas</span>
        <span style="font-size:1rem; font-weight:600; color:#3b7dd8;">{total_aprendidos}<span style="color:#8a9ab5; font-weight:400; font-size:0.82rem;"> / {total_frases_isla}</span></span>
    </div>
    <div style="margin-top: 12px;">
        <div style="height: 5px; background: rgba(255,255,255,0.08); border-radius: 99px; overflow: hidden;"><div style="height: 100%; width: {porcentaje_isla}%; background: #3b7dd8; border-radius: 99px;"></div></div>
        <p style="margin: 5px 0 0 0; font-size: 0.72rem; color: #8a9ab5; text-align: right;">{porcentaje_isla}% completada</p>
    </div>
</div>
""", unsafe_allow_html=True)

# 📦 UN SÓLO BOTÓN DISCRETO EN LA SIDEBAR (SIN TEXTO ACUMULADO)
st.sidebar.write("---")
abrir_modal_jubiladas = st.sidebar.button("📦 Ver Almacén de Jubiladas", use_container_width=True, disabled=(total_aprendidos == 0))
if total_aprendidos == 0:
    st.sidebar.caption("Aún no tienes tarjetas jubiladas.")


# ── VENTANA MODAL (POPUP FLOTANTE) PARA REPASAR Y RECUPERAR JUBILADAS ──
if abrir_modal_jubiladas:
    @st.dialog("📦 Almacén de Frases Jubiladas")
    def mostrar_popup_jubiladas():
        st.write("Estas son tus frases guardadas en azul. Puedes repasarlas y, si quieres, devolverlas a la rueda activa:")
        st.write("---")
        for _, row in df_azul.iterrows():
            col_txt, col_btn = st.columns([0.75, 0.25])
            with col_txt:
                st.markdown(f"**ES:** {row['Español']}")
                st.markdown(f"*DE:* {row['Aleman']}")
            with col_btn:
                # El botón de recuperar ahora va fino dentro de la ventana flotante
                if st.button("♻️ Traer", key=f"popup_rec_{row['id']}", use_container_width=True):
                    actualizar_estado_tarjeta(int(row['id']), 1)
                    st.toast("¡Tarjeta devuelta a la rueda activa!")
                    st.rerun()
            st.write("---")
            
    mostrar_popup_jubiladas()


# ── COMPROBACIÓN DE FIN DE ISLA ──
if total_aprendidos == total_frases_isla:
    st.title("🇩🇪 Método de Chunks & Islas")
    st.balloons()
    st.success(f"🎉 ¡ESPECTACULAR! Has completado la isla '{isla_seleccionada}' al 100%.")
    
    st.write("")
    st.markdown("### 🔄 ¿Quieres volver a estudiar esta isla?")
    if st.button("♻️ Reiniciar progreso de la Isla", use_container_width=True):
        url_reset = f"{SUPABASE_URL}/rest/v1/tarjetas?Isla=ilike.{isla_seleccionada}"
        requests.patch(url_reset, headers=headers, json={"Estado": 1})
        actualizar_puntero_db(0)
        if 'indice_actual' in st.session_state:
            st.session_state.indice_actual = 0
        st.toast("Isla reseteada. ¡A por ella!")
        st.rerun()
    st.stop()


# ── CONTENIDO PRINCIPAL DE LA APP ──
st.title("🇩🇪 Método de Chunks & Islas")

# Extraer datos reales de la tarjeta actual de la rueda
fila_actual = df_rueda.iloc[st.session_state.indice_actual]
id_tarjeta       = int(fila_actual['id'])
castellano_texto = str(fila_actual['Español'])
aleman_texto     = str(fila_actual['Aleman'])
estado_actual    = int(fila_actual['Estado'])
audio_id         = str(fila_actual['Audio_ID']).strip()
situacion_texto  = str(fila_actual['Situacion']).strip() if pd.notna(fila_actual['Situacion']) else ""

# Contador gráfico superior
pos_pantalla = st.session_state.indice_actual + 1
st.markdown(f'<div class="progreso-contador">{pos_pantalla} / {total_rueda_actual}</div>', unsafe_allow_html=True)
st.progress(pos_pantalla / total_rueda_actual)

if situacion_texto and situacion_texto != "None":
    st.markdown(f'<div class="titulo-situacion">📍 {situacion_texto}</div>', unsafe_allow_html=True)

# ── BOTONES DE NAVEGACIÓN ──
col_nav_sol, col_nav_ant, col_nav_sig = st.columns([0.34, 0.33, 0.33])

with col_nav_sol:
    if not st.session_state.ver_solucion:
        if st.button("👁️ Solución", use_container_width=True):
            st.session_state.ver_solucion = True
            st.rerun()
    else:
        if st.button("🔄 Ocultar", use_container_width=True):
            st.session_state.ver_solucion = False
            st.rerun()

with col_nav_ant:
    if st.button("⬅️ Anterior", use_container_width=True):
        if st.session_state.indice_actual > 0:
            st.session_state.indice_actual -= 1
            actualizar_puntero_db(st.session_state.indice_actual)
            st.session_state.ver_solucion = False
            st.rerun()

with col_nav_sig:
    if st.button("Siguiente ➡️", use_container_width=True):
        if st.session_state.indice_actual < total_rueda_actual - 1:
            st.session_state.indice_actual += 1
            actualizar_puntero_db(st.session_state.indice_actual)
            st.session_state.ver_solucion = False
            st.rerun()

st.write("")

# Tira de color pastel decorativa según su nivel numérico
bg_tira, color_tira = "rgba(59, 125, 216, 0.15)", "#3b7dd8"
if estado_actual == 1:   bg_tira, color_tira = "rgba(224, 84, 84, 0.15)", "#e05454"
elif estado_actual == 2: bg_tira, color_tira = "rgba(245, 158, 11, 0.15)", "#f59e0b"
elif estado_actual == 3: bg_tira, color_tira = "rgba(34, 166, 110, 0.15)", "#22a66e"

st.markdown(f'<div class="tira-historial" style="background-color: {bg_tira}; color: {color_tira}; border: 1px solid {color_tira}44;">ESTADO ACTUAL</div>', unsafe_allow_html=True)

# Bloque de contenido central (Pregunta o Solución)
if not st.session_state.ver_solucion:
    st.markdown(f'<div class="bloque-azul"><div class="texto-isla"><b>Castellano (Lee y piensa):</b><br><br>{formatear_lineas(castellano_texto)}</div></div>', unsafe_allow_html=True)
else:
    st.markdown(f'<div class="bloque-verde"><div class="texto-isla"><b>Solución en Alemán:</b><br><br>{formatear_lineas(aleman_texto)}</div></div>', unsafe_allow_html=True)

# ── BOTONES PARA CAMBIAR EL ESTADO (PASANDO NÚMEROS DIRECTOS) ──
col_c1, col_c2, col_c3, col_c4 = st.columns(4)
nuevo_estado_num = None

with col_c1:
    if st.button("🔴", use_container_width=True): nuevo_estado_num = 1
with col_c2:
    if st.button("🟠", use_container_width=True): nuevo_estado_num = 2
with col_c3:
    if st.button("🟢", use_container_width=True): nuevo_estado_num = 3
with col_c4:
    if st.button("🔵", use_container_width=True): nuevo_estado_num = 4

if nuevo_estado_num is not None:
    # 1. Guardar en Supabase
    actualizar_estado_tarjeta(id_tarjeta, nuevo_estado_num)
    st.toast(f"Nivel {nuevo_estado_num} guardado en la nube")
    
    # ACTUALIZACIÓN EN VIVO: Modificamos el DataFrame local
    df_total.loc[df_total['id'] == id_tarjeta, 'Estado'] = nuevo_estado_num
    
    # Avanzar inteligentemente de tarjeta
    if st.session_state.indice_actual < total_rueda_actual - 1:
        if nuevo_estado_num != 4:
            st.session_state.indice_actual += 1
    else:
        st.session_state.indice_actual = 0
        
    actualizar_puntero_db(st.session_state.indice_actual)
    st.session_state.ver_solucion = False
    st.rerun()


# ── REPRODUCTOR DE AUDIO INTERACTIVO (WAVESURFER.JS) ──
ruta_audio = f"Audios/{audio_id}.mp3"
if os.path.exists(ruta_audio):
    st.markdown('<p style="font-weight:600; font-size:0.95rem; margin-bottom:8px;">🎧 Onda de audio interactiva:</p>', unsafe_allow_html=True)
    with open(ruta_audio, "rb") as f:
        b64_audio = base64.b64encode(f.read()).decode()

    html_reproductor = f"""
    <div class="audio-player" style="font-family:'Montserrat'; background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.1); padding:16px; border-radius:14px; color:#e8ecf2;">
        <div style="margin-bottom:14px; background:rgba(0,0,0,0.25); border-radius:8px; padding:6px 6px 2px; cursor:pointer;"><div id="waveform"></div></div>
        <div style="display:flex; justify-content:center; align-items:center; gap:8px; margin-bottom:12px;">
            <button id="btnBack" style="padding:7px 15px; background:rgba(255,255,255,0.08); color:#e8ecf2; border:1px solid rgba(255,255,255,0.12); border-radius:8px; cursor:pointer;">⏮ −5s</button>
            <button id="btnPlay" style="padding:8px 22px; background:#3b7dd8; color:white; border:none; border-radius:8px; cursor:pointer; font-weight:600; min-width:96px;">▶ Play</button>
            <button id="btnForward" style="padding:7px 15px; background:rgba(255,255,255,0.08); color:#e8ecf2; border:1px solid rgba(255,255,255,0.12); border-radius:8px; cursor:pointer;">+5s ⏭</button>
            <button id="btnResetRegion" style="padding:7px 15px; background:rgba(224,84,84,0.15); color:#e05454; border:1px solid rgba(224,84,84,0.3); border-radius:8px; cursor:pointer;">✕ Reset</button>
        </div>
        <div style="display:flex; align-items:center; gap:12px; background:rgba(0,0,0,0.18); padding:8px 14px; border-radius:10px;">
            <span style="font-size:0.78rem; color:#8a9ab5;">⚡ Velocidad</span>
            <input type="range" id="speedSlider" min="0.5" max="2.0" step="0.1" value="1.0" style="flex-grow:1; accent-color:#3b7dd8; margin:0; cursor:pointer;">
            <span id="speedValue" style="font-size:0.88rem; font-weight:600; color:#3b7dd8; min-width:38px; text-align:right;">1.0×</span>
        </div>
    </div>
    <script src="https://unpkg.com/wavesurfer.js@7"></script>
    <script src="https://unpkg.com/wavesurfer.js@7/dist/plugins/regions.min.js"></script>
    <script>
        const wavesurfer = WaveSurfer.create({{ container: '#waveform', waveColor: '#4a5568', progressColor: '#3b7dd8', cursorColor: '#e05454', barWidth: 2, barGap: 2, barRadius: 3, height: 60, url: 'data:audio/mp3;base64,{b64_audio}' }});
        const wsRegions = wavesurfer.registerPlugin(WaveSurfer.Regions.create());
        wsRegions.enableDragSelection({{ color: 'rgba(59, 130, 246, 0.3)' }});
        wsRegions.on('region-created', (region) => {{ wsRegions.getRegions().forEach(r => {{ if (r !== region) r.remove(); }}); }});
        wavesurfer.on('timeupdate', (t) => {{ const r = wsRegions.getRegions(); if (r.length > 0 && (t >= r[0].end || t < r[0].start)) wavesurfer.setTime(r[0].start); }});
        document.getElementById('btnResetRegion').addEventListener('click', () => wsRegions.clearRegions());
        const btnPlay = document.getElementById('btnPlay');
        btnPlay.addEventListener('click', () => wavesurfer.playPause());
        wavesurfer.on('play', () => {{ btnPlay.innerHTML = "⏸ Pausa"; btnPlay.style.background = "#22a66e"; }});
        wavesurfer.on('pause', () => {{ btnPlay.innerHTML = "▶ Play"; btnPlay.style.background = "#3b7dd8"; }});
        document.getElementById('btnBack').addEventListener('click', () => wavesurfer.skip(-5));
        document.getElementById('btnForward').addEventListener('click', () => wavesurfer.skip(5));
        const slider = document.getElementById('speedSlider');
        slider.addEventListener('input', (e) => {{ wavesurfer.setPlaybackRate(parseFloat(e.target.value)); document.getElementById('speedValue').innerHTML = parseFloat(e.target.value).toFixed(1) + "×"; }});
    </script>
    """
    st.components.v1.html(html_reproductor, height=215)
else:
    st.warning(f"⚠️ Audio no encontrado en local: `{ruta_audio}`")


# ── MODO DICTADO (COMPARADOR DE TEXTO) ──
with st.expander("📝 Modo Dictado"):
    texto_usuario = st.text_area("Escribe el texto en alemán:", key=f"dictado_{id_tarjeta}", height=200)
    if st.button("🔍 Comprobar Dictado", use_container_width=True):
        if texto_usuario:
            porcentaje = calcular_similitud_parcial(texto_usuario, aleman_texto)
            bg, tx = ("rgba(16, 185, 129, 0.15)", "#10b981") if porcentaje >= 90 else (("rgba(245, 158, 11, 0.15)", "#f59e0b") if porcentaje >= 50 else ("rgba(239, 68, 68, 0.15)", "#ef4444"))
            st.markdown(f'<div class="resultado-porcentaje" style="background-color:{bg}; color:{tx}; border:1px solid {tx};">De lo que has escrito: {porcentaje:.0f}% bien</div>', unsafe_allow_html=True)
            
            html_u, html_o = comparar_palabras(texto_usuario, aleman_texto)
            st.markdown(f"""
            <div class="dictado-comparacion">
                <div style="font-size:0.7rem; font-weight:600; text-transform:uppercase; color:#8a9ab5; margin-bottom:8px;">Tu versión</div><div style="margin-bottom:14px;">{html_u}</div>
                <div style="font-size:0.7rem; font-weight:600; text-transform:uppercase; color:#8a9ab5; margin-bottom:8px;">Versión correcta</div><div>{html_o}</div>
            </div>
            """, unsafe_allow_html=True)


# ── ANOTACIONES EN VIVO ──
anotacion_inicial = str(fila_actual['Explicacion']) if pd.notna(fila_actual['Explicacion']) else ""
st.markdown('<div style="font-size: 0.85rem; font-weight: 700; text-transform: uppercase; color: #8a9ab5; margin-top: 1.5rem; margin-bottom: 8px;">ANOTACIONES</div>', unsafe_allow_html=True)

texto_anotaciones = st.text_area("Notas", value=anotacion_inicial, key=f"notas_{id_tarjeta}", height=120, label_visibility="collapsed")

if st.button("💾 Guardar Anotaciones", use_container_width=True):
    actualizar_anotacion_tarjeta(id_tarjeta, texto_anotaciones)
    st.toast("✅ Anotaciones sincronizadas en Supabase")
