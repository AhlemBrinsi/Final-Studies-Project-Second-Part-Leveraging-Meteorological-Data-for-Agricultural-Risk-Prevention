import warnings
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.utils.class_weight import compute_class_weight
import tensorflow as tf
from sklearn.model_selection import train_test_split, StratifiedShuffleSplit
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dropout, Dense, BatchNormalization
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from tensorflow.keras.regularizers import l2
import matplotlib.pyplot as plt
from sklearn.metrics import accuracy_score, classification_report
from tensorflow.keras.utils import to_categorical
from tensorflow.keras import backend as K
from collections import Counter
import keras_tuner as kt
from tensorflow.keras import backend as K
from tensorflow.keras.saving import register_keras_serializable
import os
import json
import pickle
import joblib
from tensorflow.keras.models import load_model

from model_utils import load_lstm_model, load_classification_model, focal_loss_fn
from models import OptimizedTemperatureMinLSTM, OptimizedTemperatureMaxLSTM, OptimizedHumidityMinLSTM, HumidityMaxLSTM, ImprovedSlidingWindowModel

class AgriculturalRecommendationSystem:
        def __init__(self):
            """
            Initialize the Agricultural Recommendation System
            """
            self.weather_conditions = {
                'Clear Sky': '☀️',
                'Cloudy': '☁️', 
                'Heavy Drizzle': '🌧',
                'Heavy Rain': '🌧',
                'Light Drizzle': '🌦',
                'Light Rain': '🌦',
                'Moderate Drizzle': '🌧',
                'Moderate Rain': '🌧',
                'Partly Clear': '🌤'
            }
        
            # Agricultural knowledge base
            self.crop_requirements = {
                'tomatoes': {'temp_min': 15, 'temp_max': 30, 'humidity_min': 40, 'humidity_max': 70},
                'lettuce': {'temp_min': 10, 'temp_max': 25, 'humidity_min': 50, 'humidity_max': 80},
                'corn': {'temp_min': 18, 'temp_max': 35, 'humidity_min': 45, 'humidity_max': 75},
                'wheat': {'temp_min': 12, 'temp_max': 28, 'humidity_min': 40, 'humidity_max': 65},
                'rice': {'temp_min': 20, 'temp_max': 35, 'humidity_min': 70, 'humidity_max': 90},
                'beans': {'temp_min': 16, 'temp_max': 30, 'humidity_min': 50, 'humidity_max': 75},
                'carrots': {'temp_min': 8, 'temp_max': 24, 'humidity_min': 45, 'humidity_max': 70},
                'potatoes': {'temp_min': 12, 'temp_max': 26, 'humidity_min': 60, 'humidity_max': 80}
            }
        
            # Add attribute to store the last date from input data
            self.last_input_date = None
        
        def set_last_input_date(self, last_date):
            """
            Set the last date from the input data to calculate correct forecast dates
        
            Args:
                last_date: The last date from your input data (string or datetime object)
            """
            if isinstance(last_date, str):
                # Try to parse the date string
                try:
                    # Try common date formats
                    for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%Y-%m-%d %H:%M:%S']:
                        try:
                            self.last_input_date = datetime.strptime(last_date, fmt)
                            break
                        except ValueError:
                            continue
                    else:
                        raise ValueError(f"Could not parse date: {last_date}")
                except Exception as e:
                    print(f"⚠️ Error parsing date '{last_date}': {e}")
                    self.last_input_date = datetime.now()
            elif isinstance(last_date, datetime):
                self.last_input_date = last_date
            else:
                print(f"⚠️ Invalid date type: {type(last_date)}, using current date")
                self.last_input_date = datetime.now()
            
            print(f"📅 Last input date set to: {self.last_input_date.strftime('%Y-%m-%d')}")

        def load_models(self, model_paths: Dict[str, str], processed_data: Dict[str, dict]):
            """Load all models with proper feature column mapping"""
            self.models = {}

            model_class_map = {
                'temp_min': OptimizedTemperatureMinLSTM,
                'temp_max': OptimizedTemperatureMaxLSTM,
                'humidity_min': OptimizedHumidityMinLSTM,
                'humidity_max': HumidityMaxLSTM,
                'weather_condition': ImprovedSlidingWindowModel
            }

            for model_name, path in model_paths.items():
                print(f"🔄 Loading model for: {model_name} from {path}")
                model_class = model_class_map.get(model_name)
                if model_class is None:
                    print(f"⚠️ Warning: No model class mapped for {model_name}, skipping.")
                    continue

                if model_name == 'weather_condition':
                    model = load_classification_model(path, model_class)
                else:
                    model = load_lstm_model(path, model_class)

                if model is not None:
                    # Assign feature columns and scaler if available
                    if model_name in processed_data:
                        model.feature_cols = processed_data[model_name]['feature_cols']
                        print(f"  📊 Feature columns for {model_name}: {len(model.feature_cols)} features")
                    
                        # Some models have scaler saved, if available in processed_data:
                        if 'scaler' in processed_data[model_name]:
                            model.scaler_X = processed_data[model_name]['scaler']
                            print(f"  📏 Scaler loaded for {model_name}")
                        else:
                            # For regression models, scaler might not be saved, handle accordingly
                            model.scaler_X = None
                            print(f"  ⚠️ No scaler found for {model_name}")
                    else:
                        print(f"⚠️ Warning: No processed data found for {model_name} to set feature_cols/scaler.")

                    self.models[model_name] = model
                    print(f"  ✅ Model {model_name} loaded successfully")
                else:
                    print(f"❌ Failed to load model for {model_name}")

            print("\n✅ All models loaded successfully!")

        def predict_weather(self, input_data, days_ahead: int = 3):
            """Predict weather with proper feature filtering for each model"""
            predictions = {}
        
            print(f"🔮 Starting weather prediction for {days_ahead} days...")
            print(f"📊 Input data shape: {input_data.shape}")
            print(f"📋 Available input features: {len(self.input_feature_names)}")

            for key, model in self.models.items():
                print(f"\n🔄 Processing model: {key}")
            
                if model is None:
                    raise ValueError(f"Model for {key} not loaded.")

                # Get model's expected features
                expected_features = model.feature_cols
                print(f"  📊 Model expects {len(expected_features)} features")
            
                # Find indices of expected features in input data
                try:
                    model_feature_indices = []
                    missing_features = []
                
                    for feature in expected_features:
                        if feature in self.input_feature_names:
                            idx = self.input_feature_names.index(feature)
                            model_feature_indices.append(idx)
                        else:
                            missing_features.append(feature)
                
                    if missing_features:
                        print(f"  ⚠️ Missing features: {missing_features}")
                        print(f"  📋 Available features: {self.input_feature_names}")
                        raise ValueError(f"Missing required features for {key}: {missing_features}")
                
                    print(f"  ✅ Found all {len(model_feature_indices)} required features")
                
                    # Filter input data to match model's expected features
                    filtered_input = input_data[:, :, model_feature_indices]
                    print(f"  📊 Filtered input shape: {filtered_input.shape}")
                
                    # Convert to DataFrame for LSTM models (they expect DataFrame input)
                    if key != 'weather_condition':
                        # Create DataFrame with proper column names
                        last_sequence = filtered_input[0]  # Shape: (seq_len, features)
                        df_input = pd.DataFrame(last_sequence, columns=expected_features)
                        print(f"  📊 Created DataFrame input shape: {df_input.shape}")
                    
                        # Make prediction using DataFrame
                        pred = model.predict_future(df_input)
                    
                        # Ensure pred is the right shape
                        if isinstance(pred, np.ndarray):
                            if pred.ndim == 1:
                                pred = pred[:days_ahead]
                            elif pred.ndim == 2:
                                pred = pred[0, :days_ahead]
                    
                    else:
                        # For classification model, handle differently
                        # Extract the last sequence for prediction
                        last_sequence = filtered_input[0]  # Shape: (seq_len, features)
                        pred = model.predict_future(last_sequence)
                    
                        # pred might be a tuple (conditions, confidence, entropy)
                        if isinstance(pred, tuple):
                            pred = pred[0]  # Take the predicted conditions
                    
                        # Ensure we have the right number of predictions
                        if len(pred) > days_ahead:
                            pred = pred[:days_ahead]
                        elif len(pred) < days_ahead:
                            # Repeat last prediction if needed
                            pred = np.concatenate([pred, [pred[-1]] * (days_ahead - len(pred))])
                
                    predictions[key] = pred
                    print(f"  ✅ Prediction completed for {key}")
                    print(f"  📊 Prediction shape: {np.array(pred).shape}")
                    
                except Exception as e:
                    print(f"  ❌ Error processing {key}: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    raise

            print(f"\n✅ All predictions completed!")
            return predictions

        def set_input_feature_names(self, feature_names: List[str]):
            """Set the list of input feature names used for filtering per-model inputs."""
            self.input_feature_names = feature_names
            print(f"📋 Set {len(feature_names)} input feature names")

        def analyze_irrigation_needs(self, weather_condition: str, humidity_min: float, 
                                   humidity_max: float, temp_max: float) -> Dict[str, Any]:
            irrigation_advice = {
                'priority': 'medium',
                'frequency': 'normal',
                'amount': 'moderate',
                'timing': 'morning',
                'notes': []
            }
        
            # Analyze based on weather condition
            if weather_condition in ['Heavy Rain', 'Moderate Rain', 'Heavy Drizzle', 'Moderate Drizzle']:
                irrigation_advice['priority'] = 'low'
                irrigation_advice['frequency'] = 'reduced'
                irrigation_advice['amount'] = 'minimal'
                irrigation_advice['notes'].append('Natural rainfall expected - reduce irrigation')
            
            elif weather_condition in ['Clear Sky', 'Partly Clear']:
                if temp_max > 30:
                    irrigation_advice['priority'] = 'high'
                    irrigation_advice['frequency'] = 'increased'
                    irrigation_advice['amount'] = 'generous'
                    irrigation_advice['notes'].append('Hot and sunny - increase watering')
            
            elif weather_condition == 'Cloudy':
                irrigation_advice['priority'] = 'medium'
                irrigation_advice['notes'].append('Moderate conditions - maintain regular schedule')
        
            # Adjust based on humidity
            if humidity_min < 40:
                irrigation_advice['priority'] = 'high'
                irrigation_advice['notes'].append('Low humidity - plants need extra water')
            elif humidity_max > 80:
                irrigation_advice['frequency'] = 'reduced'
                irrigation_advice['notes'].append('High humidity - reduce watering frequency')
        
            return irrigation_advice
    
        def analyze_pest_disease_risk(self, weather_condition: str, humidity_max: float, 
                                    temp_max: float, temp_min: float) -> Dict[str, Any]:
            risk_assessment = {
                'overall_risk': 'medium',
                'pest_risk': 'medium',
                'disease_risk': 'medium',
                'specific_threats': [],
                'preventive_measures': []
            }
        
            # High humidity and warm temperatures increase disease risk
            if humidity_max > 75 and temp_max > 25:
                risk_assessment['disease_risk'] = 'high'
                risk_assessment['overall_risk'] = 'high'
                risk_assessment['specific_threats'].extend(['Fungal diseases', 'Bacterial infections'])
                risk_assessment['preventive_measures'].extend([
                    'Improve air circulation',
                    'Apply preventive fungicides',
                    'Monitor for early symptoms'
                ])
        
            # Rain conditions can increase disease pressure
            if weather_condition in ['Heavy Rain', 'Moderate Rain', 'Heavy Drizzle']:
                risk_assessment['disease_risk'] = 'high'
                risk_assessment['specific_threats'].append('Soil-borne diseases')
                risk_assessment['preventive_measures'].append('Ensure proper drainage')
        
            # Hot, dry conditions may increase pest activity
            if weather_condition == 'Clear Sky' and temp_max > 30 and humidity_max < 50:
                risk_assessment['pest_risk'] = 'high'
                risk_assessment['specific_threats'].extend(['Aphids', 'Spider mites', 'Thrips'])
                risk_assessment['preventive_measures'].extend([
                    'Monitor for pest presence',
                    'Maintain adequate moisture',
                    'Consider beneficial insects'
                ])
        
            return risk_assessment
    
        def recommend_planting_activities(self, weather_condition: str, temp_max: float, 
                                        temp_min: float, humidity_avg: float) -> Dict[str, Any]:
            recommendations = {
                'planting_suitability': 'moderate',
                'recommended_crops': [],
                'field_activities': [],
                'avoid_activities': [],
                'timing_advice': []
            }
        
            # Analyze temperature conditions
            if temp_min < 10:
                recommendations['planting_suitability'] = 'poor'
                recommendations['avoid_activities'].append('Planting heat-sensitive crops')
                recommendations['timing_advice'].append('Wait for warmer conditions')
            elif temp_min > 15 and temp_max < 30:
                recommendations['planting_suitability'] = 'excellent'
                recommendations['recommended_crops'].extend(['tomatoes', 'beans', 'corn'])
        
            # Weather-specific recommendations
            if weather_condition in ['Heavy Rain', 'Moderate Rain']:
                recommendations['avoid_activities'].extend([
                    'Planting seeds (risk of rot)',
                    'Harvesting',
                    'Soil cultivation'
                ])
                recommendations['timing_advice'].append('Wait for soil to dry before field work')
            
            elif weather_condition == 'Clear Sky':
                recommendations['field_activities'].extend([
                    'Planting',
                    'Transplanting',
                    'Harvesting',
                    'Soil preparation'
                ])
                recommendations['timing_advice'].append('Ideal conditions for most field activities')
        
            # Recommend suitable crops based on conditions
            for crop, requirements in self.crop_requirements.items():
                if (requirements['temp_min'] <= temp_min <= requirements['temp_max'] and
                    requirements['humidity_min'] <= humidity_avg <= requirements['humidity_max']):
                    if crop not in recommendations['recommended_crops']:
                        recommendations['recommended_crops'].append(crop)
        
            return recommendations
    
        def generate_comprehensive_report(self, predictions: Dict[str, Any], days_ahead: int = 7) -> str:
            report = []
            report.append("🌱 AGRICULTURAL WEATHER RECOMMENDATION REPORT 🌱")
            report.append("=" * 50)
        
            # Use the last input date if available, otherwise use current date
            if self.last_input_date:
                base_date = self.last_input_date
                report.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                report.append(f"Based on data up to: {base_date.strftime('%Y-%m-%d')}")
            else:
                base_date = datetime.now()
                report.append(f"Generated on: {base_date.strftime('%Y-%m-%d %H:%M:%S')}")
                print("⚠️ Warning: No last input date set, using current date for forecasts")
        
            report.append(f"Forecast period: {days_ahead} days\n")
        
            # Daily analysis
            for day in range(days_ahead):
                day_date = base_date + timedelta(days=day+1)
                weather_cond = predictions['weather_condition'][day]
                temp_max = predictions['temp_max'][day]
                temp_min = predictions['temp_min'][day]
                humidity_max = predictions['humidity_max'][day]
                humidity_min = predictions['humidity_min'][day]
                humidity_avg = (humidity_max + humidity_min) / 2
            
                report.append(f"📅 DAY {day+1} - {day_date.strftime('%A, %B %d, %Y')}")
                report.append("-" * 30)
                report.append(f"Weather: {weather_cond} {self.weather_conditions.get(weather_cond, '🌤')}")
                report.append(f"Temperature: {temp_min:.1f}°C - {temp_max:.1f}°C")
                report.append(f"Humidity: {humidity_min:.1f}% - {humidity_max:.1f}%\n")
            
                # Irrigation analysis
                irrigation = self.analyze_irrigation_needs(weather_cond, humidity_min, humidity_max, temp_max)
                report.append(f"💧 IRRIGATION ADVICE:")
                report.append(f"  Priority: {irrigation['priority'].upper()}")
                report.append(f"  Frequency: {irrigation['frequency']}")
                report.append(f"  Amount: {irrigation['amount']}")
                report.append(f"  Best timing: {irrigation['timing']}")
                for note in irrigation['notes']:
                    report.append(f"  • {note}")
                report.append("")
            
                # Pest and disease risk
                risk = self.analyze_pest_disease_risk(weather_cond, humidity_max, temp_max, temp_min)
                report.append(f"🐛 PEST & DISEASE RISK:")
                report.append(f"  Overall risk: {risk['overall_risk'].upper()}")
                report.append(f"  Pest risk: {risk['pest_risk']}")
                report.append(f"  Disease risk: {risk['disease_risk']}")
                if risk['specific_threats']:
                    report.append(f"  Threats: {', '.join(risk['specific_threats'])}")
                if risk['preventive_measures']:
                    report.append(f"  Prevention:")
                    for measure in risk['preventive_measures']:
                        report.append(f"    • {measure}")
                report.append("")
            
                # Planting recommendations
                planting = self.recommend_planting_activities(weather_cond, temp_max, temp_min, humidity_avg)
                report.append(f"🌱 PLANTING & FIELD ACTIVITIES:")
                report.append(f"  Planting conditions: {planting['planting_suitability'].upper()}")
                if planting['recommended_crops']:
                    report.append(f"  Suitable crops: {', '.join(planting['recommended_crops'])}")
                if planting['field_activities']:
                    report.append(f"  Recommended activities: {', '.join(planting['field_activities'])}")
                if planting['avoid_activities']:
                    report.append(f"  Avoid: {', '.join(planting['avoid_activities'])}")
                for advice in planting['timing_advice']:
                    report.append(f"  • {advice}")
            
                report.append("\n" + "="*50 + "\n")
        
            # Weekly summary
            report.append("📊 WEEKLY SUMMARY & RECOMMENDATIONS")
            report.append("=" * 50)
        
            # Calculate weekly averages
            avg_temp_max = np.mean(predictions['temp_max'])
            avg_temp_min = np.mean(predictions['temp_min'])
            avg_humidity = np.mean([predictions['humidity_max'], predictions['humidity_min']])
        
            rainy_days = sum(1 for cond in predictions['weather_condition'] 
                            if 'Rain' in cond or 'Drizzle' in cond)
        
            report.append(f"Average temperatures: {avg_temp_min:.1f}°C - {avg_temp_max:.1f}°C")
            report.append(f"Average humidity: {avg_humidity:.1f}%")
            report.append(f"Rainy days expected: {rainy_days}/{days_ahead}")
            report.append("")
        
            # Weekly recommendations
            report.append("🎯 KEY WEEKLY RECOMMENDATIONS:")
            if rainy_days >= 3:
                report.append("• High rainfall expected - focus on drainage and disease prevention")
            if avg_temp_max > 30:
                report.append("• Hot week ahead - increase irrigation and provide shade where possible")
            if avg_humidity > 75:
                report.append("• High humidity - monitor closely for fungal diseases")
            if rainy_days <= 1 and avg_temp_max > 25:
                report.append("• Dry conditions - excellent for harvesting and field work")
        
            report.append("\n" + "="*50)
            report.append("Generated by Agricultural Weather Recommendation System")
        
            return "\n".join(report)
    
        def save_report(self, recommendations, filename="agricultural_recommendations.txt", 
                       encoding='utf-8', include_emojis=True):
            """
            Save the recommendations report with proper encoding handling
        
            Args:
                recommendations: The report text to save
                filename: Output filename
                encoding: Text encoding ('utf-8', 'ascii', etc.)
                include_emojis: Whether to include emoji characters
            """
            try:
                text_to_save = recommendations
            
                if not include_emojis:
                    text_to_save = remove_emojis(text_to_save)
            
                with open(filename, 'w', encoding=encoding, errors='ignore') as f:
                    f.write(text_to_save)
            
                print(f"\n📄 Report saved to '{filename}' with {encoding} encoding")
                return True
            
            except Exception as e:
                print(f"❌ Error saving file: {str(e)}")
                return False
        

        def generate_recommendation_json(self, recommendations, output_path='agricultural_recommendations.json'):
            new_entry = {
                "generated_on": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "based_on_data_until": recommendations["based_on_date"],
                "forecast_period_days": len(recommendations["daily"]),
                "daily_forecast": [],
                "weekly_summary": recommendations["summary"]
            }

            for day in recommendations["daily"]:
                # Safely convert irrigation amount to float if possible
                amount_value = day["irrigation"]["amount"]
                try:
                    amount_value = float(amount_value)
                except (ValueError, TypeError):
                    amount_value = str(amount_value)

                daily_entry = {
                    "date": day["date"],
                    "day": day["day_name"],
                    "weather": day["weather"],
                    "temperature": {
                        "min": float(day["temp_min"]),
                        "max": float(day["temp_max"])
                    },
                    "humidity": {
                        "min": float(day["humidity_min"]),
                        "max": float(day["humidity_max"])
                    },
                    "irrigation_advice": {
                        "priority": day["irrigation"]["priority"],
                        "frequency": day["irrigation"]["frequency"],
                        "amount": amount_value,
                        "best_timing": day["irrigation"]["best_timing"],
                        "notes": day["irrigation"]["notes"]
                    },
                    "pest_disease_risk": {
                        "overall_risk": day["pest"]["overall"],
                        "pest_risk": day["pest"]["pest"],
                        "disease_risk": day["pest"]["disease"],
                        "threats": day["pest"]["threats"],
                        "prevention": day["pest"]["prevention"]
                    },
                    "planting_field_activities": {
                        "planting_conditions": day["planting"]["conditions"],
                        "suitable_crops": day["planting"]["crops"]
                    }
                }
                new_entry["daily_forecast"].append(daily_entry)

            # Load existing recommendations if file exists
            if os.path.exists(output_path):
                try:
                    with open(output_path, "r", encoding="utf-8") as f:
                        existing_data = json.load(f)
                        if not isinstance(existing_data, list):
                            existing_data = [existing_data]
                except Exception as e:
                    print(f"⚠️ Warning: Failed to load existing recommendations, starting fresh. Error: {e}")
                    existing_data = []
            else:
                existing_data = []

            # Append the new entry
            existing_data.append(new_entry)

            # Save all to file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=4, ensure_ascii=False)

            print(f"✅ Appended recommendation to: {output_path}")
                


        def build_structured_recommendations(self, predictions: dict, days_ahead: int, base_date: datetime):
            """
            Build a structured dictionary suitable for JSON export from the predictions.
            """
            daily_list = []
            for day in range(days_ahead):
                day_date = base_date + timedelta(days=day + 1)
                weather_cond = predictions['weather_condition'][day]
                temp_max = predictions['temp_max'][day]
                temp_min = predictions['temp_min'][day]
                humidity_max = predictions['humidity_max'][day]
                humidity_min = predictions['humidity_min'][day]
                humidity_avg = (humidity_max + humidity_min) / 2

                irrigation = self.analyze_irrigation_needs(weather_cond, humidity_min, humidity_max, temp_max)
                pest = self.analyze_pest_disease_risk(weather_cond, humidity_max, temp_max, temp_min)
                planting = self.recommend_planting_activities(weather_cond, temp_max, temp_min, humidity_avg)

                daily_list.append({
                    "date": day_date.strftime("%Y-%m-%d"),
                    "day_name": day_date.strftime("%A"),
                    "weather": weather_cond,
                    "temp_max": temp_max,
                    "temp_min": temp_min,
                    "humidity_max": humidity_max,
                    "humidity_min": humidity_min,
                    "irrigation": {
                        "priority": irrigation['priority'],
                        "frequency": irrigation['frequency'],
                        "amount": irrigation['amount'],
                        "best_timing": irrigation['timing'],
                        "notes": irrigation['notes'],
                    },
                    "pest": {
                        "overall": pest['overall_risk'],
                        "pest": pest['pest_risk'],
                        "disease": pest['disease_risk'],
                        "threats": pest['specific_threats'],
                        "prevention": pest['preventive_measures'],
                    },
                    "planting": {
                        "conditions": planting['planting_suitability'],
                        "crops": planting['recommended_crops'],
                    }
                })

            # Weekly summary (similar to your report summary)
            weekly_summary = {
                "avg_temp_max": float(np.mean(predictions['temp_max'])),
                "avg_temp_min": float(np.mean(predictions['temp_min'])),
                "avg_humidity": float(np.mean([np.mean(predictions['humidity_max']), np.mean(predictions['humidity_min'])])),
                "rainy_days": sum(1 for cond in predictions['weather_condition'] if 'Rain' in cond or 'Drizzle' in cond),
                # Add more summary info if needed
            }

            return {
                "based_on_date": base_date.strftime("%Y-%m-%d"),
                "daily": daily_list,
                "summary": weekly_summary
            }


        def get_recommendations_with_safe_save(self,
                                       input_data: np.ndarray,
                                       days_ahead: int = 3,
                                       save_file: bool = True,
                                       filename: str = "agricultural_recommendations.txt",
                                       last_data_date: datetime = None) -> str:
    
            print(f"🌾 Generating agricultural recommendations for {days_ahead} days...")

            # Get predictions from your models
            predictions = self.predict_weather(input_data, days_ahead)

            # Use last_data_date or fallback to today
            if last_data_date is None:
                last_data_date = datetime.now()
                print("⚠️ Warning: last_data_date not provided, using current date for forecasts")

            # Generate predicted date list based on last_data_date
            predicted_dates = [(last_data_date + timedelta(days=i+1)).strftime("%Y-%m-%d") for i in range(days_ahead)]

            # Prepare the prediction log entry
            prediction_entry = {
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "based_on_data_up_to": last_data_date.strftime("%Y-%m-%d"),
                "predicted_dates": predicted_dates,
                "weather_condition": list(predictions["weather_condition"]),
                "temp_max": [float(v) for v in list(predictions["temp_max"])],
                "temp_min": [float(v) for v in list(predictions["temp_min"])],
                "humidity_max": [float(v) for v in list(predictions["humidity_max"])],
                "humidity_min": [float(v) for v in list(predictions["humidity_min"])],
            }

            # Append to JSON log file
            json_filename = "weather_predictions.json"
            try:
                if os.path.exists(json_filename):
                    with open(json_filename, "r", encoding="utf-8") as file:
                        data = json.load(file)
                else:
                    data = []

                data.append(prediction_entry)

                with open(json_filename, "w", encoding="utf-8") as file:
                    json.dump(data, file, indent=4, ensure_ascii=False)

                print(f"✅ Appended predictions to '{json_filename}'")
            except Exception as e:
                print(f"❌ Error saving predictions to JSON: {e}")


            # Build structured recommendations dictionary
            structured_recommendations = self.build_structured_recommendations(predictions, days_ahead, last_data_date)

            # Generate the detailed recommendations JSON file
            self.generate_recommendation_json(structured_recommendations, output_path="agricultural_recommendations.json")

            # Generate comprehensive recommendation report
            report = self.generate_comprehensive_report(predictions, days_ahead)

            


            # Save textual report
            if save_file:
                if not self.save_report(report, filename, encoding='utf-8', include_emojis=True):
                    print("🔄 Retrying with ASCII encoding...")
                    self.save_report(report, filename, encoding='ascii', include_emojis=False)

            return report