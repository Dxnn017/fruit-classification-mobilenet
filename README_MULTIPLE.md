# 🍎 Clasificación de Frutas - Procesamiento Múltiple

## 🚀 NUEVAS CARACTERÍSTICAS IMPLEMENTADAS

### ✨ **Procesamiento Individual y Múltiple**
- 📸 **Modo Individual**: Sube una imagen y obtén resultados instantáneos
- 📚 **Modo Múltiple**: Procesa hasta 10 imágenes simultáneamente con análisis estadístico

### 🎯 **Características Mejoradas**
- ⚡ **Batch Processing**: Predicción eficiente en lote usando TensorFlow
- 📊 **Análisis Estadístico**: Métricas de confianza, distribución y tiempo de procesamiento
- 🎨 **Interfaz Mejorada**: Diseño responsivo con tabs y visualización en grid
- 🔧 **Manejo de Errores**: Validación robusta de archivos e imágenes
- 💰 **Precios Actualizados**: Precios referenciales del mercado peruano

---

## 🖥️ **CÓMO USAR LA APLICACIÓN**

### **Opción 1: Ejecución Rápida**
```powershell
# Navegar al directorio del proyecto
cd "d:\Carrera - Ing. Sistemas\Ciclo VI\percepcion\final countdown\fruit-classification-mobilenet"

# Activar entorno virtual
.\fruit_detection_env\Scripts\Activate.ps1

# Ejecutar aplicación optimizada
python run_app_multiple.py
```

### **Opción 2: Ejecución Manual**
```powershell
# Ejecutar directamente con Streamlit
streamlit run App.py --server.maxUploadSize=50
```

### **Opción 3: Pruebas sin Interfaz**
```powershell
# Probar funcionalidad de batch processing
python test_multiple_images.py
```

---

## 📱 **INTERFAZ DE USUARIO**

### **🔍 Pestaña "Imagen Individual"**
- Sube una imagen (JPG, PNG, JPEG)
- Visualiza la imagen original redimensionada
- Obtén predicción con nivel de confianza
- Consulta precio referencial en soles

### **📊 Pestaña "Múltiples Imágenes"**
- Sube hasta 10 imágenes simultáneamente
- Procesamiento optimizado en batch
- Resultados en tabla y vista de grid
- Análisis estadístico automático:
  - Confianza promedio
  - Distribución de frutas
  - Tiempo de procesamiento
  - Métricas de rendimiento

---

## 🔧 **ARQUITECTURA TÉCNICA**

### **Optimizaciones Implementadas**
```python
# Batch Prediction (más eficiente que individual)
images_batch = np.array([preprocess(img) for img in images])
predictions = model.predict(images_batch, verbose=0)

# Procesamiento paralelo de imágenes
with ThreadPoolExecutor() as executor:
    results = executor.map(process_image, image_paths)

# Validación robusta de archivos
try:
    img = load_img(path, target_size=(224, 224, 3))
    if img.shape != (224, 224, 3):
        raise ValueError("Formato inválido")
except Exception as e:
    handle_error(e)
```

### **Estructura de Datos de Resultado**
```python
result = {
    'image_path': str,      # Ruta del archivo
    'filename': str,        # Nombre del archivo
    'prediction': str,      # Fruta predicha
    'confidence': float,    # Nivel de confianza [0-1]
    'price': str           # Precio en formato "S/. X.XX"
}
```

---

## 📊 **MÉTRICAS Y ANÁLISIS**

### **Estadísticas Disponibles**
- **Total de Imágenes**: Cantidad procesada exitosamente
- **Confianza Promedio**: Media de todas las predicciones
- **Frutas Únicas**: Tipos diferentes detectados
- **Tiempo de Proceso**: Duración total y promedio por imagen

### **Visualizaciones**
- 📋 **Tabla de Resultados**: DataFrame con todos los datos
- 🖼️ **Grid de Imágenes**: Vista visual con predicciones
- 📈 **Gráfico de Barras**: Distribución de frutas detectadas
- 🎯 **Métricas en Cards**: KPIs principales destacados

---

## ⚡ **RENDIMIENTO**

### **Benchmarks Típicos**
- **Imagen Individual**: ~0.5-1 segundo
- **Batch de 5 imágenes**: ~1.5-2.5 segundos
- **Batch de 10 imágenes**: ~2.5-4 segundos

### **Optimizaciones de Memoria**
- Procesamiento en lotes para eficiencia
- Limpieza automática de archivos temporales
- Validación previa antes de cargar en memoria
- Redimensionamiento automático a 224x224

---

## 🔍 **SOLUCIÓN DE PROBLEMAS**

### **Error: "Modelo no encontrado"**
```powershell
# Verificar que existe el archivo del modelo
ls FV_Fruits_Only.h5

# Si no existe, ejecutar entrenamiento
jupyter notebook Fruit_Veg_Classification_Mobilenet.ipynb
```

### **Error: "Memoria insuficiente"**
- Reduce el número de imágenes simultáneas
- Verifica que las imágenes no sean demasiado grandes
- Cierra otras aplicaciones que consuman memoria

### **Error: "Formato de imagen inválido"**
- Usa solo archivos JPG, PNG, JPEG
- Verifica que los archivos no estén corruptos
- Asegúrate de que sean imágenes RGB válidas

---

## 📁 **ARCHIVOS PRINCIPALES**

| Archivo | Descripción |
|---------|-------------|
| `App.py` | Aplicación principal con interfaz dual |
| `run_app_multiple.py` | Script optimizado de ejecución |
| `test_multiple_images.py` | Pruebas de batch processing |
| `FV_Fruits_Only.h5` | Modelo entrenado MobileNetV2 |
| `model_metadata.json` | Metadatos del modelo |

---

## 🎯 **PRÓXIMAS MEJORAS**

- [ ] Soporte para más de 10 imágenes con paginación
- [ ] Exportación de resultados a CSV/Excel
- [ ] API REST para integración externa
- [ ] Modo de procesamiento de carpetas completas
- [ ] Historial de predicciones
- [ ] Comparación de múltiples modelos
- [ ] Procesamiento de video frame por frame

---

## 📞 **CONTACTO Y SOPORTE**

Para reportar bugs o sugerir mejoras:
- GitHub Issues en el repositorio
- Documentación técnica en `/docs`
- Logs de error en `/logs`

**¡Disfruta clasificando frutas con IA! 🍎🚀**