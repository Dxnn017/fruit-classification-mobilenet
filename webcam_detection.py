"""
🎥 DETECCIÓN DE FRUTAS EN TIEMPO REAL - WEBCAM
Adaptación del modelo MobileNetV2 para webcam en vivo
"""

import cv2
import numpy as np
import tensorflow as tf
import tf_keras as keras
from tf_keras.preprocessing.image import img_to_array
from tf_keras.applications.mobilenet_v2 import preprocess_input
import os

# Configurar el directorio del script
script_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(script_dir, 'FV_Fruits_Only.h5')

# Cargar modelo
print("🔄 Cargando modelo...")
model = keras.models.load_model(model_path)
print("✅ Modelo cargado correctamente")

# Labels de frutas
labels = {
    0: 'Apple', 1: 'Banana', 2: 'Bell Pepper', 3: 'Chilli Pepper',
    4: 'Grapes', 5: 'Jalapeno', 6: 'Kiwi', 7: 'Lemon',
    8: 'Mango', 9: 'Orange', 10: 'Paprika', 11: 'Pear',
    12: 'Pineapple', 13: 'Pomegranate', 14: 'Watermelon'
}

# Precios en soles
precios = {
    'apple': 'S/. 6.50', 'banana': 'S/. 2.80', 'bell pepper': 'S/. 4.50',
    'chilli pepper': 'S/. 8.00', 'grapes': 'S/. 7.50', 'jalapeno': 'S/. 5.00',
    'kiwi': 'S/. 12.00', 'lemon': 'S/. 3.50', 'mango': 'S/. 4.80',
    'orange': 'S/. 3.20', 'paprika': 'S/. 6.00', 'pear': 'S/. 5.50',
    'pineapple': 'S/. 4.00', 'pomegranate': 'S/. 8.50', 'watermelon': 'S/. 1.50'
}

def preprocess_frame(frame):
    """
    Preprocesa un frame de la webcam para el modelo
    """
    # Redimensionar a 224x224
    img = cv2.resize(frame, (224, 224))
    
    # Convertir BGR a RGB (OpenCV usa BGR, el modelo espera RGB)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    # Convertir a array y normalizar
    img = img_to_array(img)
    img = preprocess_input(img)  # Normalización MobileNetV2 [-1, 1]
    
    # Añadir dimensión de batch
    img = np.expand_dims(img, axis=0)
    
    return img

def predict_fruit(frame):
    """
    Predice la fruta en el frame
    """
    processed_frame = preprocess_frame(frame)
    
    # Hacer predicción
    predictions = model.predict(processed_frame, verbose=0)
    class_idx = np.argmax(predictions[0])
    confidence = float(predictions[0][class_idx])
    
    fruit_name = labels[class_idx]
    precio = precios.get(fruit_name.lower(), 'N/A')
    
    return fruit_name, confidence, precio

def draw_prediction(frame, fruit_name, confidence, precio):
    """
    Dibuja la predicción en el frame
    """
    height, width = frame.shape[:2]
    
    # Fondo para el texto
    overlay = frame.copy()
    cv2.rectangle(overlay, (10, 10), (width-10, 120), (0, 0, 0), -1)
    frame = cv2.addWeighted(frame, 0.7, overlay, 0.3, 0)
    
    # Texto principal
    if confidence > 0.5:  # Solo mostrar si confianza > 50%
        text = f"🍎 {fruit_name}"
        conf_text = f"Confianza: {confidence*100:.1f}%"
        price_text = f"Precio: {precio}/kg"
        
        color = (0, 255, 0) if confidence > 0.7 else (0, 255, 255)  # Verde si > 70%, amarillo si > 50%
    else:
        text = "❓ No detectado"
        conf_text = f"Confianza: {confidence*100:.1f}%"
        price_text = "Acerca más la fruta"
        color = (0, 0, 255)  # Rojo
    
    # Dibujar textos
    cv2.putText(frame, text, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
    cv2.putText(frame, conf_text, (20, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    cv2.putText(frame, price_text, (20, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    # Instrucciones
    cv2.putText(frame, "Presiona 'q' para salir, 'c' para captura", 
                (20, height-20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
    
    return frame

def main():
    """
    Función principal para detección en vivo
    """
    print("🎥 Iniciando detección en vivo...")
    print("📋 Frutas detectables:", list(labels.values()))
    print("🎯 Instrucciones:")
    print("   - Presiona 'q' para salir")
    print("   - Presiona 'c' para capturar imagen")
    print("   - Coloca la fruta centrada en la cámara")
    
    # Inicializar webcam
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("❌ Error: No se puede abrir la cámara")
        return
    
    # Configurar resolución
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    frame_count = 0
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("❌ Error leyendo frame de la cámara")
                break
            
            # Procesar cada 3 frames para mejor rendimiento
            if frame_count % 3 == 0:
                fruit_name, confidence, precio = predict_fruit(frame)
            
            # Dibujar predicción en el frame
            frame = draw_prediction(frame, fruit_name, confidence, precio)
            
            # Mostrar el frame
            cv2.imshow('🍎 Detección de Frutas - MobileNetV2', frame)
            
            # Manejar teclas
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('c'):
                # Capturar imagen
                cv2.imwrite(f'captura_fruta_{frame_count}.jpg', frame)
                print(f"📸 Imagen capturada: captura_fruta_{frame_count}.jpg")
            
            frame_count += 1
    
    except KeyboardInterrupt:
        print("\n🛑 Detenido por el usuario")
    
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("✅ Cámara liberada y ventanas cerradas")

if __name__ == "__main__":
    main()