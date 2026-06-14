import streamlit as st
import pandas as pd
import os
import re
import base64
import requests
from datetime import datetime, timezone
from difflib import SequenceMatcher

@st.cache_data
def cargar_diccionario_aleman():
    """Carga el diccionario de géneros alemanes desde GitHub como dict {palabra: género}."""
    try:
        url = "https://raw.githubusercontent.com/gambolputty/german-nouns/master/german_nouns/nouns.csv"
        df = pd.read_csv(url, usecols=['lemma', 'genus'], dtype=str)
        df = df.dropna(subset=['lemma', 'genus'])
        # Quedarse con la primera entrada por palabra (evita duplicados con género incorrecto)
        df = df.drop_duplicates(subset=['lemma'], keep='first')
        return dict(zip(df['lemma'], df['genus']))
    except Exception:
        return {}

# ── CORRECCIONES MANUALES (tienen prioridad sobre el diccionario) ──
_CORRECCIONES_GENERO = {
    'Kaffee': 'm', 'Tee': 'm', 'Restaurant': 'n',
    'Computer': 'm', 'Hotel': 'n', 'Cafe': 'n',
    'Auto': 'n', 'Radio': 'n', 'Taxi': 'n',
    'Baby': 'n', 'Sofa': 'n', 'Thema': 'n',
}

def genero_sustantivo(palabra):
    if palabra in _CORRECCIONES_GENERO:
        return _CORRECCIONES_GENERO[palabra]
    diccionario = cargar_diccionario_aleman()
    return diccionario.get(palabra)

# ── TAMAÑO DE LA RUEDA ──
TAMANYO_RUEDA = 5  # Cambia este número para ajustar el tamaño de la rueda activa

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

# ── REPASO ESPACIADO: FUNCIONES ──
def obtener_jubilada_repaso(ids_en_rueda):
    """Obtiene la jubilada cuya fecha_repaso <= hoy, con id más bajo. Si tiene fecha_repaso=null la incluye también."""
    try:
        hoy = datetime.now(timezone.utc).isoformat()
        url = f"{SUPABASE_URL}/rest/v1/tarjetas?Isla=eq.{isla_seleccionada}&Estado=eq.4&or=(fecha_repaso.lte.{hoy},fecha_repaso.is.null)&order=id.asc&limit=1"
        r = requests.get(url, headers=headers)
        datos = r.json()
        if datos:
            tid = int(datos[0]['id'])
            if tid not in ids_en_rueda:
                return datos[0]
    except Exception:
        pass
    return None

def actualizar_repaso_espaciado(id_tarjeta, intervalo_actual):
    """Cuando se vuelve a jubilar una tarjeta de repaso, duplica el intervalo y programa la próxima fecha."""
    try:
        nuevo_intervalo = max(1, int(intervalo_actual or 1)) * 2
        from datetime import timedelta
        proxima = (datetime.now(timezone.utc) + timedelta(days=nuevo_intervalo)).isoformat()
        url = f"{SUPABASE_URL}/rest/v1/tarjetas?id=eq.{id_tarjeta}"
        requests.patch(url, headers=headers, json={"fecha_repaso": proxima, "intervalo_repaso": nuevo_intervalo})
    except Exception:
        pass

