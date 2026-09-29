import streamlit as st
import os
import tempfile
import time
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ImageClip, concatenate_videoclips, AudioFileClip
import moviepy.audio.fx.all as afx

# ==========================================
# CONFIGURACIÓN DE PÁGINA Y ESTILOS (GLASSMORPHISM UI)
# ==========================================
st.set_page_config(
    page_title="DGM Studio - Creador de Video",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inyección de CSS Personalizado para UI Glassmorphism
st.markdown("""
<style>
    /* Fondo principal con gradiente oscuro profesional */
    .stApp {
        background: linear-gradient(135deg, #0d0e15 0%, #1a0b1e 50%, #0a1128 100%);
        color: #ffffff;
    }

    /* Tarjetas estilo Glassmorphism */
    .glass-card {
        background: rgba(255, 255, 255, 0.04);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    }

    /* Encabezado principal personalizado */
    .main-title {
        background: linear-gradient(90deg, #ff2a6d, #9a4ef1, #00f5d4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.8rem;
        font-weight: 800;
        text-align: center;
        margin-bottom: 0.5rem;
    }

    .sub-title {
        text-align: center;
        color: #a0aab8;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }

    /* Contenedor de thumbnails */
    .thumb-card {
        background: rgba(255, 255, 255, 0.02);
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.05);
        padding: 12px;
        margin-bottom: 12px;
    }

    /* Botón personalizado con degradado */
    .stButton > button {
        width: 100%;
        background: linear-gradient(90deg, #ff2a6d 0%, #9a4ef1 100%);
        color: white;
        border: none;
        padding: 14px 28px;
        font-size: 1.1rem;
        font-weight: 700;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(255, 42, 109, 0.4);
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(255, 42, 109, 0.6);
        color: white;
    }

    /* Footer personalizado */
    .footer-container {
        margin-top: 50px;
        padding: 20px;
        background: rgba(255, 255, 255, 0.02);
        backdrop-filter: blur(10px);
        border-top: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        text-align: center;
        font-size: 0.9rem;
        color: #8c9ba5;
    }
    
    .footer-link {
        color: #00f5d4;
        text-decoration: none;
        font-weight: 600;
    }
    .footer-link:hover {
        text-decoration: underline;
    }
</style>
""", unsafe_allow_html=True)


# ==========================================
# FUNCIONES AUXILIARES DE PROCESAMIENTO
# ==========================================

def hex_to_rgba(hex_str, alpha=255):
    """Convierte un código color Hexadecimal (#RRGGBB) a una tupla RGBA."""
    hex_str = hex_str.lstrip('#')
    if len(hex_str) == 6:
        r, g, b = tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))
        return (r, g, b, int(alpha))
    return (255, 255, 255, int(alpha))

def load_resilient_font(size=38, bold=True):
    """Carga una fuente compatible (preferiblemente en negrita) en Windows, macOS y Linux."""
    font_paths_bold = [
        "arialbd.ttf",
        "C:\\Windows\\Fonts\\arialbd.ttf",
        "C:\\Windows\\Fonts\\segoeuib.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/System/Library/Fonts/Helvetica-Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
    ]
    font_paths_regular = [
        "arial.ttf",
        "C:\\Windows\\Fonts\\arial.ttf",
        "C:\\Windows\\Fonts\\segoeui.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Helvetica.ttc"
    ]
    
    selected_paths = font_paths_bold if bold else font_paths_regular + font_paths_bold

    for path in selected_paths:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    try:
        return ImageFont.load_default(size=size)
    except Exception:
        return ImageFont.load_default()

def wrap_text(text, font, max_width, draw_ctx):
    """Divide el texto en múltiples líneas para ajustar al ancho disponible."""
    lines = []
    words = text.split()
    current_line = []
    
    for word in words:
        current_line.append(word)
        test_line = " ".join(current_line)
        bbox = draw_ctx.textbbox((0, 0), test_line, font=font)
        line_width = bbox[2] - bbox[0]
        if line_width > max_width:
            current_line.pop()
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]
            
    if current_line:
        lines.append(" ".join(current_line))
    return lines

