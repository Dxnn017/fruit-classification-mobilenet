# 🚀 GUÍA DE DESPLIEGUE - ARQUITECTURA KAFKA + SPARK + SPACES

## 📋 ARQUITECTURA IMPLEMENTADA

```
Streamlit (Local/Frontend)
    ↓ Upload
Digital Ocean Spaces (S3)
    ↓ URL
Apache Kafka (165.245.129.149:9092)
    ↓ Stream
Apache Spark (165.245.129.150:7077)
    ↓ Predictions
PostgreSQL (165.245.129.150:5432)
    ↓ Query Results
Streamlit (Mostrar resultados)
```

---

## 🔧 PASO 1: CONFIGURAR POSTGRESQL EN DROPLET SPARK

### 1.1 Instalar PostgreSQL
```bash
ssh root@165.245.129.150

sudo apt update
sudo apt install postgresql postgresql-contrib -y
```

### 1.2 Configurar PostgreSQL
```bash
sudo -u postgres psql

-- Crear base de datos y usuario
CREATE DATABASE fruit_predictions;
CREATE USER postgres WITH PASSWORD 'admin123';
GRANT ALL PRIVILEGES ON DATABASE fruit_predictions TO postgres;

-- Conectar a la base de datos
\c fruit_predictions

-- Crear tabla de predicciones
CREATE TABLE predictions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100),
    filename VARCHAR(255),
    image_url TEXT,
    fruit VARCHAR(50),
    confidence FLOAT,
    received_at TIMESTAMP,
    processed_at TIMESTAMP DEFAULT NOW()
);

-- Crear índices
CREATE INDEX idx_session ON predictions(session_id);
CREATE INDEX idx_processed ON predictions(processed_at);

-- Salir
\q
```

### 1.3 Permitir conexiones remotas
```bash
# Editar postgresql.conf
sudo nano /etc/postgresql/14/main/postgresql.conf

# Cambiar:
listen_addresses = '*'

# Editar pg_hba.conf
sudo nano /etc/postgresql/14/main/pg_hba.conf

# Agregar al final:
host    all             all             0.0.0.0/0               md5

# Reiniciar PostgreSQL
sudo systemctl restart postgresql
```

---

## 🔧 PASO 2: SUBIR MODELO Y SCRIPT A DROPLET SPARK

### 2.1 Copiar archivos necesarios
```powershell
# Desde tu PC local (PowerShell)
cd "c:\Users\Daniela\Downloads\Fruit_Vegetable_Recognition-master\Fruit_Vegetable_Recognition-master"

# Copiar modelo y script al droplet
scp FV_Fruits_Only.h5 root@165.245.129.150:/home/ubuntu/
scp procesar_frutas.py root@165.245.129.150:/home/ubuntu/
```

### 2.2 Instalar dependencias en Droplet Spark
```bash
ssh root@165.245.129.150

# Instalar Python y dependencias
sudo apt install python3-pip -y

pip3 install tensorflow keras requests psycopg2-binary numpy pillow pyspark kafka-python

# Verificar instalación
python3 -c "import tensorflow as tf; print(tf.__version__)"
python3 -c "import psycopg2; print('PostgreSQL OK')"
```

---

## 🔧 PASO 3: EJECUTAR SPARK STREAMING

### 3.1 Iniciar el consumer de Spark (EN UNA TERMINAL DEL DROPLET)
```bash
ssh root@165.245.129.150

cd /home/ubuntu

# Ejecutar con spark-submit
spark-submit \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1 \
  --master spark://165.245.129.150:7077 \
  --executor-memory 4g \
  --driver-memory 2g \
  procesar_frutas.py
```

**IMPORTANTE**: Este comando debe estar **corriendo continuamente** para procesar las imágenes.

---

## 🔧 PASO 4: INSTALAR DEPENDENCIAS EN PC LOCAL

### 4.1 Instalar librerías de Python
```powershell
cd "c:\Users\Daniela\Downloads\Fruit_Vegetable_Recognition-master\Fruit_Vegetable_Recognition-master"

# Activar entorno virtual
.\fruit_detection_env\Scripts\Activate.ps1

# Instalar dependencias adicionales
pip install boto3 kafka-python psycopg2-binary
```

### 4.2 Actualizar requirements.txt
```powershell
pip freeze > requirements.txt
```

---

## 🚀 PASO 5: EJECUTAR STREAMLIT

### 5.1 Iniciar aplicación (EN OTRA TERMINAL LOCAL)
```powershell
cd "c:\Users\Daniela\Downloads\Fruit_Vegetable_Recognition-master\Fruit_Vegetable_Recognition-master"

.\fruit_detection_env\Scripts\Activate.ps1

streamlit run App.py --server.maxUploadSize=200
```

### 5.2 Probar el sistema
1. Abre el navegador en `http://localhost:8501`
2. Ve a la pestaña **"📚 Múltiples Imágenes"**
3. Verifica el estado del cluster en el sidebar:
   - ✅ Frontend: Online
   - ✅ Storage: frutas-bigdata-2025
   - ✅ Kafka: 165.245.129.149