def inicializar_repaso(id_tarjeta):
    """Primera vez que se jubila una tarjeta: intervalo=1, fecha_repaso=ahora."""
    try:
        from datetime import timedelta
        proxima = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()
        url = f"{SUPABASE_URL}/rest/v1/tarjetas?id=eq.{id_tarjeta}"
        requests.patch(url, headers=headers, json={"fecha_repaso": proxima, "intervalo_repaso": 1})
    except Exception:
        pass

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

    .stApp, .stSelectbox, .stTextArea, .stTextInput, .stButton button, .streamlit-expanderHeader, .titulo-situacion, .tira-historial, .texto-isla, .resultado-porcentaje, .dictado-comparacion, .progreso-contador {
        font-family: 'Montserrat', sans-serif !important;
    }

    /* TEXTAREA DE ANOTACIONES ULTRA ADAPTATIVA Y DE ALTO CONTRASTE */
    div[data-testid="stTextArea"] textarea {
        font-size: 1.25rem !important;
        font-weight: 500 !important; 
        line-height: 1.6 !important;
        font-family: 'Montserrat', sans-serif !important;
        background-color: rgba(255, 255, 255, 0.05) !important;
        color: inherit !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
    }

    h1 { font-family: 'Montserrat', sans-serif !important; font-weight: 700 !important; font-size: 1.85rem !important; letter-spacing: -0.5px !important; margin-bottom: 0.25rem !important; }
    h2, h3 { font-family: 'Montserrat', sans-serif !important; font-weight: 600 !important; }

    .titulo-situacion {
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
        font-weight: 400 !important; line-height: 1.8 !important; font-size: 1.25rem !important;
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

    .info-tiempos {
        display: flex; gap: 14px; background: rgba(255,255,255,0.03); 
        padding: 6px 12px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.05);
        font-size: 0.78rem; color: #a0aec0; margin-bottom: 12px; font-weight: 500;
    }

    .resultado-porcentaje { font-size: 1.5rem; font-weight: 400; text-align: center; padding: 14px 20px; border-radius: var(--radio); margin: 10px 0; }
    .dictado-comparacion { font-size: 1.1rem; line-height: 1.9; padding: 1.2rem 1.4rem; border-radius: var(--radio); background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); margin-top: 12px; }
    .palabra-ok   { color: #22a66e; font-weight: 500; }
    .palabra-mal  { color: #e05454; font-weight: 500; text-decoration: underline wavy #e05454; }
    .palabra-extra { color: #f5a623; font-weight: 500; font-style: italic; }

    .progreso-contador { font-size: 0.72rem; font-weight: 500; color: #8a9ab5; text-align: right; letter-spacing: 1px; margin-bottom: 4px; }
    
    .stButton button { border-radius: 8px !important; font-weight: 600 !important; font-size: 0.82rem !important; padding: 0.45rem 0.9rem !important; border: 1px solid rgba(255,255,255,0.08) !important; }
    section[data-testid="stSidebar"] { border-right: 1px solid rgba(255,255,255,0.06); }
    .streamlit-expanderHeader { font-weight: 500 !important; font-size: 0.95rem !important; border-radius: 8px !important; }
    hr { opacity: 0.15; }
    </style>
""", unsafe_allow_html=True)

# ── FUNCIONES AUXILIARES DE TIEMPOS Y TEXTO ──
def formatear_antiguedad(fecha_entrada_str, segundos_banco=0):
    if not fecha_entrada_str:
        return "⏳ Nuevo hoy"
    try:
        fecha_entrada = datetime.fromisoformat(fecha_entrada_str.replace("Z", "+00:00"))
        ahora = datetime.now(timezone.utc)
        segundos_activos = (ahora - fecha_entrada).total_seconds()
        total_segundos = max(0, segundos_activos + (segundos_banco or 0))
        
        horas = total_segundos / 3600
        
        if horas < 12:
            return "⏳ Entró hoy a la rueda"
        elif horas < 24:
            return "⏳ Entró ayer a la rueda"
        else:
            dias = int(total_segundos / 86400)
            if dias == 1:
                return "⏳ Lleva 1 día en la rueda"
            return f"⏳ Lleva {dias} días en la rueda"
    except:
        return "⏳ Nuevo hoy"

def formatear_ultimo_click(fecha_click_str):
    if not fecha_click_str:
        return "👀 Sin repasar hoy"
    try:
        fecha_click = datetime.fromisoformat(fecha_click_str.replace("Z", "+00:00"))
        ahora = datetime.now(timezone.utc)
        dif_segundos = (ahora - fecha_click).total_seconds()
        
        if dif_segundos < 60:
            return "👀 Repasado ahora mismo"
        minutos = dif_segundos / 60
        if minutos < 60:
            return f"👀 Visto hace {int(minutos)} min"
        horas = minutos / 60
        if horas < 24:
            return f"👀 Visto hace {int(horas)} h"
        return f"👀 Visto hace {int(horas/24)} días"
    except:
        return "👀 Sin repasar hoy"

def calcular_similitul_parcial(texto_usuario, texto_original):
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

# Colores por género gramatical alemán
_COLOR_GENERO = {'m': '#3b7dd8', 'f': '#e05454', 'n': '#22a66e'}

def colorear_sustantivos(texto):
    """Envuelve sustantivos alemanes en <span> de color según género."""
    if not cargar_diccionario_aleman():
        return texto

    def reemplazar(match):
        palabra = match.group(0)
        # Ignorar si es todo mayúsculas (sigla) o muy corta
        if len(palabra) < 3 or palabra.isupper():
            return palabra
        genero = genero_sustantivo(palabra)
        if genero and genero in _COLOR_GENERO:
            color = _COLOR_GENERO[genero]
            return f'<span style="color:{color};font-weight:600">{palabra}</span>'
        return palabra

    # Busca palabras que empiecen en mayúscula pero NO sean la primera de la frase
    # (precedidas por espacio, coma, paréntesis... no por inicio de línea o tras punto)
    return re.sub(r'(?<=\s)[A-ZÄÖÜ][a-zäöüß]+', reemplazar, texto)

def formatear_lineas(texto, colorear=False):
    # 1. Separamos por frases respetando puntos finales (. ! ?) para saltar renglón cómodamente
    frases = re.split(r'(?<=[.!?])\s+', texto.strip())
    texto_con_renglones = '<br>'.join(frases)
    
    # 2. Convertimos el formato de barras |palabra| en etiquetas HTML reales de negrita
    texto_final = re.sub(r'\|([^|]+)\|', r'<strong>\1</strong>', texto_con_renglones)
    
    # 3. Colorear sustantivos alemanes si se solicita
    if colorear:
        texto_final = colorear_sustantivos(texto_final)
    
    return texto_final

# ── LOGICA DE LLAMADAS API SUPABASE ──
def obtener_todas_tarjetas_isla(isla):
    url = f"{SUPABASE_URL}/rest/v1/tarjetas?Isla=ilike.{isla}&order=id.asc"
    res = requests.get(url, headers=headers)
    return pd.DataFrame(res.json()) if res.status_code == 200 and res.json() else pd.DataFrame()

def obtener_islas_disponibles():
    url = f"{SUPABASE_URL}/rest/v1/tarjetas?select=Isla"
    res = requests.get(url, headers=headers)
    if res.status_code == 200 and res.json():
        islas_limpias = [item['Isla'] for item in res.json() if item.get('Isla')]
        return sorted(list(set(islas_limpias)))
    return ["Chunks"]

def obtener_datos_puntero_db():
    url = f"{SUPABASE_URL}/rest/v1/puntero?id=eq.1"
    res = requests.get(url, headers=headers)
    if res.status_code == 200 and res.json():
        data = res.json()[0]
        pos = data.get('posicion_actual', 0)
        rueda_str = data.get('rueda_ids', "")
        isla_guardada = data.get('isla_actual', None)
        ids = [int(x.strip()) for x in rueda_str.split(',') if x.strip().isdigit()] if rueda_str else []
        return pos, ids, isla_guardada
    return 0, [], None

def guardar_estado_puntero_db(pos, lista_ids, nombre_isla=None):
    if len(lista_ids) > 15:
        lista_ids = lista_ids[:15]
    url = f"{SUPABASE_URL}/rest/v1/puntero?id=eq.1"
    rueda_str = ",".join(map(str, lista_ids))
    body = {"posicion_actual": pos, "rueda_ids": rueda_str}
    if nombre_isla:
        body["isla_actual"] = nombre_isla
    requests.patch(url, headers=headers, json=body)

def actualizar_estado_tarjeta(id_tarjeta, nuevo_estado_int, estampar_click=False):
    url = f"{SUPABASE_URL}/rest/v1/tarjetas?id=eq.{id_tarjeta}"
    body = {"Estado": nuevo_estado_int}
    if estampar_click:
        body["fecha_ultimo_click"] = datetime.now(timezone.utc).isoformat()
    requests.patch(url, headers=headers, json=body)

def cambiar_importancia_tarjeta(id_tarjeta, estado_bool):
    url = f"{SUPABASE_URL}/rest/v1/tarjetas?id=eq.{id_tarjeta}"
    requests.patch(url, headers=headers, json={"importante": estado_bool})

def inicializar_fecha_entrada_rueda(id_tarjeta):
    url = f"{SUPABASE_URL}/rest/v1/tarjetas?id=eq.{id_tarjeta}"
    requests.patch(url, headers=headers, json={
        "fecha_entrada_rueda": datetime.now(timezone.utc).isoformat(),
        "segundos_acumulados_banco": 0
    })

def congelar_temporizador_banquillo(id_tarjeta, fecha_entrada_str, segundos_banco_actuales=0):
    if not fecha_entrada_str:
        return
    try:
        fecha_entrada = datetime.fromisoformat(fecha_entrada_str.replace("Z", "+00:00"))
        ahora = datetime.now(timezone.utc)
        segundos_en_esta_ronda = (ahora - fecha_entrada).total_seconds()
        nuevo_total_acumulado = int(segundos_en_esta_ronda + (segundos_banco_actuales or 0))
        
        url = f"{SUPABASE_URL}/rest/v1/tarjetas?id=eq.{id_tarjeta}"
        requests.patch(url, headers=headers, json={
            "fecha_entrada_rueda": None,
            "segundos_acumulados_banco": nuevo_total_acumulado
        })
    except:
        pass

def actualizar_anotacion_tarjeta(id_tarjeta, texto_nota):
    url = f"{SUPABASE_URL}/rest/v1/tarjetas?id=eq.{id_tarjeta}"
    requests.patch(url, headers=headers, json={"Explicacion": texto_nota})


# ── SINTONIZACIÓN MULTIDISPOSITIVO AL ARRANCAR ──
pos_db, ids_rueda_db, isla_guardada_db = obtener_datos_puntero_db()

# ── CONFIGURACIÓN BARRA LATERAL ──
st.sidebar.title("Configuración")
islas = obtener_islas_disponibles()

indice_defecto = 0
if isla_guardada_db and isla_guardada_db in islas:
    indice_defecto = islas.index(isla_guardada_db)

isla_seleccionada = st.sidebar.selectbox("🏝️ Selecciona la Isla:", islas, index=indice_defecto)

filtrar_favoritas_sidebar = st.sidebar.checkbox("⭐ Ver solo VIPs en el Almacén")

df_universo = obtener_todas_tarjetas_isla(isla_seleccionada)

if df_universo.empty:
    st.warning(f"La isla '{isla_seleccionada}' todavía no tiene tarjetas dentro.")
    st.stop()

df_universo['id'] = df_universo['id'].astype(int)
df_universo['Estado'] = pd.to_numeric(df_universo['Estado'], errors='coerce').fillna(1).astype(int)
if 'importante' in df_universo.columns:
    df_universo['importante'] = df_universo['importante'].fillna(False).astype(bool)
else:
    df_universo['importante'] = False

df_activas_universo = df_universo[df_universo['Estado'] != 4].copy()
df_jubiladas_universo = df_universo[df_universo['Estado'] == 4].copy()

if filtrar_favoritas_sidebar:
    df_jubiladas_muestra = df_jubiladas_universo[df_jubiladas_universo['importante'] == True].copy()
else:
    df_jubiladas_muestra = df_jubiladas_universo.copy()

total_frases_isla = len(df_universo)
total_aprendidos = len(df_jubiladas_universo)

ids_validos_rueda = []
if ids_rueda_db and isla_seleccionada == isla_guardada_db:
    for tid in ids_rueda_db:
        if tid in df_activas_universo['id'].values:
            ids_validos_rueda.append(tid)

if len(ids_validos_rueda) > TAMANYO_RUEDA:
    ids_validos_rueda = ids_validos_rueda[:TAMANYO_RUEDA]

tarjetas_inyectadas = []
while len(ids_validos_rueda) < TAMANYO_RUEDA:
    tarjetas_candidatas = [tid for tid in df_activas_universo['id'].values if tid not in ids_validos_rueda]
    if not tarjetas_candidatas:
        break
    nueva_id = tarjetas_candidatas[0]
    ids_validos_rueda.append(nueva_id)
    tarjetas_inyectadas.append(nueva_id)

if len(ids_validos_rueda) > TAMANYO_RUEDA:
    ids_validos_rueda = ids_validos_rueda[:TAMANYO_RUEDA]

for tid in tarjetas_inyectadas:
    fila_raw = df_universo[df_universo['id'] == tid].iloc[0]
    if pd.isna(fila_raw.get('fecha_entrada_rueda')) or fila_raw.get('fecha_entrada_rueda') is None:
        inicializar_fecha_entrada_rueda(tid)

# ── TARJETA JUBILADA DE REPASO (slot extra) ──
fila_jubilada_repaso = obtener_jubilada_repaso(ids_validos_rueda)
id_jubilada_repaso = int(fila_jubilada_repaso['id']) if fila_jubilada_repaso else None

if ids_validos_rueda != ids_rueda_db or isla_seleccionada != isla_guardada_db:
    if isla_seleccionada != isla_guardada_db:
        pos_db = 0
    guardar_estado_puntero_db(pos_db, ids_validos_rueda, nombre_isla=isla_seleccionada)
    st.rerun()

if not ids_validos_rueda:
    st.title("🇩🇪 Método de Chunks & Islas")
    st.balloons()
    st.success(f"🎉 ¡ESPECTACULAR! Has completado la isla '{isla_seleccionada}' al 100%.")
    st.write("")
    if st.button("♻️ Reiniciar progreso de la Isla", use_container_width=True):
        url_reset = f"{SUPABASE_URL}/rest/v1/tarjetas?Isla=ilike.{isla_seleccionada}"
        requests.patch(url_reset, headers=headers, json={"Estado": 1, "fecha_entrada_rueda": None, "segundos_acumulados_banco": 0, "fecha_ultimo_click": None, "importante": False})
        guardar_estado_puntero_db(0, [], nombre_isla=isla_seleccionada)
        st.rerun()
    st.stop()

if pos_db >= len(ids_validos_rueda):
    pos_db = 0
    guardar_estado_puntero_db(0, ids_validos_rueda, nombre_isla=isla_seleccionada)

st.session_state.indice_actual = pos_db
if 'ver_solucion' not in st.session_state:
    st.session_state.ver_solucion = False

# Construir rueda incluyendo jubilada de repaso al final si existe
ids_rueda_completa = ids_validos_rueda.copy()
if id_jubilada_repaso:
    ids_rueda_completa.append(id_jubilada_repaso)
df_rueda = pd.DataFrame({'id': ids_rueda_completa}).merge(df_universo, on='id', how='left')
total_rueda_actual = len(df_rueda)

df_cola = df_activas_universo[~df_activas_universo['id'].isin(ids_validos_rueda)].copy()


# --- RENDIMIENTO Y RESUMEN SIDEBAR ---
estados_lista = df_activas_universo['Estado'].tolist()
n_rojos = estados_lista.count(1)
n_naranjas = estados_lista.count(2)
n_verdes = estados_lista.count(3)
porcentaje_isla = round((total_aprendidos / total_frases_isla * 100)) if total_frases_isla > 0 else 0

st.sidebar.write("---")
st.sidebar.markdown("### 📊 Estado de la Isla")
st.sidebar.markdown(f"""
<div style="background: rgba(255,255,255,0.04); padding: 16px 18px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.09);">
    <p style="margin: 0 0 4px 0; font-size: 0.7rem; color: #8a9ab5; font-weight: 500; text-transform: uppercase; letter-spacing: 2px;">🔄 En rueda activa &nbsp;·&nbsp; {total_rueda_actual} / 15</p>
    <p style="margin: 0 0 12px 0; font-size: 0.65rem; color: #6b7c96; font-style: italic;">Pendientes en cola: {len(df_cola)}</p>
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

st.sidebar.write("---")
abrir_modal_jubiladas = st.sidebar.button("📦 Ver Almacén de Jubiladas", use_container_width=True, disabled=(len(df_jubiladas_muestra) == 0))
abrir_modal_cola = st.sidebar.button("⏳ Ver Frases en Cola", use_container_width=True, disabled=(len(df_cola) == 0))

if abrir_modal_jubiladas:
    @st.dialog("📦 Almacén de Frases Jubiladas")
    def mostrar_popup_jubiladas():
        st.write("Estas son tus frases guardadas en azul. Puedes repasarlas y devolverlas a la rueda activa:")
        st.write("---")
        for _, row in df_jubiladas_muestra.iterrows():
            col_txt, col_btn = st.columns([0.75, 0.25])
            with col_txt:
                marca_vip = "⭐ " if row.get('importante') else ""
                st.markdown(f"**{marca_vip}ES:** {row['Español']}")
                st.markdown(f"*DE:* {row['Aleman']}")
            with col_btn:
                if st.button("♻️ Traer", key=f"popup_rec_{row['id']}", use_container_width=True):
                    actualizar_estado_tarjeta(int(row['id']), 1)
                    inicializar_fecha_entrada_rueda(int(row['id']))
                    _, actuales_ids, _ = obtener_datos_puntero_db()
                    
                    if len(actuales_ids) >= 15:
                        id_expulsada = actuales_ids[-1]
                        fila_expulsada = df_universo[df_universo['id'] == id_expulsada].iloc[0]
                        congelar_temporizador_banquillo(
                            id_expulsada, 
                            fila_expulsada.get('fecha_entrada_rueda'), 
                            fila_expulsada.get('segundos_acumulados_banco', 0)
                        )
                        actuales_ids = actuales_ids[:14]

                    if int(row['id']) not in actuales_ids:
                        actuales_ids.insert(0, int(row['id']))
                        
                    guardar_estado_puntero_db(0, actuales_ids, nombre_isla=isla_seleccionada)
                    st.toast("¡Tarjeta recuperada desde cero! La última se congeló.")
                    st.rerun()
            st.write("---")
    mostrar_popup_jubiladas()

if abrir_modal_cola:
    @st.dialog("⏳ Almacén de Frases en Cola")
    def mostrar_popup_cola():
        st.write("Estas son las próximas frases que entrarán a la rueda a medida que jubiles las actuales:")
        st.write("---")
        for _, row in df_cola.iterrows():
            marca_vip = "⭐ " if row.get('importante') else ""
            st.markdown(f"**{marca_vip}ES:** {row['Español']}")
            st.markdown(f"*DE:* {row['Aleman']}")
            st.write("---")
    mostrar_popup_cola()


# ── CONTENIDO PRINCIPAL DE LA APP ──
st.title("🇩🇪 Método de Chunks & Islas")

fila_actual = df_rueda.iloc[st.session_state.indice_actual]
es_tarjeta_repaso = (int(fila_actual['id']) == id_jubilada_repaso) if id_jubilada_repaso else False
id_tarjeta            = int(fila_actual['id'])
castellano_texto      = str(fila_actual['Español'])
aleman_texto          = str(fila_actual['Aleman'])
estado_actual         = int(fila_actual['Estado'])
audio_id              = str(fila_actual['Audio_ID']).strip()
situacion_texto       = str(fila_actual['Situacion']).strip() if pd.notna(fila_actual['Situacion']) else ""
es_importante         = bool(fila_actual.get('importante', False))
traduccion_literal    = str(fila_actual['Traduccion_Literal']).strip() if 'Traduccion_Literal' in fila_actual and pd.notna(fila_actual.get('Traduccion_Literal')) and str(fila_actual.get('Traduccion_Literal')).strip() not in ('', 'None', 'nan') else ""

fecha_entrada_raw = fila_actual.get('fecha_entrada_rueda')
segundos_banco_raw = fila_actual.get('segundos_acumulados_banco', 0)
fecha_click_raw = fila_actual.get('fecha_ultimo_click')

if pd.isna(fecha_entrada_raw) or fecha_entrada_raw is None:
    inicializar_fecha_entrada_rueda(id_tarjeta)
    fecha_entrada_raw = datetime.now(timezone.utc).isoformat()

# ── BARRA DESLIZANTE DE AVANCE RÁPIDO ──
pos_pantalla = st.session_state.indice_actual + 1

nueva_pos_seleccionada = st.slider(
    "Saltar a frase:", 
    min_value=1, 
    max_value=total_rueda_actual, 
    value=pos_pantalla,
    label_visibility="collapsed"
)

if nueva_pos_seleccionada != pos_pantalla:
    nuevo_ind = nueva_pos_seleccionada - 1
    guardar_estado_puntero_db(nuevo_ind, ids_validos_rueda, nombre_isla=isla_seleccionada)
    st.session_state.ver_solucion = False
    st.rerun()

st.markdown(f'<div class="progreso-contador">Frase {pos_pantalla} de {total_rueda_actual}</div>', unsafe_allow_html=True)

# ── LETRERO DISCRETO DE CRONÓMETROS E INFO DE TIEMPOS ──
txt_antiguedad = formatear_antiguedad(fecha_entrada_raw, segundos_banco_raw)
txt_click = formatear_ultimo_click(fecha_click_raw)
st.markdown(f"""
<div class="info-tiempos">
    <span>{txt_antiguedad}</span>
    <span>•</span>
    <span>{txt_click}</span>
</div>
""", unsafe_allow_html=True)


# ── SECCIÓN DE LA FRASE ACTIVA CON BOTÓN ESTRELLA ──
col_encabezado_frase, col_encabezado_estrella = st.columns([0.85, 0.15])

with col_encabezado_frase:
    if situacion_texto and situacion_texto != "None":
        st.markdown(f'<div class="titulo-situacion" style="margin-top:6px;">📍 {situacion_texto}</div>', unsafe_allow_html=True)
    else:
        st.write("")

with col_encabezado_estrella:
    label_estrella = "⭐ VIP" if es_importante else "☆ Marcar"
    if st.button(label_estrella, key=f"star_{id_tarjeta}", use_container_width=True):
        cambiar_importancia_tarjeta(id_tarjeta, not es_importante)
        st.toast("Prioridad guardada" if not es_importante else "Marcada como SÚPER importante 🔥")
        st.rerun()


# ── BOTONES DE NAVEGACIÓN (CON SOLUCIÓN INSTANTÁNEA POR RATÓN Y TECLADO) ──
col_nav_sol, col_nav_ant, col_nav_sig = st.columns([0.34, 0.33, 0.33])

with col_nav_sol:
    label_solucion = "🔄 Ocultar Frase" if st.session_state.ver_solucion else "👁️ Solución / Ocultar"
    if st.button(label_solucion, key="btn_solucion", use_container_width=True):
        st.session_state.ver_solucion = not st.session_state.ver_solucion
        st.rerun()

with col_nav_ant:
    if st.button("⬅️ Anterior", key="btn_anterior", use_container_width=True):
        nuevo_ind = st.session_state.indice_actual - 1 if st.session_state.indice_actual > 0 else total_rueda_actual - 1
        guardar_estado_puntero_db(nuevo_ind, ids_validos_rueda, nombre_isla=isla_seleccionada)
        st.session_state.ver_solucion = False
        st.rerun()

with col_nav_sig:
    if st.button("Siguiente ➡️", key="btn_siguiente", use_container_width=True):
        nuevo_ind = st.session_state.indice_actual + 1 if st.session_state.indice_actual < total_rueda_actual - 1 else 0
        guardar_estado_puntero_db(nuevo_ind, ids_validos_rueda, nombre_isla=isla_seleccionada)
        st.session_state.ver_solucion = False
        st.rerun()

st.write("")

bg_tira, color_tira = "rgba(59, 125, 216, 0.15)", "#3b7dd8"
if estado_actual == 1:   bg_tira, color_tira = "rgba(224, 84, 84, 0.15)", "#e05454"
elif estado_actual == 2: bg_tira, color_tira = "rgba(245, 158, 11, 0.15)", "#f59e0b"
elif estado_actual == 3: bg_tira, color_tira = "rgba(34, 166, 110, 0.15)", "#22a66e"

st.markdown(f'<div class="tira-historial" style="background-color: {bg_tira}; color: {color_tira}; border: 1px solid {color_tira}44;">ESTADO ACTUAL</div>', unsafe_allow_html=True)

prefijo_estrella = "⭐ " if es_importante else ""

disp_castellano = "none" if st.session_state.ver_solucion else "block"
disp_solucion = "block" if st.session_state.ver_solucion else "none"

# Badge de repaso espaciado
if es_tarjeta_repaso:
    intervalo_actual = fila_actual.get('intervalo_repaso', 1)
    st.markdown(
        f'<div style="text-align:center;margin-bottom:8px;padding:4px 12px;background:rgba(59,125,216,0.15);border:1px solid rgba(59,125,216,0.3);border-radius:8px;font-size:0.8rem;color:#3b7dd8;">🔁 Tarjeta de repaso · intervalo actual: {intervalo_actual} días</div>',
        unsafe_allow_html=True
    )

# Bloque del Castellano con renglones limpios y negritas funcionando
st.markdown(f'''
<div id="bloque-castellano" class="bloque-azul" style="display: {disp_castellano};" data-server-display="{disp_castellano}">
    <div class="texto-isla">
        <b>{prefijo_estrella}Castellano (Lee y piensa):</b><br><br>
        <span id="contenido-castellano">{formatear_lineas(castellano_texto)}</span>
    </div>
</div>
''', unsafe_allow_html=True)

# Bloque de la Solución en Alemán con renglones limpios y negritas funcionando
st.markdown(f'''
<div id="bloque-solucion" class="bloque-verde" style="display: {disp_solucion};" data-server-display="{disp_solucion}">
    <div class="texto-isla">
        <b>{prefijo_estrella}Solución en Alemán:</b><br><br>
        <span id="contenido-aleman">{formatear_lineas(aleman_texto, colorear=True)}</span>
    </div>
</div>
''', unsafe_allow_html=True)


# ── TRADUCCIÓN LITERAL (EXPANDER OPCIONAL) ──
if traduccion_literal:
    with st.expander("📖 Texto literal"):
        st.markdown(
            f'<div class="texto-isla" style="padding: 0.4rem 0.2rem;">{formatear_lineas(traduccion_literal)}</div>',
            unsafe_allow_html=True
        )

# ── DETONANTE: ASIGNACIÓN DE COLOR Y ACTUALIZACIÓN DE FECHAS ──
col_c1, col_c2, col_c3, col_c4 = st.columns(4)
nuevo_estado_num = None

with col_c1:
    if st.button("🔴", key="btn_color1", use_container_width=True): nuevo_estado_num = 1
with col_c2:
    if st.button("🟠", key="btn_color2", use_container_width=True): nuevo_estado_num = 2
with col_c3:
    if st.button("🟢", key="btn_color3", use_container_width=True): nuevo_estado_num = 3
with col_c4:
    if st.button("🔵", key="btn_color4", use_container_width=True): nuevo_estado_num = 4

if nuevo_estado_num is not None:
    estampar = True if nuevo_estado_num in [1, 2, 3] else False
    actualizar_estado_tarjeta(id_tarjeta, nuevo_estado_num, estampar_click=estampar)
    st.toast(f"Estado sincronizado")
    
    es_jubilada_repaso = (id_tarjeta == id_jubilada_repaso)

    if nuevo_estado_num == 4:
        if es_jubilada_repaso:
            # Ya era jubilada — actualizar intervalo espaciado
            intervalo_actual = fila_actual.get('intervalo_repaso', 1)
            actualizar_repaso_espaciado(id_tarjeta, intervalo_actual)
        else:
            # Primera vez que se jubila — inicializar repaso
            inicializar_repaso(id_tarjeta)
            if id_tarjeta in ids_validos_rueda:
                ids_validos_rueda.remove(id_tarjeta)
        nuevo_indice_puntero = st.session_state.indice_actual
    else:
        # Si era jubilada de repaso y la bajan de color → vuelve al pool activo
        if es_jubilada_repaso:
            from datetime import timedelta
            proxima = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
            url_reset = f"{SUPABASE_URL}/rest/v1/tarjetas?id=eq.{id_tarjeta}"
            requests.patch(url_reset, headers=headers, json={"fecha_repaso": proxima, "intervalo_repaso": 1})
        nuevo_indice_puntero = st.session_state.indice_actual + 1 if st.session_state.indice_actual < total_rueda_actual - 1 else 0

    guardar_estado_puntero_db(nuevo_indice_puntero, ids_validos_rueda, nombre_isla=isla_seleccionada)
    st.session_state.ver_solucion = False
    st.rerun()


# ── REPRODUCTOR DE AUDIO INTERACTIVO ──
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


# ── MODO DICTADO ──
with st.expander("📝 Modo Dictado"):
    texto_usuario = st.text_area("Escribe el texto en alemán:", key=f"dictado_{id_tarjeta}", height=200)
    if st.button("🔍 Comprobar Dictado", use_container_width=True):
        if texto_usuario:
            porcentaje = calcular_similitul_parcial(texto_usuario, aleman_texto)
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

texto_anotaciones = st.text_area("Notas", value=anotacion_inicial, key=f"notas_{id_tarjeta}", height=250, label_visibility="collapsed")

if st.button("💾 Guardar Anotaciones", use_container_width=True):
    actualizar_anotacion_tarjeta(id_tarjeta, texto_anotaciones)
    st.toast("✅ Anotaciones sincronizadas en Supabase")


# ── SCRIPT INVISIBLE: CONTROL TOTAL POR TECLADO ──
html_teclas = """
<script>
const doc = window.parent.document;

function buscarBoton(textos) {
    const buttons = doc.querySelectorAll('button');
    for (let btn of buttons) {
        const txt = btn.innerText.trim();
        for (let t of textos) {
            if (txt.includes(t)) return btn;
        }
    }
    return null;
}

// Cambio DOM instantáneo (visual) + sincronización Streamlit en segundo plano
function conmutarSolucionRapido() {
    const cas = doc.getElementById('bloque-castellano');
    const sol = doc.getElementById('bloque-solucion');
    if (cas && sol) {
        // Cambio visual instantáneo
        const mostrando_aleman = sol.style.display !== 'none';
        if (mostrando_aleman) {
            sol.style.display = 'none';
            cas.style.display = 'block';
        } else {
            sol.style.display = 'block';
            cas.style.display = 'none';
        }
    }
    // Sincronizar Streamlit en segundo plano (sin esperar la respuesta)
    const btnStreamlit = buscarBoton(['Solución', 'Ocultar Frase']);
    if (btnStreamlit) btnStreamlit.click();
}

doc.addEventListener('keydown', function(e) {
    if (doc.activeElement.tagName === 'TEXTAREA' || doc.activeElement.tagName === 'INPUT') return;

    let btn = null;

    if (e.key.toLowerCase() === 'a') {
        e.preventDefault();
        conmutarSolucionRapido();
        return;
    } else if (e.key === 'ArrowRight') {
        btn = buscarBoton(['Siguiente']);
    } else if (e.key === 'ArrowLeft') {
        btn = buscarBoton(['Anterior']);
    } else if (e.key === '1') {
        btn = buscarBoton(['🔴']);
    } else if (e.key === '2') {
        btn = buscarBoton(['🟠']);
    } else if (e.key === '3') {
        btn = buscarBoton(['🟢']);
    } else if (e.key === '4') {
        btn = buscarBoton(['🔵']);
    }

    if (btn) {
        e.preventDefault();
        btn.click();
    }
});

// Al cargar cada tarjeta: restaurar estado desde servidor + corregir negritas
setTimeout(() => {
    // 1. Restaurar display desde data-server-display (garantiza castellano en tarjeta nueva)
    ['bloque-castellano', 'bloque-solucion'].forEach(id => {
        const el = doc.getElementById(id);
        if (el && el.dataset.serverDisplay) el.style.display = el.dataset.serverDisplay;
    });
    // 2. Corregir negritas |texto|
    ['contenido-castellano', 'contenido-aleman'].forEach(id => {
        const el = doc.getElementById(id);
        if (el && el.innerHTML.includes('|')) {
            el.innerHTML = el.innerHTML.replace(/\\|([^|]+)\\|/g, '<strong>$1</strong>');
        }
    });
}, 100);
</script>
"""
st.components.v1.html(html_teclas, height=0, width=0)
