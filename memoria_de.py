import streamlit as st
import pandas as pd
import os
import re
import random

# Configuración de la página
st.set_page_config(page_title="Entrenador de Idiomas por Islas", page_icon="🇩🇪", layout="centered")

# Inyectar la tipografía Montserrat y estilos adaptables (¡Actualizados con tarjetas de estadísticas!)
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

    /* Tarjetas de Estadísticas con Vida */
    .contenedor-stats {
        display: flex;
        gap: 10px;
        margin-bottom: 20px;
    }
    .tarjeta-stat {
        flex: 1;
        padding: 12px;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border: 1px solid rgba(255,255,255,0.1);
    }
    .stat-numero {
        font-size: 24px;
        font-weight: 600;
        font-family: 'Montserrat', sans-serif;
        margin-top: 5px;
    }
    .stat-label {
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: #a0aec0;
    }
    </style>
""", unsafe_allow_html=True)

# Cargar la base de datos de Excel
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

# Mapeamos los índices originales
df_total['Index_Original'] = df_total.index
df_isla_original = df_total[df_total['Isla'] == isla_seleccionada].reset_index(drop=True)
total_frases = len(df_isla_original)

if 'isla_anterior' not in st.session_state or st.session_state.isla_anterior != isla_seleccionada:
    st.session_state.indice_actual = 0
    st.session_state.isla_anterior = isla_seleccionada
    st.session_state.ver_solucion = False
    st.session_state.completado = False
    if 'orden_aleatorio' in st.session_state:
        del st.session_state.orden_aleatorio

# INTERRUPTOR DE MODO ALEATORIO
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

if st.session_state.indice_actual >= total_frases:
    st.session_state.indice_actual = total_frases - 1 if total_frases > 0 else 0


# --- BOTÓN PARA RESETEAR ESTADÍSTICAS EN EL EXCEL ---
st.sidebar.write("---")
st.sidebar.subheader("📊 Zona de Datos")
if st.sidebar.button("🗑️ Resetear notas de esta Isla", type="primary", use_container_width=True):
    indices_a_resetear = df_isla_original['Index_Original'].tolist()
    df_total.loc[indices_a_resetear, 'Dominio'] = 0
    df_guardar = df_total.drop(columns=['Index_Original']) if 'Index_Original' in df_total.columns else df_total
    df_guardar.to_excel("frases.xlsx", index=False)
    st.session_state.indice_actual = 0
    st.session_state.ver_solucion = False
    st.sidebar.success("¡Progreso de la isla borrado en el Excel!")
    st.rerun()


# --- CONTENIDO PRINCIPAL ---
st.title("🇩🇪 Método de Chunks & Islas")

# Calcular estadísticas reales
valores_dominio = df_isla_original['Dominio'].fillna(0).tolist()
malas = valores_dominio.count(1)
regulares = valores_dominio.count(2)
buenas = valores_dominio.count(3)
nuevas = valores_dominio.count(0)

# Calcular porcentajes para las barras de progreso internas
pct_bien = (buenas / total_frases) * 100 if total_frases > 0 else 0

# --- NUEVO DISEÑO DE ESTADÍSTICAS CON EMOCIÓN ---
st.markdown(f"""
<div class="contenedor-stats">
    <div class="tarjeta-stat" style="background-color: rgba(239, 68, 68, 0.1); border-color: rgba(239, 68, 68, 0.3);">
        <div class="stat-label">🔴 Falladas</div>
        <div class="stat-numero" style="color: #ef4444;">{malas}</div>
    </div>
    <div class="tarjeta-stat" style="background-color: rgba(245, 158, 11, 0.1); border-color: rgba(245, 158, 11, 0.3);">
        <div class="stat-label">🟡 Regular</div>
        <div class="stat-numero" style="color: #f59e0b;">{regulares}</div>
    </div>
    <div class="tarjeta-stat" style="background-color: rgba(16, 185, 129, 0.1); border-color: rgba(16, 185, 129, 0.3);">
        <div class="stat-label">🟢 Dominadas</div>
        <div class="stat-numero" style="color: #10b981;">{buenas}</div>
    </div>
    <div class="tarjeta-stat" style="background-color: rgba(113, 128, 150, 0.1); border-color: rgba(113, 128, 150, 0.2);">
        <div class="stat-label">🆕 Nuevas</div>
        <div class="stat-numero" style="color: #a0aec0;">{nuevas}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Barra de Dominio de la Isla Completa
st.write(f"🏆 **Nivel de maestría en esta Isla:** {pct_bien:.0f}%")
st.progress(pct_bien / 100)


