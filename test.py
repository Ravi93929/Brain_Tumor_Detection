import tensorflow as tf
from tensorflow.keras.applications import VGG16
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Flatten, Dropout, Dense

IMG_SIZE = 128

# Exact base model
base_model = VGG16(
    weights=None,
    include_top=False,
    input_shape=(IMG_SIZE, IMG_SIZE, 3)
)

# Match trainable flags from saved config
for layer in base_model.layers:
    if layer.name.startswith("block5_conv"):
        layer.trainable = True
    else:
        layer.trainable = False

# Exact outer model from your saved config
model = Sequential([
    base_model,
    Flatten(name="flatten"),
    Dropout(0.3, name="dropout"),
    Dense(128, activation="relu", name="dense"),
    Dropout(0.2, name="dropout_1"),
    Dense(4, activation="softmax", name="dense_1")
], name="sequential")

try:
    model.load_weights("models/model.h5")
    print("Weights loaded successfully")
    model.summary()

    # Optional: save a clean new model file
    model.save("models/model_fixed.keras")
    print("Saved as models/model_fixed.keras")

except Exception as e:
    print("Failed to load weights:")
    print(type(e).__name__, e)