4. Sube imágenes y haz clic en **"🚀 Procesar Imagen"**

---

## 🔍 VERIFICAR QUE TODO FUNCIONE

### Verificar Kafka
```bash
ssh root@165.245.129.149

# Ver topics
kafka-topics.sh --list --bootstrap-server localhost:9092

# Consumir mensajes (para debug)
kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic fruit-images \
  --from-beginning
```

### Verificar PostgreSQL
```bash
ssh root@165.245.129.150

sudo -u postgres psql -d fruit_predictions

-- Ver predicciones
SELECT * FROM predictions ORDER BY processed_at DESC LIMIT 10;

-- Ver estadísticas por sesión
SELECT session_id, COUNT(*) as total, AVG(confidence) as avg_conf
FROM predictions
GROUP BY session_id
ORDER BY processed_at DESC;
```

### Verificar Spaces
- Ve a https://cloud.digitalocean.com/spaces
- Abre `frutas-bigdata-2025`
- Deberías ver carpetas `uploads/YYYYMMDD/session-id/`

---

## 📊 FLUJO COMPLETO DE PROCESAMIENTO

### MODO 1 y 2: Procesamiento LOCAL (Subir Imagen / Cámara)
```
Usuario → Streamlit → TensorFlow (Local) → Resultado inmediato
```

### MODO 3: Procesamiento DISTRIBUIDO (Lote Múltiple)
```
1. Usuario sube imágenes en Streamlit
2. Streamlit → Digital Ocean Spaces (upload_to_spaces)
3. Streamlit → Kafka Producer (send_to_kafka)
4. Kafka → Spark Consumer (procesar_frutas.py)
5. Spark → Descarga de Spaces
6. Spark → Predicción con MobileNetV2
7. Spark → PostgreSQL (write_to_postgres)
8. Streamlit → PostgreSQL (query_results_from_postgres)
9. Streamlit → Muestra resultados al usuario
```

---

## 🛠️ TROUBLESHOOTING

### Error: "No se puede conectar a Kafka"
```bash
# Verificar que Kafka esté corriendo
ssh root@165.245.129.149
systemctl status kafka

# Reiniciar si es necesario
sudo systemctl restart kafka
```

### Error: "Access Denied en Spaces"
- Verifica que las credenciales en `App.py` sean correctas
- Ve a Digital Ocean → API → Spaces Keys
- Regenera las keys si es necesario

### Error: "Tiempo de espera agotado"
- Verifica que `procesar_frutas.py` esté ejecutándose en Spark
- Revisa los logs de Spark:
```bash
ssh root@165.245.129.150
tail -f /opt/spark/logs/*.out
```

### Error: "PostgreSQL connection refused"
- Verifica que PostgreSQL esté escuchando en todas las interfaces
- Prueba conexión remota:
```powershell
psql -h 165.245.129.150 -U postgres -d fruit_predictions
```

---

## 📈 MÉTRICAS Y MONITOREO

### Ver logs de Spark en tiempo real
```bash
ssh root@165.245.129.150
tail -f /tmp/spark-checkpoint-fruits/offsets/0
```

### Ver métricas de Kafka
```bash
ssh root@165.245.129.149
kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 \
  --group spark-kafka-consumer \
  --describe
```

---

## ✅ CHECKLIST FINAL

Antes de presentar tu proyecto, verifica:

- [ ] PostgreSQL corriendo y accesible
- [ ] Kafka corriendo en droplet kafka
- [ ] Spark Master corriendo en droplet spark
- [ ] `procesar_frutas.py` ejecutándose con spark-submit
- [ ] Modelo `FV_Fruits_Only.h5` en `/home/ubuntu/`
- [ ] Credenciales de Spaces correctas en `App.py`
- [ ] Streamlit ejecutándose en tu PC
- [ ] Puedes procesar imágenes en Modo 1, 2 y 3
- [ ] Los resultados se guardan en PostgreSQL
- [ ] El sidebar muestra el estado correcto

---

## 🎓 DOCUMENTACIÓN PARA REPORTE

### Tecnologías utilizadas:
- **Frontend**: Streamlit 1.28+
- **ML Framework**: TensorFlow 2.16+, Keras, MobileNetV2
- **Message Queue**: Apache Kafka 3.5.0
- **Stream Processing**: Apache Spark 3.4.1 (PySpark)
- **Object Storage**: Digital Ocean Spaces (S3-compatible)
- **Database**: PostgreSQL 15
- **Cloud Provider**: Digital Ocean (2 Droplets)

### IPs de infraestructura:
- **Kafka Broker**: 165.245.129.149:9092
- **Spark Master**: 165.245.129.150:7077
- **PostgreSQL**: 165.245.129.150:5432
- **Spaces Endpoint**: https://atl1.digitaloceanspaces.com
- **Bucket**: frutas-bigdata-2025

---

## 📞 CONTACTO Y SOPORTE

Si tienes problemas, revisa:
1. Los logs de cada servicio
2. La conectividad de red entre droplets
3. Los puertos abiertos en firewall
4. Las credenciales y configuraciones

¡Éxito con tu proyecto! 🚀🍎
