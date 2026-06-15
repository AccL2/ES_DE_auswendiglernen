import streamlit as st
import pandas as pd
import os
import re

# ── Página ────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Islas · Entrenador de Alemán",
    page_icon="🏝️",
    layout="centered",
)

# ── Estilos ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300;1,9..144,300&family=DM+Sans:wght@400;500&display=swap');

/* Variables de color — se adaptan al tema de Streamlit */
:root {
    --accent-blue:  #4C9BE8;
    --accent-green: #3EC97A;
    --radius: 0.6rem;
    --transition: 160ms ease;
}

/* Tipografía global */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

/* Título principal */
h1 {
    font-family: 'Fraunces', Georgia, serif !important;
    font-weight: 300 !important;
    font-style: italic;
    letter-spacing: -0.02em;
}

/* Subtítulos */
h2, h3 {
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    letter-spacing: -0.01em;
}

/* Bloques de contenido */
.bloque {
    padding: 1.4rem 1.6rem;
    border-radius: var(--radius);
    margin-bottom: 1.2rem;
    transition: box-shadow var(--transition);
}
.bloque:hover {
    box-shadow: 0 4px 18px rgba(0,0,0,0.08);
}

.bloque-es {
    background-color: color-mix(in srgb, var(--accent-blue) 10%, transparent);
    border-left: 3px solid var(--accent-blue);
}

.bloque-de {
    background-color: color-mix(in srgb, var(--accent-green) 10%, transparent);
    border-left: 3px solid var(--accent-green);
    animation: fadeIn 220ms ease;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(6px); }
    to   { opacity: 1; transform: translateY(0);   }
}

/* Etiqueta encima del bloque */
.etiqueta {
    font-size: 0.72rem;
    font-weight: 500;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    opacity: 0.55;
    margin-bottom: 0.6rem;
}

/* Texto de frase */
.texto-frase {
    font-family: 'DM Sans', sans-serif;
    font-size: 1.08rem;
    line-height: 1.7;
}

/* Barra de progreso personalizada */
.progreso-meta {
    font-size: 0.8rem;
    opacity: 0.5;
    text-align: right;
    margin-top: -0.6rem;
    margin-bottom: 0.8rem;
}

/* Separador suave */
hr { opacity: 0.15 !important; }

