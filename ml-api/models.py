
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



class ImprovedSlidingWindowModel:
    def __init__(self, df, sequence_length=10, forecast_horizon=3):
        
        self.df = df.copy()
        self.forecast_horizon = forecast_horizon
        self.sequence_length = sequence_length
        self.scaler_X = None
        self.label_encoder = None
        self.model = None
        self.class_weights = None
        self.tuner = None
        self.best_hps = None
        
        # Improved thresholds for better balance
        self.minority_threshold = 0.08   # Very rare classes
        self.balanced_threshold = 0.20   # Medium frequency classes
        # Above 20% = majority classes
        
    def preprocess_data(self, target_col='weather_condition'):
        
        print("🧹 Enhanced preprocessing...")
        df = self.df.copy()
        
        # Handle missing values
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if col != target_col:
                df[col] = df[col].fillna(method='ffill').fillna(method='bfill')
                df[col] = df[col].interpolate(method='linear')
                df[col].fillna(df[col].median(), inplace=True)
        
        # Remove rows with missing target
        df = df.dropna(subset=[target_col])
        # 🔄 Merge specific weather classes
        df[target_col] = df[target_col].replace({
            'Mainly Clear 🌤': 'Partly Clear 🌤/⛅',
            'Partly Cloudy ⛅': 'Partly Clear 🌤/⛅'
        })
        
        # Three-tier class analysis
        class_counts = df[target_col].value_counts()
        total_samples = len(df)
        print(f"Original class distribution:\n{class_counts}")
        print(f"Class percentages:\n{(class_counts/total_samples*100).round(2)}")
        
        # Categorize classes into three tiers
        self.minority_classes = []    # < 8%
        self.balanced_classes = []    # 8% - 20%  
        self.majority_classes = []    # > 20%
        
        for class_name, count in class_counts.items():
            percentage = count / total_samples
            if percentage < self.minority_threshold:
                self.minority_classes.append(class_name)
            elif percentage < self.balanced_threshold:
                self.balanced_classes.append(class_name)
            else:
                self.majority_classes.append(class_name)
        
        print(f"\nMinority classes (<{self.minority_threshold*100}%): {self.minority_classes}")
        print(f"Balanced classes ({self.minority_threshold*100}%-{self.balanced_threshold*100}%): {self.balanced_classes}")
        print(f"Majority classes (>{self.balanced_threshold*100}%): {self.majority_classes}")
        
        # Encode target
        self.label_encoder = LabelEncoder()
        df[target_col + '_encoded'] = self.label_encoder.fit_transform(df[target_col])
        
        # Feature engineering
        feature_cols = [col for col in df.columns if col not in ['date', target_col, target_col + '_encoded']]
        
        # Scale features
        self.scaler_X = StandardScaler()
        df[feature_cols] = self.scaler_X.fit_transform(df[feature_cols])
        
        # Calculate class weights
        unique_classes = np.unique(df[target_col + '_encoded'])
        self.class_weights = compute_class_weight('balanced', classes=unique_classes, y=df[target_col + '_encoded'])
        self.class_weight_dict = dict(zip(unique_classes, self.class_weights))
        
        # Store processed data
        self.df = df
        self.feature_cols = feature_cols
        self.target_col = target_col + '_encoded'
        self.original_target_col = target_col
        
        return df

    def create_improved_sliding_windows(self):
        
        print(f"\n🪟 Creating improved sliding windows with controlled rebalancing...")
        
        X, y = [], []
        data = self.df
        features = data[self.feature_cols].values
        target = data[self.target_col].values
        
        # Get class IDs for each tier
        minority_class_ids = [self.label_encoder.transform([cls])[0] 
                             for cls in self.minority_classes 
                             if cls in self.label_encoder.classes_]
        balanced_class_ids = [self.label_encoder.transform([cls])[0] 
                             for cls in self.balanced_classes 
                             if cls in self.label_encoder.classes_]
        majority_class_ids = [self.label_encoder.transform([cls])[0] 
                             for cls in self.majority_classes 
                             if cls in self.label_encoder.classes_]
        
        print(f"Minority class IDs: {minority_class_ids}")
        print(f"Balanced class IDs: {balanced_class_ids}")
        print(f"Majority class IDs: {majority_class_ids}")
        
        # Strategy 1: Intensive sampling for minority classes
        minority_windows = 0
        print("Creating intensive windows for minority classes...")
        
        for i in range(len(target)):
            if target[i] in minority_class_ids:
                # Create 7 overlapping windows around each minority event
                for offset in range(-3, 4):
                    start_idx = max(0, i - self.sequence_length + offset)
                    end_idx = start_idx + self.sequence_length + self.forecast_horizon
                    
                    if end_idx <= len(data):
                        X_seq = features[start_idx:start_idx + self.sequence_length]
                        y_seq = target[start_idx + self.sequence_length:end_idx]
                        
                        if len(X_seq) == self.sequence_length and len(y_seq) == self.forecast_horizon:
                            X.append(X_seq)
                            y.append(y_seq)
                            minority_windows += 1
        
        # Strategy 2: Moderate sampling for balanced classes
        balanced_windows = 0
        print("Creating moderate windows for balanced classes...")
        
        for i in range(0, len(data) - self.sequence_length - self.forecast_horizon + 1, 2):
            y_seq = target[i + self.sequence_length:i + self.sequence_length + self.forecast_horizon]
            
            # Check if sequence contains balanced classes
            if any(cls_id in balanced_class_ids for cls_id in y_seq):
                X_seq = features[i:i + self.sequence_length]
                X.append(X_seq)
                y.append(y_seq)
                balanced_windows += 1
        
        # Strategy 3: Controlled sampling for majority classes
        majority_windows = 0
        print("Creating controlled windows for majority classes...")
        
        # Calculate target number of majority windows (don't let them dominate)
        target_majority_windows = max(minority_windows * 1.5, balanced_windows * 0.8)
        
        majority_stride = max(3, int((len(data) - self.sequence_length - self.forecast_horizon) / target_majority_windows))
        
        for i in range(0, len(data) - self.sequence_length - self.forecast_horizon + 1, majority_stride):
            if majority_windows >= target_majority_windows:
                break
                
            y_seq = target[i + self.sequence_length:i + self.sequence_length + self.forecast_horizon]
            
            # Only add if it's primarily majority class and we haven't hit our limit
            if all(cls_id in majority_class_ids for cls_id in y_seq):
                X_seq = features[i:i + self.sequence_length]
                X.append(X_seq)
                y.append(y_seq)
                majority_windows += 1
        
        # Strategy 4: Add transitional windows (sequences that show class changes)
        transition_windows = 0
        print("Adding transitional windows...")
        
        for i in range(len(target) - self.forecast_horizon):
            current_class = target[i]
            future_classes = target[i+1:i+self.forecast_horizon+1]
            
            # Look for transitions from/to minority classes
            if (current_class in minority_class_ids or any(cls in minority_class_ids for cls in future_classes)):
                start_idx = max(0, i - self.sequence_length + 1)
                if start_idx + self.sequence_length + self.forecast_horizon <= len(data):
                    X_seq = features[start_idx:start_idx + self.sequence_length]
                    y_seq = target[start_idx + self.sequence_length:start_idx + self.sequence_length + self.forecast_horizon]
                    
                    if len(X_seq) == self.sequence_length and len(y_seq) == self.forecast_horizon:
                        X.append(X_seq)
                        y.append(y_seq)
                        transition_windows += 1
        
        X = np.array(X)
        y = np.array(y)
        
        print(f"\nWindow creation results:")
        print(f"Minority class windows: {minority_windows}")
        print(f"Balanced class windows: {balanced_windows}")
        print(f"Majority class windows: {majority_windows}")
        print(f"Transition windows: {transition_windows}")
        print(f"Total windows: {len(X)}")
        
        # Analyze final distribution
        final_dist = Counter(y.flatten())
        total_predictions = len(y.flatten())
        print(f"\nFinal class distribution:")
        for class_id, count in sorted(final_dist.items()):
            class_name = self.label_encoder.inverse_transform([class_id])[0]
            percentage = (count / total_predictions) * 100
            print(f"  {class_name}: {count} ({percentage:.1f}%)")
        
        return X, y
    
    def add_targeted_augmentation(self, X, y, augment_factor=1):
        
        print(f"\n🔄 Adding targeted augmentation for minority classes...")
        
        minority_class_ids = [self.label_encoder.transform([cls])[0] 
                             for cls in self.minority_classes 
                             if cls in self.label_encoder.classes_]
        
        X_aug = list(X)
        y_aug = list(y)
        augmented_count = 0
        
        for i in range(len(X)):
            # Check if sequence contains minority classes
            if any(cls_id in minority_class_ids for cls_id in y[i]):
                for _ in range(augment_factor):
                    # Add controlled noise to features
                    noise_scale = 0.01  # Very small noise
                    noise = np.random.normal(0, noise_scale, X[i].shape)
                    X_noisy = X[i] + noise
                    
                    # Add small temporal shifts occasionally
                    if np.random.random() < 0.3:
                        shift = np.random.randint(-1, 2)
                        if shift != 0:
                            X_shifted = np.roll(X[i], shift, axis=0)
                            X_aug.append(X_shifted)
                        else:
                            X_aug.append(X_noisy)
                    else:
                        X_aug.append(X_noisy)
                    
                    y_aug.append(y[i])
                    augmented_count += 1
        
        print(f"Added {augmented_count} augmented sequences for minority classes")
        return np.array(X_aug), np.array(y_aug)
    
    def focal_loss(self, alpha=0.25, gamma=2.0):
        
        def focal_loss_fn(y_true, y_pred):
            epsilon = K.epsilon()
            y_pred = K.clip(y_pred, epsilon, 1. - epsilon)
            
            # Cross entropy
            ce = -y_true * K.log(y_pred)
            
            # Focal weight: (1-p)^gamma
            p_t = K.sum(y_true * y_pred, axis=-1, keepdims=True)
            focal_weight = K.pow((1 - p_t), gamma)
            
            # Alpha weighting
            alpha_t = y_true * alpha + (1 - y_true) * (1 - alpha)
            
            # Final focal loss
            focal_loss = alpha_t * focal_weight * ce
            
            return K.mean(K.sum(focal_loss, axis=-1))
        
        return focal_loss_fn
    
    def build_enhanced_model(self, input_shape, num_classes):
        
        model = Sequential([
            # First LSTM layer - larger for pattern recognition
            LSTM(256, return_sequences=True, input_shape=input_shape,
                 kernel_regularizer=l2(0.001), 
                 dropout=0.2, recurrent_dropout=0.2),
            BatchNormalization(),
            
            # Second LSTM layer - medium size
            LSTM(128, return_sequences=True,
                 kernel_regularizer=l2(0.001),
                 dropout=0.2, recurrent_dropout=0.2),
            BatchNormalization(),
            
            # Third LSTM layer - smaller for final processing
            LSTM(64, return_sequences=False,
                 kernel_regularizer=l2(0.001),
                 dropout=0.2, recurrent_dropout=0.2),
            BatchNormalization(),
            Dropout(0.3),
            
            # Dense layers with progressive size reduction
            Dense(256, activation='relu', kernel_regularizer=l2(0.001)),
            BatchNormalization(),
            Dropout(0.4),
            
            Dense(128, activation='relu', kernel_regularizer=l2(0.001)),
            Dropout(0.3),
            
            Dense(64, activation='relu'),
            Dropout(0.2),
            
            # Output layer
            Dense(self.forecast_horizon * num_classes, activation='softmax'),
        ])
        
        # Reshape to (batch_size, forecast_horizon, num_classes)
        model.add(tf.keras.layers.Reshape((self.forecast_horizon, num_classes)))
        return model
    
    def build_hypermodel(self, hp):
        
        # Tunable hyperparameters
        lstm1_units = hp.Int('lstm1_units', min_value=64, max_value=512, step=64)
        lstm2_units = hp.Int('lstm2_units', min_value=32, max_value=256, step=32)
        lstm3_units = hp.Int('lstm3_units', min_value=16, max_value=128, step=16)
        
        dense1_units = hp.Int('dense1_units', min_value=64, max_value=512, step=64)
        dense2_units = hp.Int('dense2_units', min_value=32, max_value=256, step=32)
        dense3_units = hp.Int('dense3_units', min_value=16, max_value=128, step=16)
        
        dropout_rate = hp.Float('dropout_rate', min_value=0.1, max_value=0.5, step=0.1)
        recurrent_dropout = hp.Float('recurrent_dropout', min_value=0.1, max_value=0.4, step=0.1)
        l2_reg = hp.Float('l2_reg', min_value=1e-4, max_value=1e-2, sampling='LOG')
        
        learning_rate = hp.Float('learning_rate', min_value=1e-4, max_value=1e-2, sampling='LOG')
        focal_alpha = hp.Float('focal_alpha', min_value=0.1, max_value=0.5, step=0.1)
        focal_gamma = hp.Float('focal_gamma', min_value=1.0, max_value=3.0, step=0.5)
        
        num_classes = len(self.label_encoder.classes_)
        input_shape = (self.sequence_length, len(self.feature_cols))
        
        model = Sequential([
            # First LSTM layer
            LSTM(lstm1_units, return_sequences=True, input_shape=input_shape,
                 kernel_regularizer=l2(l2_reg), 
                 dropout=dropout_rate, recurrent_dropout=recurrent_dropout),
            BatchNormalization(),
            
            # Second LSTM layer
            LSTM(lstm2_units, return_sequences=True,
                 kernel_regularizer=l2(l2_reg),
                 dropout=dropout_rate, recurrent_dropout=recurrent_dropout),
            BatchNormalization(),
            
            # Third LSTM layer
            LSTM(lstm3_units, return_sequences=False,
                 kernel_regularizer=l2(l2_reg),
                 dropout=dropout_rate, recurrent_dropout=recurrent_dropout),
            BatchNormalization(),
            Dropout(dropout_rate),
            
            # Dense layers
            Dense(dense1_units, activation='relu', kernel_regularizer=l2(l2_reg)),
            BatchNormalization(),
            Dropout(dropout_rate + 0.1),
            
            Dense(dense2_units, activation='relu', kernel_regularizer=l2(l2_reg)),
            Dropout(dropout_rate),
            
            Dense(dense3_units, activation='relu'),
            Dropout(dropout_rate - 0.1),
            
            # Output layer
            Dense(self.forecast_horizon * num_classes, activation='softmax'),
        ])
        
        # Reshape to (batch_size, forecast_horizon, num_classes)
        model.add(tf.keras.layers.Reshape((self.forecast_horizon, num_classes)))
        
        # Compile with tuned hyperparameters
        model.compile(
            optimizer=Adam(learning_rate=learning_rate, clipnorm=1.0),
            loss=self.focal_loss(alpha=focal_alpha, gamma=focal_gamma),
            metrics=['accuracy']
        )
        
        return model
    
    def hyperparameter_tuning(self, X_train, y_train, max_trials=20):
        
        print("\n" + "="*70)
        print("🔧 HYPERPARAMETER TUNING")
        print("="*70)
        
        # Initialize tuner
        self.tuner = kt.RandomSearch(
            self.build_hypermodel,
            objective='val_accuracy',
            max_trials=max_trials,
            directory='weather_tuning',
            project_name='lstm_weather_forecast'
        )
        
        # Search callbacks
        stop_early = EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)
        
        print(f"Starting hyperparameter search with {max_trials} trials...")
        print("This may take a while depending on your hardware...")
        
        # Perform search
        self.tuner.search(
            X_train, y_train,
            epochs=15,
            batch_size=32,
            validation_split=0.2,
            callbacks=[stop_early],
            verbose=1
        )
        
        # Get best hyperparameters
        self.best_hps = self.tuner.get_best_hyperparameters(num_trials=1)[0]
        
        print("\n🏆 BEST HYPERPARAMETERS FOUND:")
        print("="*50)
        print(f"LSTM Layer 1 Units: {self.best_hps.get('lstm1_units')}")
        print(f"LSTM Layer 2 Units: {self.best_hps.get('lstm2_units')}")
        print(f"LSTM Layer 3 Units: {self.best_hps.get('lstm3_units')}")
        print(f"Dense Layer 1 Units: {self.best_hps.get('dense1_units')}")
        print(f"Dense Layer 2 Units: {self.best_hps.get('dense2_units')}")
        print(f"Dense Layer 3 Units: {self.best_hps.get('dense3_units')}")
        print(f"Dropout Rate: {self.best_hps.get('dropout_rate'):.3f}")
        print(f"Recurrent Dropout: {self.best_hps.get('recurrent_dropout'):.3f}")
        print(f"L2 Regularization: {self.best_hps.get('l2_reg'):.6f}")
        print(f"Learning Rate: {self.best_hps.get('learning_rate'):.6f}")
        print(f"Focal Loss Alpha: {self.best_hps.get('focal_alpha'):.3f}")
        print(f"Focal Loss Gamma: {self.best_hps.get('focal_gamma'):.1f}")
        
        # Build best model
        self.model = self.tuner.hypermodel.build(self.best_hps)
        
        return self.best_hps
    
    def train_improved_model(self, use_augmentation=True, use_hypertuning=True, max_trials=20):
        
        print("\n" + "="*70)
        print("TRAINING IMPROVED SLIDING WINDOW + REBALANCING MODEL")
        if use_hypertuning:
            print("WITH HYPERPARAMETER TUNING")
        print("="*70)
        
        # Create improved sliding windows
        X, y = self.create_improved_sliding_windows()
        
        # Add targeted augmentation if requested
        if use_augmentation:
            X, y = self.add_targeted_augmentation(X, y, augment_factor=1)
        
        num_classes = len(self.label_encoder.classes_)
        
        if len(X) == 0:
            raise ValueError("No sequences created!")
        
        print(f"\nFinal training data: X={X.shape}, y={y.shape}")
        print(f"Number of classes: {num_classes}")
        
        # Convert to categorical
        y_onehot = to_categorical(y, num_classes=num_classes)
        
        # Stratified train-test split
        sss = StratifiedShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
        train_idx, test_idx = next(sss.split(X, y[:, 0]))
        
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y_onehot[train_idx], y_onehot[test_idx]
        
        print(f"Training samples: {len(X_train)}, Test samples: {len(X_test)}")
        
        # Hyperparameter tuning
        if use_hypertuning:
            self.hyperparameter_tuning(X_train, y_train, max_trials=max_trials)
        else:
            # Build default model
            self.model = self.build_enhanced_model((self.sequence_length, X.shape[2]), num_classes)
            
            # Use default focal loss
            self.model.compile(
                optimizer=Adam(learning_rate=0.0005, clipnorm=1.0),
                loss=self.focal_loss(alpha=0.25, gamma=2.0),
                metrics=['accuracy']
            )
        
        # Enhanced callbacks
        callbacks = [
            EarlyStopping(monitor='val_loss', patience=20, restore_best_weights=True, verbose=1),
            ReduceLROnPlateau(monitor='val_loss', factor=0.3, patience=10, min_lr=1e-7, verbose=1)
        ]
        
        # Train model with best hyperparameters
        print(f"\nTraining {'hypertuned' if use_hypertuning else 'default'} model...")
        history = self.model.fit(
            X_train, y_train,
            epochs=200,
            batch_size=32,
            validation_split=0.2,
            callbacks=callbacks,
            verbose=1
        )
        
        # Evaluate
        print(f"\nEvaluating {'hypertuned' if use_hypertuning else 'default'} model...")
        y_pred_prob = self.model.predict(X_test, verbose=0)
        y_pred = np.argmax(y_pred_prob, axis=-1)
        y_true = np.argmax(y_test, axis=-1)
        
        return self.evaluate_improved_results(y_true, y_pred, history, use_hypertuning)
    
    def evaluate_improved_results(self, y_true, y_pred, history, hypertuned=False):
        """
        Comprehensive evaluation with class-tier analysis
        """
        model_type = "HYPERTUNED" if hypertuned else "DEFAULT"
        print("\n" + "="*70)
        print(f"IMPROVED SLIDING WINDOW + REBALANCING RESULTS ({model_type})")
        print("="*70)
        
        # Overall accuracy
        overall_acc = accuracy_score(y_true.flatten(), y_pred.flatten())
        print(f"Overall Test Accuracy: {overall_acc:.4f}")
        
        # Daily accuracies
        daily_accuracies = []
        for day in range(self.forecast_horizon):
            day_acc = accuracy_score(y_true[:, day], y_pred[:, day])
            daily_accuracies.append(day_acc)
            print(f"Day {day+1} accuracy: {day_acc:.4f}")
        
        # Detailed classification report for Day 1
        print(f"\nDetailed Classification Report (Day 1):")
        print("-" * 70)
        target_names = self.label_encoder.classes_
        report = classification_report(y_true[:, 0], y_pred[:, 0], 
                                     target_names=target_names, 
                                     zero_division=0,
                                     output_dict=True)
        print(classification_report(y_true[:, 0], y_pred[:, 0], 
                                  target_names=target_names, 
                                  zero_division=0))
        
        # Class-tier performance analysis
        print(f"\n🎯 CLASS-TIER PERFORMANCE ANALYSIS:")
        print("="*70)
        
        for tier_name, class_list in [
            ("MINORITY", self.minority_classes),
            ("BALANCED", self.balanced_classes), 
            ("MAJORITY", self.majority_classes)
        ]:
            print(f"\n{tier_name} CLASSES:")
            print("-" * 40)
            tier_f1_scores = []
            tier_recalls = []
            tier_precisions = []
            
            for class_name in class_list:
                if class_name in report:
                    metrics = report[class_name]
                    f1 = metrics['f1-score']
                    precision = metrics['precision']
                    recall = metrics['recall']
                    support = metrics['support']
                    
                    tier_f1_scores.append(f1)
                    tier_recalls.append(recall)
                    tier_precisions.append(precision)
                    
                    status = "✅" if f1 > 0.3 else "⚠️" if f1 > 0.1 else "❌"
                    print(f"  {status} {class_name:20s}: P={precision:.3f}, R={recall:.3f}, F1={f1:.3f}, N={support}")
            
            if tier_f1_scores:
                avg_f1 = np.mean(tier_f1_scores)
                avg_precision = np.mean(tier_precisions)
                avg_recall = np.mean(tier_recalls)
                print(f"\n  📊 {tier_name} AVERAGES:")
                print(f"     Precision: {avg_precision:.4f}")
                print(f"     Recall: {avg_recall:.4f}")
                print(f"     F1-Score: {avg_f1:.4f}")
        
        # Problem class identification
        print(f"\n⚠️  CLASSES STILL STRUGGLING (F1 < 0.2):")
        print("-" * 50)
        struggling_classes = []
        for class_name in target_names:
            if class_name in report and report[class_name]['f1-score'] < 0.2:
                struggling_classes.append(class_name)
                f1 = report[class_name]['f1-score']
                support = report[class_name]['support']
                print(f"  ❌ {class_name}: F1={f1:.3f}, N={support}")
        
        if not struggling_classes:
            print("  🎉 No classes with F1 < 0.2!")
        
        # Success stories
        print(f"\n🎉 BIGGEST IMPROVEMENTS (F1 > 0.5):")
        print("-" * 50)
        success_classes = []
        for class_name in target_names:
            if class_name in report and report[class_name]['f1-score'] > 0.5:
                success_classes.append(class_name)
                f1 = report[class_name]['f1-score']
                support = report[class_name]['support']
                print(f"  ✅ {class_name}: F1={f1:.3f}, N={support}")
        
        # Hyperparameter summary if tuned
        if hypertuned and self.best_hps:
            print(f"\n🔧 HYPERPARAMETER SUMMARY:")
            print("-" * 50)
            print(f"  Best Learning Rate: {self.best_hps.get('learning_rate'):.6f}")
            print(f"  Best Dropout Rate: {self.best_hps.get('dropout_rate'):.3f}")
            print(f"  Best LSTM Units: {self.best_hps.get('lstm1_units')}-{self.best_hps.get('lstm2_units')}-{self.best_hps.get('lstm3_units')}")
            print(f"  Best Dense Units: {self.best_hps.get('dense1_units')}-{self.best_hps.get('dense2_units')}-{self.best_hps.get('dense3_units')}")
            print(f"  Best Focal Loss: α={self.best_hps.get('focal_alpha'):.3f}, γ={self.best_hps.get('focal_gamma'):.1f}")
        
        return overall_acc, daily_accuracies, history, y_true, y_pred
    
    def predict_future(self, recent_data):
        
        if isinstance(recent_data, pd.DataFrame):
            recent_scaled = self.scaler_X.transform(recent_data[self.feature_cols])
        elif isinstance(recent_data, np.ndarray):
            if recent_data.shape[1] == len(self.feature_cols):
                recent_scaled = self.scaler_X.transform(recent_data)
            else:
                recent_scaled = recent_data
        else:
            raise ValueError("recent_data must be either a DataFrame or numpy array")
        
        input_seq = recent_scaled[-self.sequence_length:].reshape(1, self.sequence_length, -1)
        pred_prob = self.model.predict(input_seq, verbose=0)
        pred_classes = np.argmax(pred_prob[0], axis=-1)
        
        predicted_conditions = self.label_encoder.inverse_transform(pred_classes)
        confidence_scores = np.max(pred_prob[0], axis=-1)
        
        # Calculate prediction uncertainty
        entropy = -np.sum(pred_prob[0] * np.log(pred_prob[0] + 1e-8), axis=-1)
        normalized_entropy = entropy / np.log(len(self.label_encoder.classes_))
        
        return predicted_conditions, confidence_scores, normalized_entropy
    
