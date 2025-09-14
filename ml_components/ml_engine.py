import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor, RandomForestRegressor
from sklearn.neural_network import MLPRegressor
from typing import List, Dict, Tuple
import logging

class MarketMLEngine:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.scaler = StandardScaler()
        self.models = {}
        self.setup_models()
        
    def train_model(self, model_name: str, features: np.ndarray, targets: np.ndarray, validation_split: float = 0.2) -> Dict:
        """Train a machine learning model and evaluate its performance."""
        try:
            model = RandomForestRegressor(n_estimators=100, random_state=42)
            split_idx = int((1 - validation_split) * len(features))

            train_features, val_features = features[:split_idx], features[split_idx:]
            train_targets, val_targets = targets[:split_idx], targets[split_idx:]

            model.fit(train_features, train_targets)

            train_score = model.score(train_features, train_targets)
            val_score = model.score(val_features, val_targets)

            self.models[model_name] = model

            return {
                'train_score': train_score,
                'val_score': val_score
            }
        except Exception as e:
            logging.error(f"Error training model '{model_name}': {str(e)}")
            return {}

    def train_model(self, features: np.ndarray, targets: np.ndarray, validation_split: float = 0.2) -> dict:
        """Train models with improved validation."""
        try:
            X_scaled = self.feature_scaler.fit_transform(features)
            y_scaled = self.target_scaler.fit_transform(targets.reshape(-1, 1)).ravel()

            split_idx = int(len(features) * (1 - validation_split))
            X_train, X_val = X_scaled[:split_idx], X_scaled[split_idx:]
            y_train, y_val = y_scaled[:split_idx], y_scaled[split_idx:]

            self.models['price_prediction'].fit(X_train, y_train)
            self.models['validation'].fit(X_train, y_train)

            train_score = self.models['price_prediction'].score(X_train, y_train)
            val_score = self.models['price_prediction'].score(X_val, y_val)
            rf_score = self.models['validation'].score(X_val, y_val)

            print(f"Debug - Train Score: {train_score}")
            print(f"Debug - Validation Score: {val_score}")
            print(f"Debug - RF Score: {rf_score}")

            return {
                'train_score': train_score,
                'val_score': val_score,
                'rf_score': rf_score
            }
        except Exception as e:
            self.logger.error(f"Error training model: {e}")
            return {}
 
    def predict(self, features: np.ndarray) -> Tuple[float, float]:
        """
        Predict using the trained model and calculate confidence.

        Parameters:
        - features (np.ndarray): Input feature array for prediction.

        Returns:
        - Tuple[float, float]: Predicted value and confidence score.
        """
        try:
            model = self.models.get('price_prediction', None)
            if not model:
                raise ValueError("Model 'price_prediction' is not trained.")

            prediction = model.predict(features)
            confidence = self.calculate_prediction_confidence(prediction[0])

            print(f"Debug - Raw Confidence Before Conversion: {confidence}")
            confidence = float(confidence)
            print(f"Debug - Converted Confidence to Scalar: {confidence}")

            return prediction[0], confidence
        except Exception as e:
            logging.error(f"Error in prediction: {str(e)}")
            return 0.0, 0.0
    
    def calculate_prediction_confidence(self, prediction: float, baseline_error: float = 0.05) -> float:
        """Calculate confidence level with controlled scaling."""
        try:
            max_confidence = 1.0
            min_confidence = 0.0

            # Confidence calculation logic
            raw_confidence = 1 - (abs(prediction) / baseline_error)
            confidence = max(min(raw_confidence, max_confidence), min_confidence) * 100

            return confidence
        except Exception as e:
            logging.error(f"Error calculating confidence: {str(e)}")
            return 0.0
            
    def setup_models(self):
        """Initialize different ML models for various tasks"""
        try:
            # Price prediction model using Gradient Boosting
            self.models['price_prediction'] = GradientBoostingRegressor(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=5
            )
            
            # Pattern recognition model using Random Forest
            self.models['pattern_recognition'] = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )
            
            # Neural network for complex patterns using MLPRegressor
            self.models['deep_learning'] = MLPRegressor(
                hidden_layer_sizes=(100, 50),
                activation='relu',
                solver='adam',
                random_state=42
            )
            
        except Exception as e:
            self.logger.error(f"Error setting up ML models: {str(e)}")

