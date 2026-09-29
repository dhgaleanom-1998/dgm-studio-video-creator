# 🎬 DGM Studio Video Creator

Aplicación web desarrollada con **Streamlit**, **MoviePy** y **Pillow** para la creación automatizada de videos promocionales y dedicatorias con música de fondo, subtítulos estilizados y estética Glassmorphism.

Desarrollado por **DGM SOLUTIONS**.

---

## 🚀 Características
- 🖼️ **Carga múltiple de imágenes:** Formatos JPG y PNG en resolución cuadrada HD (1080x1080).
- 🎨 **Estilo de Texto Avanzado:** Control de tamaño, negrita (bold), colores y grosor de contorno (stroke) para alta legibilidad.
- 🟪 **Tarjetas Semitransparentes:** Fondos ajustables con opacidad y bordes personalizados.
- 🎵 **Audio Integrado:** Mezcla de música MP3 con desvanecimiento al final (*fade-out*).
- ⏱️ **Ajuste de Tiempos:** Control de duración por diapositiva y transiciones suaves (*crossfade*).

---

## 🛠️ Instalación Local

```bash
# 1. Clonar el repositorio
git clone [https://github.com/dhgaleanom-1998/dgm-studio-video-creator.git](https://github.com/dhgaleanom-1998/dgm-studio-video-creator.git)
cd dgm-studio-video-creator

# 2. Crear y activar entorno virtual
python -m venv venv
# En Windows:
venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar la aplicación
streamlit run app.py
