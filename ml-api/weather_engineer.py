
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

class WeatherFeatureEngineer:
        def __init__(self):
            self.cols_to_drop = [
                'dew_point_2m_max (°C)',
                'wind_speed_10m_max (km/h)',
                'surface_pressure_max (hPa)',
                'surface_pressure_min (hPa)',
                'wet_bulb_temperature_2m_max (°C)',
                'wet_bulb_temperature_2m_min (°C)',
                'soil_temperature_0_to_100cm_mean (°C)'
            ]
            self.low_importance_features = [
                'et0_fao_evapotranspiration_sum (mm)'
            ]
            self.desired_order = [
                'date', 'year', 'month', 'day', 'dayofweek', 'is_weekend', 'dayofyear', 'month_sin', 'month_cos',
                'dayofyear_sin', 'dayofyear_cos',

                'temperature_2m_max (°C)', 'temperature_2m_min (°C)', 'temp_range',
                'dew_point_2m_max (°C)', 'dew_point_2m_min (°C)', 'dew_point_range',
                'wet_bulb_temperature_2m_max (°C)', 'wet_bulb_temperature_2m_min (°C)',

                'relative_humidity_2m_max (%)', 'relative_humidity_2m_min (%)', 'humidity_range',

                'daylight_duration (s)', 'sunshine_duration (s)', 'sunshine_ratio', 'daylight_to_sunshine_ratio',

                'cloud_cover_min (%)', 'cloud_cover_max (%)',

                'rain_sum (mm)', 'precipitation_hours (h)', 'rain_today',

                'wind_speed_10m_max (km/h)', 'wind_speed_10m_min (km/h)', 'avg_wind_speed',
                'wind_gusts_10m_max (km/h)', 'wind_gusts_10m_min (km/h)', 'wind_gust_range', 'wind_variability',

                'surface_pressure_max (hPa)', 'surface_pressure_min (hPa)',
                'pressure_msl_max (hPa)', 'pressure_msl_min (hPa)', 'pressure_range',

                'soil_moisture_0_to_100cm_mean (m³/m³)', 'soil_temperature_0_to_100cm_mean (°C)',

                'et0_fao_evapotranspiration_sum (mm)',

                'weather_condition'  # target at the end
            ]

        def create_temporal_features(self, df):
            """Create temporal features ensuring all expected features are present"""
            # Ensure date column exists and is properly formatted
            if 'date' not in df.columns:
                # If no date column, create one with current date as starting point
                print("Warning: No 'date' column found. Creating synthetic dates.")
                df['date'] = pd.date_range(start='2024-01-01', periods=len(df), freq='D')
        
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
        
            # Handle any NaT values in date column
            if df['date'].isna().any():
                print("Warning: Found NaT values in date column. Forward filling...")
                df['date'] = df['date'].fillna(method='ffill')
                if df['date'].isna().any():  # If still NaT after ffill
                    df['date'] = df['date'].fillna(pd.Timestamp('2024-01-01'))
        
            # Basic calendar features
            df['day'] = df['date'].dt.day
            df['month'] = df['date'].dt.month
            df['year'] = df['date'].dt.year
            df['dayofweek'] = df['date'].dt.dayofweek       # Monday=0, Sunday=6
            df['is_weekend'] = (df['dayofweek'] >= 5).astype(int)  # Ensure it's int, not bool
        
            # Seasonal encodings (sin/cos to handle cyclic nature)
            df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
            df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
            df['dayofyear'] = df['date'].dt.dayofyear
            df['dayofyear_sin'] = np.sin(2 * np.pi * df['dayofyear'] / 365.25)
            df['dayofyear_cos'] = np.cos(2 * np.pi * df['dayofyear'] / 365.25)
        
            # Debug: Print to verify is_weekend is created
            print(f"DEBUG: is_weekend created. Shape: {df['is_weekend'].shape}, dtype: {df['is_weekend'].dtype}")
            print(f"DEBUG: is_weekend values: {df['is_weekend'].unique()}")
        
            return df

        def create_additional_features(self, df):
            """Create additional features with proper error handling"""
            # Temperature-related features
            if 'temperature_2m_max (°C)' in df.columns and 'temperature_2m_min (°C)' in df.columns:
                df['temp_range'] = df['temperature_2m_max (°C)'] - df['temperature_2m_min (°C)']

            # Wind-related features
            if 'wind_gusts_10m_max (km/h)' in df.columns and 'wind_gusts_10m_min (km/h)' in df.columns:
                df['wind_gust_range'] = df['wind_gusts_10m_max (km/h)'] - df['wind_gusts_10m_min (km/h)']
        
            if 'wind_speed_10m_max (km/h)' in df.columns and 'wind_speed_10m_min (km/h)' in df.columns:
                df['avg_wind_speed'] = (df['wind_speed_10m_max (km/h)'] + df['wind_speed_10m_min (km/h)']) / 2
                df['wind_variability'] = df['wind_speed_10m_max (km/h)'] - df['wind_speed_10m_min (km/h)']

            # Humidity & Dew Point
            if 'relative_humidity_2m_max (%)' in df.columns and 'relative_humidity_2m_min (%)' in df.columns:
                df['humidity_range'] = df['relative_humidity_2m_max (%)'] - df['relative_humidity_2m_min (%)']
        
            if 'dew_point_2m_max (°C)' in df.columns and 'dew_point_2m_min (°C)' in df.columns:
                df['dew_point_range'] = df['dew_point_2m_max (°C)'] - df['dew_point_2m_min (°C)']

            # Cloud & Sun
            if 'sunshine_duration (s)' in df.columns and 'daylight_duration (s)' in df.columns:
                # Avoid division by zero
                df['sunshine_ratio'] = df['sunshine_duration (s)'] / (df['daylight_duration (s)'] + 1e-8)

            # Rain/Precipitation
            if 'rain_sum (mm)' in df.columns:
                df['rain_today'] = df['rain_sum (mm)'].apply(lambda x: 1 if x > 0 else 0)

            # Pressure Features
            if 'surface_pressure_max (hPa)' in df.columns and 'surface_pressure_min (hPa)' in df.columns:
                df['pressure_range'] = df['surface_pressure_max (hPa)'] - df['surface_pressure_min (hPa)']

            # Daylight to Sunshine Ratio
            if 'daylight_duration (s)' in df.columns and 'sunshine_duration (s)' in df.columns:
                df['daylight_to_sunshine_ratio'] = df['daylight_duration (s)'] / (df['sunshine_duration (s)'] + 1)

            # Fill missing values after creating new features
            df = df.fillna(method='ffill').fillna(method='bfill')
        
            # If still NaN values, fill with median for numeric columns
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            for col in numeric_cols:
                if df[col].isna().any():
                    df[col] = df[col].fillna(df[col].median())

            return df

        def create_targeted_weather_features(self, df):
            """Create targeted weather features with proper feature preservation"""
            df_enhanced = df.copy()
    
            # Ensure date is datetime for proper sorting
            if 'date' in df_enhanced.columns:
                df_enhanced['date'] = pd.to_datetime(df_enhanced['date'])
                df_enhanced = df_enhanced.sort_values('date').reset_index(drop=True)
        
            print("Creating targeted weather features based on importance analysis...")
        
            # CRITICAL: Check if is_weekend exists before proceeding
            if 'is_weekend' not in df_enhanced.columns:
                print("ERROR: is_weekend not found! Recreating temporal features...")
                df_enhanced = self.create_temporal_features(df_enhanced)
        
            print("1. Engineering Tier 1 (Core Weather State) features...")
        
            tier1_features = [
                'cloud_cover_max (%)',
                'rain_sum (mm)', 
                'precipitation_hours (h)',
                'cloud_cover_min (%)'
            ]
    
            # Focus heavy engineering on these top features
            for feature in tier1_features:
                if feature in df_enhanced.columns:
                    feature_clean = feature.replace(' ', '_').replace('(%)', '').replace('(mm)', '').replace('(h)', '')
                
                    # Lagged features (1-7 days) - weather persistence is crucial
                    for lag in [1, 2, 3, 7]:
                        df_enhanced[f'{feature_clean}_lag_{lag}'] = df_enhanced[feature].shift(lag)
                
                    # Rolling statistics (key for weather patterns)
                    for window in [3, 7, 14]:
                        df_enhanced[f'{feature_clean}_rolling_mean_{window}d'] = df_enhanced[feature].rolling(window, min_periods=1).mean()
                        df_enhanced[f'{feature_clean}_rolling_std_{window}d'] = df_enhanced[feature].rolling(window, min_periods=1).std()
                        df_enhanced[f'{feature_clean}_rolling_max_{window}d'] = df_enhanced[feature].rolling(window, min_periods=1).max()
                
                    # Trend features
                    df_enhanced[f'{feature_clean}_3day_trend'] = df_enhanced[feature].diff(3)
                    df_enhanced[f'{feature_clean}_7day_trend'] = df_enhanced[feature].diff(7)
                
                    # Exponential weighted moving average
                    df_enhanced[f'{feature_clean}_ewm_3d'] = df_enhanced[feature].ewm(span=3, min_periods=1).mean()
                    df_enhanced[f'{feature_clean}_ewm_7d'] = df_enhanced[feature].ewm(span=7, min_periods=1).mean()
        
            # Special handling for rain_today (binary feature)
            if 'rain_today' in df_enhanced.columns:
                # Rain persistence patterns
                df_enhanced['rain_today_lag_1'] = df_enhanced['rain_today'].shift(1)
                df_enhanced['rain_today_lag_2'] = df_enhanced['rain_today'].shift(2)
                df_enhanced['rain_today_lag_3'] = df_enhanced['rain_today'].shift(3)
            
                # Rolling rain frequency
                df_enhanced['rain_frequency_7d'] = df_enhanced['rain_today'].rolling(7, min_periods=1).mean()
                df_enhanced['rain_frequency_14d'] = df_enhanced['rain_today'].rolling(14, min_periods=1).mean()
            
                # Consecutive rain days
                df_enhanced['consecutive_rain_days'] = (
                    df_enhanced['rain_today'].groupby(
                        (df_enhanced['rain_today'] != df_enhanced['rain_today'].shift()).cumsum()
                    ).cumsum()
                )
        
                # Days since last rain
                rain_dates = df_enhanced[df_enhanced['rain_today'] == 1].index
                df_enhanced['days_since_rain'] = np.nan
                for i in df_enhanced.index:
                    prev_rain = rain_dates[rain_dates < i]
                    if len(prev_rain) > 0:
                        df_enhanced.loc[i, 'days_since_rain'] = i - prev_rain.max()
                df_enhanced['days_since_rain'] = df_enhanced['days_since_rain'].fillna(30)  # Cap at 30 days
        
            print("2. Engineering Tier 2 (Physical Variables) features...")
        
            tier2_features = [
                'temp_range',
                'relative_humidity_2m_min (%)',
                'temperature_2m_max (°C)',
                'humidity_range',
                'relative_humidity_2m_max (%)'
            ]
        
            # Lighter engineering for these features
            for feature in tier2_features:
                if feature in df_enhanced.columns:
                    feature_clean = feature.replace(' ', '_').replace('(%)', '').replace('(°C)', '')
                
                    # Key lagged features only
                    for lag in [1, 3, 7]:
                        df_enhanced[f'{feature_clean}_lag_{lag}'] = df_enhanced[feature].shift(lag)
                
                    # Essential rolling statistics
                    df_enhanced[f'{feature_clean}_rolling_mean_7d'] = df_enhanced[feature].rolling(7, min_periods=1).mean()
                    df_enhanced[f'{feature_clean}_rolling_std_7d'] = df_enhanced[feature].rolling(7, min_periods=1).std()
                
                    # Trend features
                    df_enhanced[f'{feature_clean}_7day_trend'] = df_enhanced[feature].diff(7)
        
            print("3. Creating interaction features...")
        
            # High-impact feature interactions
            if 'cloud_cover_max (%)' in df_enhanced.columns and 'rain_sum (mm)' in df_enhanced.columns:
                df_enhanced['cloud_rain_interaction'] = df_enhanced['cloud_cover_max (%)'] * df_enhanced['rain_sum (mm)']
        
            if 'temp_range' in df_enhanced.columns and 'relative_humidity_2m_min (%)' in df_enhanced.columns:
                df_enhanced['temp_humidity_interaction'] = df_enhanced['temp_range'] * df_enhanced['relative_humidity_2m_min (%)']
        
            if 'precipitation_hours (h)' in df_enhanced.columns and 'cloud_cover_max (%)' in df_enhanced.columns:
                df_enhanced['precip_cloud_interaction'] = df_enhanced['precipitation_hours (h)'] * df_enhanced['cloud_cover_max (%)']
        
            print("4. Creating weather pattern features...")
        
            # Weather stability indicators
            if 'cloud_cover_max (%)' in df_enhanced.columns:
                df_enhanced['cloud_volatility_7d'] = df_enhanced['cloud_cover_max (%)'].rolling(7, min_periods=1).std()
        
            if 'rain_sum (mm)' in df_enhanced.columns:
                df_enhanced['rain_volatility_7d'] = df_enhanced['rain_sum (mm)'].rolling(7, min_periods=1).std()
        
            # Seasonal anomalies for top features
            if 'temperature_2m_max (°C)' in df_enhanced.columns and 'dayofyear' in df_enhanced.columns:
                df_enhanced['temp_seasonal_anomaly'] = (
                    df_enhanced['temperature_2m_max (°C)'] - 
                    df_enhanced.groupby('dayofyear')['temperature_2m_max (°C)'].transform('mean')
                )
        
            print("5. Optimizing feature set...")
    
            # Identify and remove low-importance features (keeping time features)
            low_importance_features = [
                'et0_fao_evapotranspiration_sum (mm)',  # Remove if score < 0.1 and not in top tier
            ]
        
            # Remove low-importance features (but keep ALL time features)
            time_related_keywords = ['year', 'month', 'day', 'dayof', 'weekend', 'sin', 'cos']
    
            features_to_drop = []
            for feature in low_importance_features:
                if feature in df_enhanced.columns:
                    # Don't drop if it's a time-related feature
                    if not any(keyword in feature.lower() for keyword in time_related_keywords):
                        features_to_drop.append(feature)
        
            if features_to_drop:
                print(f"Removing {len(features_to_drop)} low-importance non-temporal features...")
                df_enhanced = df_enhanced.drop(columns=features_to_drop)
        
            # CRITICAL: Final check for is_weekend
            if 'is_weekend' not in df_enhanced.columns:
                print("CRITICAL ERROR: is_weekend missing after feature engineering!")
                # Recreate it if missing
                if 'date' in df_enhanced.columns:
                    df_enhanced['date'] = pd.to_datetime(df_enhanced['date'])
                    df_enhanced['dayofweek'] = df_enhanced['date'].dt.dayofweek
                    df_enhanced['is_weekend'] = (df_enhanced['dayofweek'] >= 5).astype(int)
                    print("is_weekend recreated!")
        
            original_features = len(df.columns)
            final_features = len(df_enhanced.columns)
            new_features = final_features - original_features
            
            print(f"\n{'='*50}")
            print("TARGETED FEATURE ENGINEERING SUMMARY")
            print(f"{'='*50}")
            print(f"Original features: {original_features}")
            print(f"Final features: {final_features}")
            print(f"New features added: {new_features}")
            print(f"Features removed: {len(features_to_drop)}")
        
            # Feature breakdown
            tier1_count = len([col for col in df_enhanced.columns if any(t1 in col for t1 in ['cloud_cover', 'rain_', 'precipitation'])])
            tier2_count = len([col for col in df_enhanced.columns if any(t2 in col for t2 in ['temp_', 'humidity_'])])
            time_count = len([col for col in df_enhanced.columns if any(t in col.lower() for t in time_related_keywords)])
        
            print(f"\nFeature Categories:")
            print(f"  Weather State (Tier 1): ~{tier1_count} features")
            print(f"  Physical Variables (Tier 2): ~{tier2_count} features") 
            print(f"  Temporal Features: {time_count} features")
            print(f"  Other Features: {final_features - tier1_count - tier2_count - time_count} features")
        
            # Final verification of critical features
            critical_features = ['is_weekend', 'year', 'month', 'day', 'dayofweek']
            missing_critical = [f for f in critical_features if f not in df_enhanced.columns]
            if missing_critical:
                print(f"WARNING: Missing critical features: {missing_critical}")
            else:
                print("✅ All critical temporal features present")
        
            return df_enhanced

        def drop_unimportant_columns(self, df: pd.DataFrame) -> pd.DataFrame:
            """Drop unimportant columns while preserving critical features"""
            # Don't drop temporal features even if they're in cols_to_drop
            temporal_features = ['year', 'month', 'day', 'dayofweek', 'is_weekend', 'dayofyear', 
                               'month_sin', 'month_cos', 'dayofyear_sin', 'dayofyear_cos']
        
            cols_to_drop_safe = [col for col in self.cols_to_drop 
                               if col not in temporal_features and col in df.columns]
        
            if cols_to_drop_safe:
                print(f"Dropping {len(cols_to_drop_safe)} unimportant columns: {cols_to_drop_safe}")
                df = df.drop(columns=cols_to_drop_safe)
        
            return df

        def transform(self, df: pd.DataFrame) -> pd.DataFrame:
            """Main transformation pipeline with feature preservation"""
            print("Starting feature transformation pipeline...")
        
            # 🧭 Map weather_code to human-readable weather_condition
            weather_conditions = {
                0: "Clear Sky ☀️",
                1: "Mainly Clear 🌤",
                2: "Partly Cloudy ⛅",
                3: "Cloudy ☁️",
                45: "Fog 🌫",
                48: "Fog 🌫",
                51: "Light Drizzle 🌦",
                53: "Moderate Drizzle 🌧",
                55: "Heavy Drizzle 🌧",
                61: "Light Rain 🌦",
                63: "Moderate Rain 🌧",
                65: "Heavy Rain 🌧",
                71: "Light Snow ❄️",
                73: "Moderate Snow ❄️",
                75: "Heavy Snow ❄️",
                95: "Thunderstorm ⛈"
            }
        
            if 'weather_code' in df.columns:
                df['weather_condition'] = df['weather_code'].map(weather_conditions)
                df = df.drop(columns=['weather_code'], errors='ignore')
        
            # Create temporal features first
            df = self.create_temporal_features(df)
        
            # Verify is_weekend exists
            if 'is_weekend' not in df.columns:
                raise ValueError("Critical error: is_weekend not created in temporal features!")
        
            # Create additional features
            df = self.create_additional_features(df)
        
            # Reorder columns safely (ignore missing columns)
            cols_in_df = [col for col in self.desired_order if col in df.columns]
            remaining_cols = [col for col in df.columns if col not in cols_in_df]
            df = df[cols_in_df + remaining_cols]  # Add any new columns at the end
        
            # Drop unimportant columns (but preserve temporal features)
            df = self.drop_unimportant_columns(df)
        
            # Final verification before advanced feature engineering
            if 'is_weekend' not in df.columns:
                raise ValueError("Critical error: is_weekend lost during basic transformations!")
        
            # Create targeted weather features
            df = self.create_targeted_weather_features(df)
        
            # Final check
            if 'is_weekend' not in df.columns:
                raise ValueError("Critical error: is_weekend lost during targeted feature engineering!")
        
            print("✅ Feature transformation completed successfully!")
            print(f"Final dataframe shape: {df.shape}")
            print(f"is_weekend present: {'is_weekend' in df.columns}")
        
            return df

        def generate_model_inputs(self, df: pd.DataFrame, model_type: str, scaler_X=None):
            """Generate model inputs with proper feature handling"""
            df = df.copy()
        
            # Ensure is_weekend exists
            if 'is_weekend' not in df.columns:
                print("WARNING: is_weekend missing in generate_model_inputs. Recreating...")
                if 'date' in df.columns:
                    df['date'] = pd.to_datetime(df['date'])
                    df['dayofweek'] = df['date'].dt.dayofweek
                    df['is_weekend'] = (df['dayofweek'] >= 5).astype(int)
                else:
                    # If no date, assume weekday
                    df['is_weekend'] = 0

            if model_type == 'weather_condition':
                # Classification model handling
                df['weather_condition'] = df['weather_condition'].replace({
                    'Mainly Clear': 'Partly Clear',
                    'Partly Cloudy': 'Partly Clear'
                })

                df = df.dropna(subset=['weather_condition'])

                # Fill missing numerics
                numeric_cols = df.select_dtypes(include=[np.number]).columns
                for col in numeric_cols:
                    df[col] = df[col].fillna(method='ffill').fillna(method='bfill')
                    df[col] = df[col].interpolate().fillna(df[col].median())

                # Encode labels
                from sklearn.preprocessing import LabelEncoder
                from sklearn.utils.class_weight import compute_class_weight
            
                label_encoder = LabelEncoder()
                encoded_col = 'weather_condition_encoded'
                df[encoded_col] = label_encoder.fit_transform(df['weather_condition'])

                # Compute class weights
                unique_classes = df[encoded_col].unique()
                class_weights = compute_class_weight('balanced', classes=unique_classes, y=df[encoded_col])
                class_weight_dict = dict(zip(unique_classes, class_weights))

                # Select features (exclude date + original & encoded target)
                feature_cols = [col for col in df.columns if col not in ['date', 'weather_condition', encoded_col]]

                # Scale features
                from sklearn.preprocessing import StandardScaler
                scaler_X = StandardScaler()
                df[feature_cols] = scaler_X.fit_transform(df[feature_cols])

                X = df[feature_cols].values
                y = df[encoded_col].values

                return X, y, feature_cols, label_encoder, class_weight_dict, scaler_X

            else:
                # Regression models
                model_exclude_map = {
                    'temp_max': ['date', 'weather_condition', 'relative_humidity_2m_max (%)',
                                'relative_humidity_2m_min (%)', 'temperature_2m_min (°C)', 'temperature_2m_max (°C)'],
                
                    'temp_min': ['date', 'weather_condition', 'temperature_2m_max (°C)', 
                                'relative_humidity_2m_max (%)', 'relative_humidity_2m_min (%)', 'temperature_2m_min (°C)'],
                
                    'humidity_max': ['date', 'weather_condition', 'temperature_2m_max (°C)', 'temperature_2m_min (°C)',
                                    'relative_humidity_2m_min (%)', 'relative_humidity_2m_max (%)'],
                
                    'humidity_min': ['date', 'weather_condition', 'temperature_2m_max (°C)', 'temperature_2m_min (°C)',
                                    'relative_humidity_2m_min (%)', 'relative_humidity_2m_max (%)']
                }

                if model_type not in model_exclude_map:
                    raise ValueError(f"Unknown model_type: {model_type}")

                exclude_cols = model_exclude_map[model_type]

                # Select features
                feature_cols = [col for col in df.columns if col not in exclude_cols]
                numeric_feature_cols = df[feature_cols].select_dtypes(include=[np.number]).columns.tolist()

                # Verify is_weekend is in the feature set
                if 'is_weekend' not in numeric_feature_cols:
                    if 'is_weekend' in df.columns:
                        print(f"WARNING: is_weekend exists but not in numeric_feature_cols. Adding it...")
                        numeric_feature_cols.append('is_weekend')
                    else:
                        print(f"ERROR: is_weekend missing for model {model_type}!")
                        raise ValueError(f"is_weekend feature missing for model {model_type}")

                # Clean missing values
                df[numeric_feature_cols] = (
                    df[numeric_feature_cols]
                    .fillna(method='ffill')
                    .fillna(method='bfill')
                    .interpolate()
                    .fillna(df[numeric_feature_cols].median())
                )

                # Scale if scaler provided
                if scaler_X:
                    X_scaled = scaler_X.transform(df[numeric_feature_cols])
                    return X_scaled, numeric_feature_cols
                else:
                    return df[numeric_feature_cols].values, numeric_feature_cols

