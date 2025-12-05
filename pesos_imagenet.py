import tf_keras as keras

# Cargar modelo
model = keras.applications.MobileNetV2(weights='imagenet')

print('📁 DONDE ESTÁN LOS PESOS DE IMAGENET:')
print('Total parámetros:', f'{model.count_params():,}')
print('Tamaño en memoria:', f'{model.count_params() * 4 / 1024 / 1024:.1f} MB')

print('\n🗃️ CADA PARÁMETRO ES UN NÚMERO ENTRENADO:')
layers_with_weights = [layer for layer in model.layers if layer.get_weights()]
print(f'Capas con pesos: {len(layers_with_weights)}')

for i, layer in enumerate(layers_with_weights[:5]):
    weights = layer.get_weights()
    if weights:
        total_params = sum([w.size for w in weights])
        print(f'{i+1}. {layer.name}: {total_params:,} parámetros')

print('\n🔢 EJEMPLO DE COMO SE VEN LOS NÚMEROS:')
first_layer = model.get_layer('Conv1')
weights = first_layer.get_weights()[0]
print(f'Forma del primer filtro: {weights.shape}')
print('Primeros 5 números del filtro:')
flat_weights = weights.flatten()
for i in range(5):
    print(f'  Parámetro {i+1}: {flat_weights[i]:.6f}')

print('\n💡 RESUMEN:')
print('- ImageNet entrenó durante SEMANAS para encontrar estos números')
print('- Cada número representa conocimiento sobre bordes, texturas, formas')
print('- TU proyecto usa estos 2.2M números como punto de partida')
print('- Solo entrenas las últimas capas (128 + 128 + 15 neuronas)')