/* Botones — más compactos y con color coherente */
.stButton > button {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.9rem !important;
    border-radius: var(--radius) !important;
    transition: opacity var(--transition) !important;
}
.stButton > button:hover { opacity: 0.8; }
</style>
""", unsafe_allow_html=True)


# ── Datos ─────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=30)
def cargar_datos() -> pd.DataFrame:
    df = pd.read_excel("frases.xlsx")
    df.columns = df.columns.str.strip()
    return df


try:
    df_total = cargar_datos()
except Exception as exc:
    st.error(f"No se pudo cargar **frases.xlsx**: {exc}")
    st.stop()


# ── Helpers ───────────────────────────────────────────────────────────────────
def partir_en_lineas(texto: str) -> str:
    """Divide el texto en oraciones separadas por <br>."""
    texto = str(texto).strip()
    partes = re.split(r'(?<=[.!?])\s+', texto)
    return "<br>".join(p for p in partes if p)


def bloque_html(clase: str, etiqueta: str, contenido: str) -> str:
    return f"""
    <div class="bloque {clase}">
        <div class="etiqueta">{etiqueta}</div>
        <div class="texto-frase">{contenido}</div>
    </div>"""


def resaltar_chunks(texto: str, chunks_raw: str) -> str:
    """Resalta en negrita cada chunk (separados por |) dentro del texto."""
    if not chunks_raw or str(chunks_raw).strip() in ("", "nan"):
        return texto
    chunks = [c.strip() for c in str(chunks_raw).split("|") if c.strip()]
    for chunk in chunks:
        texto = texto.replace(chunk, f"<strong>{chunk}</strong>")
    return texto


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Configuración")
    st.divider()

    islas = df_total["Isla"].unique()
    isla = st.selectbox("🏝️ Isla", islas)

    df_isla = df_total[df_total["Isla"] == isla].reset_index(drop=True)
    n = len(df_isla)

    # Reiniciar estado al cambiar de isla
    if st.session_state.get("isla_anterior") != isla:
        st.session_state.update({"idx": 0, "isla_anterior": isla, "ver": False})

    # Navegación directa
    idx_nav = st.selectbox(
        "🎯 Ir a frase",
        options=range(n),
        format_func=lambda i: f"Frase {i + 1}",
        index=int(st.session_state.get("idx", 0)),
        key=f"nav_{st.session_state.get('idx', 0)}",
    )
    if idx_nav != st.session_state.get("idx", 0):
        st.session_state.update({"idx": idx_nav, "ver": False})
        st.rerun()

    st.divider()
    st.caption("💡 Usa los botones principales para avanzar.")


# ── Estado de sesión (valores por defecto) ────────────────────────────────────
ss = st.session_state
ss.setdefault("idx", 0)
ss.setdefault("ver", False)

# Clamp de seguridad
ss.idx = max(0, min(ss.idx, n - 1))

fila        = df_isla.iloc[ss.idx]
es_texto    = str(fila["Castellano"])
de_texto    = str(fila["Aleman"])
audio_id    = fila["Audio_ID"]
chunks_raw  = fila.get("Chunk_Clave", "")


# ── Cabecera ──────────────────────────────────────────────────────────────────
st.markdown("# Islas · Alemán")
st.caption("Active Recall + Shadowing — Método de Chunks")

st.divider()

# Progreso
porcentaje = (ss.idx + 1) / n
st.progress(porcentaje)
st.markdown(
    f'<div class="progreso-meta">Frase {ss.idx + 1} / {n}</div>',
    unsafe_allow_html=True,
)

# ── Bloque español ────────────────────────────────────────────────────────────
st.markdown(
    bloque_html("bloque-es", "🇪🇸 Castellano — piensa tu traducción", partir_en_lineas(es_texto)),
    unsafe_allow_html=True,
)

# ── Audio ─────────────────────────────────────────────────────────────────────
ruta_audio = f"audios/{int(audio_id)}.mp3"
if os.path.exists(ruta_audio):
    st.markdown("🎧 **Shadowing** — escucha antes de revelar la solución")
    st.audio(ruta_audio, format="audio/mp3")
else:
    st.caption(f"⚠️ Audio no encontrado: `{ruta_audio}`")

st.divider()

# ── Bloque alemán (revelado) ──────────────────────────────────────────────────
if ss.ver:
    de_resaltado = resaltar_chunks(partir_en_lineas(de_texto), chunks_raw)
    st.markdown(
        bloque_html("bloque-de", "🇩🇪 Solución en alemán", de_resaltado),
        unsafe_allow_html=True,
    )
    st.write("")

# ── Botones ───────────────────────────────────────────────────────────────────
col_ver, col_sig = st.columns(2)

with col_ver:
    if not ss.ver:
        if st.button("👁️ Mostrar solución", use_container_width=True, type="secondary"):
            ss.ver = True
            st.rerun()
    else:
        st.button("✅ Solución visible", use_container_width=True, disabled=True)

with col_sig:
    ultimo = ss.idx >= n - 1
    label  = "🔁 Reiniciar isla" if ultimo and ss.ver else "Siguiente ➡️"

    if st.button(label, use_container_width=True, type="primary"):
        if ultimo:
            ss.idx = 0
        else:
            ss.idx += 1
        ss.ver = False
        st.rerun()

# ── Mensaje de isla completada ────────────────────────────────────────────────
if ss.idx == n - 1 and ss.ver:
    st.success("🎉 ¡Has completado todas las frases de esta isla! Pulsa **Reiniciar isla** para repetir.")
