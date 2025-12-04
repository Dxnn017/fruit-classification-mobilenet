import numpy as np
import tf_keras as keras
from tf_keras.preprocessing.image import load_img, img_to_array
from flask import Flask, jsonify, request

# Cargar modelo entrenado solo con frutas
model = keras.models.load_model('FV_Fruits_Only.h5')

labels = {
    0: 'apple', 1: 'banana', 2: 'bell pepper', 3: 'chilli pepper', 
    4: 'grapes', 5: 'jalepeno', 6: 'kiwi', 7: 'lemon', 
    8: 'mango', 9: 'orange', 10: 'paprika', 11: 'pear', 
    12: 'pineapple', 13: 'pomegranate', 14: 'watermelon'
}


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


app = Flask(__name__)


@app.route('/predict', methods=['POST'])
def infer_image():
    if 'file' not in request.files:
        return jsonify(error="Please try again. The Image doesn't exist")

    file = request.files.get('file')
    img_bytes = file.read()
    img_path = "./upload_images/test.jpg"
    with open(img_path, "wb") as img:
        img.write(img_bytes)
    result = prepare_image(img_path)
    return jsonify(prediction=result)


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0')