class MarketPatternLearner:
    def __init__(self, ml_engine: MarketMLEngine):
        self.ml_engine = ml_engine
        self.pattern_memory = {}
        
    def learn_patterns(self, market_data: pd.DataFrame) -> None:
        """
        Learn patterns from market data
        """
        try:
            # Extract features
            features = self.extract_features(market_data)
            
            # Train pattern recognition model
            self.ml_engine.models['pattern_recognition'].fit(
                features,
                self.generate_pattern_labels(market_data)
            )
            
        except Exception as e:
            logging.error(f"Error in pattern learning: {str(e)}")
    
    def extract_features(self, data: pd.DataFrame) -> np.ndarray:
        """Extract relevant features from market data"""
        features = []
        try:
            # Technical indicators
            data['SMA_20'] = data['Close'].rolling(window=20).mean()
            data['SMA_50'] = data['Close'].rolling(window=50).mean()
            data['RSI'] = self.calculate_rsi(data['Close'])
            
            # Volatility
            data['Volatility'] = data['Close'].rolling(window=20).std()
            
            # Price momentum
            data['Momentum'] = data['Close'] - data['Close'].shift(20)
            
            # Volume features
            data['Volume_SMA'] = data['Volume'].rolling(window=20).mean()
            data['Volume_Ratio'] = data['Volume'] / data['Volume_SMA']
            
            features = data[['SMA_20', 'SMA_50', 'RSI', 'Volatility', 
                           'Momentum', 'Volume_Ratio']].dropna().values
            
            return features
            
        except Exception as e:
            logging.error(f"Error extracting features: {str(e)}")
            return np.array([])

    def calculate_rsi(self, prices: pd.Series, periods: int = 14) -> pd.Series:
        """Calculate RSI technical indicator"""
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=periods).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=periods).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi
            
        except Exception as e:
            logging.error(f"Error calculating RSI: {str(e)}")
            return pd.Series()

    def generate_pattern_labels(self, data: pd.DataFrame) -> np.ndarray:
        """Generate labels for pattern recognition"""
        try:
            # Simple labeling based on price movement
            returns = data['Close'].pct_change()
            labels = np.where(returns > 0, 1, 0)
            return labels[len(labels)-len(self.extract_features(data)):]
        except Exception as e:
            logging.error(f"Error generating labels: {str(e)}")
            return np.array([])

class MarketPredictor:
    def __init__(self, ml_engine: MarketMLEngine):
        self.ml_engine = ml_engine
        
    def predict_price_movement(self, stock_data: pd.DataFrame, time_horizon: str = '1d') -> Dict:
        """Predict price movement for a given time horizon with enhanced confidence logic."""
        try:
            # Prepare features
            features = self.prepare_prediction_features(stock_data)
            
            if len(features) == 0:
                return {}
            
            # Make predictions with multiple models
            nn_pred = self.ml_engine.models['deep_learning'].predict(features.reshape(1, -1))
            rf_pred = self.ml_engine.models['price_prediction'].predict(features.reshape(1, -1))
            
            # Combine predictions for final output
            nn_pred_unscaled = nn_pred[0]
            rf_pred_unscaled = rf_pred[0]
            final_pred = 0.6 * nn_pred_unscaled + 0.4 * rf_pred_unscaled
            
            # Calculate confidence
            pred_diff = abs(nn_pred_unscaled - rf_pred_unscaled)
            max_diff = max(abs(nn_pred_unscaled), abs(rf_pred_unscaled))
            # Add epsilon to avoid division by zero or overly small values
            epsilon = 1e-5
            pred_diff = abs(nn_pred_unscaled - rf_pred_unscaled)
            epsilon = 1e-5
            max_diff = max(abs(nn_pred_unscaled).max(), abs(rf_pred_unscaled).max(), epsilon)
            confidence = (1 - pred_diff / max_diff) * 100

            confidence = min(max(confidence, 0), 100)  # Ensure within range.
            print(f"Debug - Normalized Confidence: {confidence}")

            return {
                'predicted_movement': final_pred,
                'confidence': confidence,
                'time_horizon': time_horizon
            }
        except Exception as e:
            logging.error(f"Error in price prediction: {str(e)}")
            return {}
    
    def prepare_prediction_features(self, stock_data: pd.DataFrame) -> np.ndarray:
        """Prepare features for price prediction"""
        try:
            learner = MarketPatternLearner(self.ml_engine)
            features = learner.extract_features(stock_data)

            # Debugging feature values
            # Debugging extracted feature values
            print(f"Debug - Extracted Features Shape: {features.shape}")
            print(f"Debug - Extracted Features: {features}")

            # Check for NaN or infinite values
            if np.isnan(features).any():
                print("Debug - Extracted Features contain NaN values.")
            if np.isinf(features).any():
                print("Debug - Extracted Features contain infinite values.")

            # Normalize features
            features = (features - np.mean(features, axis=0)) / np.std(features, axis=0)

            # Debug normalized feature statistics
            print(f"Debug - Normalized Features Shape: {features.shape}")
            print(f"Debug - Normalized Features Mean: {np.mean(features, axis=0)}")
            print(f"Debug - Normalized Features Std Dev: {np.std(features, axis=0)}")
            print(f"Debug - Normalized Features Min: {np.min(features, axis=0)}")
            print(f"Debug - Normalized Features Max: {np.max(features, axis=0)}")

            return features
        except Exception as e:
            logging.error(f"Error preparing features: {str(e)}")
            return np.array([])
    
    def calculate_prediction_confidence(self, prediction: float) -> float:
        """Calculate confidence level with controlled scaling to avoid extreme values."""
        try:
            max_prediction = 0.2  # Set a threshold to limit extreme scaling
            scaled_confidence = min(abs(prediction) / max_prediction, 1.0)  # Cap at 1.0
            # Normalize confidence to ensure it remains within [0, 100]
            confidence = scaled_confidence * 100
            print(f"Debug - Prediction: {prediction}, Scaled Confidence: {scaled_confidence}, Final Confidence: {confidence}")
            print(f"Debug - Prediction Difference: {pred_diff}, Max Difference: {max_diff}") # type: ignore
            return confidence
        except Exception as e:
            logging.error(f"Error calculating confidence: {str(e)}")
            return 0.0
