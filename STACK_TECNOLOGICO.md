# 🔧 STACK TECNOLÓGICO COMPLETO DEL PROYECTO
# Análisis detallado de herramientas y tecnologías utilizadas

## 💻 LENGUAJES DE PROGRAMACIÓN Y ENTORNO

### **Lenguaje Principal:**
- **Python 3.13** - Lenguaje base del proyecto

### **Entornos de Desarrollo:**
- **Jupyter Notebook** - Para experimentación y entrenamiento
- **VS Code** - Editor principal con extensiones de Python
- **PowerShell** - Terminal en Windows
- **Entorno Virtual** - `fruit_detection_env` (venv)

### **Frameworks de Interfaz:**
- **Streamlit 1.28+** - Aplicación web interactiva
- **Flask 3.0+** - API REST (ec2_api.py)
- **OpenCV 4.12** - Detección en tiempo real con webcam

---

## 🎨 PROCESAMIENTO Y AUMENTO DE IMÁGENES

### **Librerías de Procesamiento:**
- **tf_keras.preprocessing.image.ImageDataGenerator**
  ```python
  # Data Augmentation aplicado:
  rotation_range=30,          # Rotación ±30°
  zoom_range=0.15,           # Zoom ±15%
  width_shift_range=0.2,     # Desplazamiento horizontal ±20%
  height_shift_range=0.2,    # Desplazamiento vertical ±20%
  shear_range=0.15,          # Inclinación ±15%
  horizontal_flip=True,      # Volteo horizontal
  fill_mode="nearest"        # Relleno de píxeles
  ```

- **Pillow (PIL) 10.0+** - Manipulación básica de imágenes
- **OpenCV (cv2) 4.12** - Procesamiento de video/webcam
- **NumPy 1.24+** - Operaciones matriciales

### **Preprocesamiento Específico:**
- **MobileNetV2.preprocess_input** - Normalización [-1, 1]
- **Redimensionamiento** - 224×224 píxeles uniformes
- **Conversión RGB** - Formato estándar de color

### **Alternativa Avanzada (Implementada):**
- **Albumentations** - Data augmentation más sofisticado
  ```python
  # Transformaciones implementadas:
  A.HorizontalFlip(p=0.5)
  A.Rotate(limit=15, p=0.7)
  A.RandomBrightnessContrast()
  A.HueSaturationValue()
  A.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD)
  ```

---

## 🧠 MODELOS PREENTRENADOS Y ARQUITECTURAS BASE

### **Arquitectura Principal:**
- **MobileNetV2** - Modelo base de Google
  - **Parámetros:** 3,538,984 parámetros pre-entrenados
  - **Pesos:** ImageNet (14+ millones de imágenes)
  - **Optimización:** Diseñado para dispositivos móviles
  - **Técnica:** Inverted Residual Blocks + Depthwise Convolutions

### **Transfer Learning:**
```python
# Configuración utilizada:
pretrained_model = keras.applications.MobileNetV2(
    input_shape=(224, 224, 3),
    include_top=False,           # Sin clasificador original
    weights='imagenet',          # Pesos pre-entrenados
    pooling='avg'               # Global Average Pooling
)
pretrained_model.trainable = False  # Congelar pesos base
```

### **Capas Personalizadas:**
```python
# Arquitectura final:
inputs = pretrained_model.input
x = keras.layers.Dense(128, activation='relu')(pretrained_model.output)
x = keras.layers.Dense(128, activation='relu')(x)
outputs = keras.layers.Dense(15, activation='softmax')(x)  # 15 frutas
```

### **Framework Deep Learning:**
- **TensorFlow 2.15+** - Backend de computación
- **tf_keras** - API de alto nivel
- **Keras Applications** - Modelos pre-entrenados

---

## 📊 MANEJO Y EVALUACIÓN DE DATOS

### **Manipulación de Datos:**
- **Pandas** - DataFrames para organización de datasets
  ```python
  # Estructura de datos:
  train_df, val_df, test_df = pd.DataFrame({
      'Filepath': rutas_imagenes,
      'Label': etiquetas_frutas
  })
  ```

- **Pathlib** - Gestión moderna de rutas de archivos
- **NumPy** - Operaciones matemáticas y matriciales

### **Métricas de Evaluación:**
- **Scikit-learn** - Métricas de clasificación
  ```python
  # Métricas implementadas:
  from sklearn.metrics import:
    - accuracy_score()          # Precisión general
    - classification_report()   # Precision, Recall, F1-Score
    - confusion_matrix()        # Matriz de confusión
  ```

### **División del Dataset:**
- **Training:** 1,135 imágenes (80.5%)
- **Validation:** 137 imágenes (9.7%)
- **Test:** 137 imágenes (9.7%)
- **Total:** 1,409 imágenes de 15 frutas

### **Formato de Datos:**
- **Imágenes:** JPG/JPEG/PNG
- **Resolución:** 224×224×3 (RGB)
- **Normalización:** [-1, 1] (MobileNetV2 estándar)
- **Batches:** 32 imágenes por lote

---

## 📈 VISUALIZACIÓN Y ANÁLISIS DE RESULTADOS

### **Librerías de Visualización:**
- **Matplotlib** - Gráficos base y personalizados
  ```python
  # Gráficos implementados:
  - Training/Validation accuracy curves
  - Training/Validation loss curves
  - Confusion matrix heatmaps
  - Filter visualizations
  ```

- **Seaborn** - Visualizaciones estadísticas elegantes
  ```python
  # Usado para:
  - sns.heatmap(confusion_matrix)  # Matriz de confusión
  - Paletas de colores profesionales
  ```

### **Métricas Mostradas:**
```python
# Resultados del modelo:
Training Accuracy:   99.82%
Validation Accuracy: 97.08%
Test Accuracy:       95.0%+ (estimado)

# Arquitectura:
Total params:        3,538,984
Trainable params:    ~500 (capas finales)
Non-trainable:       3,538,484 (MobileNetV2)
```

### **Análisis Avanzado:**
- **Activaciones de capas** - Visualización de filtros
- **Feature maps** - Mapas de características
- **Gradient visualization** - Análisis de gradientes

### **Reportes Generados:**
- **JSON metadata** - Configuración del modelo
- **Training history** - Historial de entrenamiento
- **Classification report** - Métricas por clase
- **Confusion matrix** - Errores de clasificación

### **Interfaz Visual:**
- **Streamlit Dashboard** - Métricas en tiempo real
- **Progress bars** - Progreso de entrenamiento
- **Interactive plots** - Gráficos interactivos
- **Image preview** - Previsualización de predicciones

---

## 🚀 DEPLOYMENT Y PRODUCCIÓN

### **Aplicaciones:**
- **Streamlit App** - Interfaz web completa
- **OpenCV App** - Detección en tiempo real
- **Flask API** - Servicio REST

### **Optimizaciones:**
- **Model caching** - Cache del modelo cargado
- **Batch processing** - Procesamiento por lotes
- **Real-time inference** - Inferencia en tiempo real

---

## 📦 DEPENDENCIES SUMMARY

```txt
# Core ML & DL
tensorflow>=2.15.0
tf-keras>=2.20.0
numpy>=1.24.0

# Image Processing
opencv-python>=4.12.0
Pillow>=10.0.0
albumentations>=1.3.0

# Data Science
pandas>=1.5.0
scikit-learn>=1.3.0

# Visualization
matplotlib>=3.6.0
seaborn>=0.12.0

# Web Interface
streamlit>=1.28.0
flask>=3.0.0

# Utilities
requests>=2.31.0
beautifulsoup4>=4.12.0
```