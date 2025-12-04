# 🍎 Clasificación de Frutas con Deep Learning

[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/)
[![TensorFlow](https://img.shields.io/badge/TensorFlow-2.15+-orange.svg)](https://www.tensorflow.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io/)

## 📊 Resultados del Modelo

- **Accuracy en Training**: 99.82%
- **Accuracy en Validation**: 97.08%
- **Arquitectura**: MobileNetV2 + Transfer Learning
- **Épocas de entrenamiento**: 10
- **Dataset**: 1,409 imágenes (1,135 train / 137 val / 137 test)

## 🎯 Características

- ✅ Clasifica **15 tipos de frutas** con alta precisión
- ✅ Interfaz web interactiva con Streamlit
- ✅ Muestra **precios aproximados en soles peruanos** (S/.)
- ✅ Transfer Learning con MobileNetV2 pre-entrenado en ImageNet
- ✅ Data Augmentation para mejor generalización
- ✅ Modelo `.h5` incluido en el repositorio (listo para usar)

## 🍎 Frutas que puede identificar:

**Apple** 🍎 | **Banana** 🍌 | **Bell Pepper** 🫑 | **Chilli Pepper** 🌶️ | **Grapes** 🍇

**Jalapeño** | **Kiwi** 🥝 | **Lemon** 🍋 | **Mango** 🥭 | **Orange** 🍊

**Paprika** | **Pear** 🍐 | **Pineapple** 🍍 | **Pomegranate** | **Watermelon** 🍉

## 📋 Instalación

### 1. Clonar el repositorio
```bash
git clone https://github.com/Dxnn017/fruit-classification-mobilenet.git
cd fruit-classification-mobilenet
```

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 3. Descargar el dataset (opcional - solo si quieres entrenar)

**Opción A: Usando Kaggle API** (recomendado)
```bash
kaggle datasets download -d kritikseth/fruit-and-vegetable-image-recognition
unzip fruit-and-vegetable-image-recognition.zip -d dataset
```

**Opción B: Descarga manual**
1. Ir a [Kaggle Dataset](https://www.kaggle.com/kritikseth/fruit-and-vegetable-image-recognition)
2. Descargar el ZIP
3. Extraer en la carpeta `./dataset`

## 🚀 Uso

### Opción 1: Usar el modelo pre-entrenado (recomendado)

El modelo `FV_Fruits_Only.h5` ya está incluido en el repositorio. Solo ejecuta:

```bash
streamlit run Fruits_Vegetable_Classification.py
```

Abre tu navegador en: `http://localhost:8501`

### Opción 2: Entrenar tu propio modelo

1. Asegúrate de tener el dataset descargado
2. Abre `Fruit_Veg_Classification_Mobilenet.ipynb` en Jupyter/VS Code
3. Ejecuta todas las celdas (tarda ~15-20 min)
4. Se generará un nuevo `FV_Fruits_Only.h5`

## 🏗️ Arquitectura del Modelo

```
Input (224x224x3)
    ↓
MobileNetV2 (pre-trained ImageNet)
    ↓
GlobalAveragePooling2D
    ↓
Dense(128, activation='relu')
    ↓
Dense(128, activation='relu')
    ↓
Dense(15, activation='softmax')
```

**Parámetros de entrenamiento:**
- Optimizer: Adam
- Loss: Categorical Crossentropy
- Batch size: 32
- Epochs: 10 (con Early Stopping patience=3)
- Data Augmentation: rotación ±30°, zoom ±15%, shift ±20%

## 📂 Estructura del Proyecto

```
fruit-classification-mobilenet/
│
├── Fruits_Vegetable_Classification.py  # App principal Streamlit
├── App.py                              # App alternativa
├── ec2_api.py                          # API REST con Flask
├── FV_Fruits_Only.h5                   # Modelo entrenado (11.2 MB)
├── Fruit_Veg_Classification_Mobilenet.ipynb  # Notebook de entrenamiento
├── requirements.txt                    # Dependencias Python
├── .gitignore                          # Archivos ignorados
└── README.md                           # Esta documentación
```

## 🔧 Tecnologías Utilizadas

- **Python 3.13**
- **TensorFlow 2.15+** / **tf-keras** - Framework de Deep Learning
- **Streamlit 1.28+** - Interfaz web interactiva
- **MobileNetV2** - Arquitectura de red neuronal eficiente
- **Pandas & NumPy** - Procesamiento de datos
- **Pillow** - Procesamiento de imágenes

## 📊 Dataset

- **Fuente**: [Fruit and Vegetable Image Recognition (Kaggle)](https://www.kaggle.com/kritikseth/fruit-and-vegetable-image-recognition)
- **Tamaño**: ~2 GB
- **Clases usadas**: 15 frutas (filtradas del dataset original de 36 clases)
- **Resolución**: 224x224 píxeles RGB

## 👥 Autores

Desarrollado por **Daniela** ([@Dxnn017](https://github.com/Dxnn017))

## ⭐ Si te sirvió el proyecto

Dale una estrella ⭐ al repositorio para ayudar a más personas a encontrarlo!

## 📝 Licencia

Este proyecto está disponible para uso educativo y de investigación.