class OptimizedHumidityMinLSTM:
    def __init__(self, df, sequence_length=10, forecast_horizon=3):
        self.df = df.copy()
        self.sequence_length = sequence_length
        self.forecast_horizon = forecast_horizon
        self.scaler_features = None
        self.scaler_targets = None
        self.model = None
        self.best_params = None
        self.study = None
        
        # Temperature target columns
        self.target_cols = [
            'relative_humidity_2m_min (%)'
        ]
        
    def preprocess_data(self):
        print("🧹 Preprocessing data for max temperature prediction...")
        df = self.df.copy()
        
        # Check which target columns are available
        available_targets = [col for col in self.target_cols if col in df.columns]
        if not available_targets:
            raise ValueError(f"None of the target columns {self.target_cols} found in the dataframe")
        
        self.available_targets = available_targets
        print(f"Available target columns: {available_targets}")
        
        # Handle missing values for targets
        for col in available_targets:
            df[col] = df[col].fillna(method='ffill').fillna(method='bfill')
            df[col] = df[col].interpolate(method='linear')
            df[col].fillna(df[col].median(), inplace=True)
        
        # Remove rows with any missing target values
        df = df.dropna(subset=available_targets)
        
        # Define feature columns (exclude date, weather_condition, and target columns)
        exclude_cols = ['date', 'weather_condition', 'temperature_2m_max (°C)', 'relative_humidity_2m_max (%)', 'temperature_2m_min (°C)'] + available_targets
        feature_cols = [col for col in df.columns if col not in exclude_cols]
        
        # Handle missing values for features
        numeric_cols = df[feature_cols].select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            df[col] = df[col].fillna(method='ffill').fillna(method='bfill')
            df[col] = df[col].interpolate(method='linear')
            df[col].fillna(df[col].median(), inplace=True)
        
        # Scale features
        self.scaler_features = StandardScaler()
        df[feature_cols] = self.scaler_features.fit_transform(df[feature_cols])
        
        # Scale targets
        self.scaler_targets = StandardScaler()
        df[available_targets] = self.scaler_targets.fit_transform(df[available_targets])
        
        # Store processed data
        self.df_processed = df
        self.feature_cols = feature_cols
        
        print(f"Feature columns ({len(feature_cols)}): {feature_cols[:5]}..." if len(feature_cols) > 5 else f"Feature columns: {feature_cols}")
        print(f"Target columns: {available_targets}")
        print(f"Data shape after preprocessing: {df.shape}")
        
        return df
    
    def create_sequences(self):
        print(f"🪟 Creating sequences for Maximum temperature prediction...")
        
        X, y = [], []
        data = self.df_processed
        features = data[self.feature_cols].values
        targets = data[self.available_targets].values
        
        # Create sequences with sliding window
        for i in range(len(data) - self.sequence_length - self.forecast_horizon + 1):
            # Input sequence
            X_seq = features[i:i + self.sequence_length]
            
            # Target sequence (next forecast_horizon days)
            y_seq = targets[i + self.sequence_length:i + self.sequence_length + self.forecast_horizon]
            
            X.append(X_seq)
            y.append(y_seq)
        
        X = np.array(X)
        y = np.array(y)
        
        print(f"Created sequences: X={X.shape}, y={y.shape}")
        print(f"Input sequence length: {self.sequence_length}")
        print(f"Forecast horizon: {self.forecast_horizon}")
        print(f"Number of features: {X.shape[2]}")
        print(f"Number of target variables: {y.shape[2]}")
        
        return X, y
    
    def build_model_with_params(self, trial, input_shape, output_shape):
        
        # Hyperparameters to optimize
        lstm1_units = trial.suggest_int('lstm1_units', 32, 256, step=32)
        lstm2_units = trial.suggest_int('lstm2_units', 16, 128, step=16)
        lstm3_units = trial.suggest_int('lstm3_units', 8, 64, step=8)
        
        dense1_units = trial.suggest_int('dense1_units', 32, 128, step=16)
        dense2_units = trial.suggest_int('dense2_units', 16, 64, step=8)
        
        dropout_rate = trial.suggest_float('dropout_rate', 0.1, 0.5, step=0.1)
        recurrent_dropout = trial.suggest_float('recurrent_dropout', 0.1, 0.4, step=0.1)
        l2_reg = trial.suggest_float('l2_reg', 1e-5, 1e-2, log=True)
        
        learning_rate = trial.suggest_float('learning_rate', 1e-4, 1e-2, log=True)
        batch_norm = trial.suggest_categorical('batch_norm', [True, False])
        
        model = Sequential()
        
        # First LSTM layer
        model.add(LSTM(lstm1_units, return_sequences=True, input_shape=input_shape,
                      kernel_regularizer=l2(l2_reg), 
                      dropout=dropout_rate, recurrent_dropout=recurrent_dropout))
        if batch_norm:
            model.add(BatchNormalization())
        
        # Second LSTM layer
        model.add(LSTM(lstm2_units, return_sequences=True,
                      kernel_regularizer=l2(l2_reg),
                      dropout=dropout_rate, recurrent_dropout=recurrent_dropout))
        if batch_norm:
            model.add(BatchNormalization())
        
        # Third LSTM layer
        model.add(LSTM(lstm3_units, return_sequences=False,
                      kernel_regularizer=l2(l2_reg),
                      dropout=dropout_rate, recurrent_dropout=recurrent_dropout))
        if batch_norm:
            model.add(BatchNormalization())
        
        model.add(Dropout(dropout_rate + 0.1))
        
        # Dense layers
        model.add(Dense(dense1_units, activation='relu', kernel_regularizer=l2(l2_reg)))
        if batch_norm:
            model.add(BatchNormalization())
        model.add(Dropout(dropout_rate + 0.1))
        
        model.add(Dense(dense2_units, activation='relu', kernel_regularizer=l2(l2_reg)))
        model.add(Dropout(dropout_rate))
        
        # Output layer
        model.add(Dense(output_shape[0] * output_shape[1], activation='linear'))
        
        # Reshape to (forecast_horizon, num_target_variables)
        model.add(tf.keras.layers.Reshape(output_shape))
        
        # Compile model
        model.compile(
            optimizer=Adam(learning_rate=learning_rate, clipnorm=1.0),
            loss='mse',
            metrics=['mae']
        )
        
        return model
    
    def objective(self, trial):
        
        try:
            # Create sequences
            X, y = self.create_sequences()
            
            if len(X) == 0:
                return float('inf')
            
            # Train-validation split
            X_train, X_val, y_train, y_val = train_test_split(
                X, y, test_size=0.2, random_state=42, shuffle=True
            )
            
            # Build model with trial parameters
            input_shape = (self.sequence_length, X.shape[2])
            output_shape = (self.forecast_horizon, len(self.available_targets))
            
            model = self.build_model_with_params(trial, input_shape, output_shape)
            
            # Training parameters
            batch_size = trial.suggest_categorical('batch_size', [16, 32, 64])
            
            # Callbacks
            callbacks = [
                EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True, verbose=0),
                ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=5, min_lr=1e-7, verbose=0)
            ]
            
            # Train model
            history = model.fit(
                X_train, y_train,
                epochs=50,  # Reduced for faster optimization
                batch_size=batch_size,
                validation_data=(X_val, y_val),
                callbacks=callbacks,
                verbose=0
            )
            
            # Get best validation loss
            best_val_loss = min(history.history['val_loss'])
            
            # Clean up to free memory
            del model
            tf.keras.backend.clear_session()
            
            return best_val_loss
            
        except Exception as e:
            print(f"Trial failed with error: {e}")
            return float('inf')
    
    def optimize_hyperparameters(self, n_trials=20, timeout=None):
        
        print("\n" + "="*70)
        print("🔧 HYPERPARAMETER OPTIMIZATION WITH OPTUNA")
        print("="*70)
        
        # Create study
        self.study = optuna.create_study(direction='minimize', 
                                        study_name='temperature_lstm_optimization')
        
        print(f"Starting optimization with {n_trials} trials...")
        if timeout:
            print(f"Timeout set to {timeout} seconds")
        
        # Optimize
        self.study.optimize(self.objective, n_trials=n_trials, timeout=timeout)
        
        # Get best parameters
        self.best_params = self.study.best_params
        
        print("\n🏆 OPTIMIZATION COMPLETED!")
        print("="*50)
        print(f"Best validation loss: {self.study.best_value:.6f}")
        print(f"Number of trials: {len(self.study.trials)}")
        
        print(f"\n🎯 BEST HYPERPARAMETERS:")
        print("-" * 40)
        for key, value in self.best_params.items():
            print(f"{key:20s}: {value}")
        
        return self.best_params
    
    def build_best_model(self, input_shape, output_shape):
        """Build model with best parameters found by Optuna"""
        if self.best_params is None:
            raise ValueError("No optimization performed yet. Run optimize_hyperparameters() first.")
        
        model = Sequential()
        
        # Use best parameters
        lstm1_units = self.best_params['lstm1_units']
        lstm2_units = self.best_params['lstm2_units']
        lstm3_units = self.best_params['lstm3_units']
        dense1_units = self.best_params['dense1_units']
        dense2_units = self.best_params['dense2_units']
        dropout_rate = self.best_params['dropout_rate']
        recurrent_dropout = self.best_params['recurrent_dropout']
        l2_reg = self.best_params['l2_reg']
        learning_rate = self.best_params['learning_rate']
        batch_norm = self.best_params['batch_norm']
        
        # Build architecture
        model.add(LSTM(lstm1_units, return_sequences=True, input_shape=input_shape,
                      kernel_regularizer=l2(l2_reg), 
                      dropout=dropout_rate, recurrent_dropout=recurrent_dropout))
        if batch_norm:
            model.add(BatchNormalization())
        
        model.add(LSTM(lstm2_units, return_sequences=True,
                      kernel_regularizer=l2(l2_reg),
                      dropout=dropout_rate, recurrent_dropout=recurrent_dropout))
        if batch_norm:
            model.add(BatchNormalization())
        
        model.add(LSTM(lstm3_units, return_sequences=False,
                      kernel_regularizer=l2(l2_reg),
                      dropout=dropout_rate, recurrent_dropout=recurrent_dropout))
        if batch_norm:
            model.add(BatchNormalization())
        
        model.add(Dropout(dropout_rate + 0.1))
        
        model.add(Dense(dense1_units, activation='relu', kernel_regularizer=l2(l2_reg)))
        if batch_norm:
            model.add(BatchNormalization())
        model.add(Dropout(dropout_rate + 0.1))
        
        model.add(Dense(dense2_units, activation='relu', kernel_regularizer=l2(l2_reg)))
        model.add(Dropout(dropout_rate))
        
        model.add(Dense(output_shape[0] * output_shape[1], activation='linear'))
        model.add(tf.keras.layers.Reshape(output_shape))
        
        # Compile with best parameters
        model.compile(
            optimizer=Adam(learning_rate=learning_rate, clipnorm=1.0),
            loss='mse',
            metrics=['mae']
        )
        
        return model
    
    def train_optimized_model(self, validation_split=0.2, epochs=200):
        
        print("\n" + "="*70)
        print("TRAINING OPTIMIZED TEMPERATURE MAX LSTM MODEL")
        print("="*70)
        
        if self.best_params is None:
            raise ValueError("No optimization performed yet. Run optimize_hyperparameters() first.")
        
        # Create sequences
        X, y = self.create_sequences()
        
        if len(X) == 0:
            raise ValueError("No sequences created!")
        
        # Train-test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, shuffle=True
        )
        
        print(f"Training samples: {len(X_train)}, Test samples: {len(X_test)}")
        
        # Build optimized model
        input_shape = (self.sequence_length, X.shape[2])
        output_shape = (self.forecast_horizon, len(self.available_targets))
        
        self.model = self.build_best_model(input_shape, output_shape)
        
        print(f"\nOptimized model architecture:")
        self.model.summary()
        
        # Use best batch size
        batch_size = self.best_params.get('batch_size', 32)
        
        # Callbacks
        callbacks = [
            EarlyStopping(monitor='val_loss', patience=20, restore_best_weights=True, verbose=1),
            ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=10, min_lr=1e-7, verbose=1)
        ]
        
        # Train model
        print(f"\nTraining optimized model...")
        history = self.model.fit(
            X_train, y_train,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            callbacks=callbacks,
            verbose=1
        )
        
        # Evaluate
        print(f"\nEvaluating optimized model...")
        y_pred = self.model.predict(X_test, verbose=0)
        
        return self.evaluate_model(y_test, y_pred, history)
    
    def evaluate_model(self, y_true, y_pred, history):
        print("\n" + "="*70)
        print("OPTIMIZED TEMPERATURE MAX LSTM RESULTS")
        print("="*70)
        
        # Inverse transform predictions and true values to original scale
        y_true_original = np.zeros_like(y_true)
        y_pred_original = np.zeros_like(y_pred)
        
        for day in range(self.forecast_horizon):
            y_true_original[:, day, :] = self.scaler_targets.inverse_transform(y_true[:, day, :])
            y_pred_original[:, day, :] = self.scaler_targets.inverse_transform(y_pred[:, day, :])
        
        # Calculate metrics for each target variable and forecast day
        results = {}
        
        for i, target_name in enumerate(self.available_targets):
            print(f"\n🌡️ {target_name}:")
            print("-" * 50)
            
            target_results = {
                'mae': [],
                'rmse': [],
                'r2': [],
                'mape': []
            }
            
            for day in range(self.forecast_horizon):
                y_true_day = y_true_original[:, day, i]
                y_pred_day = y_pred_original[:, day, i]
                
                mae = mean_absolute_error(y_true_day, y_pred_day)
                rmse = np.sqrt(mean_squared_error(y_true_day, y_pred_day))
                r2 = r2_score(y_true_day, y_pred_day)
                
                # Calculate MAPE (Mean Absolute Percentage Error)
                mape = np.mean(np.abs((y_true_day - y_pred_day) / (y_true_day + 1e-8))) * 100
                
                target_results['mae'].append(mae)
                target_results['rmse'].append(rmse)
                target_results['r2'].append(r2)
                target_results['mape'].append(mape)
                
                print(f"  Day {day+1}: MAE={mae:.3f}, RMSE={rmse:.3f}, R²={r2:.3f}, MAPE={mape:.2f}%")
            
            # Calculate averages
            avg_mae = np.mean(target_results['mae'])
            avg_rmse = np.mean(target_results['rmse'])
            avg_r2 = np.mean(target_results['r2'])
            avg_mape = np.mean(target_results['mape'])
            
            target_results['avg_mae'] = avg_mae
            target_results['avg_rmse'] = avg_rmse
            target_results['avg_r2'] = avg_r2
            target_results['avg_mape'] = avg_mape
            
            print(f"  Average: MAE={avg_mae:.3f}, RMSE={avg_rmse:.3f}, R²={avg_r2:.3f}, MAPE={avg_mape:.2f}%")
            
            results[target_name] = target_results
        
        # Overall performance summary
        print(f"\n📊 OVERALL PERFORMANCE SUMMARY:")
        print("="*50)
        
        all_maes = [results[target]['avg_mae'] for target in self.available_targets]
        all_rmses = [results[target]['avg_rmse'] for target in self.available_targets]
        all_r2s = [results[target]['avg_r2'] for target in self.available_targets]
        all_mapes = [results[target]['avg_mape'] for target in self.available_targets]
        
        print(f"Overall Average MAE: {np.mean(all_maes):.3f}")
        print(f"Overall Average RMSE: {np.mean(all_rmses):.3f}")
        print(f"Overall Average R²: {np.mean(all_r2s):.3f}")
        print(f"Overall Average MAPE: {np.mean(all_mapes):.2f}%")
        
        # Optimization summary
        if self.best_params:
            print(f"\n🔧 OPTIMIZATION SUMMARY:")
            print("-" * 40)
            print(f"Best validation loss: {self.study.best_value:.6f}")
            print(f"Number of trials completed: {len(self.study.trials)}")
            print(f"Best LSTM architecture: {self.best_params['lstm1_units']}-{self.best_params['lstm2_units']}-{self.best_params['lstm3_units']}")
            print(f"Best Dense architecture: {self.best_params['dense1_units']}-{self.best_params['dense2_units']}")
            print(f"Best learning rate: {self.best_params['learning_rate']:.6f}")
            print(f"Best dropout rate: {self.best_params['dropout_rate']:.3f}")
        
        return results, history, y_true_original, y_pred_original
    
    def predict_future(self, recent_data):
        if isinstance(recent_data, pd.DataFrame):
            recent_scaled = self.scaler_features.transform(recent_data[self.feature_cols])
        elif isinstance(recent_data, np.ndarray):
            if recent_data.shape[1] == len(self.feature_cols):
                recent_scaled = self.scaler_features.transform(recent_data)
            else:
                recent_scaled = recent_data
        else:
            raise ValueError("recent_data must be a DataFrame or NumPy array")

        input_seq = recent_scaled[-self.sequence_length:].reshape(1, self.sequence_length, -1)
        prediction_scaled = self.model.predict(input_seq, verbose=0)

        # Inverse transform
        prediction_original = np.zeros_like(prediction_scaled)
        for day in range(self.forecast_horizon):
            prediction_original[0, day, :] = self.scaler_targets.inverse_transform(
                prediction_scaled[0, day, :].reshape(1, -1)
            )

        predicted_values = prediction_original[0, :, 0]  

        return predicted_values
    
    def plot_training_history(self, history):
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))
        
        # Loss
        ax1.plot(history.history['loss'], label='Training Loss')
        ax1.plot(history.history['val_loss'], label='Validation Loss')
        ax1.set_title('Optimized Model Loss')
        ax1.set_xlabel('Epoch')
        ax1.set_ylabel('Loss')
        ax1.legend()
        
        # MAE
        ax2.plot(history.history['mae'], label='Training MAE')
        ax2.plot(history.history['val_mae'], label='Validation MAE')
        ax2.set_title('Optimized Model MAE')
        ax2.set_xlabel('Epoch')
        ax2.set_ylabel('MAE')
        ax2.legend()
        
        plt.tight_layout()
        plt.show()
    
    def plot_optimization_history(self):
        
        if self.study is None:
            print("No optimization study available to plot.")
            return
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))
        
        # Optimization history
        values = [trial.value for trial in self.study.trials if trial.value is not None]
        ax1.plot(values)
        ax1.set_title('Optimization History')
        ax1.set_xlabel('Trial')
        ax1.set_ylabel('Validation Loss')
        ax1.grid(True)
        
        # Parameter importance (if available)
        try:
            importance = optuna.importance.get_param_importances(self.study)
            params = list(importance.keys())
            importances = list(importance.values())
            
            ax2.barh(params, importances)
            ax2.set_title('Parameter Importance')
            ax2.set_xlabel('Importance')
        except:
            ax2.text(0.5, 0.5, 'Parameter importance\nnot available', 
                    ha='center', va='center', transform=ax2.transAxes)
        
        plt.tight_layout()
        plt.show()



