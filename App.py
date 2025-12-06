import streamlit as st
from PIL import Image
import numpy as np
import tf_keras as keras
from tf_keras.preprocessing.image import load_img, img_to_array
import os
import time
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
import boto3
from botocore.client import Config
from kafka import KafkaProducer
import json
import uuid
from datetime import datetime
import psycopg2
from io import BytesIO

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

# ============================================================
# CONFIGURACIÓN DIGITAL OCEAN SPACES + KAFKA
# ============================================================
REGION = "atl1"
DO_SPACE_ENDPOINT = f"https://{REGION}.digitaloceanspaces.com"
DO_SPACE_NAME = "frutas-bigdata-2025"
DO_ACCESS_KEY = "DO801BXNYAPL87NEY9FV"
DO_SECRET_KEY = "pEBwYd8LYWGTUnYoACAoQypdd0ttp4B27G2R2zhxATA"

# Configuración Kafka
KAFKA_BROKER = "165.245.129.149:9092"
KAFKA_TOPIC = "fruit-images"

# Configuración PostgreSQL
PG_HOST = "165.245.129.150"
PG_PORT = 5432
PG_DATABASE = "fruit_predictions"
PG_USER = "postgres"
PG_PASSWORD = "admin123"

# Cliente S3 para Digital Ocean Spaces
try:
    s3_client = boto3.client(
        's3',
        region_name=REGION,
        endpoint_url=DO_SPACE_ENDPOINT,
        aws_access_key_id=DO_ACCESS_KEY,
        aws_secret_access_key=DO_SECRET_KEY,
        config=Config(signature_version='s3v4')
    )
    spaces_available = True
except Exception as e:
    spaces_available = False
    st.sidebar.error(f"⚠️ Error conectando a Spaces: {str(e)}")

# Productor Kafka
try:
    kafka_producer = KafkaProducer(
        bootstrap_servers=[KAFKA_BROKER],
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        api_version=(0, 10, 1),
        request_timeout_ms=30000,
        max_block_ms=60000
    )
    kafka_available = True
except Exception as e:
    kafka_available = False
    st.sidebar.error(f"⚠️ Error conectando a Kafka: {str(e)}")

# Obtener el directorio del script
script_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(script_dir, 'FV_Fruits_Only.h5')

# Cargar modelo entrenado solo con frutas (para modos 1 y 2)
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

def process_image(pil_image):
    """Procesa una imagen PIL directamente (para cámara y uploads)"""
    # Convertir PIL a array y redimensionar
    img = pil_image.resize((224, 224))
    img = img_to_array(img)
    img = img / 255.0
    img = np.expand_dims(img, axis=0)
    
    # Predicción
    answer = model.predict(img, verbose=0)
    y_class = answer.argmax(axis=-1)
    y = int(y_class[0])
    res = labels[y]
    
    return res.capitalize()

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


def process_image(img_pil):
    """Procesa una imagen PIL y retorna la predicción"""
    # Crear directorio upload_images si no existe
    upload_dir = os.path.join(script_dir, 'upload_images')
    os.makedirs(upload_dir, exist_ok=True)
    
    # Guardar imagen temporalmente
    temp_path = os.path.join(upload_dir, 'temp_image.jpg')
    img_pil.save(temp_path)
    
    # Procesar y predecir
    result = prepare_image(temp_path)
    return result


# ============================================================
# FUNCIONES PARA KAFKA + SPARK + SPACES
# ============================================================

def upload_to_spaces(image_bytes, filename, session_id):
    """Sube imagen a Digital Ocean Spaces y retorna la URL"""
    try:
        # Generar key único con fecha
        date_folder = datetime.now().strftime('%Y%m%d')
        image_key = f"uploads/{date_folder}/{session_id}/{filename}"
        
        # Subir a Spaces
        s3_client.put_object(
            Bucket=DO_SPACE_NAME,
            Key=image_key,
            Body=image_bytes,
            ACL='private',
            ContentType='image/jpeg'
        )
        
        # Retornar URL completa
        image_url = f"{DO_SPACE_ENDPOINT}/{DO_SPACE_NAME}/{image_key}"
        return image_url
    except Exception as e:
        raise Exception(f"Error subiendo a Spaces: {str(e)}")


