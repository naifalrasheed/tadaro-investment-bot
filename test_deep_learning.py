from datetime import datetime, timedelta
from ml_components.deep_learning import DeepLearningEngine
import unittest
import logging
import os
import sys
from pathlib import Path

# Add src directory to Python path
current_dir = Path(__file__).resolve().parent
ml_components_dir = current_dir.parent
src_dir = ml_components_dir.parent
sys.path.append(str(src_dir))

from ml_components.deep_learning import DeepLearningModel
import pandas as pd
import numpy as np

class TestDeepLearning(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures before all tests"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        cls.logger = logging.getLogger(__name__)
        
        try:
            cls.model = DeepLearningModel()
        except Exception as e:
            cls.logger.error(f"Error in setup: {str(e)}")
            raise

    def test_initialization(self):
        """Test if model can be initialized"""
        self.assertIsInstance(self.model, DeepLearningModel)
        self.logger.info("Model initialization successful")

def test_deep_learning():
    # Initialize engine
    dl_engine = DeepLearningEngine()
    
    # Get sample data
    symbol = "AAPL"
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    try:
        # Fetch data
        stock = yf.Ticker(symbol)
        data = stock.history(start=start_date, end=end_date)
        
        if data.empty:
            print("No data fetched")
            return
            
        # Extract features
        features_df = dl_engine.extract_advanced_features(data)
        
        if features_df.empty:
            print("Error extracting features")
            return
            
        # Create sequences
        sequences = dl_engine.create_feature_sequences(features_df)
        
        if len(sequences) == 0:
            print("Error creating sequences")
            return
            
        # Prepare target variable (next day's return)
        targets = data['Close'].pct_change().shift(-1).dropna().values[:-50]
        
        # Train model
        print("\nTraining price prediction model...")
        training_results = dl_engine.train_model('price_prediction', 
                                               sequences[:-1], 
                                               targets)
        
        print("\nTraining Results:")
        print(f"Training Score: {training_results.get('train_score', 'N/A')}")
        print(f"Validation Score: {training_results.get('val_score', 'N/A')}")
        
        # Make prediction
        latest_sequence = sequences[-1].reshape(1, -1)
        prediction, confidence = dl_engine.predict('price_prediction', 
                                                 latest_sequence)
        
        print(f"\nPrediction for {symbol}:")
        print(f"Expected Return: {prediction[0]:.4f}")
        print(f"Confidence: {confidence:.2f}")
        
    except Exception as e:
        print(f"Error in test: {str(e)}")

if __name__ == "__main__":
    test_deep_learning()