if st.session_state.indice_actual >= total_frases - 1 and st.session_state.get('completado', False):
    if buenas == total_frases:
        st.balloons() # ¡Efecto fiesta total si todo está en verde!
        st.success("👑 ¡BRUTAL! Has completado la isla y dominas absolutamente todas las frases. ¡Eres un crack!")
    else:
        st.success("🎉 ¡Enhorabuena! Has llegado al final de esta vuelta por la isla.")
        
    if st.button("Repetir Isla (Volver a empezar)", use_container_width=True):
        st.session_state.indice_actual = 0
        st.session_state.ver_solucion = False
        st.session_state.completado = False
        if 'orden_aleatorio' in st.session_state:
            del st.session_state.orden_aleatorio
        st.rerun()
    st.stop()

# Cargar fila actual
fila_actual = df_isla.iloc[st.session_state.indice_actual]
castellano_texto = str(fila_actual['Castellano'])
aleman_texto = str(fila_actual['Aleman'])
index_real_excel = fila_actual['Index_Original']

audio_id_raw = fila_actual['Audio_ID']
if pd.isna(audio_id_raw): audio_id = "sin_audio"
elif isinstance(audio_id_raw, float): audio_id = str(int(audio_id_raw))
else: audio_id = str(audio_id_raw).strip()

situacion_texto = ""
if 'Situacion' in fila_actual and pd.notna(fila_actual['Situacion']):
    situacion_texto = str(fila_actual['Situacion']).strip()

def formatear_lineas(texto):
    frases = re.split(r'(?<=[.!?])\s+', texto.strip())
    return "<br>".join(frases)

# Leer estado actual de la frase
nota_num = df_total.loc[index_real_excel, 'Dominio']
mapa_notas = {0: "🆕 Nueva", 1: "🔴 Mal", 2: "🟡 Regular", 3: "🟢 Bien"}
nota_actual_texto = mapa_notas.get(int(nota_num) if pd.notna(nota_num) else 0, "🆕 Nueva")

st.subheader(f"Frase {st.session_state.indice_actual + 1} de {total_frases} ({nota_actual_texto})")

if situacion_texto:
    st.markdown(f'<div class="titulo-situacion">📍 Situación: {situacion_texto}</div>', unsafe_allow_html=True)

# --- BLOQUE DINÁMICO ---
if not st.session_state.ver_solucion:
    castellano_formateado = formatear_lineas(castellano_texto)
    st.markdown(f"""<div class="bloque-azul"><div class="texto-isla"><b>Castellano:</b><br><br>{castellano_formateado}</div></div>""", unsafe_allow_html=True)
else:
    aleman_formateado = formatear_lineas(aleman_texto)
    st.markdown(f"""<div class="bloque-verde"><div class="texto-isla"><b>Solución en Alemán:</b><br><br>{aleman_formateado}</div></div>""", unsafe_allow_html=True)

# Audio
ruta_audio = f"Audios/{audio_id}.mp3"
if os.path.exists(ruta_audio):
    st.write("🎧 **Escucha el audio:**")
    st.audio(ruta_audio, format="audio/mp3")
else:
    st.warning(f"⚠️ Audio no encontrado.")

# --- BOTONES DE CALIFICACIÓN ---
st.write("¿Cómo te ha salido?")
st_col1, st_col2, st_col3 = st.columns(3)

def calificar_y_guardar(valor_numerico):
    df_total.loc[index_real_excel, 'Dominio'] = valor_numerico
    df_escribir = df_total.drop(columns=['Index_Original']) if 'Index_Original' in df_total.columns else df_total
    df_escribir.to_excel("frases.xlsx", index=False)
    
    if st.session_state.indice_actual < total_frases - 1:
        st.session_state.indice_actual += 1
        st.session_state.ver_solucion = False
    else:
        st.session_state.completado = True
    st.rerun()

with st_col1:
    if st.button("🔴 Mal", use_container_width=True): calificar_y_guardar(1)
with st_col2:
    if st.button("🟡 Regular", use_container_width=True): calificar_y_guardar(2)
with st_col3:
    if st.button("🟢 Bien", use_container_width=True): calificar_y_guardar(3)

st.write("---")

# Botones de navegación clásicos
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
    if st.button("Saltar Frase ➡️", use_container_width=True):
        if st.session_state.indice_actual < total_frases - 1:
            st.session_state.indice_actual += 1
            st.session_state.ver_solucion = False
        else:
            st.session_state.completado = True
        st.rerun()
