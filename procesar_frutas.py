#!/usr/bin/env python3
"""
Script de Spark Streaming para procesar imágenes de frutas desde Kafka
Debe ejecutarse en el Droplet Spark: 165.245.129.150

Uso:
    spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1 procesar_frutas.py
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, udf, current_timestamp
from pyspark.sql.types import StructType, StructField, StringType, DoubleType
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras.preprocessing.image import load_img, img_to_array
import requests
from io import BytesIO
import psycopg2
import json
import sys

# ============================================================
# CONFIGURACIÓN
# ============================================================

# Configuración Kafka
KAFKA_BROKER = "165.245.129.149:9092"
KAFKA_TOPIC = "fruit-images"

# Configuración PostgreSQL
PG_HOST = "165.245.129.150"  # Localhost si está en el mismo droplet
PG_PORT = 5432
PG_DATABASE = "fruit_predictions"
PG_USER = "postgres"
PG_PASSWORD = "admin123"

# Labels del modelo
LABELS = {
    0: 'apple', 1: 'banana', 2: 'bell pepper', 3: 'chilli pepper', 
    4: 'grapes', 5: 'jalepeno', 6: 'kiwi', 7: 'lemon', 
    8: 'mango', 9: 'orange', 10: 'paprika', 11: 'pear', 
    12: 'pineapple', 13: 'pomegranate', 14: 'watermelon'
}

# ============================================================
# CARGAR MODELO TENSORFLOW/KERAS
# ============================================================

print("🔄 Cargando modelo MobileNetV2...")
try:
    # Asegúrate de que esta ruta sea correcta en tu Droplet Spark
    MODEL_PATH = "/home/ubuntu/FV_Fruits_Only.h5"  # Ajustar según tu instalación
    model = keras.models.load_model(MODEL_PATH)
    print("✅ Modelo cargado exitosamente")
except Exception as e:
    print(f"❌ Error cargando modelo: {e}")
    sys.exit(1)

# ============================================================
# FUNCIÓN DE PREDICCIÓN
# ============================================================

def predict_fruit_from_url(image_url):
    """
    Descarga imagen desde URL (Spaces) y predice la fruta usando MobileNetV2
    
    Args:
        image_url (str): URL de la imagen en Digital Ocean Spaces
    
    Returns:
        str: JSON string con formato "fruta|confianza"
    """
    try:
        # Descargar imagen desde Spaces
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
        
        # Cargar y preprocesar imagen
        img = load_img(BytesIO(response.content), target_size=(224, 224, 3))
        img_array = img_to_array(img) / 255.0
        img_array = np.expand_dims(img_array, axis=0)
        
        # Predicción
        prediction = model.predict(img_array, verbose=0)
        class_id = prediction.argmax(axis=-1)[0]
        confidence = float(prediction[0][class_id])
        
        # Retornar resultado en formato delimitado
        fruit_name = LABELS[class_id]
        return f"{fruit_name}|{confidence:.6f}"
    
    except requests.exceptions.RequestException as e:
        return f"error|Error descargando imagen: {str(e)}"
    except Exception as e:
        return f"error|Error procesando: {str(e)}"

# ============================================================
# CREAR SESIÓN SPARK
# ============================================================

print("🚀 Iniciando Spark Session...")
spark = SparkSession.builder \
    .appName("FruitClassificationStreaming") \
    .master("spark://165.245.129.150:7077") \
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1") \
    .config("spark.executor.memory", "4g") \
    .config("spark.driver.memory", "2g") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")
print("✅ Spark Session iniciada")

# Registrar UDF para predicción
predict_udf = udf(predict_fruit_from_url, StringType())

# ============================================================
# DEFINIR SCHEMA DE KAFKA
# ============================================================

kafka_schema = StructType([
    StructField("image_url", StringType(), True),
    StructField("session_id", StringType(), True),
    StructField("filename", StringType(), True),
    StructField("timestamp", StringType(), True)
])

# ============================================================
# LEER STREAM DE KAFKA
# ============================================================

print(f"📨 Conectando a Kafka: {KAFKA_BROKER}")
print(f"📚 Suscrito al topic: {KAFKA_TOPIC}")

try:
    df_stream = spark \
        .readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BROKER) \
        .option("subscribe", KAFKA_TOPIC) \
        .option("startingOffsets", "latest") \
        .option("failOnDataLoss", "false") \
        .load()
    
    print("✅ Stream de Kafka configurado")
    
except Exception as e:
    print(f"❌ Error conectando a Kafka: {e}")
    sys.exit(1)

# ============================================================
# PROCESAR MENSAJES
# ============================================================

# Parsear JSON de Kafka
df_parsed = df_stream \
    .select(from_json(col("value").cast("string"), kafka_schema).alias("data")) \
    .select("data.*")

# Aplicar predicción con UDF
df_predictions = df_parsed \
    .withColumn("prediction_raw", predict_udf(col("image_url"))) \
    .selectExpr(
        "session_id",
        "filename",
        "image_url",
        "timestamp as received_at",
        "split(prediction_raw, '\\\\|')[0] as fruit",
        "cast(split(prediction_raw, '\\\\|')[1] as double) as confidence"
    )

# ============================================================
# ESCRIBIR A POSTGRESQL
# ============================================================

def write_to_postgres(batch_df, batch_id):
    """
    Escribe cada batch de resultados en PostgreSQL
    
    Args:
        batch_df: DataFrame de Spark con las predicciones
        batch_id: ID del batch
    """
    try:
        # Conectar a PostgreSQL
        conn = psycopg2.connect(
            host=PG_HOST,
            port=PG_PORT,
            database=PG_DATABASE,
            user=PG_USER,
            password=PG_PASSWORD
        )
        cur = conn.cursor()
        
        # Crear tabla si no existe
        cur.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id SERIAL PRIMARY KEY,
                session_id VARCHAR(100),
                filename VARCHAR(255),
                image_url TEXT,
                fruit VARCHAR(50),
                confidence FLOAT,
                received_at TIMESTAMP,
                processed_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # Crear índices si no existen
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_session 
            ON predictions(session_id)
        """)
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_processed 
            ON predictions(processed_at)
        """)
        
        conn.commit()
        
        # Insertar predicciones
        rows = batch_df.collect()
        inserted_count = 0
        
        for row in rows:
            # Validar que no sea un error
            if row.fruit != "error":
                cur.execute("""
                    INSERT INTO predictions 
                    (session_id, filename, image_url, fruit, confidence, received_at)
                    VALUES (%s, %s, %s, %s, %s, NOW())
                """, (
                    row.session_id, 
                    row.filename, 
                    row.image_url, 
                    row.fruit, 
                    row.confidence
                ))
                inserted_count += 1
            else:
                print(f"⚠️ Error procesando {row.filename}: {row.confidence}")
        
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"✅ Batch {batch_id}: {inserted_count} predicciones guardadas en PostgreSQL")
        
    except Exception as e:
        print(f"❌ Error escribiendo a PostgreSQL (batch {batch_id}): {e}")

# ============================================================
# INICIAR STREAMING
# ============================================================

print("\n" + "="*60)
print("🚀 SPARK STREAMING INICIADO - Esperando mensajes de Kafka...")
print("="*60 + "\n")

try:
    query = df_predictions \
        .writeStream \
        .foreachBatch(write_to_postgres) \
        .outputMode("append") \
        .option("checkpointLocation", "/tmp/spark-checkpoint-fruits") \
        .start()
    
    print("✅ Query de streaming iniciada")
    print("📊 Procesando imágenes de frutas desde Kafka...")
    print("🔄 Presiona Ctrl+C para detener\n")
    
    query.awaitTermination()
    
except KeyboardInterrupt:
    print("\n⚠️ Deteniendo Spark Streaming...")
    spark.stop()
    print("✅ Spark Session cerrada")
    
except Exception as e:
    print(f"\n❌ Error en streaming: {e}")
    spark.stop()
    sys.exit(1)
