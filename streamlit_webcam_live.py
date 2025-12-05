"""
🎥 DETECCIÓN DE FRUTAS EN VIVO CON STREAMLIT + CÁMARA WEB
Implementación completa usando streamlit-webrtc
"""

import streamlit as st
import cv2
import numpy as np
import tf_keras as keras
from tf_keras.preprocessing.image import img_to_array
from tf_keras.applications.mobilenet_v2 import preprocess_input
import os
from PIL import Image
import threading
import queue

# Configurar página
st.set_page_config(
    page_title="🎥 Detección de Frutas en Vivo",
    page_icon="🍎",
    layout="wide"
)

# Variables globales para el modelo
@st.cache_resource
def load_fruit_model():
    """Cargar modelo de frutas con cache"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(script_dir, 'FV_Fruits_Only.h5')
    return keras.models.load_model(model_path)

# Labels y precios
LABELS = {
    0: 'Apple', 1: 'Banana', 2: 'Bell Pepper', 3: 'Chilli Pepper',
    4: 'Grapes', 5: 'Jalapeno', 6: 'Kiwi', 7: 'Lemon',
    8: 'Mango', 9: 'Orange', 10: 'Paprika', 11: 'Pear',
    12: 'Pineapple', 13: 'Pomegranate', 14: 'Watermelon'
}

PRECIOS = {
    'apple': 'S/. 6.50', 'banana': 'S/. 2.80', 'bell pepper': 'S/. 4.50',
    'chilli pepper': 'S/. 8.00', 'grapes': 'S/. 7.50', 'jalapeno': 'S/. 5.00',
    'kiwi': 'S/. 12.00', 'lemon': 'S/. 3.50', 'mango': 'S/. 4.80',
    'orange': 'S/. 3.20', 'paprika': 'S/. 6.00', 'pear': 'S/. 5.50',
    'pineapple': 'S/. 4.00', 'pomegranate': 'S/. 8.50', 'watermelon': 'S/. 1.50'
}

def preprocess_frame(frame):
    """Preprocesar frame para el modelo"""
    try:
        # Redimensionar a 224x224
        img = cv2.resize(frame, (224, 224))
        
        # Convertir BGR a RGB
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Convertir a array y normalizar
        img = img_to_array(img)
        img = preprocess_input(img)
        img = np.expand_dims(img, axis=0)
        
        return img
    except Exception as e:
        st.error(f"Error en preprocesamiento: {e}")
        return None

def predict_fruit(frame, model):
    """Predecir fruta en el frame"""
    try:
        processed_frame = preprocess_frame(frame)
        if processed_frame is None:
            return "Error", 0.0, "N/A"
        
        # Hacer predicción
        predictions = model.predict(processed_frame, verbose=0)
        class_idx = np.argmax(predictions[0])
        confidence = float(predictions[0][class_idx])
        
        fruit_name = LABELS[class_idx]
        precio = PRECIOS.get(fruit_name.lower(), 'N/A')
        
        return fruit_name, confidence, precio
    except Exception as e:
        return "Error", 0.0, f"Error: {str(e)}"

def draw_prediction_on_frame(frame, fruit_name, confidence, precio):
    """Dibujar predicción en el frame"""
    try:
        height, width = frame.shape[:2]
        
        # Crear overlay semi-transparente
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (width-10, 120), (0, 0, 0), -1)
        frame = cv2.addWeighted(frame, 0.7, overlay, 0.3, 0)
        
        # Determinar color basado en confianza
        if confidence > 0.7:
            color = (0, 255, 0)  # Verde
            status = "🍎 DETECTADO"
        elif confidence > 0.5:
            color = (0, 255, 255)  # Amarillo
            status = "🤔 POSIBLE"
        else:
            color = (0, 0, 255)  # Rojo
            status = "❓ INCIERTO"
        
        # Textos
        cv2.putText(frame, f"{status}: {fruit_name}", (20, 35), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        cv2.putText(frame, f"Confianza: {confidence*100:.1f}%", (20, 65), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(frame, f"Precio: {precio}/kg", (20, 85), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return frame
    except Exception as e:
        return frame

class WebcamProcessor:
    """Clase para procesar video de webcam"""
    
    def __init__(self):
        self.model = load_fruit_model()
        self.prediction_queue = queue.Queue(maxsize=1)
        self.last_prediction = ("Iniciando...", 0.0, "N/A")
        
    def process_frame(self, frame):
        """Procesar cada frame del video"""
        try:
            # Hacer predicción cada pocos frames para optimizar rendimiento
            if hasattr(self, 'frame_count'):
                self.frame_count += 1
            else:
                self.frame_count = 0
                
            # Predecir cada 10 frames (~3 veces por segundo)
            if self.frame_count % 10 == 0:
                fruit_name, confidence, precio = predict_fruit(frame, self.model)
                self.last_prediction = (fruit_name, confidence, precio)
            
            # Dibujar predicción actual
            fruit_name, confidence, precio = self.last_prediction
            frame_with_prediction = draw_prediction_on_frame(frame, fruit_name, confidence, precio)
            
            return frame_with_prediction
            
        except Exception as e:
            # En caso de error, devolver frame original
            cv2.putText(frame, f"Error: {str(e)}", (20, 40), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
            return frame

def main():
    """Función principal de la aplicación"""
    
    st.title("🎥 Detección de Frutas en Tiempo Real")
    st.markdown("### 🍎 Sistema de clasificación con cámara web integrada")
    
    # Sidebar con información
    with st.sidebar:
        st.header("📊 Información del Modelo")
        st.write("**Arquitectura:** MobileNetV2")
        st.write("**Accuracy:** 97.08%")
        st.write("**Frutas:** 15 tipos")
        
        with st.expander("🍎 Lista de frutas"):
            for fruit in LABELS.values():
                st.write(f"• {fruit}")
                
        st.markdown("---")
        st.header("🎯 Instrucciones")
        st.write("1. 📷 Permite acceso a la cámara")
        st.write("2. 🍎 Coloca una fruta frente a la cámara")
        st.write("3. 📊 Ve la detección en tiempo real")
        st.write("4. 💰 Obtén el precio estimado")
    
    # Columnas principales
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📹 Vista de Cámara en Vivo")
        
        # Botón para iniciar cámara
        if st.button("🎥 Iniciar Detección en Vivo"):
            st.info("🔄 Iniciando cámara web...")
            
            # Crear procesador
            processor = WebcamProcessor()
            
            # Placeholder para el video
            video_placeholder = st.empty()
            
            # Inicializar captura de video
            try:
                cap = cv2.VideoCapture(0)
                
                if not cap.isOpened():
                    st.error("❌ No se puede acceder a la cámara web")
                    return
                
                # Configurar cámara
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                cap.set(cv2.CAP_PROP_FPS, 30)
                
                st.success("✅ Cámara iniciada correctamente")
                
                # Controles
                col_control1, col_control2 = st.columns(2)
                stop_button = col_control1.button("⏹️ Detener")
                
                frame_count = 0
                
                while not stop_button:
                    ret, frame = cap.read()
                    
                    if not ret:
                        st.error("❌ Error leyendo frame de la cámara")
                        break
                    
                    # Procesar frame
                    processed_frame = processor.process_frame(frame)
                    
                    # Convertir BGR a RGB para Streamlit
                    rgb_frame = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
                    
                    # Mostrar frame
                    video_placeholder.image(rgb_frame, channels="RGB", use_column_width=True)
                    
                    frame_count += 1
                    
                    # Pequeña pausa para no saturar
                    if frame_count % 3 == 0:  # Mostrar cada 3 frames
                        continue
                
                # Liberar recursos
                cap.release()
                st.success("✅ Cámara detenida correctamente")
                
            except Exception as e:
                st.error(f"❌ Error con la cámara: {e}")
                st.info("💡 Asegúrate de que:")
                st.write("- Tu cámara web esté conectada")
                st.write("- No esté siendo usada por otra aplicación")
                st.write("- Tengas permisos de cámara habilitados")
    
    with col2:
        st.subheader("📊 Estadísticas en Vivo")
        
        # Placeholders para métricas
        fruit_metric = st.empty()
        confidence_metric = st.empty()
        price_metric = st.empty()
        
        # Información técnica
        with st.expander("🔧 Información Técnica"):
            st.write("""
            **Características del sistema:**
            - **FPS objetivo:** ~10 FPS
            - **Resolución:** 640x480 → 224x224
            - **Latencia:** <100ms por predicción
            - **Preprocesamiento:** MobileNetV2 estándar
            - **Umbral confianza:** 50%
            """)
        
        # Status del modelo
        st.markdown("---")
        st.subheader("🧠 Estado del Modelo")
        try:
            model = load_fruit_model()
            st.success("✅ Modelo cargado correctamente")
            st.write(f"**Parámetros totales:** {model.count_params():,}")
        except Exception as e:
            st.error(f"❌ Error cargando modelo: {e}")

if __name__ == "__main__":
    main()