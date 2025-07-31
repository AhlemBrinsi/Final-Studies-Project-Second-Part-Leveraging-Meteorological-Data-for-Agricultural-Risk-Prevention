from flask import Flask, request, jsonify
import pandas as pd
import numpy as np
from datetime import datetime
from weather_engineer import WeatherFeatureEngineer
from agri_recommender import AgriculturalRecommendationSystem
import os
import traceback
from db import test_data_col


app = Flask(__name__)

# Load models once when the app starts
engineer = WeatherFeatureEngineer()
agri_system = AgriculturalRecommendationSystem()

model_paths = {
    'weather_condition': 'models/BestWeatherModel_20250707_043444',
    'humidity_min': 'models/BestMinimumHumidityLSTM_Model1_20250704_150613',
    'humidity_max': 'models/MaximumHumidityLSTM_Model1_20250726_221759',
    'temp_min': 'models/BestMinimumTemperatureLSTM_Model1_20250704_122946',
    'temp_max': 'models/BestMaximumTemperatureLSTM_Model1_20250704_110121',
}

@app.route('/predict', methods=['POST'])
def predict():
    try:
        # Expect a JSON or CSV file
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file)
            # Save raw test data to MongoDB
            df_dict = df.to_dict(orient='records') 
            test_data_col.insert_many(df_dict)

        elif file.filename.endswith('.json'):
            df = pd.read_json(file)
            # Save raw test data to MongoDB
            df_dict = df.to_dict(orient='records') 
            test_data_col.insert_many(df_dict)
        else:
            return jsonify({"error": "Unsupported file format"}), 400

        # Get last date
        if 'date' in df.columns:
            last_date_str = df['date'].iloc[-1]
            last_date = datetime.strptime(last_date_str, "%Y-%m-%d")
        else:
            last_date = datetime.strptime("2025-05-15", "%Y-%m-%d")

        # Feature engineering
        df_transformed = engineer.transform(df)

        # Prepare processed data
        models = ['temp_max', 'temp_min', 'humidity_max', 'humidity_min', 'weather_condition']
        processed_data = {}
        for model_type in models:
            if model_type == 'weather_condition':
                X, y, feature_cols, label_encoder, class_weight_dict, scaler = engineer.generate_model_inputs(df_transformed, model_type)
                processed_data[model_type] = {
                    'X': X,
                    'y': y,
                    'feature_cols': feature_cols,
                    'label_encoder': label_encoder,
                    'class_weight_dict': class_weight_dict,
                    'scaler': scaler,
                }
            else:
                X_scaled, feature_cols = engineer.generate_model_inputs(df_transformed, model_type)
                processed_data[model_type] = {
                    'X': X_scaled,
                    'feature_cols': feature_cols,
                }

        # Load models
        agri_system.set_last_input_date(last_date)
        agri_system.load_models(model_paths, processed_data)

        # Input features
        exclude_cols = ['date', 'weather_condition']
        input_feature_names = [col for col in df_transformed.columns if col not in exclude_cols]
        agri_system.set_input_feature_names(input_feature_names)

        # Prepare input data
        seq_len = list(agri_system.models.values())[0].sequence_length
        input_sequence = df_transformed[input_feature_names].iloc[-seq_len:].values
        input_data = np.expand_dims(input_sequence, axis=0)

        # Run predictions
        result = agri_system.get_recommendations_with_safe_save(
            input_data, days_ahead=3, save_file=False, last_data_date=last_date
        )

        return jsonify(result), 200
    

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