def send_to_kafka(image_url, session_id, filename):
    """Envía mensaje a Kafka con la URL de la imagen"""
    try:
        message = {
            'image_url': image_url,
            'session_id': session_id,
            'filename': filename,
            'timestamp': datetime.now().isoformat()
        }
        
        future = kafka_producer.send(KAFKA_TOPIC, value=message)
        kafka_producer.flush()
        
        result = future.get(timeout=10)
        return True
    except Exception as e:
        raise Exception(f"Error enviando a Kafka: {str(e)}")


def query_results_from_postgres(session_id, max_wait_seconds=60):
    """Consulta resultados de PostgreSQL para una sesión específica"""
    try:
        conn = psycopg2.connect(
            host=PG_HOST,
            port=PG_PORT,
            database=PG_DATABASE,
            user=PG_USER,
            password=PG_PASSWORD
        )
        cur = conn.cursor()
        
        # Esperar hasta que todos los resultados estén listos
        start_time = time.time()
        results = []
        
        while time.time() - start_time < max_wait_seconds:
            cur.execute("""
                SELECT filename, fruit, confidence, processed_at, image_url
                FROM predictions
                WHERE session_id = %s
                ORDER BY processed_at
            """, (session_id,))
            
            results = cur.fetchall()
            
            if len(results) > 0:
                break
            
            time.sleep(2)  # Esperar 2 segundos antes de volver a consultar
        
        cur.close()
        conn.close()
        
        # Convertir a formato dict
        formatted_results = []
        for row in results:
            formatted_results.append({
                'filename': row[0],
                'prediction': row[1],
                'confidence': float(row[2]),
                'processed_at': row[3],
                'image_url': row[4],
                'price': get_precio(row[1])
            })
        
        return formatted_results
    except Exception as e:
        raise Exception(f"Error consultando PostgreSQL: {str(e)}")