class OptimizedTemperatureMinLSTM:
    def __init__(self, df, sequence_length=10, forecast_horizon=3):
        self.df = df.copy()
        self.sequence_length = sequence_length
        self.forecast_horizon = forecast_horizon
        self.scaler_features = None
        self.scaler_targets = None
        self.model = None
        self.best_params = None
        self.study = None
        
        # Temperature target columns
        self.target_cols = [
            'temperature_2m_min (°C)'
        ]
        
    def preprocess_data(self):
        print("🧹 Preprocessing data for max temperature prediction...")
        df = self.df.copy()
        
        # Check which target columns are available
        available_targets = [col for col in self.target_cols if col in df.columns]
        if not available_targets:
            raise ValueError(f"None of the target columns {self.target_cols} found in the dataframe")
        
        self.available_targets = available_targets
        print(f"Available target columns: {available_targets}")
        
        # Handle missing values for targets
        for col in available_targets:
            df[col] = df[col].fillna(method='ffill').fillna(method='bfill')
            df[col] = df[col].interpolate(method='linear')
            df[col].fillna(df[col].median(), inplace=True)
        
        # Remove rows with any missing target values
        df = df.dropna(subset=available_targets)
        
        # Define feature columns (exclude date, weather_condition, and target columns)
        exclude_cols = ['date', 'weather_condition', 'relative_humidity_2m_max (%)', 'relative_humidity_2m_min (%)', 'temperature_2m_max (°C)'] + available_targets
        feature_cols = [col for col in df.columns if col not in exclude_cols]
        
        # Handle missing values for features
        numeric_cols = df[feature_cols].select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            df[col] = df[col].fillna(method='ffill').fillna(method='bfill')
            df[col] = df[col].interpolate(method='linear')
            df[col].fillna(df[col].median(), inplace=True)
        
        # Scale features
        self.scaler_features = StandardScaler()
        df[feature_cols] = self.scaler_features.fit_transform(df[feature_cols])
        
        # Scale targets
        self.scaler_targets = StandardScaler()
        df[available_targets] = self.scaler_targets.fit_transform(df[available_targets])
        
        # Store processed data
        self.df_processed = df
        self.feature_cols = feature_cols
        
        print(f"Feature columns ({len(feature_cols)}): {feature_cols[:5]}..." if len(feature_cols) > 5 else f"Feature columns: {feature_cols}")
        print(f"Target columns: {available_targets}")
        print(f"Data shape after preprocessing: {df.shape}")
        
        return df
    
    def create_sequences(self):
        print(f"🪟 Creating sequences for Maximum temperature prediction...")
        
        X, y = [], []
        data = self.df_processed
        features = data[self.feature_cols].values
        targets = data[self.available_targets].values
        
        # Create sequences with sliding window
        for i in range(len(data) - self.sequence_length - self.forecast_horizon + 1):
            # Input sequence
            X_seq = features[i:i + self.sequence_length]
            
            # Target sequence (next forecast_horizon days)
            y_seq = targets[i + self.sequence_length:i + self.sequence_length + self.forecast_horizon]
            
            X.append(X_seq)
            y.append(y_seq)
        
        X = np.array(X)
        y = np.array(y)
        
        print(f"Created sequences: X={X.shape}, y={y.shape}")
        print(f"Input sequence length: {self.sequence_length}")
        print(f"Forecast horizon: {self.forecast_horizon}")
        print(f"Number of features: {X.shape[2]}")
        print(f"Number of target variables: {y.shape[2]}")
        
        return X, y
    
    def build_model_with_params(self, trial, input_shape, output_shape):
        
        # Hyperparameters to optimize
        lstm1_units = trial.suggest_int('lstm1_units', 32, 256, step=32)
        lstm2_units = trial.suggest_int('lstm2_units', 16, 128, step=16)
        lstm3_units = trial.suggest_int('lstm3_units', 8, 64, step=8)
        
        dense1_units = trial.suggest_int('dense1_units', 32, 128, step=16)
        dense2_units = trial.suggest_int('dense2_units', 16, 64, step=8)
        
        dropout_rate = trial.suggest_float('dropout_rate', 0.1, 0.5, step=0.1)
        recurrent_dropout = trial.suggest_float('recurrent_dropout', 0.1, 0.4, step=0.1)
        l2_reg = trial.suggest_float('l2_reg', 1e-5, 1e-2, log=True)
        
        learning_rate = trial.suggest_float('learning_rate', 1e-4, 1e-2, log=True)
        batch_norm = trial.suggest_categorical('batch_norm', [True, False])
        
        model = Sequential()
        
        # First LSTM layer
        model.add(LSTM(lstm1_units, return_sequences=True, input_shape=input_shape,
                      kernel_regularizer=l2(l2_reg), 
                      dropout=dropout_rate, recurrent_dropout=recurrent_dropout))
        if batch_norm:
            model.add(BatchNormalization())
        
        # Second LSTM layer
        model.add(LSTM(lstm2_units, return_sequences=True,
                      kernel_regularizer=l2(l2_reg),
                      dropout=dropout_rate, recurrent_dropout=recurrent_dropout))
        if batch_norm:
            model.add(BatchNormalization())
        
        # Third LSTM layer
        model.add(LSTM(lstm3_units, return_sequences=False,
                      kernel_regularizer=l2(l2_reg),
                      dropout=dropout_rate, recurrent_dropout=recurrent_dropout))
        if batch_norm:
            model.add(BatchNormalization())
        
        model.add(Dropout(dropout_rate + 0.1))
        
        # Dense layers
        model.add(Dense(dense1_units, activation='relu', kernel_regularizer=l2(l2_reg)))
        if batch_norm:
            model.add(BatchNormalization())
        model.add(Dropout(dropout_rate + 0.1))
        
        model.add(Dense(dense2_units, activation='relu', kernel_regularizer=l2(l2_reg)))
        model.add(Dropout(dropout_rate))
        
        # Output layer
        model.add(Dense(output_shape[0] * output_shape[1], activation='linear'))
        
        # Reshape to (forecast_horizon, num_target_variables)
        model.add(tf.keras.layers.Reshape(output_shape))
        
        # Compile model
        model.compile(
            optimizer=Adam(learning_rate=learning_rate, clipnorm=1.0),
            loss='mse',
            metrics=['mae']
        )
        
        return model
    
    def objective(self, trial):
        
        try:
            # Create sequences
            X, y = self.create_sequences()
            
            if len(X) == 0:
                return float('inf')
            
            # Train-validation split
            X_train, X_val, y_train, y_val = train_test_split(
                X, y, test_size=0.2, random_state=42, shuffle=True
            )
            
            # Build model with trial parameters
            input_shape = (self.sequence_length, X.shape[2])
            output_shape = (self.forecast_horizon, len(self.available_targets))
            
            model = self.build_model_with_params(trial, input_shape, output_shape)
            
            # Training parameters
            batch_size = trial.suggest_categorical('batch_size', [16, 32, 64])
            
            # Callbacks
            callbacks = [
                EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True, verbose=0),
                ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=5, min_lr=1e-7, verbose=0)
            ]
            
            # Train model
            history = model.fit(
                X_train, y_train,
                epochs=50,  # Reduced for faster optimization
                batch_size=batch_size,
                validation_data=(X_val, y_val),
                callbacks=callbacks,
                verbose=0
            )
            
            # Get best validation loss
            best_val_loss = min(history.history['val_loss'])
            
            # Clean up to free memory
            del model
            tf.keras.backend.clear_session()
            
            return best_val_loss
            
        except Exception as e:
            print(f"Trial failed with error: {e}")
            return float('inf')
    
    def optimize_hyperparameters(self, n_trials=20, timeout=None):
        
        print("\n" + "="*70)
        print("🔧 HYPERPARAMETER OPTIMIZATION WITH OPTUNA")
        print("="*70)
        
        # Create study
        self.study = optuna.create_study(direction='minimize', 
                                        study_name='temperature_lstm_optimization')
        
        print(f"Starting optimization with {n_trials} trials...")
        if timeout:
            print(f"Timeout set to {timeout} seconds")
        
        # Optimize
        self.study.optimize(self.objective, n_trials=n_trials, timeout=timeout)
        
        # Get best parameters
        self.best_params = self.study.best_params
        
        print("\n🏆 OPTIMIZATION COMPLETED!")
        print("="*50)
        print(f"Best validation loss: {self.study.best_value:.6f}")
        print(f"Number of trials: {len(self.study.trials)}")
        
        print(f"\n🎯 BEST HYPERPARAMETERS:")
        print("-" * 40)
        for key, value in self.best_params.items():
            print(f"{key:20s}: {value}")
        
        return self.best_params
    
    def build_best_model(self, input_shape, output_shape):
        """Build model with best parameters found by Optuna"""
        if self.best_params is None:
            raise ValueError("No optimization performed yet. Run optimize_hyperparameters() first.")
        
        model = Sequential()
        
        # Use best parameters
        lstm1_units = self.best_params['lstm1_units']
        lstm2_units = self.best_params['lstm2_units']
        lstm3_units = self.best_params['lstm3_units']
        dense1_units = self.best_params['dense1_units']
        dense2_units = self.best_params['dense2_units']
        dropout_rate = self.best_params['dropout_rate']
        recurrent_dropout = self.best_params['recurrent_dropout']
        l2_reg = self.best_params['l2_reg']
        learning_rate = self.best_params['learning_rate']
        batch_norm = self.best_params['batch_norm']
        
        # Build architecture
        model.add(LSTM(lstm1_units, return_sequences=True, input_shape=input_shape,
                      kernel_regularizer=l2(l2_reg), 
                      dropout=dropout_rate, recurrent_dropout=recurrent_dropout))
        if batch_norm:
            model.add(BatchNormalization())
        
        model.add(LSTM(lstm2_units, return_sequences=True,
                      kernel_regularizer=l2(l2_reg),
                      dropout=dropout_rate, recurrent_dropout=recurrent_dropout))
        if batch_norm:
            model.add(BatchNormalization())
        
        model.add(LSTM(lstm3_units, return_sequences=False,
                      kernel_regularizer=l2(l2_reg),
                      dropout=dropout_rate, recurrent_dropout=recurrent_dropout))
        if batch_norm:
            model.add(BatchNormalization())
        
        model.add(Dropout(dropout_rate + 0.1))
        
        model.add(Dense(dense1_units, activation='relu', kernel_regularizer=l2(l2_reg)))
        if batch_norm:
            model.add(BatchNormalization())
        model.add(Dropout(dropout_rate + 0.1))
        
        model.add(Dense(dense2_units, activation='relu', kernel_regularizer=l2(l2_reg)))
        model.add(Dropout(dropout_rate))
        
        model.add(Dense(output_shape[0] * output_shape[1], activation='linear'))
        model.add(tf.keras.layers.Reshape(output_shape))
        
        # Compile with best parameters
        model.compile(
            optimizer=Adam(learning_rate=learning_rate, clipnorm=1.0),
            loss='mse',
            metrics=['mae']
        )
        
        return model
    
    def train_optimized_model(self, validation_split=0.2, epochs=200):
        
        print("\n" + "="*70)
        print("TRAINING OPTIMIZED TEMPERATURE MAX LSTM MODEL")
        print("="*70)
        
        if self.best_params is None:
            raise ValueError("No optimization performed yet. Run optimize_hyperparameters() first.")
        
        # Create sequences
        X, y = self.create_sequences()
        
        if len(X) == 0:
            raise ValueError("No sequences created!")
        
        # Train-test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, shuffle=True
        )
        
        print(f"Training samples: {len(X_train)}, Test samples: {len(X_test)}")
        
        # Build optimized model
        input_shape = (self.sequence_length, X.shape[2])
        output_shape = (self.forecast_horizon, len(self.available_targets))
        
        self.model = self.build_best_model(input_shape, output_shape)
        
        print(f"\nOptimized model architecture:")
        self.model.summary()
        
        # Use best batch size
        batch_size = self.best_params.get('batch_size', 32)
        
        # Callbacks
        callbacks = [
            EarlyStopping(monitor='val_loss', patience=20, restore_best_weights=True, verbose=1),
            ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=10, min_lr=1e-7, verbose=1)
        ]
        
        # Train model
        print(f"\nTraining optimized model...")
        history = self.model.fit(
            X_train, y_train,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            callbacks=callbacks,
            verbose=1
        )
        
        # Evaluate
        print(f"\nEvaluating optimized model...")
        y_pred = self.model.predict(X_test, verbose=0)
        
        return self.evaluate_model(y_test, y_pred, history)
    
    def evaluate_model(self, y_true, y_pred, history):
        print("\n" + "="*70)
        print("OPTIMIZED TEMPERATURE MAX LSTM RESULTS")
        print("="*70)
        
        # Inverse transform predictions and true values to original scale
        y_true_original = np.zeros_like(y_true)
        y_pred_original = np.zeros_like(y_pred)
        
        for day in range(self.forecast_horizon):
            y_true_original[:, day, :] = self.scaler_targets.inverse_transform(y_true[:, day, :])
            y_pred_original[:, day, :] = self.scaler_targets.inverse_transform(y_pred[:, day, :])
        
        # Calculate metrics for each target variable and forecast day
        results = {}
        
        for i, target_name in enumerate(self.available_targets):
            print(f"\n🌡️ {target_name}:")
            print("-" * 50)
            
            target_results = {
                'mae': [],
                'rmse': [],
                'r2': [],
                'mape': []
            }
            
            for day in range(self.forecast_horizon):
                y_true_day = y_true_original[:, day, i]
                y_pred_day = y_pred_original[:, day, i]
                
                mae = mean_absolute_error(y_true_day, y_pred_day)
                rmse = np.sqrt(mean_squared_error(y_true_day, y_pred_day))
                r2 = r2_score(y_true_day, y_pred_day)
                
                # Calculate MAPE (Mean Absolute Percentage Error)
                mape = np.mean(np.abs((y_true_day - y_pred_day) / (y_true_day + 1e-8))) * 100
                
                target_results['mae'].append(mae)
                target_results['rmse'].append(rmse)
                target_results['r2'].append(r2)
                target_results['mape'].append(mape)
                
                print(f"  Day {day+1}: MAE={mae:.3f}, RMSE={rmse:.3f}, R²={r2:.3f}, MAPE={mape:.2f}%")
            
            # Calculate averages
            avg_mae = np.mean(target_results['mae'])
            avg_rmse = np.mean(target_results['rmse'])
            avg_r2 = np.mean(target_results['r2'])
            avg_mape = np.mean(target_results['mape'])
            
            target_results['avg_mae'] = avg_mae
            target_results['avg_rmse'] = avg_rmse
            target_results['avg_r2'] = avg_r2
            target_results['avg_mape'] = avg_mape
            
            print(f"  Average: MAE={avg_mae:.3f}, RMSE={avg_rmse:.3f}, R²={avg_r2:.3f}, MAPE={avg_mape:.2f}%")
            
            results[target_name] = target_results
        
        # Overall performance summary
        print(f"\n📊 OVERALL PERFORMANCE SUMMARY:")
        print("="*50)
        
        all_maes = [results[target]['avg_mae'] for target in self.available_targets]
        all_rmses = [results[target]['avg_rmse'] for target in self.available_targets]
        all_r2s = [results[target]['avg_r2'] for target in self.available_targets]
        all_mapes = [results[target]['avg_mape'] for target in self.available_targets]
        
        print(f"Overall Average MAE: {np.mean(all_maes):.3f}")
        print(f"Overall Average RMSE: {np.mean(all_rmses):.3f}")
        print(f"Overall Average R²: {np.mean(all_r2s):.3f}")
        print(f"Overall Average MAPE: {np.mean(all_mapes):.2f}%")
        
        # Optimization summary
        if self.best_params:
            print(f"\n🔧 OPTIMIZATION SUMMARY:")
            print("-" * 40)
            print(f"Best validation loss: {self.study.best_value:.6f}")
            print(f"Number of trials completed: {len(self.study.trials)}")
            print(f"Best LSTM architecture: {self.best_params['lstm1_units']}-{self.best_params['lstm2_units']}-{self.best_params['lstm3_units']}")
            print(f"Best Dense architecture: {self.best_params['dense1_units']}-{self.best_params['dense2_units']}")
            print(f"Best learning rate: {self.best_params['learning_rate']:.6f}")
            print(f"Best dropout rate: {self.best_params['dropout_rate']:.3f}")
        
        return results, history, y_true_original, y_pred_original
    
    def predict_future(self, recent_data):
        if isinstance(recent_data, pd.DataFrame):
            recent_scaled = self.scaler_features.transform(recent_data[self.feature_cols])
        elif isinstance(recent_data, np.ndarray):
            if recent_data.shape[1] == len(self.feature_cols):
                recent_scaled = self.scaler_features.transform(recent_data)
            else:
                recent_scaled = recent_data
        else:
            raise ValueError("recent_data must be a DataFrame or NumPy array")

        input_seq = recent_scaled[-self.sequence_length:].reshape(1, self.sequence_length, -1)
        prediction_scaled = self.model.predict(input_seq, verbose=0)

        # Inverse transform
        prediction_original = np.zeros_like(prediction_scaled)
        for day in range(self.forecast_horizon):
            prediction_original[0, day, :] = self.scaler_targets.inverse_transform(
                prediction_scaled[0, day, :].reshape(1, -1)
            )

        predicted_values = prediction_original[0, :, 0] 

        return predicted_values
    
    def plot_training_history(self, history):
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))
        
        # Loss
        ax1.plot(history.history['loss'], label='Training Loss')
        ax1.plot(history.history['val_loss'], label='Validation Loss')
        ax1.set_title('Optimized Model Loss')
        ax1.set_xlabel('Epoch')
        ax1.set_ylabel('Loss')
        ax1.legend()
        
        # MAE
        ax2.plot(history.history['mae'], label='Training MAE')
        ax2.plot(history.history['val_mae'], label='Validation MAE')
        ax2.set_title('Optimized Model MAE')
        ax2.set_xlabel('Epoch')
        ax2.set_ylabel('MAE')
        ax2.legend()
        
        plt.tight_layout()
        plt.show()
    
    def plot_optimization_history(self):
        
        if self.study is None:
            print("No optimization study available to plot.")
            return
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))
        
        # Optimization history
        values = [trial.value for trial in self.study.trials if trial.value is not None]
        ax1.plot(values)
        ax1.set_title('Optimization History')
        ax1.set_xlabel('Trial')
        ax1.set_ylabel('Validation Loss')
        ax1.grid(True)
        
        # Parameter importance (if available)
        try:
            importance = optuna.importance.get_param_importances(self.study)
            params = list(importance.keys())
            importances = list(importance.values())
            
            ax2.barh(params, importances)
            ax2.set_title('Parameter Importance')
            ax2.set_xlabel('Importance')
        except:
            ax2.text(0.5, 0.5, 'Parameter importance\nnot available', 
                    ha='center', va='center', transform=ax2.transAxes)
        
        plt.tight_layout()
        plt.show()


