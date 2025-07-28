from tensorflow.keras.utils import register_keras_serializable
from tensorflow.keras.models import load_model
from tensorflow.keras import backend as K
import json
import pickle
import joblib
import os
import pandas as pd

@register_keras_serializable()
def focal_loss_fn(y_true, y_pred, gamma=2.0, alpha=0.25):
    epsilon = K.epsilon()
    y_pred = K.clip(y_pred, epsilon, 1. - epsilon)

    ce = -y_true * K.log(y_pred)
    p_t = K.sum(y_true * y_pred, axis=-1, keepdims=True)
    focal_weight = K.pow((1 - p_t), gamma)
    alpha_t = y_true * alpha + (1 - y_true) * (1 - alpha)
    focal_loss = alpha_t * focal_weight * ce

    return K.mean(K.sum(focal_loss, axis=-1))


def load_lstm_model(model_folder, model_class, custom_objects=None):
    try:
        print(f"📂 Loading model from: {model_folder}")

        keras_model = load_model(f"{model_folder}/keras_model.keras", custom_objects=custom_objects)

        with open(f"{model_folder}/model_config.json", 'r') as f:
            config = json.load(f)

        with open(f"{model_folder}/full_model.pkl", 'rb') as f:
            model_dict = pickle.load(f)

        model = model_class(pd.DataFrame(), config['sequence_length'], config['forecast_horizon'])
        model.model = keras_model

        scaler_path = os.path.join(model_folder, 'scaler_features.pkl')
        if os.path.exists(scaler_path):
            model.scaler_features = joblib.load(scaler_path)
        else:
            model.scaler_features = None

        scaler_target_path = os.path.join(model_folder, 'scaler_targets.pkl')
        if os.path.exists(scaler_target_path):
            model.scaler_targets = joblib.load(scaler_target_path)
        else:
            model.scaler_targets = None

        for key, value in model_dict.items():
            setattr(model, key, value)

        print(f"✅ Model '{config['model_name']}' successfully loaded!")
        return model

    except Exception as e:
        print(f"❌ Error loading model: {e}")
        return None


def load_classification_model(model_folder, model_class):
    try:
        print(f"📂 Loading classification model from: {model_folder}")

        keras_model = load_model(
            f"{model_folder}/keras_model.keras",
            custom_objects={'focal_loss_fn': focal_loss_fn}
        )

        with open(f"{model_folder}/label_encoder.pkl", 'rb') as f:
            label_encoder = pickle.load(f)

        with open(f"{model_folder}/scaler.pkl", 'rb') as f:
            scaler = pickle.load(f)

        with open(f"{model_folder}/model_config.json", 'r') as f:
            config = json.load(f)

        with open(f"{model_folder}/essential_attributes.pkl", 'rb') as f:
            essential_attributes = pickle.load(f)

        model = model_class(df=pd.DataFrame(), sequence_length=config['sequence_length'], forecast_horizon=config['forecast_horizon'])
        model.model = keras_model
        model.label_encoder = label_encoder
        model.scaler_X = scaler

        for attr, value in essential_attributes.items():
            setattr(model, attr, value)

        print(f"✅ Classification model '{config['model_name']}' successfully loaded!")
        return model

    except Exception as e:
        print(f"❌ Error loading classification model: {e}")
        return None
