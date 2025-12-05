import streamlit as st
from PIL import Image
import numpy as np
import tf_keras as keras
from tf_keras.preprocessing.image import load_img, img_to_array
import os
import time
from concurrent.futures import ThreadPoolExecutor
import pandas as pd

# Obtener el directorio del script
script_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(script_dir, 'FV_Fruits_Only.h5')

# Cargar modelo entrenado solo con frutas
model = keras.models.load_model(model_path)

labels = {
    0: 'apple', 1: 'banana', 2: 'bell pepper', 3: 'chilli pepper', 
    4: 'grapes', 5: 'jalepeno', 6: 'kiwi', 7: 'lemon', 
    8: 'mango', 9: 'orange', 10: 'paprika', 11: 'pear', 
    12: 'pineapple', 13: 'pomegranate', 14: 'watermelon'
}

fruits = ['Apple', 'Banana', 'Bell Pepper', 'Chilli Pepper', 'Grapes', 'Jalepeno', 
          'Kiwi', 'Lemon', 'Mango', 'Orange', 'Paprika', 'Pear', 
          'Pineapple', 'Pomegranate', 'Watermelon']

# Precios aproximados en soles peruanos por kilogramo (S/./kg)
precios_soles = {
    'apple': 'S/. 6.50',
    'banana': 'S/. 2.80',
    'bell pepper': 'S/. 4.50',
    'chilli pepper': 'S/. 8.00',
    'grapes': 'S/. 9.50',
    'jalepeno': 'S/. 7.50',
    'kiwi': 'S/. 12.00',
    'lemon': 'S/. 3.50',
    'mango': 'S/. 5.50',
    'orange': 'S/. 4.00',
    'paprika': 'S/. 5.00',
    'pear': 'S/. 7.00',
    'pineapple': 'S/. 6.00',
    'pomegranate': 'S/. 15.00',
    'watermelon': 'S/. 2.50'
}

def get_precio(prediction):
    """Obtiene el precio aproximado de la fruta en soles peruanos"""
    return precios_soles.get(prediction.lower(), 'Precio no disponible')


def prepare_image(img_path):
    """Procesa una sola imagen y retorna la predicción"""
    img = load_img(img_path, target_size=(224, 224, 3))
    img = img_to_array(img)
    img = img / 255
    img = np.expand_dims(img, [0])
    answer = model.predict(img, verbose=0)
    y_class = answer.argmax(axis=-1)
    y = int(y_class[0])
    res = labels[y]
    confidence = float(answer[0][y_class[0]])
    return res.capitalize(), confidence

def prepare_multiple_images(image_paths):
    """Procesa múltiples imágenes de forma eficiente usando batch prediction"""
    if not image_paths:
        return []
    
    # Cargar y preprocesar todas las imágenes
    images_batch = []
    valid_paths = []
    error_files = []
    
    for img_path in image_paths:
        try:
            if os.path.exists(img_path):
                # Validar que el archivo sea una imagen válida
                img = load_img(img_path, target_size=(224, 224, 3))
                img = img_to_array(img)
                
                # Verificar que la imagen tenga el formato correcto
                if img.shape == (224, 224, 3):
                    img = img / 255.0  # Normalización
                    images_batch.append(img)
                    valid_paths.append(img_path)
                else:
                    error_files.append((img_path, "Formato de imagen inválido"))
            else:
                error_files.append((img_path, "Archivo no encontrado"))
        except Exception as e:
            error_files.append((img_path, f"Error al procesar: {str(e)}"))
    
    if not images_batch:
        st.error("❌ No se pudieron procesar las imágenes. Verifica que sean archivos de imagen válidos.")
        return []
    
    if error_files:
        st.warning(f"⚠️ {len(error_files)} archivo(s) no se pudieron procesar:")
        for file_path, error in error_files:
            st.caption(f"• {os.path.basename(file_path)}: {error}")
    
    # Convertir a numpy array para predicción en batch
    images_batch = np.array(images_batch)
    
    try:
        # Predicción en batch (más eficiente)
        predictions = model.predict(images_batch, verbose=0)
    except Exception as e:
        st.error(f"❌ Error durante la predicción: {str(e)}")
        return []
    
    # Procesar resultados
    results = []
    for i, prediction in enumerate(predictions):
        try:
            y_class = prediction.argmax()
            confidence = float(prediction[y_class])
            
            # Validar que la confianza esté en rango válido
            if 0 <= confidence <= 1:
                fruit_name = labels[y_class].capitalize()
                results.append({
                    'image_path': valid_paths[i],
                    'prediction': fruit_name,
                    'confidence': confidence,
                    'price': get_precio(fruit_name),
                    'filename': os.path.basename(valid_paths[i])
                })
            else:
                st.warning(f"⚠️ Confianza inválida para {os.path.basename(valid_paths[i])}")
        except Exception as e:
            st.error(f"❌ Error procesando resultado para {os.path.basename(valid_paths[i])}: {str(e)}")
    
    return results