class OptimizedTemperatureMaxLSTM:
    def __init__(self, df, sequence_length=10, forecast_horizon=3):
        self.df = df.copy()
        self.sequence_length = sequence_length
        self.forecast_horizon = forecast_horizon
        self.scaler_features = None
        self.scaler_targets = None
        self.model = None
        self.best_params = None
        self.study = None
        
        # Temperature target columns
        self.target_cols = [
            'temperature_2m_max (°C)'
        ]
        
    def preprocess_data(self):
        print("🧹 Preprocessing data for max temperature prediction...")
        df = self.df.copy()
        
        # Check which target columns are available
        available_targets = [col for col in self.target_cols if col in df.columns]
        if not available_targets:
            raise ValueError(f"None of the target columns {self.target_cols} found in the dataframe")
        
        self.available_targets = available_targets
        print(f"Available target columns: {available_targets}")
        
        # Handle missing values for targets
        for col in available_targets:
            df[col] = df[col].fillna(method='ffill').fillna(method='bfill')
            df[col] = df[col].interpolate(method='linear')
            df[col].fillna(df[col].median(), inplace=True)
        
        # Remove rows with any missing target values
        df = df.dropna(subset=available_targets)
        
        # Define feature columns (exclude date, weather_condition, and target columns)
        exclude_cols = ['date', 'weather_condition', 'relative_humidity_2m_max (%)', 'relative_humidity_2m_min (%)', 'temperature_2m_min (°C)'] + available_targets
        feature_cols = [col for col in df.columns if col not in exclude_cols]
        
        # Handle missing values for features
        numeric_cols = df[feature_cols].select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            df[col] = df[col].fillna(method='ffill').fillna(method='bfill')
            df[col] = df[col].interpolate(method='linear')
            df[col].fillna(df[col].median(), inplace=True)
        
        # Scale features
        self.scaler_features = StandardScaler()
        df[feature_cols] = self.scaler_features.fit_transform(df[feature_cols])
        
        # Scale targets
        self.scaler_targets = StandardScaler()
        df[available_targets] = self.scaler_targets.fit_transform(df[available_targets])
        
        # Store processed data
        self.df_processed = df
        self.feature_cols = feature_cols
        
        print(f"Feature columns ({len(feature_cols)}): {feature_cols[:5]}..." if len(feature_cols) > 5 else f"Feature columns: {feature_cols}")
        print(f"Target columns: {available_targets}")
        print(f"Data shape after preprocessing: {df.shape}")
        
        return df
    
    def create_sequences(self):
        print(f"🪟 Creating sequences for Maximum temperature prediction...")
        
        X, y = [], []
        data = self.df_processed
        features = data[self.feature_cols].values
        targets = data[self.available_targets].values
        
        # Create sequences with sliding window
        for i in range(len(data) - self.sequence_length - self.forecast_horizon + 1):
            # Input sequence
            X_seq = features[i:i + self.sequence_length]
            
            # Target sequence (next forecast_horizon days)
            y_seq = targets[i + self.sequence_length:i + self.sequence_length + self.forecast_horizon]
            
            X.append(X_seq)
            y.append(y_seq)
        
        X = np.array(X)
        y = np.array(y)
        
        print(f"Created sequences: X={X.shape}, y={y.shape}")
        print(f"Input sequence length: {self.sequence_length}")
        print(f"Forecast horizon: {self.forecast_horizon}")
        print(f"Number of features: {X.shape[2]}")
        print(f"Number of target variables: {y.shape[2]}")
        
        return X, y
    
    def build_model_with_params(self, trial, input_shape, output_shape):
        
        # Hyperparameters to optimize
        lstm1_units = trial.suggest_int('lstm1_units', 32, 256, step=32)
        lstm2_units = trial.suggest_int('lstm2_units', 16, 128, step=16)
        lstm3_units = trial.suggest_int('lstm3_units', 8, 64, step=8)
        
        dense1_units = trial.suggest_int('dense1_units', 32, 128, step=16)
        dense2_units = trial.suggest_int('dense2_units', 16, 64, step=8)
        
        dropout_rate = trial.suggest_float('dropout_rate', 0.1, 0.5, step=0.1)
        recurrent_dropout = trial.suggest_float('recurrent_dropout', 0.1, 0.4, step=0.1)
        l2_reg = trial.suggest_float('l2_reg', 1e-5, 1e-2, log=True)
        
        learning_rate = trial.suggest_float('learning_rate', 1e-4, 1e-2, log=True)
        batch_norm = trial.suggest_categorical('batch_norm', [True, False])
        
        model = Sequential()
        
        # First LSTM layer
        model.add(LSTM(lstm1_units, return_sequences=True, input_shape=input_shape,
                      kernel_regularizer=l2(l2_reg), 
                      dropout=dropout_rate, recurrent_dropout=recurrent_dropout))
        if batch_norm:
            model.add(BatchNormalization())
        
        # Second LSTM layer
        model.add(LSTM(lstm2_units, return_sequences=True,
                      kernel_regularizer=l2(l2_reg),
                      dropout=dropout_rate, recurrent_dropout=recurrent_dropout))
        if batch_norm:
            model.add(BatchNormalization())
        
        # Third LSTM layer
        model.add(LSTM(lstm3_units, return_sequences=False,
                      kernel_regularizer=l2(l2_reg),
                      dropout=dropout_rate, recurrent_dropout=recurrent_dropout))
        if batch_norm:
            model.add(BatchNormalization())
        
        model.add(Dropout(dropout_rate + 0.1))
        
        # Dense layers
        model.add(Dense(dense1_units, activation='relu', kernel_regularizer=l2(l2_reg)))
        if batch_norm:
            model.add(BatchNormalization())
        model.add(Dropout(dropout_rate + 0.1))
        
        model.add(Dense(dense2_units, activation='relu', kernel_regularizer=l2(l2_reg)))
        model.add(Dropout(dropout_rate))
        
        # Output layer
        model.add(Dense(output_shape[0] * output_shape[1], activation='linear'))
        
        # Reshape to (forecast_horizon, num_target_variables)
        model.add(tf.keras.layers.Reshape(output_shape))
        
        # Compile model
        model.compile(
            optimizer=Adam(learning_rate=learning_rate, clipnorm=1.0),
            loss='mse',
            metrics=['mae']
        )
        
        return model
    
    def objective(self, trial):
        
        try:
            # Create sequences
            X, y = self.create_sequences()
            
            if len(X) == 0:
                return float('inf')
            
            # Train-validation split
            X_train, X_val, y_train, y_val = train_test_split(
                X, y, test_size=0.2, random_state=42, shuffle=True
            )
            
            # Build model with trial parameters
            input_shape = (self.sequence_length, X.shape[2])
            output_shape = (self.forecast_horizon, len(self.available_targets))
            
            model = self.build_model_with_params(trial, input_shape, output_shape)
            
            # Training parameters
            batch_size = trial.suggest_categorical('batch_size', [16, 32, 64])
            
            # Callbacks
            callbacks = [
                EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True, verbose=0),
                ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=5, min_lr=1e-7, verbose=0)
            ]
            
            # Train model
            history = model.fit(
                X_train, y_train,
                epochs=50,  # Reduced for faster optimization
                batch_size=batch_size,
                validation_data=(X_val, y_val),
                callbacks=callbacks,
                verbose=0
            )
            
            # Get best validation loss
            best_val_loss = min(history.history['val_loss'])
            
            # Clean up to free memory
            del model
            tf.keras.backend.clear_session()
            
            return best_val_loss
            
        except Exception as e:
            print(f"Trial failed with error: {e}")
            return float('inf')
    
    def optimize_hyperparameters(self, n_trials=20, timeout=None):
        
        print("\n" + "="*70)
        print("🔧 HYPERPARAMETER OPTIMIZATION WITH OPTUNA")
        print("="*70)
        
        # Create study
        self.study = optuna.create_study(direction='minimize', 
                                        study_name='temperature_lstm_optimization')
        
        print(f"Starting optimization with {n_trials} trials...")
        if timeout:
            print(f"Timeout set to {timeout} seconds")
        
        # Optimize
        self.study.optimize(self.objective, n_trials=n_trials, timeout=timeout)
        
        # Get best parameters
        self.best_params = self.study.best_params
        
        print("\n🏆 OPTIMIZATION COMPLETED!")
        print("="*50)
        print(f"Best validation loss: {self.study.best_value:.6f}")
        print(f"Number of trials: {len(self.study.trials)}")
        
        print(f"\n🎯 BEST HYPERPARAMETERS:")
        print("-" * 40)
        for key, value in self.best_params.items():
            print(f"{key:20s}: {value}")
        
        return self.best_params
    
    def build_best_model(self, input_shape, output_shape):
        """Build model with best parameters found by Optuna"""
        if self.best_params is None:
            raise ValueError("No optimization performed yet. Run optimize_hyperparameters() first.")
        
        model = Sequential()
        
        # Use best parameters
        lstm1_units = self.best_params['lstm1_units']
        lstm2_units = self.best_params['lstm2_units']
        lstm3_units = self.best_params['lstm3_units']
        dense1_units = self.best_params['dense1_units']
        dense2_units = self.best_params['dense2_units']
        dropout_rate = self.best_params['dropout_rate']
        recurrent_dropout = self.best_params['recurrent_dropout']
        l2_reg = self.best_params['l2_reg']
        learning_rate = self.best_params['learning_rate']
        batch_norm = self.best_params['batch_norm']
        
        # Build architecture
        model.add(LSTM(lstm1_units, return_sequences=True, input_shape=input_shape,
                      kernel_regularizer=l2(l2_reg), 
                      dropout=dropout_rate, recurrent_dropout=recurrent_dropout))
        if batch_norm:
            model.add(BatchNormalization())
        
        model.add(LSTM(lstm2_units, return_sequences=True,
                      kernel_regularizer=l2(l2_reg),
                      dropout=dropout_rate, recurrent_dropout=recurrent_dropout))
        if batch_norm:
            model.add(BatchNormalization())
        
        model.add(LSTM(lstm3_units, return_sequences=False,
                      kernel_regularizer=l2(l2_reg),
                      dropout=dropout_rate, recurrent_dropout=recurrent_dropout))
        if batch_norm:
            model.add(BatchNormalization())
        
        model.add(Dropout(dropout_rate + 0.1))
        
        model.add(Dense(dense1_units, activation='relu', kernel_regularizer=l2(l2_reg)))
        if batch_norm:
            model.add(BatchNormalization())
        model.add(Dropout(dropout_rate + 0.1))
        
        model.add(Dense(dense2_units, activation='relu', kernel_regularizer=l2(l2_reg)))
        model.add(Dropout(dropout_rate))
        
        model.add(Dense(output_shape[0] * output_shape[1], activation='linear'))
        model.add(tf.keras.layers.Reshape(output_shape))
        
        # Compile with best parameters
        model.compile(
            optimizer=Adam(learning_rate=learning_rate, clipnorm=1.0),
            loss='mse',
            metrics=['mae']
        )
        
        return model
    
    def train_optimized_model(self, validation_split=0.2, epochs=200):
        
        print("\n" + "="*70)
        print("TRAINING OPTIMIZED TEMPERATURE MAX LSTM MODEL")
        print("="*70)
        
        if self.best_params is None:
            raise ValueError("No optimization performed yet. Run optimize_hyperparameters() first.")
        
        # Create sequences
        X, y = self.create_sequences()
        
        if len(X) == 0:
            raise ValueError("No sequences created!")
        
        # Train-test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, shuffle=True
        )
        
        print(f"Training samples: {len(X_train)}, Test samples: {len(X_test)}")
        
        # Build optimized model
        input_shape = (self.sequence_length, X.shape[2])
        output_shape = (self.forecast_horizon, len(self.available_targets))
        
        self.model = self.build_best_model(input_shape, output_shape)
        
        print(f"\nOptimized model architecture:")
        self.model.summary()
        
        # Use best batch size
        batch_size = self.best_params.get('batch_size', 32)
        
        # Callbacks
        callbacks = [
            EarlyStopping(monitor='val_loss', patience=20, restore_best_weights=True, verbose=1),
            ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=10, min_lr=1e-7, verbose=1)
        ]
        
        # Train model
        print(f"\nTraining optimized model...")
        history = self.model.fit(
            X_train, y_train,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            callbacks=callbacks,
            verbose=1
        )
        
        # Evaluate
        print(f"\nEvaluating optimized model...")
        y_pred = self.model.predict(X_test, verbose=0)
        
        return self.evaluate_model(y_test, y_pred, history)
    
    def evaluate_model(self, y_true, y_pred, history):
        print("\n" + "="*70)
        print("OPTIMIZED TEMPERATURE MAX LSTM RESULTS")
        print("="*70)
        
        # Inverse transform predictions and true values to original scale
        y_true_original = np.zeros_like(y_true)
        y_pred_original = np.zeros_like(y_pred)
        
        for day in range(self.forecast_horizon):
            y_true_original[:, day, :] = self.scaler_targets.inverse_transform(y_true[:, day, :])
            y_pred_original[:, day, :] = self.scaler_targets.inverse_transform(y_pred[:, day, :])
        
        # Calculate metrics for each target variable and forecast day
        results = {}
        
        for i, target_name in enumerate(self.available_targets):
            print(f"\n🌡️ {target_name}:")
            print("-" * 50)
            
            target_results = {
                'mae': [],
                'rmse': [],
                'r2': [],
                'mape': []
            }
            
            for day in range(self.forecast_horizon):
                y_true_day = y_true_original[:, day, i]
                y_pred_day = y_pred_original[:, day, i]
                
                mae = mean_absolute_error(y_true_day, y_pred_day)
                rmse = np.sqrt(mean_squared_error(y_true_day, y_pred_day))
                r2 = r2_score(y_true_day, y_pred_day)
                
                # Calculate MAPE (Mean Absolute Percentage Error)
                mape = np.mean(np.abs((y_true_day - y_pred_day) / (y_true_day + 1e-8))) * 100
                
                target_results['mae'].append(mae)
                target_results['rmse'].append(rmse)
                target_results['r2'].append(r2)
                target_results['mape'].append(mape)
                
                print(f"  Day {day+1}: MAE={mae:.3f}, RMSE={rmse:.3f}, R²={r2:.3f}, MAPE={mape:.2f}%")
            
            # Calculate averages
            avg_mae = np.mean(target_results['mae'])
            avg_rmse = np.mean(target_results['rmse'])
            avg_r2 = np.mean(target_results['r2'])
            avg_mape = np.mean(target_results['mape'])
            
            target_results['avg_mae'] = avg_mae
            target_results['avg_rmse'] = avg_rmse
            target_results['avg_r2'] = avg_r2
            target_results['avg_mape'] = avg_mape
            
            print(f"  Average: MAE={avg_mae:.3f}, RMSE={avg_rmse:.3f}, R²={avg_r2:.3f}, MAPE={avg_mape:.2f}%")
            
            results[target_name] = target_results
        
        # Overall performance summary
        print(f"\n📊 OVERALL PERFORMANCE SUMMARY:")
        print("="*50)
        
        all_maes = [results[target]['avg_mae'] for target in self.available_targets]
        all_rmses = [results[target]['avg_rmse'] for target in self.available_targets]
        all_r2s = [results[target]['avg_r2'] for target in self.available_targets]
        all_mapes = [results[target]['avg_mape'] for target in self.available_targets]
        
        print(f"Overall Average MAE: {np.mean(all_maes):.3f}")
        print(f"Overall Average RMSE: {np.mean(all_rmses):.3f}")
        print(f"Overall Average R²: {np.mean(all_r2s):.3f}")
        print(f"Overall Average MAPE: {np.mean(all_mapes):.2f}%")
        
        # Optimization summary
        if self.best_params:
            print(f"\n🔧 OPTIMIZATION SUMMARY:")
            print("-" * 40)
            print(f"Best validation loss: {self.study.best_value:.6f}")
            print(f"Number of trials completed: {len(self.study.trials)}")
            print(f"Best LSTM architecture: {self.best_params['lstm1_units']}-{self.best_params['lstm2_units']}-{self.best_params['lstm3_units']}")
            print(f"Best Dense architecture: {self.best_params['dense1_units']}-{self.best_params['dense2_units']}")
            print(f"Best learning rate: {self.best_params['learning_rate']:.6f}")
            print(f"Best dropout rate: {self.best_params['dropout_rate']:.3f}")
        
        return results, history, y_true_original, y_pred_original
    
    def predict_future(self, recent_data):
        if isinstance(recent_data, pd.DataFrame):
            recent_scaled = self.scaler_features.transform(recent_data[self.feature_cols])
        elif isinstance(recent_data, np.ndarray):
            if recent_data.shape[1] == len(self.feature_cols):
                recent_scaled = self.scaler_features.transform(recent_data)
            else:
                recent_scaled = recent_data
        else:
            raise ValueError("recent_data must be a DataFrame or NumPy array")

        input_seq = recent_scaled[-self.sequence_length:].reshape(1, self.sequence_length, -1)
        prediction_scaled = self.model.predict(input_seq, verbose=0)

        # Inverse transform
        prediction_original = np.zeros_like(prediction_scaled)
        for day in range(self.forecast_horizon):
            prediction_original[0, day, :] = self.scaler_targets.inverse_transform(
                prediction_scaled[0, day, :].reshape(1, -1)
            )

        predicted_values = prediction_original[0, :, 0]  # shape: (forecast_horizon,)

        return predicted_values

    def plot_training_history(self, history):
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))
        
        # Loss
        ax1.plot(history.history['loss'], label='Training Loss')
        ax1.plot(history.history['val_loss'], label='Validation Loss')
        ax1.set_title('Optimized Model Loss')
        ax1.set_xlabel('Epoch')
        ax1.set_ylabel('Loss')
        ax1.legend()
        
        # MAE
        ax2.plot(history.history['mae'], label='Training MAE')
        ax2.plot(history.history['val_mae'], label='Validation MAE')
        ax2.set_title('Optimized Model MAE')
        ax2.set_xlabel('Epoch')
        ax2.set_ylabel('MAE')
        ax2.legend()
        
        plt.tight_layout()
        plt.show()
    
    def plot_optimization_history(self):
        
        if self.study is None:
            print("No optimization study available to plot.")
            return
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))
        
        # Optimization history
        values = [trial.value for trial in self.study.trials if trial.value is not None]
        ax1.plot(values)
        ax1.set_title('Optimization History')
        ax1.set_xlabel('Trial')
        ax1.set_ylabel('Validation Loss')
        ax1.grid(True)
        
        # Parameter importance (if available)
        try:
            importance = optuna.importance.get_param_importances(self.study)
            params = list(importance.keys())
            importances = list(importance.values())
            
            ax2.barh(params, importances)
            ax2.set_title('Parameter Importance')
            ax2.set_xlabel('Importance')
        except:
            ax2.text(0.5, 0.5, 'Parameter importance\nnot available', 
                    ha='center', va='center', transform=ax2.transAxes)
        
        plt.tight_layout()
        plt.show()


