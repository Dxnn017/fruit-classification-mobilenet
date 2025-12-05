"""
🚀 PREPROCESAMIENTO MEJORADO CON ALBUMENTATIONS
Para igualar exactamente la descripción del proyecto de referencia
"""

import albumentations as A
from albumentations.pytorch import ToTensorV2
import cv2
import numpy as np

# 📊 ESTADÍSTICAS DE IMAGENET (como en la descripción)
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

# 🔄 PREPROCESAMIENTO PARA ENTRENAMIENTO (416x416 + Albumentations)
train_transform = A.Compose([
    # 📏 REDIMENSIONAMIENTO UNIFORME
    A.Resize(416, 416, always_apply=True),
    
    # 🎨 AUMENTO DE DATOS (DATA AUGMENTATION)
    A.HorizontalFlip(p=0.5),                    # Volteo horizontal 50%
    A.Rotate(limit=15, p=0.7),                  # Rotación ±15°
    A.RandomBrightnessContrast(               # Brillo y contraste dinámico
        brightness_limit=0.2,
        contrast_limit=0.2,
        p=0.5
    ),
    A.HueSaturationValue(                     # Tono, saturación y valor
        hue_shift_limit=10,
        sat_shift_limit=20,
        val_shift_limit=10,
        p=0.5
    ),
    
    # 🔢 NORMALIZACIÓN CON ESTADÍSTICAS DE IMAGENET
    A.Normalize(
        mean=IMAGENET_MEAN,
        std=IMAGENET_STD,
        always_apply=True
    ),
    
    # 📦 CONVERSIÓN A TENSOR
    ToTensorV2(always_apply=True)
])

# ✅ PREPROCESAMIENTO PARA VALIDACIÓN/TEST (416x416, solo normalización)
val_transform = A.Compose([
    # 📏 REDIMENSIONAMIENTO UNIFORME
    A.Resize(416, 416, always_apply=True),
    
    # 🔢 NORMALIZACIÓN ESTANDARIZADA (sin aumentos)
    A.Normalize(
        mean=IMAGENET_MEAN,
        std=IMAGENET_STD,
        always_apply=True
    ),
    
    # 📦 CONVERSIÓN A TENSOR
    ToTensorV2(always_apply=True)
])

def preprocess_image_albumentations(image_path, is_training=False):
    """
    Preprocesa imagen usando Albumentations (como en la descripción)
    
    Args:
        image_path: Ruta a la imagen
        is_training: Si True, aplica data augmentation
    
    Returns:
        Tensor procesado listo para el modelo
    """
    # Cargar imagen
    image = cv2.imread(image_path)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # Aplicar transformaciones según el modo
    if is_training:
        transformed = train_transform(image=image)
    else:
        transformed = val_transform(image=image)
    
    return transformed['image']

def show_augmentation_examples(image_path, num_examples=4):
    """
    Muestra ejemplos de data augmentation aplicado
    """
    import matplotlib.pyplot as plt
    
    # Cargar imagen original
    image = cv2.imread(image_path)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # Crear figura
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    fig.suptitle('🎨 DATA AUGMENTATION CON ALBUMENTATIONS', fontsize=16, fontweight='bold')
    
    # Imagen original
    axes[0, 0].imshow(image)
    axes[0, 0].set_title('📸 Original')
    axes[0, 0].axis('off')
    
    # Aplicar transformaciones
    transformations = [
        ('🔄 Rotación', A.Compose([A.Resize(416, 416), A.Rotate(limit=15, p=1.0)])),
        ('↔️ Volteo', A.Compose([A.Resize(416, 416), A.HorizontalFlip(p=1.0)])),
        ('🌟 Brillo/Contraste', A.Compose([A.Resize(416, 416), A.RandomBrightnessContrast(p=1.0)])),
        ('🎨 HSV', A.Compose([A.Resize(416, 416), A.HueSaturationValue(hue_shift_limit=20, p=1.0)])),
        ('🔄 Completo', train_transform)
    ]
    
    positions = [(0, 1), (0, 2), (1, 0), (1, 1), (1, 2)]
    
    for i, (title, transform) in enumerate(transformations):
        row, col = positions[i]
        
        # Aplicar transformación
        if 'Completo' in title:
            # Para la transformación completa, desnormalizar para visualización
            transformed = transform(image=image)['image']
            # Desnormalizar
            if isinstance(transformed, np.ndarray):
                img_vis = transformed
            else:  # tensor
                img_vis = transformed.permute(1, 2, 0).numpy()
                img_vis = img_vis * np.array(IMAGENET_STD) + np.array(IMAGENET_MEAN)
                img_vis = np.clip(img_vis, 0, 1)
        else:
            img_vis = transform(image=image)['image']
        
        axes[row, col].imshow(img_vis)
        axes[row, col].set_title(title)
        axes[row, col].axis('off')
    
    plt.tight_layout()
    plt.savefig('augmentation_examples.png', dpi=150, bbox_inches='tight')
    plt.show()

# 📋 EJEMPLO DE USO
if __name__ == "__main__":
    print("🚀 PREPROCESAMIENTO CON ALBUMENTATIONS")
    print("=" * 50)
    
    print("✅ Configuración de entrenamiento:")
    print("   - Tamaño: 416×416 píxeles")
    print("   - Normalización: ImageNet stats")
    print("   - Augmentation: Flip, Rotación, Brillo, HSV")
    
    print("\n✅ Configuración de validación:")
    print("   - Tamaño: 416×416 píxeles") 
    print("   - Normalización: ImageNet stats")
    print("   - Sin augmentation")
    
    print("\n💡 Para usar:")
    print("   tensor = preprocess_image_albumentations('imagen.jpg', is_training=True)")
    print("   show_augmentation_examples('imagen.jpg')")