def run():
    st.title("🍎 Clasificación de Frutas")
    st.markdown("### Identifica frutas mediante imagen, cámara o procesamiento múltiple con Kafka + Spark")
    
    # Mostrar lista de frutas disponibles
    with st.expander("📋 Ver lista de frutas que puedo identificar"):
        cols = st.columns(3)
        for idx, fruit in enumerate(fruits):
            cols[idx % 3].write(f"• {fruit}")
 
    # Crear pestañas para los diferentes modos
    tab1, tab2, tab3 = st.tabs(["📁 Subir Imagen", "📷 Capturar con Cámara", "📚 Lote (Múltiple)"])
    
    # ========== PESTAÑA 1: SUBIR IMAGEN ==========
    with tab1:
        st.markdown("#### Selecciona una imagen desde tu dispositivo")
        img_file = st.file_uploader("Selecciona una imagen", type=["jpg", "png", "jpeg"], key="file_uploader")
        
        if img_file is not None:
            # Crear columnas para mejor diseño
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 📸 Imagen Original")
                img = Image.open(img_file).resize((250, 250))
                st.image(img, use_container_width=True)
            
            with col2:
                st.markdown("#### 🔍 Resultados")
                
                with st.spinner('Analizando fruta...'):
                    result = process_image(Image.open(img_file))
                    
                # Mostrar predicción
                st.success(f"🍎 **Identificado como: {result}**")
                
                # Mostrar precio
                precio = get_precio(result)
                st.info(f'💰 **Precio aproximado: {precio}** por kilogramo')
                st.caption('💡 Precios referenciales del mercado peruano')
                
                # Botón para cargar otra imagen
                if st.button("🔄 Cargar otra imagen", key="reload_upload"):
                    st.rerun()
    
    # ========== PESTAÑA 2: CÁMARA ==========
    with tab2:
        st.markdown("#### Captura una imagen usando tu cámara web")
        st.caption("💡 La detección se realizará automáticamente al capturar la foto")
        
        # Inicializar estado de sesión para controlar capturas
        if 'camera_key' not in st.session_state:
            st.session_state.camera_key = 0
        
        camera_photo = st.camera_input(
            "📷 Toma una foto de la fruta", 
            key=f"camera_{st.session_state.camera_key}"
        )
        
        if camera_photo is not None:
            # Crear columnas para mejor diseño
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 📸 Imagen Capturada")
                img = Image.open(camera_photo).resize((250, 250))
                st.image(img, use_container_width=True)
            
            with col2:
                st.markdown("#### 🔍 Resultados")
                
                with st.spinner('🔍 Analizando fruta...'):
                    result = process_image(Image.open(camera_photo))
                    
                # Mostrar predicción
                st.success(f"🍎 **Identificado como: {result}**")
                
                # Mostrar precio
                precio = get_precio(result)
                st.info(f'💰 **Precio aproximado: {precio}** por kilogramo')
                st.caption('💡 Precios referenciales del mercado peruano')
            
            # Botón para tomar otra foto
            st.markdown("---")
            if st.button("📷 Tomar otra foto", key="retake_photo", type="primary"):
                st.session_state.camera_key += 1
                st.rerun()
    
    # ========== PESTAÑA 3: LOTE (MÚLTIPLE) - KAFKA + SPARK ==========
    with tab3:
        st.markdown("### 🚀 Procesamiento Distribuido con Kafka + Spark")
        
        # Mostrar estado del cluster en sidebar
        with st.sidebar:
            st.markdown("### 🔧 Estado del Cluster")
            if spaces_available:
                st.success("✅ **Frontend**: Online")
            else:
                st.error("❌ **Frontend**: Offline")
            
            st.info(f"📦 **Storage**: {DO_SPACE_NAME}")
            
            if kafka_available:
                st.info(f"📨 **Kafka**: {KAFKA_BROKER.split(':')[0]}")
            else:
                st.error(f"❌ **Kafka**: Error de conexión")
            
            if spaces_available and kafka_available:
                st.success("💡 **Asegúrate que 'procesar_frutas.py' esté corriendo en la otra terminal.**")
            else:
                st.error("⚠️ Kafka o Spaces no disponible")
        
        st.info("📝 **Arquitectura**: Spaces (S3) → Kafka → Spark Streaming → PostgreSQL")
        st.caption("💡 Las imágenes se suben a Digital Ocean Spaces, se envían a Kafka y Spark las procesa de forma distribuida")
        
        # Verificar disponibilidad de servicios
        if not spaces_available or not kafka_available:
            st.error("❌ **Error**: No se puede conectar a Kafka o Spaces. Verifica que los servicios estén activos.")
            st.markdown("""
            **Servicios requeridos:**
            - ✅ Digital Ocean Spaces configurado
            - ✅ Kafka corriendo en `165.245.129.149:9092`
            - ✅ Spark Streaming ejecutando `procesar_frutas.py`
            - ✅ PostgreSQL en `165.245.129.150:5432`
            """)
            return
        
        # Subir múltiples archivos
        uploaded_files = st.file_uploader(
            "Selecciona múltiples imágenes (máx. 10)", 
            type=["jpg", "png", "jpeg"], 
            accept_multiple_files=True,
            key="multiple",
            help="Limit 200MB per file • JPG, PNG, JPEG"
        )
        
        if uploaded_files:
            # Validar límite de archivos
            if len(uploaded_files) > 10:
                st.error("❌ Por favor, sube máximo 10 imágenes a la vez")
                return
            
            st.success(f"✅ {len(uploaded_files)} imágenes cargadas correctamente")
            
            # Mostrar preview de imágenes
            with st.expander("🖼️ Vista previa de imágenes", expanded=False):
                cols = st.columns(min(len(uploaded_files), 5))
                for i, uploaded_file in enumerate(uploaded_files[:5]):
                    with cols[i]:
                        img = Image.open(uploaded_file)
                        st.image(img, caption=uploaded_file.name, use_container_width=True)
                if len(uploaded_files) > 5:
                    st.caption(f"... y {len(uploaded_files) - 5} imágenes más")
            
            # Botón para procesar
            if st.button("🚀 Procesar Imagen", type="primary", key="process_batch"):
                # Generar ID de sesión único
                session_id = str(uuid.uuid4())
                
                # Progress bar
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                start_time = time.time()
                
                try:
                    # PASO 1: Subir imágenes a Spaces
                    status_text.text("📤 Subiendo imágenes a Digital Ocean Spaces...")
                    progress_bar.progress(20)
                    
                    uploaded_urls = []
                    for i, uploaded_file in enumerate(uploaded_files):
                        try:
                            # Leer bytes de la imagen
                            image_bytes = uploaded_file.getvalue()
                            
                            # Subir a Spaces
                            image_url = upload_to_spaces(image_bytes, uploaded_file.name, session_id)
                            uploaded_urls.append((uploaded_file.name, image_url))
                            
                            st.caption(f"✅ Subido: {uploaded_file.name}")
                        except Exception as e:
                            st.error(f"❌ Error subiendo {uploaded_file.name}: {str(e)}")
                    
                    if not uploaded_urls:
                        st.error("❌ No se pudieron subir las imágenes a Spaces")
                        return
                    
                    progress_bar.progress(40)
                    
                    # PASO 2: Enviar mensajes a Kafka
                    status_text.text("📨 Enviando mensajes a Kafka...")
                    
                    for filename, image_url in uploaded_urls:
                        try:
                            send_to_kafka(image_url, session_id, filename)
                            st.caption(f"✅ Enviado a Kafka: {filename}")
                        except Exception as e:
                            st.error(f"❌ Error enviando a Kafka {filename}: {str(e)}")
                    
                    progress_bar.progress(60)
                    
                    # PASO 3: Esperar resultados de Spark/PostgreSQL
                    status_text.text("⏳ Esperando procesamiento de Spark...")
                    st.warning("💡 **Spark está procesando las imágenes**. Esto puede tomar unos segundos...")
                    
                    progress_bar.progress(80)
                    
                    # Consultar resultados
                    results = query_results_from_postgres(session_id, max_wait_seconds=60)
                    
                    progress_bar.progress(100)
                    end_time = time.time()
                    processing_time = end_time - start_time
                    
                    if not results:
                        st.error("❌ **Tiempo de espera agotado o error en el cluster**. Verifica que Spark esté procesando correctamente.")
                        st.markdown("""
                        **Posibles causas:**
                        - El script `procesar_frutas.py` no está corriendo en Spark
                        - PostgreSQL no está disponible
                        - Kafka no está recibiendo mensajes
                        """)
                        return
                    
                    status_text.text(f"✅ Procesamiento completado en {processing_time:.2f} segundos")
                    
                    # PASO 4: Mostrar resultados
                    st.markdown("## 📊 Resultados del Procesamiento Distribuido")
                    st.success(f"✅ **{len(results)}** imágenes procesadas por Spark en **{processing_time:.2f}s**")
                    
                    # Crear DataFrame para mostrar resultados tabulares
                    df_results = []
                    for result in results:
                        df_results.append({
                            'Imagen': result['filename'],
                            'Fruta Detectada': result['prediction'],
                            'Confianza': f"{result['confidence']:.2%}",
                            'Precio (S/./kg)': result['price'],
                            'Procesado': result['processed_at'].strftime('%H:%M:%S')
                        })
                    
                    df = pd.DataFrame(df_results)
                    st.dataframe(df, use_container_width=True)
                    
                    # Mostrar imágenes con resultados en grid
                    st.markdown("### 🖼️ Vista Detallada de Resultados (desde Spark)")
                    
                    # Crear grid de imágenes
                    cols_per_row = 3
                    for i in range(0, len(results), cols_per_row):
                        cols = st.columns(cols_per_row)
                        
                        for j in range(cols_per_row):
                            idx = i + j
                            if idx < len(results):
                                with cols[j]:
                                    result = results[idx]
                                    
                                    # Buscar la imagen original en uploaded_files
                                    matching_file = next((f for f in uploaded_files if f.name == result['filename']), None)
                                    
                                    if matching_file:
                                        # Mostrar imagen
                                        img = Image.open(matching_file).resize((200, 200))
                                        st.image(img, use_container_width=True)
                                    
                                    # Mostrar resultados
                                    st.markdown(f"**📝 {result['filename']}**")
                                    st.success(f"🍎 {result['prediction']}")
                                    st.info(f"🎯 {result['confidence']:.1%}")
                                    st.caption(f"💰 {result['price']}")
                                    st.caption(f"⏱️ {result['processed_at'].strftime('%H:%M:%S')}")
                    
                    # Resumen estadístico
                    st.markdown("### 📈 Resumen Estadístico del Cluster")
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
                        st.metric("Tiempo Total", f"{processing_time:.2f}s")
                    
                    # Mostrar distribución de frutas detectadas
                    fruit_counts = {}
                    for result in results:
                        fruit = result['prediction']
                        fruit_counts[fruit] = fruit_counts.get(fruit, 0) + 1
                    
                    if len(fruit_counts) > 1:
                        st.markdown("### 📊 Distribución de Frutas Detectadas")
                        chart_data = pd.DataFrame(list(fruit_counts.items()), columns=['Fruta', 'Cantidad'])
                        st.bar_chart(chart_data.set_index('Fruta'))
                    
                    # Información de la sesión
                    st.markdown("---")
                    st.caption(f"🔑 **Session ID**: `{session_id}`")
                    st.caption("💡 Los resultados se almacenaron en PostgreSQL y se procesaron con Apache Spark")
                    
                except Exception as e:
                    st.error(f"❌ **Error durante el procesamiento**: {str(e)}")
                    st.markdown("""
                    **Verifica:**
                    - Kafka está corriendo en `165.245.129.149:9092`
                    - Spark está ejecutando `procesar_frutas.py`
                    - PostgreSQL está disponible en `165.245.129.150:5432`
                    - Digital Ocean Spaces está configurado correctamente
                    """)
                    
                # Mostrar predicción
                st.success(f"🍎 **Identificado como: {result}**")
                
                # Mostrar precio
                precio = get_precio(result)
                st.info(f'💰 **Precio aproximado: {precio}** por kilogramo')
                st.caption('💡 Precios referenciales del mercado peruano')
                
                # Botón para cargar otra imagen
                if st.button("🔄 Cargar otra imagen", key="reload_upload"):
                    st.rerun()
    
    # ========== PESTAÑA 2: CÁMARA ==========
    with tab2:
        st.markdown("#### Captura una imagen usando tu cámara web")
        st.caption("💡 La detección se realizará automáticamente al capturar la foto")
        
        # Inicializar estado de sesión para controlar capturas
        if 'camera_key' not in st.session_state:
            st.session_state.camera_key = 0
        
        camera_photo = st.camera_input(
            "📷 Toma una foto de la fruta", 
            key=f"camera_{st.session_state.camera_key}"
        )
        
        if camera_photo is not None:
            # Crear columnas para mejor diseño
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 📸 Imagen Capturada")
                img = Image.open(camera_photo).resize((250, 250))
                st.image(img, use_container_width=True)
            
            with col2:
                st.markdown("#### 🔍 Resultados")
                
                with st.spinner('🔍 Analizando fruta...'):
                    result = process_image(Image.open(camera_photo))
                    
                # Mostrar predicción
                st.success(f"🍎 **Identificado como: {result}**")
                
                # Mostrar precio
                precio = get_precio(result)
                st.info(f'💰 **Precio aproximado: {precio}** por kilogramo')
                st.caption('💡 Precios referenciales del mercado peruano')
            
            # Botón para tomar otra foto
            st.markdown("---")
            if st.button("📷 Tomar otra foto", key="retake_photo", type="primary"):
                st.session_state.camera_key += 1
                st.rerun()

# Sidebar con información
with st.sidebar:
    st.markdown("## 🔧 Información del Sistema")
    st.info("**Modelo:** MobileNetV2 + Transfer Learning")
    st.info("**Clases:** 15 tipos de frutas")
    st.info("**Resolución:** 224x224 píxeles")
    
    st.markdown("## 📊 Características")
    st.markdown("""
    - ✅ Procesamiento individual (local)
    - ✅ Captura con cámara web (local)
    - ✅ Procesamiento distribuido (Kafka + Spark)
    - ✅ Digital Ocean Spaces (S3)
    - ✅ Apache Kafka streaming
    - ✅ Apache Spark processing
    - ✅ PostgreSQL persistencia
    - ✅ Predicción con confianza
    - ✅ Precios referenciales en soles
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
    