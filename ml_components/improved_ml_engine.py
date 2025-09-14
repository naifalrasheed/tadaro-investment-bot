import numpy as np
import pandas as pd
import logging
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.feature_selection import VarianceThreshold
from sklearn.model_selection import cross_val_score


class ImprovedMLEngine:
    def __init__(self):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        self.feature_scaler = StandardScaler()
        self.target_scaler = StandardScaler()
        self.models = {}
        self.setup_models()  # Initialize models without features and targets

    def setup_models(self, features: np.ndarray = None, targets: np.ndarray = None):
        """Initialize models with optional hyperparameter optimization."""
        try:
            if features is not None and targets is not None and len(features) > 0:
                best_params = self.optimize_hyperparameters(features, targets)
                self.models['price_prediction'] = MLPRegressor(**best_params)
            else:
                # Default MLP setup if no optimization is possible
                self.models['price_prediction'] = MLPRegressor(
                    hidden_layer_sizes=(128, 64, 32),
                    activation='relu',
                    solver='adam',
                    alpha=0.01,
                    learning_rate='adaptive',
                    max_iter=1500,
                    early_stopping=True,
                    validation_fraction=0.2,
                    n_iter_no_change=20,
                    verbose=False
                )

            self.models['validation'] = RandomForestRegressor(
                n_estimators=100,
                max_depth=8,
                min_samples_split=5,
                min_samples_leaf=2,
                max_features='sqrt',
                random_state=42
            )
        except Exception as e:
            self.logger.error(f"Error setting up models: {str(e)}")

    def prepare_features(self, data: pd.DataFrame, symbol: str = None) -> tuple:
        """Prepare enhanced feature set with optional symbol-based features."""
        try:
            features = pd.DataFrame(index=data.index)

            # Basic price features
            features['returns'] = data['Close'].pct_change()
            features['log_returns'] = np.log(data['Close'] / data['Close'].shift(1))

            # Moving averages and trends
            for window in [5, 10, 20, 50]:
                features[f'ma_{window}'] = data['Close'].rolling(window=window).mean() / data['Close'] - 1
                features[f'vol_{window}'] = features['returns'].rolling(window=window).std()
                features[f'trend_{window}'] = (data['Close'] > data['Close'].shift(window)).astype(int)

            # Price channels
            for window in [10, 20]:
                features[f'upper_channel_{window}'] = data['High'].rolling(window).max() / data['Close'] - 1
                features[f'lower_channel_{window}'] = data['Low'].rolling(window).min() / data['Close'] - 1

            # Volume features
            features['volume_ma5'] = data['Volume'].rolling(window=5).mean() / data['Volume'] - 1
            features['volume_ma20'] = data['Volume'].rolling(window=20).mean() / data['Volume'] - 1
            features['volume_returns'] = data['Volume'].pct_change()

            # Volatility features
            features['high_low_ratio'] = (data['High'] - data['Low']) / data['Close']
            features['close_to_high'] = (data['Close'] - data['Low']) / (data['High'] - data['Low'])

            # Momentum indicators
            features['rsi_14'] = self.calculate_rsi(data['Close'], 14)
            features['roc_10'] = (data['Close'] - data['Close'].shift(10)) / data['Close'].shift(10)

            # Add sentiment score if symbol is provided
            if symbol:
                features['sentiment_score'] = self.get_sentiment_score(symbol)

            # Handle NaN values
            features = features.ffill().bfill()
            
            # Create targets
            targets = data['Close'].pct_change().shift(-1).fillna(0)
            
            # Filter features before returning
            if len(features) > 0:
                # Log feature shape for debugging
                self.logger.debug(f"Features Shape Before Filtering: {features.shape}")
                
                # Apply VarianceThreshold with more conservative threshold
                if features.shape[1] > 2:  # Only apply if we have enough features
                    try:
                        selector = VarianceThreshold(threshold=0.0001)  # Lower threshold to avoid removing too many features
                        features_array = selector.fit_transform(features.values)
                        
                        # Check if we still have features after selection
                        if features_array.shape[1] > 0:
                            selected_features = pd.DataFrame(
                                features_array,
                                index=features.index,
                                columns=features.columns[selector.get_support()]
                            )
                            self.logger.debug(f"Features Shape After Filtering: {selected_features.shape}")
                            return selected_features, targets
                    except Exception as e:
                        self.logger.warning(f"Feature selection error, using original features: {str(e)}")
                
                # Return original features if selection fails or not applicable
                self.logger.debug("Using original features without variance filtering")
                return features, targets
            
            return features, targets

        except Exception as e:
            self.logger.error(f"Error preparing features: {str(e)}")
            return pd.DataFrame(), pd.Series()

    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI (Relative Strength Index) for the given prices."""
        try:
            delta = prices.diff()
            gain = delta.where(delta > 0, 0).rolling(window=period).mean()
            loss = -delta.where(delta < 0, 0).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi.fillna(0)  # Replace NaN values with 0
        except Exception as e:
            self.logger.error(f"Error calculating RSI: {str(e)}")
            return pd.Series([0] * len(prices), index=prices.index)

    def get_sentiment_score(self, symbol: str) -> float:
        """Fetch sentiment score for the given stock symbol.
        
        Note: This is a placeholder. In a production system, this would
        call an actual sentiment analysis service or API.
        """
        try:
            # Replace with actual sentiment analysis API call in production
            self.logger.info(f"Getting sentiment score for {symbol} (placeholder)")
            return 0.5  # Placeholder neutral sentiment
        except Exception as e:
            self.logger.error(f"Error fetching sentiment score for {symbol}: {str(e)}")
            return 0.0

    def train_model(self, features: np.ndarray, targets: np.ndarray, validation_split: float = 0.2) -> dict:
        """Train models with improved validation."""
        try:
            # Scale features and targets
            X_scaled = self.feature_scaler.fit_transform(features)
            y_scaled = self.target_scaler.fit_transform(targets.reshape(-1, 1)).ravel()

            # Split indices
            split_idx = int(len(features) * (1 - validation_split))
            X_train = X_scaled[:split_idx]
            X_val = X_scaled[split_idx:]
            y_train = y_scaled[:split_idx]
            y_val = y_scaled[split_idx:]

            if X_train.shape[0] == 0 or X_val.shape[0] == 0:
                raise ValueError("Insufficient samples in training or validation set.")

            # Setup models with features and targets for hyperparameter optimization
            self.setup_models(X_train, y_train)

            # Train neural network
            self.models['price_prediction'].fit(X_train, y_train)

            # Train random forest for validation
            self.models['validation'].fit(X_train, y_train)

            # Calculate scores
            nn_train_score = self.models['price_prediction'].score(X_train, y_train)
            nn_val_score = self.models['price_prediction'].score(X_val, y_val)
            rf_val_score = self.models['validation'].score(X_val, y_val)

            return {
                'train_score': nn_train_score,
                'val_score': nn_val_score,
                'rf_score': rf_val_score
            }

        except Exception as e:
            self.logger.error(f"Error training model: {str(e)}")
            return {}

    def optimize_hyperparameters(self, features: np.ndarray, targets: np.ndarray) -> dict:
        """Simplified hyperparameter tuning.
        
        Note: In a production system, this would implement proper
        hyperparameter optimization using grid search, random search,
        or Bayesian optimization.
        """
        return {
            "hidden_layer_sizes": (128, 64, 32),
            "activation": "relu",
            "solver": "adam",
            "alpha": 0.01,
            "learning_rate": "adaptive",
            "max_iter": 1500,
        }

    def predict(self, features: np.ndarray) -> tuple:
        """Make predictions with confidence scores"""
        try:
            X_scaled = self.feature_scaler.transform(features)
            
            nn_pred = self.models['price_prediction'].predict(X_scaled)
            rf_pred = self.models['validation'].predict(X_scaled)
            
            nn_pred_unscaled = self.target_scaler.inverse_transform(nn_pred.reshape(-1, 1)).ravel()
            rf_pred_unscaled = self.target_scaler.inverse_transform(rf_pred.reshape(-1, 1)).ravel()
            
            final_pred = 0.6 * nn_pred_unscaled + 0.4 * rf_pred_unscaled
            
            # Improved confidence calculation
            pred_diff = np.abs(nn_pred_unscaled - rf_pred_unscaled)
            avg_pred = np.abs(final_pred).mean()
            
            # Base confidence on model agreement and prediction magnitude
            base_confidence = 100 * np.exp(-pred_diff / (avg_pred + 1e-6))
            magnitude_factor = min(abs(final_pred[0]) * 100, 100)  # Scale based on prediction size
            
            # Combine factors with weights
            confidence = 0.7 * base_confidence + 0.3 * magnitude_factor
            confidence = float(np.clip(confidence.item() if isinstance(confidence, np.ndarray) else confidence, 0, 100))
            
            # Log prediction details at debug level
            if self.logger.isEnabledFor(logging.DEBUG):
                self.logger.debug(f"Prediction details - diff: {pred_diff}, avg: {avg_pred}, confidence: {confidence}")
            
            return float(final_pred[0]), confidence
            
        except Exception as e:
            self.logger.error(f"Error making prediction: {str(e)}")
            return 0.0, 0.0