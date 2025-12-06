"""
🎥 STREAMLIT + WEBCAM - Detección en Tiempo Real
Versión mejorada con interfaz web y webcam
"""

import streamlit as st
import cv2
import numpy as np
import tensorflow as tf
import tf_keras as keras
from tf_keras.preprocessing.image import img_to_array
from tf_keras.applications.mobilenet_v2 import preprocess_input
import os
from PIL import Image
import tempfile

# Configurar página
st.set_page_config(
    page_title="🎥 Detección de Frutas en Vivo",
    page_icon="🍎",
    layout="wide"
)

# Obtener directorio del script
script_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(script_dir, 'FV_Fruits_Only.h5')

# Cache del modelo para mejor rendimiento
@st.cache_resource
def load_model():
    return keras.models.load_model(model_path)

# Cargar modelo
model = load_model()

# Labels y precios
labels = {
    0: 'Apple', 1: 'Banana', 2: 'Bell Pepper', 3: 'Chilli Pepper',
    4: 'Grapes', 5: 'Jalapeno', 6: 'Kiwi', 7: 'Lemon',
    8: 'Mango', 9: 'Orange', 10: 'Paprika', 11: 'Pear',
    12: 'Pineapple', 13: 'Pomegranate', 14: 'Watermelon'
}

precios = {
    'apple': 'S/. 6.50', 'banana': 'S/. 2.80', 'bell pepper': 'S/. 4.50',
    'chilli pepper': 'S/. 8.00', 'grapes': 'S/. 7.50', 'jalapeno': 'S/. 5.00',
    'kiwi': 'S/. 12.00', 'lemon': 'S/. 3.50', 'mango': 'S/. 4.80',
    'orange': 'S/. 3.20', 'paprika': 'S/. 6.00', 'pear': 'S/. 5.50',
    'pineapple': 'S/. 4.00', 'pomegranate': 'S/. 8.50', 'watermelon': 'S/. 1.50'
}

def preprocess_image(image):
    """Preprocesa imagen para el modelo"""
    img = cv2.resize(image, (224, 224))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = img_to_array(img)
    img = preprocess_input(img)
    img = np.expand_dims(img, axis=0)
    return img

def predict_fruit(image):
    """Predice fruta en la imagen"""
    processed_img = preprocess_image(image)
    predictions = model.predict(processed_img, verbose=0)
    class_idx = np.argmax(predictions[0])
    confidence = float(predictions[0][class_idx])
    
    fruit_name = labels[class_idx]
    precio = precios.get(fruit_name.lower(), 'N/A')
    
    return fruit_name, confidence, precio

# Interfaz principal
st.title("🎥 Detección de Frutas en Tiempo Real")
st.markdown("### Usa tu cámara web para identificar frutas al instante")

# Sidebar con información
with st.sidebar:
    st.header("📋 Información del Modelo")
    st.write("**Arquitectura:** MobileNetV2")
    st.write("**Accuracy:** 97.08%")
    st.write("**Frutas detectables:** 15")
    
    with st.expander("🍎 Lista de frutas"):
        for fruit in labels.values():
            st.write(f"• {fruit}")

# Modo de detección
mode = st.radio(
    "🎯 Selecciona el modo:",
    ["📸 Subir Imagen", "🎥 Cámara Web (Experimental)"]
)

if mode == "📸 Subir Imagen":
    # Modo imagen (existente mejorado)
    uploaded_file = st.file_uploader(
        "Selecciona una imagen de fruta", 
        type=["jpg", "jpeg", "png"]
    )
    
    if uploaded_file is not None:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📸 Imagen Original")
            image = Image.open(uploaded_file)
            st.image(image, use_container_width=True)
        
        with col2:
            st.subheader("🔍 Resultados")
            
            # Convertir PIL a OpenCV
            img_array = np.array(image)
            if len(img_array.shape) == 3:
                img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            
            with st.spinner("Analizando fruta..."):
                fruit_name, confidence, precio = predict_fruit(img_array)
            
            # Mostrar resultados
            if confidence > 0.5:
                st.success(f"🍎 **{fruit_name}**")
                st.metric("🎯 Confianza", f"{confidence*100:.1f}%")
                st.info(f"💰 **{precio}** por kilogramo")
            else:
                st.warning(f"❓ Detección incierta: {fruit_name}")
                st.metric("🎯 Confianza", f"{confidence*100:.1f}%")
                st.caption("Prueba con una imagen más clara")

elif mode == "🎥 Cámara Web (Experimental)":
    st.info("🚧 **Función experimental**: Requiere permisos de cámara")
    
    # Placeholder para webcam
    camera_placeholder = st.empty()
    results_placeholder = st.empty()
    
    # Botones de control
    col1, col2, col3 = st.columns(3)
    start_camera = col1.button("▶️ Iniciar Cámara")
    capture_frame = col2.button("📸 Capturar")
    stop_camera = col3.button("⏹️ Detener")
    
    if start_camera:
        st.warning("⚠️ **Instrucciones para usar la cámara web:**")
        st.write("1. Ejecuta el archivo `webcam_detection.py` desde terminal")
        st.write("2. O instala las dependencias necesarias:")
        st.code("pip install opencv-python", language="bash")
        st.write("3. Luego ejecuta:")
        st.code("python webcam_detection.py", language="bash")
        
        st.info("""
        **¿Por qué no funciona directamente en Streamlit?**
        - Streamlit ejecuta en servidor web
        - Acceso directo a cámara requiere permisos especiales
        - OpenCV funciona mejor en aplicaciones nativas
        """)

# Información adicional
with st.expander("ℹ️ Información Técnica"):
    st.write("""
    **🔧 Características técnicas:**
    - **Modelo**: MobileNetV2 + Transfer Learning
    - **Resolución**: 224x224 píxeles
    - **Preprocesamiento**: Normalización [-1, 1]
    - **Velocidad**: ~30 FPS (depende del hardware)
    - **Precisión**: 97.08% en conjunto de validación
    
    **📱 Requisitos para cámara web:**
    - OpenCV instalado (`pip install opencv-python`)
    - Cámara web funcional
    - Permisos de cámara habilitados
    """)

st.markdown("---")
st.caption("🍎 Desarrollado con MobileNetV2 y Streamlit | Precios referenciales del mercado peruano")