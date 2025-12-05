"""
🔍 VISUALIZANDO EL CONOCIMIENTO DE IMAGENET
Este código muestra los FILTROS REALES que ImageNet entrenó
"""

import numpy as np
import matplotlib.pyplot as plt
import tf_keras as keras
from tf_keras.applications import MobileNetV2
import cv2

# Cargar modelo pre-entrenado con pesos de ImageNet
model = MobileNetV2(weights='imagenet', include_top=False, input_shape=(224, 224, 3))

print("🧠 EXTRAYENDO CONOCIMIENTO DE IMAGENET...")
print("=" * 60)

def visualizar_filtros_conv(layer, layer_name, num_filters=8):
    """
    Extrae y visualiza los filtros de una capa convolucional
    Estos son los DETECTORES que ImageNet entrenó
    """
    # Obtener pesos de la capa
    weights = layer.get_weights()
    if not weights:
        print(f"❌ {layer_name}: Sin pesos para visualizar")
        return
    
    filters = weights[0]  # [height, width, input_channels, output_channels]
    print(f"✅ {layer_name}: Forma de filtros: {filters.shape}")
    
    # Normalizar filtros para visualización
    f_min, f_max = filters.min(), filters.max()
    filters = (filters - f_min) / (f_max - f_min)
    
    # Crear visualización
    fig, axes = plt.subplots(2, 4, figsize=(12, 6))
    fig.suptitle(f'🔍 Filtros de {layer_name} (ImageNet)', fontsize=14, fontweight='bold')
    
    for i in range(min(num_filters, filters.shape[-1])):
        row = i // 4
        col = i % 4
        
        if filters.shape[2] == 1:  # Filtro de 1 canal
            filter_img = filters[:, :, 0, i]
            axes[row, col].imshow(filter_img, cmap='viridis')
        else:  # Filtro multicanal - tomar promedio
            filter_img = np.mean(filters[:, :, :, i], axis=2)
            axes[row, col].imshow(filter_img, cmap='viridis')
        
        axes[row, col].set_title(f'Filtro {i+1}')
        axes[row, col].axis('off')
    
    plt.tight_layout()
    plt.savefig(f'filtros_{layer_name}.png', dpi=150, bbox_inches='tight')
    plt.show()
    
    # Analizar qué detecta cada filtro
    print(f"📊 Análisis de filtros de {layer_name}:")
    for i in range(min(4, filters.shape[-1])):
        filter_data = filters[:, :, :, i] if len(filters.shape) == 4 else filters[:, :, i]
        varianza = np.var(filter_data)
        print(f"   Filtro {i+1}: Varianza={varianza:.4f} - ", end="")
        
        if varianza > 0.01:
            print("🔥 Detector activo (bordes/texturas)")
        elif varianza > 0.005:
            print("🟡 Detector moderado")
        else:
            print("🔵 Detector suave")

# 1️⃣ PRIMERA CAPA: Detectores de bordes básicos
print("\n🔲 CAPA 1: DETECTORES DE BORDES Y LÍNEAS")
print("-" * 50)
first_conv = model.get_layer('Conv1')
visualizar_filtros_conv(first_conv, 'Conv1_Bordes')

# 2️⃣ CAPA INTERMEDIA: Detectores de patrones
print("\n🟣 CAPA INTERMEDIA: DETECTORES DE FORMAS")
print("-" * 50)
try:
    mid_conv = model.get_layer('block_1_expand')
    visualizar_filtros_conv(mid_conv, 'Block1_Formas')
except:
    print("❌ No se pudo acceder a capa intermedia")

def mostrar_activaciones(imagen_path):
    """
    Muestra qué detecta cada capa en una imagen real
    """
    # Cargar y preprocesar imagen
    img = cv2.imread(imagen_path)
    if img is None:
        print(f"❌ No se pudo cargar imagen: {imagen_path}")
        return
    
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img_resized = cv2.resize(img, (224, 224))
    img_array = np.expand_dims(img_resized / 255.0, axis=0)
    
    # Crear modelo para extraer activaciones
    layer_outputs = []
    layer_names = []
    
    for layer in model.layers:
        if 'conv' in layer.name.lower() or 'Conv' in layer.name:
            layer_outputs.append(layer.output)
            layer_names.append(layer.name)
    
    if not layer_outputs:
        print("❌ No se encontraron capas convolucionales")
        return
    
    activation_model = keras.Model(inputs=model.input, outputs=layer_outputs[:3])
    activations = activation_model.predict(img_array)
    
    # Visualizar activaciones
    fig, axes = plt.subplots(2, 4, figsize=(15, 8))
    fig.suptitle('🔍 QUÉ VE IMAGENET EN TU IMAGEN', fontsize=16, fontweight='bold')
    
    # Imagen original
    axes[0, 0].imshow(img_resized)
    axes[0, 0].set_title('📸 Imagen Original')
    axes[0, 0].axis('off')
    
    # Activaciones de las primeras capas
    for i, (activation, layer_name) in enumerate(zip(activations[:3], layer_names[:3])):
        if i >= 3:
            break
        
        # Tomar el promedio de todos los filtros
        activation_avg = np.mean(activation[0], axis=2)
        
        row = (i + 1) // 4
        col = (i + 1) % 4
        
        im = axes[row, col].imshow(activation_avg, cmap='viridis')
        axes[row, col].set_title(f'🔍 {layer_name}')
        axes[row, col].axis('off')
    
    # Llenar el resto con texto explicativo
    for i in range(4, 8):
        row = i // 4
        col = i % 4
        axes[row, col].text(0.5, 0.5, 
                           f'🧠 Capa {i-3}\nDetecta patrones\nmás complejos', 
                           ha='center', va='center', fontsize=12,
                           transform=axes[row, col].transAxes)
        axes[row, col].axis('off')
    
    plt.tight_layout()
    plt.savefig('activaciones_imagenet.png', dpi=150, bbox_inches='tight')
    plt.show()

print("\n" + "=" * 60)
print("🔍 RESUMEN: DÓNDE ESTÁ EL CÓDIGO DE IMAGENET")
print("=" * 60)
print("""
❌ ImageNet NO es código que puedas ver ejecutándose
✅ ImageNet son 14M de imágenes que YA se usaron para entrenar

🧠 EL CONOCIMIENTO ESTÁ EN LOS PESOS (NÚMEROS):
   - Filtros de convolución: matrices 3x3, 5x5
   - Pesos de neuronas: valores entre -1 y 1
   - 3.4 millones de parámetros en MobileNetV2

🔢 EJEMPLO DE UN FILTRO REAL:
   Filtro detector de bordes verticales:
   [[-1, 0, 1],
    [-2, 0, 2], 
    [-1, 0, 1]]

📊 PROCESO ORIGINAL (ya completado):
   1. Tomar 14M imágenes de ImageNet
   2. Entrenar durante semanas en supercomputadoras
   3. Ajustar 3.4M parámetros
   4. Guardar pesos finales (archivo .h5)
   5. TU usas esos pesos pre-entrenados

💡 TU NO VES EL ENTRENAMIENTO, VES EL RESULTADO
""")

# Ejemplo de cómo usar este conocimiento
print("\n🎯 PARA PROBAR CON UNA IMAGEN:")
print("mostrar_activaciones('ruta/a/tu/imagen.jpg')")