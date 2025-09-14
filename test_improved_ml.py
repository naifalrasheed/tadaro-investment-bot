from ml_components.improved_ml_engine import ImprovedMLEngine
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def test_improved_prediction(symbol: str = "AAPL"):
    print(f"\nTesting improved ML prediction for {symbol}")
    print("-" * 50)
    
    # Initialize engine
    ml_engine = ImprovedMLEngine()
    
    try:
        # Fetch stock data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=750)  # 2 years of data
        print(f"Fetching data for {symbol}...")
        stock = yf.Ticker(symbol)
        data = stock.history(start=start_date, end=end_date)
        
        if len(data) < 200:
            print("Error: Insufficient data")
            return None
        print(f"Retrieved {len(data)} days of data")
        
        # Prepare features and calculate targets separately
        features_df = ml_engine.prepare_features(data, symbol)  # Now just getting features
        if features_df.empty:
            print("Error: Insufficient data for training.")
            return None

        # Calculate targets separately
        targets = data['Close'].pct_change().shift(-1)  # Next day returns
        targets = targets[:-1]  # Remove last row since we won't have a target for it

        # Align features and targets
        features = features_df[:-1]  # Remove last row to align with targets
        common_index = features.index.intersection(targets.index)
        features = features.loc[common_index]
        targets = targets.loc[common_index]
        
        print(f"Debug - Combined Features and Targets Shape: {features.shape}, {targets.shape}")
        
        # Split into training and prediction data
        training_features = features  # Already aligned above
        training_targets = targets    # Already aligned above
        latest_features = features_df.iloc[-1:]  # Use original features_df for prediction
        
        print(f"Training with {len(training_features)} samples")
        print(f"Features shape: {training_features.shape}")
        print(f"Targets shape: {training_targets.shape}")
        
        # Train the model
        training_results = ml_engine.train_model(training_features.values, training_targets.values)
        
        print("\nTraining Results:")
        print("-" * 30)
        for metric, value in training_results.items():
            if isinstance(value, (int, float)):
                print(f"{metric.replace('_', ' ').title()}: {value:.4f}")
        
        # Make prediction
        prediction, confidence = ml_engine.predict(latest_features.values)
        
        # Ensure confidence is scalar
        confidence = float(confidence.item() if isinstance(confidence, np.ndarray) else confidence)
        confidence = min(max(confidence, 0), 100)  # Ensure between 0-100
        print(f"Debug - Converted Confidence to Scalar: {confidence}")
        
        # Calculate predicted price
        current_price = data['Close'].iloc[-1]
        predicted_price = current_price * (1 + prediction)
        
        # Market statistics
        volatility = data['Close'].pct_change().std() * np.sqrt(252)
        market_stats = {
            'current_price': current_price,
            'predicted_price': predicted_price,
            'predicted_return': prediction,
            'confidence': confidence,
            'volatility': volatility,
            '30d_high': data['High'].iloc[-30:].max(),
            '30d_low': data['Low'].iloc[-30:].min(),
            '30d_avg': data['Close'].iloc[-30:].mean(),
            'volume_avg': data['Volume'].iloc[-30:].mean()
        }
        
        # Print detailed results
        print("\nPrediction Results:")
        print("-" * 30)
        print(f"Current Price: ${market_stats['current_price']:.2f}")
        print(f"Predicted Price: ${market_stats['predicted_price']:.2f}")
        print(f"Expected Return: {market_stats['predicted_return']:.2%}")
        print(f"Prediction Confidence: {market_stats['confidence']:.1f}%")
        
        print("\nMarket Statistics:")
        print("-" * 30)
        print(f"30-Day High: ${market_stats['30d_high']:.2f}")
        print(f"30-Day Low: ${market_stats['30d_low']:.2f}")
        print(f"30-Day Average: ${market_stats['30d_avg']:.2f}")
        print(f"Volatility (Annualized): {market_stats['volatility']:.2%}")
 
        return {
            'symbol': symbol,
            'market_stats': market_stats,
            'training_results': training_results
        }
        
    except Exception as e:
        print(f"Error in testing: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return None

def main():
    print("Starting Improved ML Stock Analysis")
    print("=" * 50)
    
    stocks = ["AAPL", "MSFT", "GOOGL"]
    results = []
    
    for symbol in stocks:
        result = test_improved_prediction(symbol)
        if result:
            results.append(result)
        
        if symbol != stocks[-1]:  # Don't prompt after last stock
            print("\nPress Enter to continue with next stock...")
            input()
    
    # Print summary
    if results:
        print("\nSummary of All Predictions:")
        print("=" * 50)
        for result in results:
            stats = result['market_stats']
            print(f"\n{result['symbol']}:")
            print(f"Current: ${stats['current_price']:.2f}")
            print(f"Predicted: ${stats['predicted_price']:.2f}")
            print(f"Return: {stats['predicted_return']:.2%}")
            print(f"Confidence: {stats['confidence']:.1f}%")
            print(f"Volatility: {stats['volatility']:.2%}")

if __name__ == "__main__":
    main()