class HumidityMaxLSTM:
    def __init__(self, df, sequence_length=10, forecast_horizon=3):
        """
        Dedicated LSTM model for humidity max prediction
        """
        self.df = df.copy()
        self.sequence_length = sequence_length
        self.forecast_horizon = forecast_horizon
        self.scaler_features = None
        self.scaler_targets = None
        self.model = None
        
        # Temperature and humidity target columns
        self.target_cols = [ 
            'relative_humidity_2m_max (%)'
        ]
        
    def preprocess_data(self):
        """Preprocess data specifically for max humidity prediction"""
        print("🧹 Preprocessing data for max humidity prediction...")
        df = self.df.copy()
        
        # Check which target columns are available
        available_targets = [col for col in self.target_cols if col in df.columns]
        if not available_targets:
            raise ValueError(f"None of the target columns {self.target_cols} found in the dataframe")
        
        self.available_targets = available_targets
        print(f"Available target columns: {available_targets}")
        
        # Handle missing values for targets
        for col in available_targets:
            df[col] = df[col].fillna(method='ffill').fillna(method='bfill')
            df[col] = df[col].interpolate(method='linear')
            df[col].fillna(df[col].median(), inplace=True)
        
        # Remove rows with any missing target values
        df = df.dropna(subset=available_targets)
        
        # Define feature columns (exclude date, weather_condition, and target columns)
        exclude_cols = ['date', 'weather_condition','relative_humidity_2m_min (%)','temperature_2m_min (°C)', 'temperature_2m_max (°C)'] + available_targets
        feature_cols = [col for col in df.columns if col not in exclude_cols]
        
        # Handle missing values for features
        numeric_cols = df[feature_cols].select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            df[col] = df[col].fillna(method='ffill').fillna(method='bfill')
            df[col] = df[col].interpolate(method='linear')
            df[col].fillna(df[col].median(), inplace=True)
        
        # Scale features
        self.scaler_features = StandardScaler()
        df[feature_cols] = self.scaler_features.fit_transform(df[feature_cols])
        
        # Scale targets
        self.scaler_targets = StandardScaler()
        df[available_targets] = self.scaler_targets.fit_transform(df[available_targets])
        
        # Store processed data
        self.df_processed = df
        self.feature_cols = feature_cols
        
        print(f"Feature columns ({len(feature_cols)}): {feature_cols[:5]}..." if len(feature_cols) > 5 else f"Feature columns: {feature_cols}")
        print(f"Target columns: {available_targets}")
        print(f"Data shape after preprocessing: {df.shape}")
        
        return df
    
    def create_sequences(self):
        """Create sequences for Maximum humidity prediction"""
        print(f"🪟 Creating sequences for Maximum humidity prediction...")
        
        X, y = [], []
        data = self.df_processed
        features = data[self.feature_cols].values
        targets = data[self.available_targets].values
        
        # Create sequences with sliding window
        for i in range(len(data) - self.sequence_length - self.forecast_horizon + 1):
            # Input sequence
            X_seq = features[i:i + self.sequence_length]
            
            # Target sequence (next forecast_horizon days)
            y_seq = targets[i + self.sequence_length:i + self.sequence_length + self.forecast_horizon]
            
            X.append(X_seq)
            y.append(y_seq)
        
        X = np.array(X)
        y = np.array(y)
        
        print(f"Created sequences: X={X.shape}, y={y.shape}")
        print(f"Input sequence length: {self.sequence_length}")
        print(f"Forecast horizon: {self.forecast_horizon}")
        print(f"Number of features: {X.shape[2]}")
        print(f"Number of target variables: {y.shape[2]}")
        
        return X, y
    
    def build_model(self, input_shape, output_shape):
        """Build LSTM model for Maximum humidity prediction"""
        model = Sequential([
            # First LSTM layer
            LSTM(128, return_sequences=True, input_shape=input_shape,
                 kernel_regularizer=l2(0.001), dropout=0.2, recurrent_dropout=0.2),
            BatchNormalization(),
            
            # Second LSTM layer
            LSTM(64, return_sequences=True,
                 kernel_regularizer=l2(0.001), dropout=0.2, recurrent_dropout=0.2),
            BatchNormalization(),
            
            # Third LSTM layer
            LSTM(32, return_sequences=False,
                 kernel_regularizer=l2(0.001), dropout=0.2, recurrent_dropout=0.2),
            BatchNormalization(),
            Dropout(0.3),
            
            # Dense layers for multi-step prediction
            Dense(64, activation='relu', kernel_regularizer=l2(0.001)),
            BatchNormalization(),
            Dropout(0.3),
            
            Dense(32, activation='relu', kernel_regularizer=l2(0.001)),
            Dropout(0.2),
            
            # Output layer - predict all forecast steps and variables at once
            Dense(output_shape[0] * output_shape[1], activation='linear'),
            
            # Reshape to (forecast_horizon, num_target_variables)
            tf.keras.layers.Reshape(output_shape)
        ])
        
        return model
    
    def train_model(self, validation_split=0.2, epochs=150, batch_size=32):
        """Train the Humidity max LSTM model"""
        print("\n" + "="*70)
        print("TRAINING HUMIDITY MAX LSTM MODEL")
        print("="*70)
        
        # Create sequences
        X, y = self.create_sequences()
        
        if len(X) == 0:
            raise ValueError("No sequences created!")
        
        # Train-test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, shuffle=True
        )
        
        print(f"Training samples: {len(X_train)}, Test samples: {len(X_test)}")
        
        # Build model
        input_shape = (self.sequence_length, X.shape[2])
        output_shape = (self.forecast_horizon, len(self.available_targets))
        
        self.model = self.build_model(input_shape, output_shape)
        
        # Compile model
        self.model.compile(
            optimizer=Adam(learning_rate=0.001, clipnorm=1.0),
            loss='mse',
            metrics=['mae']
        )
        
        print(f"\nModel architecture:")
        self.model.summary()
        
        # Callbacks
        callbacks = [
            EarlyStopping(monitor='val_loss', patience=15, restore_best_weights=True, verbose=1),
            ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=8, min_lr=1e-7, verbose=1)
        ]
        
        # Train model
        print(f"\nTraining model...")
        history = self.model.fit(
            X_train, y_train,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            callbacks=callbacks,
            verbose=1
        )
        
        # Evaluate
        print(f"\nEvaluating model...")
        y_pred = self.model.predict(X_test, verbose=0)
        
        return self.evaluate_model(y_test, y_pred, history)
    
    def evaluate_model(self, y_true, y_pred, history):
        """Evaluate the humidity max model"""
        print("\n" + "="*70)
        print("HUMIDITY MAX LSTM RESULTS")
        print("="*70)
        
        # Inverse transform predictions and true values to original scale
        y_true_original = np.zeros_like(y_true)
        y_pred_original = np.zeros_like(y_pred)
        
        for day in range(self.forecast_horizon):
            y_true_original[:, day, :] = self.scaler_targets.inverse_transform(y_true[:, day, :])
            y_pred_original[:, day, :] = self.scaler_targets.inverse_transform(y_pred[:, day, :])
        
        # Calculate metrics for each target variable and forecast day
        results = {}
        
        for i, target_name in enumerate(self.available_targets):
            print(f"\n🌡️ {target_name}:")
            print("-" * 50)
            
            target_results = {
                'mae': [],
                'rmse': [],
                'r2': [],
                'mape': []
            }
            
            for day in range(self.forecast_horizon):
                y_true_day = y_true_original[:, day, i]
                y_pred_day = y_pred_original[:, day, i]
                
                mae = mean_absolute_error(y_true_day, y_pred_day)
                rmse = np.sqrt(mean_squared_error(y_true_day, y_pred_day))
                r2 = r2_score(y_true_day, y_pred_day)
                
                # Calculate MAPE (Mean Absolute Percentage Error)
                mape = np.mean(np.abs((y_true_day - y_pred_day) / (y_true_day + 1e-8))) * 100
                
                target_results['mae'].append(mae)
                target_results['rmse'].append(rmse)
                target_results['r2'].append(r2)
                target_results['mape'].append(mape)
                
                print(f"  Day {day+1}: MAE={mae:.3f}, RMSE={rmse:.3f}, R²={r2:.3f}, MAPE={mape:.2f}%")
            
            # Calculate averages
            avg_mae = np.mean(target_results['mae'])
            avg_rmse = np.mean(target_results['rmse'])
            avg_r2 = np.mean(target_results['r2'])
            avg_mape = np.mean(target_results['mape'])
            
            target_results['avg_mae'] = avg_mae
            target_results['avg_rmse'] = avg_rmse
            target_results['avg_r2'] = avg_r2
            target_results['avg_mape'] = avg_mape
            
            print(f"  Average: MAE={avg_mae:.3f}, RMSE={avg_rmse:.3f}, R²={avg_r2:.3f}, MAPE={avg_mape:.2f}%")
            
            results[target_name] = target_results
        
        # Overall performance summary
        print(f"\n📊 OVERALL PERFORMANCE SUMMARY:")
        print("="*50)
        
        all_maes = [results[target]['avg_mae'] for target in self.available_targets]
        all_rmses = [results[target]['avg_rmse'] for target in self.available_targets]
        all_r2s = [results[target]['avg_r2'] for target in self.available_targets]
        all_mapes = [results[target]['avg_mape'] for target in self.available_targets]
        
        print(f"Overall Average MAE: {np.mean(all_maes):.3f}")
        print(f"Overall Average RMSE: {np.mean(all_rmses):.3f}")
        print(f"Overall Average R²: {np.mean(all_r2s):.3f}")
        print(f"Overall Average MAPE: {np.mean(all_mapes):.2f}%")
        
        # Best and worst performing variables
        best_target = min(results.keys(), key=lambda x: results[x]['avg_mae'])
        worst_target = max(results.keys(), key=lambda x: results[x]['avg_mae'])
        
        print(f"\n🏆 Best performing variable: {best_target} (MAE: {results[best_target]['avg_mae']:.3f})")
        print(f"⚠️  Worst performing variable: {worst_target} (MAE: {results[worst_target]['avg_mae']:.3f})")
        
        return results, history, y_true_original, y_pred_original
    
    def predict_future(self, recent_data):
        if isinstance(recent_data, pd.DataFrame):
            recent_scaled = self.scaler_features.transform(recent_data[self.feature_cols])
        elif isinstance(recent_data, np.ndarray):
            if recent_data.shape[1] == len(self.feature_cols):
                recent_scaled = self.scaler_features.transform(recent_data)
            else:
                recent_scaled = recent_data
        else:
            raise ValueError("recent_data must be a DataFrame or NumPy array")

        input_seq = recent_scaled[-self.sequence_length:].reshape(1, self.sequence_length, -1)
        prediction_scaled = self.model.predict(input_seq, verbose=0)

        # Inverse transform
        prediction_original = np.zeros_like(prediction_scaled)
        for day in range(self.forecast_horizon):
            prediction_original[0, day, :] = self.scaler_targets.inverse_transform(
                prediction_scaled[0, day, :].reshape(1, -1)
            )

        predicted_values = prediction_original[0, :, 0]  # shape: (forecast_horizon,)

        return predicted_values
    
    def plot_training_history(self, history):
        """Plot training history"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))
        
        # Loss
        ax1.plot(history.history['loss'], label='Training Loss')
        ax1.plot(history.history['val_loss'], label='Validation Loss')
        ax1.set_title('Model Loss')
        ax1.set_xlabel('Epoch')
        ax1.set_ylabel('Loss')
        ax1.legend()
        
        # MAE
        ax2.plot(history.history['mae'], label='Training MAE')
        ax2.plot(history.history['val_mae'], label='Validation MAE')
        ax2.set_title('Model MAE')
        ax2.set_xlabel('Epoch')
        ax2.set_ylabel('MAE')
        ax2.legend()
        
        plt.tight_layout()
        plt.show()

        