def process_image_with_text(
    uploaded_file, 
    text, 
    target_size=(1080, 1080),
    font_size=38,
    is_bold=True,
    text_color_hex="#FFFFFF",
    stroke_width=2,
    stroke_color_hex="#000000",
    card_bg_hex="#0F0F19",
    card_alpha=180,
    card_outline_hex="#FFFFFF"
):
    """
    Procesa la imagen en memoria usando Pillow con configuraciones personalizadas de texto:
    1. Ajusta la imagen al formato cuadrado HD (1080x1080).
    2. Dibuja una tarjeta semitransparente personalizable en la parte inferior.
    3. Renderiza el texto en negrita, con contorno (grosor) y color personalizado.
    """
    img = Image.open(uploaded_file).convert("RGBA")
    
    # Redimensionamiento proporcional preservando aspect ratio con fondo oscuro
    img.thumbnail(target_size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", target_size, (15, 15, 25, 255))
    offset = ((target_size[0] - img.width) // 2, (target_size[1] - img.height) // 2)
    canvas.paste(img, offset)
    
    text_clean = text.strip()
    if not text_clean:
        return np.array(canvas.convert("RGB"))
        
    # Capa de superposición para transparencia
    overlay = Image.new("RGBA", target_size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    font = load_resilient_font(size=font_size, bold=is_bold)
    max_text_width = int(target_size[0] * 0.82)
    lines = wrap_text(text_clean, font, max_text_width, draw)
    
    if not lines:
        return np.array(canvas.convert("RGB"))
        
    # Cálculo de métricas del texto
    line_heights = []
    line_widths = []
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font, stroke_width=stroke_width)
        line_widths.append(bbox[2] - bbox[0])
        line_heights.append(bbox[3] - bbox[1])
        
    total_text_height = sum(line_heights) + (len(lines) - 1) * 12
    max_line_width = max(line_widths)
    
    # Dimensiones y posición de la tarjeta inferior
    padding_x, padding_y = 35, 25
    card_w = max_line_width + (padding_x * 2)
    card_h = total_text_height + (padding_y * 2)
    
    card_x = (target_size[0] - card_w) // 2
    card_y = target_size[1] - card_h - 70 # Distancia desde el borde inferior
    
    # Convertir colores seleccionados a formato RGBA
    card_fill = hex_to_rgba(card_bg_hex, card_alpha)
    card_outline = hex_to_rgba(card_outline_hex, 60)
    text_color = hex_to_rgba(text_color_hex, 255)
    stroke_color = hex_to_rgba(stroke_color_hex, 255)
    
    # Dibujar tarjeta de cristal oscura semitransparente
    draw.rounded_rectangle(
        [card_x, card_y, card_x + card_w, card_y + card_h],
        radius=20,
        fill=card_fill,
        outline=card_outline,
        width=2
    )
    
    # Renderizar cada línea de texto con contorno (stroke) y sombra
    current_y = card_y + padding_y
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font, stroke_width=stroke_width)
        lw = bbox[2] - bbox[0]
        lx = card_x + (card_w - lw) // 2
        
        # Texto Principal con Contorno (Grosor/Outline)
        draw.text(
            (lx, current_y), 
            line, 
            font=font, 
            fill=text_color,
            stroke_width=stroke_width,
            stroke_fill=stroke_color
        )
        
        current_y += line_heights[i] + 12
        
    # Fusionar capas y retornar matriz NumPy para MoviePy
    final_canvas = Image.alpha_composite(canvas, overlay).convert("RGB")
    return np.array(final_canvas)


# ==========================================
# INTERFAZ DE USUARIO Y FLUJO PRINCIPAL
# ==========================================

st.markdown('<h1 class="main-title">DGM Studio Video Creator 🎬✨</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Diseñado por DGM SOLUTIONS • Crea videos profesionales con imágenes, música y tipografía personalizada.</p>', unsafe_allow_html=True)

# Panel Lateral de Configuración
with st.sidebar:
    st.header("⚙️ Configuración del Video")
    slide_duration = st.slider(
        "Duración por foto (segundos):",
        min_value=1.0,
        max_value=10.0,
        value=4.0,
        step=0.5
    )
    st.info("💡 Transición fluida de 1 segundo entre cada diapositiva.")

    st.markdown("---")
    st.header("🎨 Estilo de Texto y Tipografía")
    
    font_size = st.slider("Tamaño de Fuente:", min_value=24, max_value=60, value=38, step=2)
    is_bold = st.checkbox("Texto en Negrita (Bold)", value=True)
    text_color_hex = st.color_picker("Color del Texto:", "#FFFFFF")
    
    st.markdown("**Grosor y Borde de Letras:**")
    stroke_width = st.slider("Grosor del Contorno (px):", min_value=0, max_value=6, value=2)
    stroke_color_hex = st.color_picker("Color del Contorno:", "#000000")

    st.markdown("---")
    st.header("🟪 Estilo de Tarjeta (Fondo)")
    card_bg_hex = st.color_picker("Color de Fondo de Tarjeta:", "#0F0F19")
    card_alpha = st.slider("Opacidad de Tarjeta (0-255):", min_value=0, max_value=255, value=180)
    card_outline_hex = st.color_picker("Borde de Tarjeta:", "#FFFFFF")


# Sección Principal (Columns Layout)
col_left, col_right = st.columns([1.1, 0.9], gap="large")

with col_left:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("1. Carga de Archivos")
    
    uploaded_images = st.file_uploader(
        "Selecciona tus imágenes (JPG, PNG):",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True
    )
    
    uploaded_audio = st.file_uploader(
        "Selecciona tu canción de fondo (MP3):",
        type=["mp3"]
    )
    st.markdown('</div>', unsafe_allow_html=True)

    # Cálculo dinámico de la duración total
    if uploaded_images:
        num_images = len(uploaded_images)
        fade_time = min(1.0, slide_duration / 2.0)
        total_sec = num_images * slide_duration - (num_images - 1) * fade_time if num_images > 1 else slide_duration
        
        st.markdown(f"""
        <div style="background: rgba(0, 245, 212, 0.1); border: 1px solid #00f5d4; padding: 15px; border-radius: 12px; margin-bottom: 20px;">
            ⏱️ <b>Duración estimada del video:</b> {total_sec:.1f} segundos ({num_images} fotos)
        </div>
        """, unsafe_allow_html=True)

    # Editor Dinámico de Frases
    phrases = []
    if uploaded_images:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("2. Mensajes para cada Foto")
        st.caption("Escribe la dedicatoria o subtítulo que aparecerá sobre cada imagen:")
        
        for idx, img_file in enumerate(uploaded_images):
            st.markdown('<div class="thumb-card">', unsafe_allow_html=True)
            c1, c2 = st.columns([0.25, 0.75])
            with c1:
                st.image(img_file, use_container_width=True)
            with c2:
                txt = st.text_input(
                    f"Foto #{idx+1}",
                    key=f"phrase_{idx}",
                    placeholder="Ej: Un recuerdo inolvidable ❤️"
                )
                phrases.append(txt)
            st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

with col_right:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("3. Vista Previa y Generación")
    
    if not uploaded_images:
        st.info("👈 Sube tus fotos en el panel izquierdo para comenzar.")
    else:
        st.write(f"✓ **{len(uploaded_images)}** fotos cargadas correctamente.")
        if uploaded_audio:
            st.write("✓ Música de fondo cargada.")
        else:
            st.warning("⚠️ No has subido audio. El video se generará en silencio.")

        st.markdown("<br>", unsafe_allow_html=True)
        
        # Botón para Iniciar Renderizado
        if st.button("🚀 Generar Video MP4"):
            with st.spinner("⏳ Procesando imágenes, renderizando texto y ensamblando video..."):
                try:
                    # Crear directorio temporal
                    with tempfile.TemporaryDirectory() as temp_dir:
                        processed_frames = []
                        
                        # 1. Procesar imágenes con Pillow (Texto + Tarjeta + Estilos)
                        for img_file, text in zip(uploaded_images, phrases):
                            frame_np = process_image_with_text(
                                uploaded_file=img_file,
                                text=text,
                                font_size=font_size,
                                is_bold=is_bold,
                                text_color_hex=text_color_hex,
                                stroke_width=stroke_width,
                                stroke_color_hex=stroke_color_hex,
                                card_bg_hex=card_bg_hex,
                                card_alpha=card_alpha,
                                card_outline_hex=card_outline_hex
                            )
                            processed_frames.append(frame_np)
                        
                        # 2. Ensamblar clips en MoviePy
                        clips = []
                        fade_duration = min(1.0, slide_duration / 2.0)
                        
                        for frame in processed_frames:
                            clip = ImageClip(frame).set_duration(slide_duration)
                            clips.append(clip)
                            
                        if len(clips) == 1:
                            final_video = clips[0]
                        else:
                            clips_with_fade = [clips[0]] + [c.crossfadein(fade_duration) for c in clips[1:]]
                            final_video = concatenate_videoclips(clips_with_fade, method="compose", padding=-fade_duration)
                        
                        # 3. Procesar Audio
                        if uploaded_audio is not None:
                            audio_path = os.path.join(temp_dir, "temp_audio.mp3")
                            with open(audio_path, "wb") as f:
                                f.write(uploaded_audio.read())
                                
                            audio_clip = AudioFileClip(audio_path)
                            video_dur = final_video.duration
                            
                            # Recortar si el audio es más largo
                            if audio_clip.duration > video_dur:
                                audio_clip = audio_clip.subclip(0, video_dur)
                                
                            # Aplicar desvanecimiento al final del audio
                            fade_out_time = min(2.0, video_dur)
                            try:
                                audio_clip = audio_clip.fx(afx.audio_fadeout, fade_out_time)
                            except Exception:
                                pass
                                
                            final_video = final_video.set_audio(audio_clip)
                        
                        # 4. Renderizar archivo MP4 de salida
                        output_mp4_path = os.path.join(temp_dir, "dgm_studio_output.mp4")
                        final_video.write_videofile(
                            output_mp4_path,
                            fps=24,
                            codec="libx264",
                            audio_codec="aac",
                            logger=None
                        )
                        
                        # Cargar en memoria para reproducción y descarga
                        with open(output_mp4_path, "rb") as v_file:
                            video_bytes = v_file.read()
                            
                        # Limpiar clips
                        final_video.close()
                        
                        # Guardar resultado en session_state
                        st.session_state["video_bytes"] = video_bytes
                        st.session_state["generated"] = True

                except Exception as e:
                    st.error(f"Ocurrió un error al generar el video: {str(e)}")

    # Mostrar Resultado si ya fue generado
    if st.session_state.get("generated", False):
        st.balloons()
        st.success("🎉 ¡Tu video se ha generado con éxito!")
        
        st.video(st.session_state["video_bytes"])
        
        st.download_button(
            label="⬇️ Descargar Video MP4",
            data=st.session_state["video_bytes"],
            file_name="DGM_Studio_Video.mp4",
            mime="video/mp4"
        )
        
    st.markdown('</div>', unsafe_allow_html=True)


# ==========================================
# FOOTER PROFESIONAL DGM SOLUTIONS
# ==========================================
st.markdown("""
<div class="footer-container">
    <p style="margin-bottom: 8px;"><b>DGM Studio Video Creator</b> &copy; 2026 | Todos los derechos reservados.</p>
    <p style="margin-bottom: 8px;">
        Desarrollado por <b>DGM SOLUTIONS</b> &bull; Área de Ingeniería de Software & Multimedia
    </p>
    <p>
        <a href="https://github.com" target="_blank" class="footer-link">GitHub</a> &bull; 
        <a href="https://linkedin.com" target="_blank" class="footer-link">LinkedIn</a> &bull; 
        <a href="mailto:contacto@dgmsolutions.com" class="footer-link">Contacto</a>
    </p>
</div>
""", unsafe_allow_html=True)

