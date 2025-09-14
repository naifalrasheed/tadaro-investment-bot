import unittest
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock
import logging

# Import the DeepLearningEngine class
from ml_components.deep_learning import DeepLearningEngine

class TestDeepLearningEngine(unittest.TestCase):
    def setUp(self):
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Initialize the deep learning engine
        self.engine = DeepLearningEngine()
    
    def test_initialization(self):
        """Test if the engine initializes correctly"""
        self.assertIsNotNone(self.engine.models)
        self.assertIsNotNone(self.engine.scalers)
        self.assertIn('price_prediction', self.engine.models)
        self.assertIn('pattern_recognition', self.engine.models)
        self.assertIn('regime_detection', self.engine.models)
        self.logger.info("Engine initialization successful")
    
    def test_create_feature_sequences(self):
        """Test sequence creation for temporal learning"""
        # Create dummy data
        dates = pd.date_range(start='2020-01-01', periods=100, freq='D')
        data = pd.DataFrame({
            'feature1': np.random.rand(100),
            'feature2': np.random.rand(100)
        }, index=dates)
        
        # Test with default sequence length (50)
        sequences = self.engine.create_feature_sequences(data)
        
        # Expected shape: (n_samples, sequence_length * n_features)
        expected_samples = 100 - 50  # (length - sequence_length)
        expected_features = 50 * 2  # sequence_length * n_features
        
        self.assertEqual(sequences.shape, (expected_samples, expected_features))
        
        # Test with custom sequence length
        custom_length = 30
        sequences = self.engine.create_feature_sequences(data, sequence_length=custom_length)
        
        # Expected shape: (n_samples, custom_length * n_features)
        expected_samples = 100 - custom_length
        expected_features = custom_length * 2
        
        self.assertEqual(sequences.shape, (expected_samples, expected_features))
    
    def test_extract_advanced_features(self):
        """Test feature extraction from price data"""
        # Create dummy price data
        dates = pd.date_range(start='2020-01-01', periods=100, freq='D')
        price_data = pd.DataFrame({
            'Open': np.random.normal(100, 2, 100),
            'High': np.random.normal(102, 2, 100),
            'Low': np.random.normal(98, 2, 100),
            'Close': np.random.normal(101, 2, 100),
            'Volume': np.random.randint(1000, 10000, 100)
        }, index=dates)
        
        # Extract features
        features_df = self.engine.extract_advanced_features(price_data)
        
        # Check if features were created
        expected_features = [
            'SMA_20', 'SMA_50', 'EMA_20', 'Daily_Return', 
            'Return_Volatility', 'High_Low_Range', 'Volume_SMA',
            'Volume_Ratio', 'Price_Momentum', 'Price_Acceleration',
            'Trend_Strength'
        ]
        
        for feature in expected_features:
            self.assertIn(feature, features_df.columns)
        
        # Check if NaN values were dropped
        self.assertFalse(features_df.isnull().any().any())
    
    @patch('ml_components.deep_learning.MLPRegressor')
    def test_train_model(self, mock_mlp):
        """Test model training functionality"""
        # Setup mock MLPRegressor
        mock_model = MagicMock()
        mock_model.score.return_value = 0.85
        mock_model.n_iter_ = 100
        mock_model.get_params.return_value = {'hidden_layer_sizes': (128, 64)}
        
        # Replace the actual model with our mock
        self.engine.models['price_prediction'] = mock_model
        
        # Create dummy training data
        X = np.random.rand(100, 10)
        y = np.random.rand(100)
        
        # Mock the scaler transform
        self.engine.scalers['price_prediction'] = MagicMock()
        self.engine.scalers['price_prediction'].fit_transform.return_value = X
        self.engine.scalers['price_prediction'].transform.return_value = X
        
        # Train the model
        results = self.engine.train_model('price_prediction', X, y)
        
        # Check if the model was trained
        mock_model.fit.assert_called_once()
        
        # Check if we got the expected results
        self.assertIn('train_score', results)
        self.assertIn('val_score', results)
        self.assertIn('iterations', results)
        self.assertEqual(results['train_score'], 0.85)
    
    @patch('ml_components.deep_learning.MLPRegressor')
    def test_predict(self, mock_mlp):
        """Test prediction functionality"""
        # Setup mock MLPRegressor
        mock_model = MagicMock()
        mock_model.predict.return_value = np.array([0.05])
        
        # Setup mock internal methods
        mock_model._forward_pass_fast.return_value = [np.array([[0.05, 0.04, 0.06]])]
        mock_model.loss_curve_ = [1.0, 0.5, 0.2]
        
        # Replace the actual model with our mock
        self.engine.models['price_prediction'] = mock_model
        
        # Create dummy features
        features = np.random.rand(1, 10)
        
        # Mock the scaler transform
        self.engine.scalers['price_prediction'] = MagicMock()
        self.engine.scalers['price_prediction'].transform.return_value = features
        
        # Make a prediction
        prediction, confidence = self.engine.predict('price_prediction', features)
        
        # Check if predict was called
        mock_model.predict.assert_called_once()
        
        # Check if we got a prediction and confidence
        self.assertEqual(len(prediction), 1)
        self.assertGreaterEqual(confidence, 0)
        self.assertLessEqual(confidence, 100)


if __name__ == '__main__':
    unittest.main()