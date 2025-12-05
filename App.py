import streamlit as st
from PIL import Image
import numpy as np
import tf_keras as keras
from tf_keras.preprocessing.image import load_img, img_to_array

# Cargar modelo entrenado solo con frutas
model = keras.models.load_model('FV_Fruits_Only.h5')

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
    img = load_img(img_path, target_size=(224, 224, 3))
    img = img_to_array(img)
    img = img / 255
    img = np.expand_dims(img, [0])
    answer = model.predict(img)
    y_class = answer.argmax(axis=-1)
    print(y_class)
    y = " ".join(str(x) for x in y_class)
    y = int(y)
    res = labels[y]
    print(res)
    return res.capitalize()


def run():
    st.title("🍎 Clasificación de Frutas")
    st.markdown("### Sube una imagen para identificar una de 15 frutas")
    
    # Mostrar lista de frutas disponibles
    with st.expander("📋 Ver lista de frutas que puedo identificar"):
        cols = st.columns(3)
        for idx, fruit in enumerate(fruits):
            cols[idx % 3].write(f"• {fruit}")
    
    img_file = st.file_uploader("Selecciona una imagen", type=["jpg", "png", "jpeg"])
    
    if img_file is not None:
        # Crear columnas para mejor diseño
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📸 Imagen Original")
            img = Image.open(img_file).resize((250, 250))
            st.image(img, use_container_width=True)
        
        with col2:
            st.markdown("#### 🔍 Resultados")
            save_image_path = './upload_images/' + img_file.name
            with open(save_image_path, "wb") as f:
                f.write(img_file.getbuffer())
            
            with st.spinner('Analizando fruta...'):
                result = prepare_image(save_image_path)
                
            # Mostrar predicción
            st.success(f"🍎 **Identificado como: {result}**")
            
            # Mostrar precio
            precio = get_precio(result)
            st.info(f'💰 **Precio aproximado: {precio}** por kilogramo')
            st.caption('💡 Precios referenciales del mercado peruano')


run()