def run():
    st.title("🍎 Clasificación de Frutas - Procesamiento Individual y Múltiple")
    
    # Tabs para diferentes modos
    tab1, tab2 = st.tabs(["📸 Imagen Individual", "📚 Múltiples Imágenes"])
    
    with tab1:
        st.markdown("### Sube una imagen para identificar una fruta")
        
        # Mostrar lista de frutas disponibles
        with st.expander("📋 Ver lista de frutas que puedo identificar"):
            cols = st.columns(3)
            for idx, fruit in enumerate(fruits):
                cols[idx % 3].write(f"• {fruit}")
        
        img_file = st.file_uploader("Selecciona una imagen", type=["jpg", "png", "jpeg"], key="single")
        
        if img_file is not None:
            # Crear columnas para mejor diseño
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 📸 Imagen Original")
                img = Image.open(img_file).resize((250, 250))
                st.image(img, use_container_width=True)
            
            with col2:
                st.markdown("#### 🔍 Resultados")
                
                # Crear directorio upload_images si no existe
                upload_dir = os.path.join(script_dir, 'upload_images')
                os.makedirs(upload_dir, exist_ok=True)
                
                save_image_path = os.path.join(upload_dir, f"single_{img_file.name}")
                with open(save_image_path, "wb") as f:
                    f.write(img_file.getbuffer())
                
                with st.spinner('Analizando fruta...'):
                    result, confidence = prepare_image(save_image_path)
                    
                # Mostrar predicción
                st.success(f"🍎 **Identificado como: {result}**")
                st.info(f"🎯 **Confianza: {confidence:.2%}**")
                
                # Mostrar precio
                precio = get_precio(result)
                st.info(f'💰 **Precio aproximado: {precio}** por kilogramo')
                st.caption('💡 Precios referenciales del mercado peruano')
    
    with tab2:
        st.markdown("### 🚀 Procesamiento de múltiples imágenes simultáneas")
        st.info("📝 Puedes subir hasta 10 imágenes para procesamiento en lote")
        
        # Subir múltiples archivos
        uploaded_files = st.file_uploader(
            "Selecciona múltiples imágenes", 
            type=["jpg", "png", "jpeg"], 
            accept_multiple_files=True,
            key="multiple"
        )
        
        if uploaded_files:
            # Validar límite de archivos
            if len(uploaded_files) > 10:
                st.error("❌ Por favor, sube máximo 10 imágenes a la vez")
                return
            
            st.success(f"✅ {len(uploaded_files)} imágenes cargadas correctamente")
            
            # Crear directorio para múltiples imágenes
            upload_dir = os.path.join(script_dir, 'upload_images', 'batch')
            os.makedirs(upload_dir, exist_ok=True)
            
            # Guardar archivos y crear paths
            image_paths = []
            for i, uploaded_file in enumerate(uploaded_files):
                file_path = os.path.join(upload_dir, f"batch_{i}_{uploaded_file.name}")
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                image_paths.append(file_path)
            
            # Botón para procesar
            if st.button("🔍 Analizar todas las imágenes", type="primary"):
                # Progress bar
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                start_time = time.time()
                
                # Procesar en batch
                with st.spinner('Procesando múltiples imágenes...'):
                    progress_bar.progress(50)
                    status_text.text("Analizando imágenes...")
                    
                    results = prepare_multiple_images(image_paths)
                    
                    progress_bar.progress(100)
                    end_time = time.time()
                    processing_time = end_time - start_time
                
                status_text.text(f"✅ Procesamiento completado en {processing_time:.2f} segundos")
                
                # Mostrar resultados
                st.markdown("## 📊 Resultados del Procesamiento en Lote")
                
                # Crear DataFrame para mostrar resultados tabulares
                df_results = []
                for i, result in enumerate(results):
                    df_results.append({
                        'Imagen': uploaded_files[i].name,
                        'Fruta Detectada': result['prediction'],
                        'Confianza': f"{result['confidence']:.2%}",
                        'Precio (S/./ kg)': result['price']
                    })
                
                df = pd.DataFrame(df_results)
                st.dataframe(df, use_container_width=True)
                
                # Mostrar imágenes con resultados en grid
                st.markdown("### 🖼️ Vista Detallada de Resultados")
                
                # Crear grid de imágenes
                cols_per_row = 3
                for i in range(0, len(uploaded_files), cols_per_row):
                    cols = st.columns(cols_per_row)
                    
                    for j in range(cols_per_row):
                        idx = i + j
                        if idx < len(uploaded_files):
                            with cols[j]:
                                # Mostrar imagen
                                img = Image.open(uploaded_files[idx]).resize((200, 200))
                                st.image(img, use_container_width=True)
                                
                                # Mostrar resultados
                                result = results[idx]
                                st.markdown(f"**📝 {uploaded_files[idx].name}**")
                                st.success(f"🍎 {result['prediction']}")
                                st.info(f"🎯 {result['confidence']:.1%}")
                                st.caption(f"💰 {result['price']}")
                
                # Resumen estadístico
                st.markdown("### 📈 Resumen Estadístico")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total de Imágenes", len(results))
                
                with col2:
                    avg_confidence = np.mean([r['confidence'] for r in results])
                    st.metric("Confianza Promedio", f"{avg_confidence:.1%}")
                
                with col3:
                    unique_fruits = len(set([r['prediction'] for r in results]))
                    st.metric("Frutas Únicas", unique_fruits)
                
                with col4:
                    st.metric("Tiempo de Proceso", f"{processing_time:.2f}s")
                
                # Mostrar distribución de frutas detectadas
                fruit_counts = {}
                for result in results:
                    fruit = result['prediction']
                    fruit_counts[fruit] = fruit_counts.get(fruit, 0) + 1
                
                if len(fruit_counts) > 1:
                    st.markdown("### 📊 Distribución de Frutas Detectadas")
                    chart_data = pd.DataFrame(list(fruit_counts.items()), columns=['Fruta', 'Cantidad'])
                    st.bar_chart(chart_data.set_index('Fruta'))
                
                # Botón para limpiar resultados
                if st.button("🗑️ Limpiar y procesar nuevas imágenes"):
                    st.rerun()

