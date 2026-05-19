import streamlit as st
import pandas as pd
import os
import re
import random

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
    </style>
""", unsafe_allow_html=True)

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

# Filtrar las frases de la isla seleccionada de forma ordenada
df_isla_original = df_total[df_total['Isla'] == isla_seleccionada].reset_index(drop=True)
total_frases = len(df_isla_original)

# CONTROL DE CAMBIO DE ISLA O INICIALIZACIÓN
if 'isla_anterior' not in st.session_state or st.session_state.isla_anterior != isla_seleccionada:
    st.session_state.indice_actual = 0
    st.session_state.isla_anterior = isla_seleccionada
    st.session_state.ver_solucion = False
    st.session_state.completado = False
    if 'orden_aleatorio' in st.session_state:
        del st.session_state.orden_aleatorio

# --- NUEVO INTERRUPTOR DE MODO ALEATORIO (CORREGIDO) ---
modo_aleatorio = st.sidebar.toggle("🔀 Activar orden aleatorio")

if modo_aleatorio:
    # Si se activa, creamos la mezcla UNA SOLA VEZ y la dejamos fija en memoria
    if 'orden_aleatorio' not in st.session_state:
        indices_mezclados = list(range(total_frases))
        random.shuffle(indices_mezclados)
        st.session_state.orden_aleatorio = indices_mezclados
        st.session_state.indice_actual = 0  
        st.session_state.ver_solucion = False
    
    # Construimos el orden usando el mapa que guardamos en memoria (así no cambia al dar Siguiente)
    df_isla = df_isla_original.iloc[st.session_state.orden_aleatorio].reset_index(drop=True)
else:
    # Si se apaga, borramos la mezcla para que la próxima vez sea distinta
    if 'orden_aleatorio' in st.session_state:
        del st.session_state.orden_aleatorio
        st.session_state.indice_actual = 0  
        st.session_state.ver_solucion = False
    df_isla = df_isla_original

# Asegurar inicialización básica del índice
if 'indice_actual' not in st.session_state:
    st.session_state.indice_actual = 0

if 'ver_solucion' not in st.session_state:
    st.session_state.ver_solucion = False

# Asegurar que el índice esté dentro de los límites válidos
if st.session_state.indice_actual >= total_frases:
    st.session_state.indice_actual = total_frases - 1 if total_frases > 0 else 0

# Selector para saltar a una frase específica
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

# Cargar la fila actual basada en el dataframe activo
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

def formatear_lineas(texto):
    frases = re.split(r'(?<=[.!?])\s+', texto.strip())
    return "<br>".join(frases)

st.subheader(f"Progreso: Frase {st.session_state.indice_actual + 1} de {total_frases}")
st.progress((st.session_state.indice_actual + 1) / total_frases)

if situacion_texto:
    st.markdown(f'<div class="titulo-situacion">📍 Situación: {situacion_texto}</div>', unsafe_allow_html=True)

# --- BLOQUE DINÁMICO (INTERRUPTOR CAS/ALE) ---
if not st.session_state.ver_solucion:
    castellano_formateado = formatear_lineas(castellano_texto)
    st.markdown(f"""
    <div class="bloque-azul">
        <div class="texto-isla">
            <b>Castellano (Lee y piensa tu traducción):</b><br><br>
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

# Reproductor de Audio
ruta_audio = f"Audios/{audio_id}.mp3"
if os.path.exists(ruta_audio):
    st.write("🎧 **Escucha el audio para hacer Shadowing:**")
    st.audio(ruta_audio, format="audio/mp3")
else:
    st.warning(f"⚠️ Audio no encontrado en la ruta: `{ruta_audio}`")

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
