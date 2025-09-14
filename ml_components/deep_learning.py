import numpy as np
import pandas as pd
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
from typing import List, Dict, Tuple, Optional
import logging
import joblib
from datetime import datetime
import json

class DeepLearningEngine:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.models = {}
        self.scalers = {}
        self.model_metadata = {}
        self.setup_models()
        
    def setup_models(self):
        """Initialize multiple neural networks for different tasks"""
        try:
            # Price Prediction Network (Deeper network)
            self.models['price_prediction'] = MLPRegressor(
                hidden_layer_sizes=(256, 128, 64, 32),  # Deeper architecture
                activation='relu',
                solver='adam',
                alpha=0.0001,
                batch_size='auto',
                learning_rate='adaptive',
                max_iter=1000,
                early_stopping=True,
                validation_fraction=0.1,
                n_iter_no_change=50,
                verbose=True
            )
            
            # Pattern Recognition Network
            self.models['pattern_recognition'] = MLPRegressor(
                hidden_layer_sizes=(128, 64, 32),
                activation='relu',
                solver='adam',
                alpha=0.0001,
                batch_size='auto',
                learning_rate='adaptive',
                max_iter=1000
            )
            
            # Market Regime Detection Network
            self.models['regime_detection'] = MLPRegressor(
                hidden_layer_sizes=(64, 32, 16),
                activation='tanh',  # Different activation for regime detection
                solver='adam',
                alpha=0.0001,
                batch_size='auto',
                max_iter=1000
            )
            
            # Initialize scalers for each model
            for model_name in self.models.keys():
                self.scalers[model_name] = StandardScaler()
                
        except Exception as e:
            self.logger.error(f"Error setting up deep learning models: {str(e)}")

    def create_feature_sequences(self, data: pd.DataFrame, 
                               sequence_length: int = 50) -> np.ndarray:
        """Create sequences for temporal learning"""
        try:
            features = []
            for i in range(len(data) - sequence_length):
                sequence = data.iloc[i:(i + sequence_length)]
                features.append(sequence.values.flatten())
            return np.array(features)
        except Exception as e:
            self.logger.error(f"Error creating sequences: {str(e)}")
            return np.array([])

    def extract_advanced_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Extract advanced features for deep learning"""
        try:
            df = data.copy()
            
            # Technical Indicators
            df['SMA_20'] = df['Close'].rolling(window=20).mean()
            df['SMA_50'] = df['Close'].rolling(window=50).mean()
            df['EMA_20'] = df['Close'].ewm(span=20).mean()
            
            # Volatility Features
            df['Daily_Return'] = df['Close'].pct_change()
            df['Return_Volatility'] = df['Daily_Return'].rolling(window=20).std()
            df['High_Low_Range'] = (df['High'] - df['Low']) / df['Close']
            
            # Volume Features
            df['Volume_SMA'] = df['Volume'].rolling(window=20).mean()
            df['Volume_Ratio'] = df['Volume'] / df['Volume_SMA']
            
            # Price Patterns
            df['Price_Momentum'] = df['Close'] - df['Close'].shift(20)
            df['Price_Acceleration'] = df['Price_Momentum'] - df['Price_Momentum'].shift(1)
            
            # Trend Features
            df['Trend_Strength'] = abs(df['SMA_20'] - df['SMA_50']) / df['Close']
            
            return df.dropna()
            
        except Exception as e:
            self.logger.error(f"Error extracting advanced features: {str(e)}")
            return pd.DataFrame()

    def train_model(self, model_name: str, X: np.ndarray, y: np.ndarray, 
                   validation_split: float = 0.2) -> Dict:
        """Train a specific model with advanced tracking"""
        try:
            # Scale features
            X_scaled = self.scalers[model_name].fit_transform(X)
            
            # Split data
            split_idx = int(len(X) * (1 - validation_split))
            X_train, X_val = X_scaled[:split_idx], X_scaled[split_idx:]
            y_train, y_val = y[:split_idx], y[split_idx:]
            
            # Train model
            model = self.models[model_name]
            model.fit(X_train, y_train)
            
            # Calculate metrics
            train_score = model.score(X_train, y_train)
            val_score = model.score(X_val, y_val)
            
            # Store metadata
            self.model_metadata[model_name] = {
                'training_date': datetime.now().isoformat(),
                'train_score': train_score,
                'val_score': val_score,
                'input_shape': X.shape,
                'architecture': str(model.get_params()),
                'convergence': model.n_iter_
            }
            
            return {
                'train_score': train_score,
                'val_score': val_score,
                'iterations': model.n_iter_
            }
            
        except Exception as e:
            self.logger.error(f"Error training {model_name}: {str(e)}")
            return {}

    def predict(self, model_name: str, features: np.ndarray) -> Tuple[np.ndarray, float]:
        """Make predictions with confidence estimation"""
        try:
            # Scale features
            features_scaled = self.scalers[model_name].transform(features)
            
            # Get prediction
            prediction = self.models[model_name].predict(features_scaled)
            
            # Calculate confidence
            confidence = self.estimate_prediction_confidence(
                self.models[model_name], 
                features_scaled, 
                prediction
            )
            
            return prediction, confidence
            
        except Exception as e:
            self.logger.error(f"Error predicting with {model_name}: {str(e)}")
            return np.array([]), 0.0

    def estimate_prediction_confidence(self, model: MLPRegressor, features: np.ndarray, prediction: np.ndarray) -> float:
        """Estimate prediction confidence using model characteristics"""
        try:
            stability = max(min(1.0 - (model.loss_curve_[-1] / model.loss_curve_[0]), 1.0), 0.0)
            prediction_variance = np.std(model._forward_pass_fast(features)[0][-1])
            
            confidence = (stability * 0.6 + (1 / (1 + prediction_variance)) * 0.4) * 100
            confidence = min(max(confidence, 0), 100)  # Cap confidence between 0% and 100%
            
            print(f"Debug - Stability: {stability}, Prediction Variance: {prediction_variance}, Capped Confidence: {confidence}")
            return confidence
        except Exception as e:
            self.logger.error(f"Error estimating confidence: {str(e)}")
            return 0.0

    def save_model(self, model_name: str, path: str):
        """Save model and its metadata"""
        try:
            model_path = f"{path}/{model_name}_model.joblib"
            scaler_path = f"{path}/{model_name}_scaler.joblib"
            metadata_path = f"{path}/{model_name}_metadata.json"
            
            # Save model and scaler
            joblib.dump(self.models[model_name], model_path)
            joblib.dump(self.scalers[model_name], scaler_path)
            
            # Save metadata
            with open(metadata_path, 'w') as f:
                json.dump(self.model_metadata[model_name], f)
                
        except Exception as e:
            self.logger.error(f"Error saving {model_name}: {str(e)}")

    def load_model(self, model_name: str, path: str):
        """Load model and its metadata"""
        try:
            model_path = f"{path}/{model_name}_model.joblib"
            scaler_path = f"{path}/{model_name}_scaler.joblib"
            metadata_path = f"{path}/{model_name}_metadata.json"
            
            # Load model and scaler
            self.models[model_name] = joblib.load(model_path)
            self.scalers[model_name] = joblib.load(scaler_path)
            
            # Load metadata
            with open(metadata_path, 'r') as f:
                self.model_metadata[model_name] = json.load(f)
                
        except Exception as e:
            self.logger.error(f"Error loading {model_name}: {str(e)}")