# Updated main execution code with proper date handling
from weather_engineer import WeatherFeatureEngineer
from agri_recommender import AgriculturalRecommendationSystem


if __name__ == "__main__":
    import pandas as pd
    import numpy as np
    from pathlib import Path
    from datetime import datetime

    # Load raw data
    df = pd.read_csv("test_data.csv")
    
    # Get the last date from your data
    # Assuming your CSV has a 'date' column
    if 'date' in df.columns:
        last_date_str = df['date'].iloc[-1]  # last date string
        last_date = datetime.strptime(last_date_str, "%Y-%m-%d")  # convert to datetime
        print(f"📅 Last date in data: {last_date.strftime('%Y-%m-%d')}")
    else:
        # If no date column, set manually as datetime object
        last_date = datetime.strptime("2025-05-15", "%Y-%m-%d")
        print(f"📅 Manually set last date: {last_date.strftime('%Y-%m-%d')}")

    # Initialize and transform with feature engineer
    engineer = WeatherFeatureEngineer()
    df_transformed = engineer.transform(df)

    # Prepare models
    models = ['temp_max', 'temp_min', 'humidity_max', 'humidity_min', 'weather_condition']
    processed_data = {}

    for model_type in models:
        print(f"\nProcessing data for model: {model_type}")
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
            print(f"  📊 Features for {model_type}: {len(feature_cols)}")
        else:
            X_scaled, feature_cols = engineer.generate_model_inputs(df_transformed, model_type)
            processed_data[model_type] = {
                'X': X_scaled,
                'feature_cols': feature_cols,
            }
            print(f"  📊 Features for {model_type}: {len(feature_cols)}")

    print("\n✅ All model inputs prepared and ready.")

    # ============================
    # 🎯 Use in Agricultural System
    # ============================
    agri_system = AgriculturalRecommendationSystem()
    
    # Set the last input date BEFORE making predictions
    agri_system.set_last_input_date(last_date)

    model_paths = {
        'weather_condition': 'models/BestWeatherModel_20250707_043444',
        'humidity_min': 'models/BestMinimumHumidityLSTM_Model1_20250704_150613',
        'humidity_max': 'models/MaximumHumidityLSTM_Model1_20250726_221759',
        'temp_min': 'models/BestMinimumTemperatureLSTM_Model1_20250704_122946',
        'temp_max': 'models/BestMaximumTemperatureLSTM_Model1_20250704_110121',
    }

    # Load models with processed data
    agri_system.load_models(model_paths, processed_data)

    # Extract input feature names from your feature engineer's transformed df
    exclude_cols = ['date', 'weather_condition']
    input_feature_names = [col for col in df_transformed.columns if col not in exclude_cols]
    
    print(f"\n📋 Available input features ({len(input_feature_names)}): {input_feature_names[:10]}...")  # Show first 10
    
    agri_system.set_input_feature_names(input_feature_names)

    # Get sequence_length from one model
    sample_model = list(agri_system.models.values())[0]
    seq_len = sample_model.sequence_length
    print(f"📏 Sequence length: {seq_len}")

    # Prepare input data correctly
    print(f"\n🔧 Preparing input data...")
    
    # Get the last sequence from the transformed data
    feature_data = df_transformed[input_feature_names]
    
    # Take the last seq_len rows
    input_sequence = feature_data.iloc[-seq_len:].values
    print(f"📊 Input sequence shape: {input_sequence.shape}")
    
    # Add batch dimension
    input_data = np.expand_dims(input_sequence, axis=0)
    print(f"📊 Final input shape: {input_data.shape}")

    # Get recommendations
    try:
        recommendations = agri_system.get_recommendations_with_safe_save(
            input_data, days_ahead=3, save_file=True,last_data_date=last_date
        )
        print(recommendations)
        
        
    except Exception as e:
        print(f"\n❌ Error generating recommendations: {str(e)}")
        import traceback
        traceback.print_exc()