# Configuración de la página de Streamlit
st.set_page_config(
    page_title="🍎 Clasificador de Frutas AI",
    page_icon="🍎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado para mejorar la apariencia
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #2e7d32;
        padding: 1rem 0;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #4caf50;
    }
    .error-message {
        background-color: #ffebee;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #f44336;
    }
    .success-message {
        background-color: #e8f5e9;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #4caf50;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar con información
with st.sidebar:
    st.markdown("## 🔧 Información del Sistema")
    st.info("**Modelo:** MobileNetV2 + Transfer Learning")
    st.info("**Clases:** 15 tipos de frutas")
    st.info("**Resolución:** 224x224 píxeles")
    
    st.markdown("## 📊 Características")
    st.markdown("""
    - ✅ Procesamiento individual
    - ✅ Procesamiento en lote (hasta 10 imágenes)
    - ✅ Predicción con confianza
    - ✅ Precios referenciales en soles
    - ✅ Análisis estadístico
    - ✅ Visualización de resultados
    """)
    
    st.markdown("## 🎯 Tipos de Fruta Soportados")
    st.markdown("""
    🍎 Manzana | 🍌 Banana | 🫑 Bell Pepper
    🌶️ Chilli Pepper | 🍇 Uvas | 🌶️ Jalapeño  
    🥝 Kiwi | 🍋 Limón | 🥭 Mango
    🍊 Naranja | 🫑 Paprika | 🍐 Pera
    🍍 Piña | 🍎 Granada | 🍉 Sandía
    """)

# Ejecutar la aplicación principal
if __name__ == "__main__":
    run()
