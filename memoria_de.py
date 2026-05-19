import streamlit as st
import random

# CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(page_title="Entrenador de Alemán", page_icon="🇩🇪", layout="centered")

# 1. BASE DE DATOS DE TUS ISLAS DE VOCABULARIO
# (Aquí están todas tus frases organizadas)
ISLAS = {
    "Isla 1: Saludos básicos": [
        {"de": "Guten Morgen", "es": "Buenos días"},
        {"de": "Wie geht es dir?", "es": "¿Cómo estás?"},
        {"de": "Hallo", "es": "Hola"},
        {"de": "Tschüss", "es": "Adiós"},
        {"de": "Vielen Dank", "es": "Muchas gracias"}
    ],
    "Isla 2: En la cafetería": [
        {"de": "Ich möchte einen Kaffee", "es": "Quiero un café"},
        {"de": "Ein Bier, bitte", "es": "Una cerveza, por favor"},
        {"de": "Die Rechnung, bitte", "es": "La cuenta, por favor"},
        {"de": "Es schmeckt gut", "es": "Está rico / Sabe bien"}
    ],
    "Isla 3: Frases útiles": [
        {"de": "Ich verstehe nicht", "es": "No entiendo"},
        {"de": "Sprechen Sie Spanisch?", "es": "¿Habla usted español?"},
        {"de": "Wo ist die Toilette?", "es": "¿Dónde está el baño?"},
        {"de": "Es tut mir leid", "es": "Lo siento"}
    ]
}

# 2. INICIALIZACIÓN DE LA MEMORIA DE LA APP (Session State)
if "isla_actual" not in st.session_state:
    st.session_state.isla_actual = list(ISLAS.keys())[0]

# Si cambiamos de isla, necesitamos resetear el orden y la posición
if "isla_previa" not in st.session_state:
    st.session_state.isla_previa = st.session_state.isla_actual

if st.session_state.isla_actual != st.session_state.isla_previa:
    st.session_state.indice = 0
    st.session_state.mostrar_aleman = True
    if "lista_mezclada" in st.session_state:
        del st.session_state.lista_mezclada
    st.session_state.isla_previa = st.session_state.isla_actual

# Cargamos las preguntas de la isla seleccionada
preguntas_originales = ISLAS[st.session_state.isla_actual]

if "indice" not in st.session_state:
    st.session_state.indice = 0

if "mostrar_aleman" not in st.session_state:
    st.session_state.mostrar_aleman = True


# INTERFAZ VISUAL: Selector de Isla
st.title("🏝️ Tus Islas de Alemán")
isla_seleccionada = st.selectbox("Elige la isla que quieres repasar:", list(ISLAS.keys()), key="isla_actual")

st.write("---")

# --- CONTROL DEL MODO ALEATORIO ---
# Ponemos el interruptor arriba para que decidas antes de empezar a pasar tarjetas
modo_aleatorio = st.toggle("🔀 Activar orden aleatorio (Mezclar isla)")

if modo_aleatorio:
    # Si se activa y no hemos creado una lista mezclada todavía, la creamos
    if "lista_mezclada" not in st.session_state:
        lista_copia = preguntas_originales.copy()
        random.shuffle(lista_copia)
        st.session_state.lista_mezclada = lista_copia
        st.session_state.indice = 0  # Empezamos desde la primera de la mezcla
    preguntas_activas = st.session_state.lista_mezclada
else:
    # Si está apagado, nos aseguramos de borrar la mezcla para la próxima vez
    if "lista_mezclada" in st.session_state:
        del st.session_state.lista_mezclada
        st.session_state.indice = 0  # Volvemos al inicio del orden normal
    preguntas_activas = preguntas_originales

# Conseguimos la frase que toca mostrar según el orden activo
frase_actual = preguntas_activas[st.session_state.indice]


# 3. EL BLOQUE CONMUTADOR (Visualización de la tarjeta)
# Si es True muestra Alemán, si es False muestra Español
texto_a_mostrar = frase_actual["de"] if st.session_state.mostrar_aleman else frase_actual["es"]
color_bloque = "alert-info" if st.session_state.mostrar_aleman else "alert-success"
idioma_etiqueta = "🇩🇪 ALEMÁN" if st.session_state.mostrar_aleman else "🇪🇸 ESPAÑOL"

# Diseño HTML del bloque que cambia
st.markdown(f"""
    <div class="stAlert" style="padding: 25px; border-radius: 10px; background-color: rgba(28, 133, 235, 0.1) if '{color_bloque}' == 'alert-info' else rgba(40, 167, 69, 0.1); border-left: 5px solid {'#1c85eb' if color_bloque == 'alert-info' else '#28a745'}; text-align: center; margin-bottom: 20px;">
        <p style="margin: 0; font-size: 14px; font-weight: bold; color: gray;">{idioma_etiqueta}</p>
        <h2 style="margin: 10px 0 0 0; font-size: 28px;">{texto_a_mostrar}</h2>
    </div>
""", unsafe_allowed_items=True)


# BUTTONS: Controles de la app en línea
col1, col2 = st.columns(2)

with col1:
    if st.button("🔄 Voltear Tarjeta", use_container_width=True):
        st.session_state.mostrar_aleman = not st.session_state.mostrar_aleman
        st.rerun()

with col2:
    if st.button("➡️ Siguiente", use_container_width=True):
        # Avanzamos al siguiente índice si no es el final
        if st.session_state.indice < len(preguntas_activas) - 1:
            st.session_state.indice += 1
        else:
            st.balloons()  # ¡Efecto fiesta al terminar la isla!
            st.session_state.indice = 0
        
        # Siempre que pasamos de tarjeta, queremos ver primero el Alemán
        st.session_state.mostrar_aleman = True
        st.rerun()

# Barra de progreso para saber cuánto te queda
progreso = (st.session_state.indice + 1) / len(preguntas_activas)
st.progress(progreso)
st.caption(f"Frase {st.session_state.indice + 1} de {len(preguntas_activas)}")
