import tensorflow as tf
from tensorflow.keras.layers import *
from tensorflow.keras.models import Model
from tensorflow.keras.applications import ResNet50
from core.config import settings

def attention_block(inputs):
    u = Dense(inputs.shape[-1], activation="tanh")(inputs)
    alpha = Softmax(axis=1)(Dense(1)(u))
    return Lambda(lambda x: tf.reduce_sum(x[0] * x[1], axis=1))([inputs, alpha])

def build_gru_model(num_classes=2):
    """Build model architecture for both Binary and Tri-class"""
    inp = Input(shape=(settings.SEQUENCE_LENGTH, settings.IMG_SIZE, settings.IMG_SIZE, 3))
    base = ResNet50(weights="imagenet", include_top=False, input_shape=(settings.IMG_SIZE, settings.IMG_SIZE, 3))
    base.trainable = True
    for layer in base.layers[:-20]: 
        layer.trainable = False
    
    x = TimeDistributed(base)(inp)
    x = TimeDistributed(GlobalAveragePooling2D())(x)
    x = TimeDistributed(Dense(256, activation="relu"))(x)
    x = Bidirectional(GRU(32, return_sequences=True))(x)
    x = attention_block(LayerNormalization()(x))
    x = Dense(128, activation="relu", kernel_regularizer=tf.keras.regularizers.l2(0.02))(x)
    out = Dense(num_classes, activation="softmax")(Dropout(0.6)(x))
    return Model(inp, out)

# Segmentation Custom Objects
smooth = 1e-15
def dice_coef(y_true, y_pred):
    y_true = tf.cast(y_true, tf.float32)
    y_pred = tf.cast(y_pred, tf.float32)
    y_true = tf.reshape(y_true, [-1])
    y_pred = tf.reshape(y_pred, [-1])
    intersection = tf.reduce_sum(y_true * y_pred)
    return (2. * intersection + smooth) / (tf.reduce_sum(y_true) + tf.reduce_sum(y_pred) + smooth)

def dice_loss(y_true, y_pred): return 1.0 - dice_coef(y_true, y_pred)
def combined_loss(y_true, y_pred): return 0.5 * dice_loss(y_true, y_pred) + 0.5 * tf.keras.losses.BinaryCrossentropy()(y_true, y_pred)
def iou(y_true, y_pred): return dice_coef(y_true, y_pred)

seg_custom_objects = {"combined_loss": combined_loss, "dice_loss": dice_loss, "dice_coef": dice_coef, "iou": iou}