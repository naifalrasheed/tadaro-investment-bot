import sys
import os
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from ml_components.deep_learning import DeepLearningEngine
import yfinance as yf
from sklearn.preprocessing import MinMaxScaler, StandardScaler
import warnings
warnings.filterwarnings('ignore')  # Suppress warnings

def calculate_market_metrics(symbol: str, data: pd.DataFrame) -> dict:
    """Calculate market metrics safely"""
    try:
        # Get S&P 500 data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        market_data = yf.download('^GSPC', start=start_date, end=end_date, progress=False)
        
        # Calculate returns
        stock_returns = data['Close'].pct_change().dropna()
        market_returns = market_data['Close'].pct_change().dropna()
        
        # Calculate volatility
        volatility = stock_returns.std() * np.sqrt(252)
        
        # Calculate beta
        if len(stock_returns) > 0 and len(market_returns) > 0:
            # Align dates
            common_index = stock_returns.index.intersection(market_returns.index)
            if len(common_index) > 0:
                stock_returns_aligned = stock_returns[common_index]
                market_returns_aligned = market_returns[common_index]
                
                # Calculate beta
                covariance = np.cov(stock_returns_aligned, market_returns_aligned)[0][1]
                market_variance = np.var(market_returns_aligned)
                beta = covariance / market_variance if market_variance != 0 else np.nan
            else:
                beta = np.nan
        else:
            beta = np.nan
            
        return {
            'volatility': volatility,
            'beta': beta
        }
    except Exception as e:
        print(f"Error calculating market metrics: {str(e)}")
        return {'volatility': np.nan, 'beta': np.nan}

def test_single_stock(symbol: str = "AAPL"):
    """Test deep learning prediction for a single stock"""
    print(f"\nTesting deep learning prediction for {symbol}")
    print("-" * 50)
    
    # Initialize engine and scalers
    dl_engine = DeepLearningEngine()
    feature_scaler = StandardScaler()
    target_scaler = StandardScaler()
    
    try:
        # Get more historical data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=1000)
        
        print(f"Fetching data for {symbol} from {start_date.date()} to {end_date.date()}")
        stock = yf.Ticker(symbol)
        data = stock.history(period="2y")  # Use fixed period for consistency
        
        if len(data) < 200:
            print(f"Error: Insufficient data for {symbol}")
            return None
            
        print(f"Retrieved {len(data)} days of data")
        
        # Calculate daily returns first
        data['Returns'] = data['Close'].pct_change()
        
        # Extract features
        print("\nExtracting and normalizing features...")
        features_df = pd.DataFrame()
        
        # Price-based features
        features_df['Returns'] = data['Returns']
        features_df['MA5'] = data['Close'].rolling(window=5).mean() / data['Close'] - 1
        features_df['MA20'] = data['Close'].rolling(window=20).mean() / data['Close'] - 1
        features_df['MA50'] = data['Close'].rolling(window=50).mean() / data['Close'] - 1
        
        # Volatility features
        features_df['Volatility'] = data['Returns'].rolling(window=20).std()
        features_df['HighLowRange'] = (data['High'] - data['Low']) / data['Close']
        
        # Volume features
        features_df['VolumeChange'] = data['Volume'].pct_change()
        features_df['VolumePriceRatio'] = data['Volume'] / data['Close']
        
        # Remove NaN values
        features_df = features_df.dropna()
        
        # Normalize features
        normalized_features = feature_scaler.fit_transform(features_df)
        features_df = pd.DataFrame(normalized_features, columns=features_df.columns, index=features_df.index)
        
        # Prepare sequences and targets
        sequence_length = 10  # Shorter sequence length
        sequences = []
        targets = []
        
        for i in range(len(features_df) - sequence_length):
            sequence = features_df.iloc[i:(i + sequence_length)].values
            target = data['Returns'].iloc[i + sequence_length]
            
            sequences.append(sequence.flatten())
            targets.append(target)
        
        sequences = np.array(sequences)
        targets = np.array(targets)
        
        # Remove extreme outliers from targets
        target_mean = np.mean(targets)
        target_std = np.std(targets)
        valid_mask = np.abs(targets - target_mean) <= 3 * target_std
        
        sequences = sequences[valid_mask]
        targets = targets[valid_mask]
        
        print(f"Created {len(sequences)} valid sequences")
        
        if len(sequences) == 0:
            print("Error: No valid sequences created")
            return None
        
        # Train model
        print("\nTraining price prediction model...")
        training_results = dl_engine.train_model('price_prediction', 
                                               sequences, 
                                               targets,
                                               validation_split=0.2)
        
        print("\nTraining Results:")
        train_score = training_results.get('train_score')
        val_score = training_results.get('val_score')
        
        print(f"Training Score: {train_score:.4f}")
        print(f"Validation Score: {val_score:.4f}")
        
        # Make prediction
        print("\nMaking prediction...")
        latest_sequence = sequences[-1].reshape(1, -1)
        prediction, confidence = dl_engine.predict('price_prediction', latest_sequence)
        
        current_price = data['Close'].iloc[-1]
        predicted_return = prediction[0]
        predicted_price = current_price * (1 + predicted_return)
        
        # Calculate market metrics
        market_metrics = calculate_market_metrics(symbol, data)
        
        print("\nPrediction Results:")
        print(f"Symbol: {symbol}")
        print(f"Current Price: ${current_price:.2f}")
        print(f"Predicted Next Price: ${predicted_price:.2f}")
        print(f"Expected Return: {predicted_return:.4%}")
        print(f"Prediction Confidence: {confidence:.2%}")
        
        print("\nMarket Statistics:")
        print(f"30-Day High: ${data['High'].iloc[-30:].max():.2f}")
        print(f"30-Day Low: ${data['Low'].iloc[-30:].min():.2f}")
        print(f"30-Day Average: ${data['Close'].iloc[-30:].mean():.2f}")
        print(f"Annualized Volatility: {market_metrics['volatility']:.2%}")
        
        if not np.isnan(market_metrics['beta']):
            print(f"Beta: {market_metrics['beta']:.2f}")
        else:
            print("Beta: Not available")
        
        return {
            'symbol': symbol,
            'current_price': current_price,
            'predicted_price': predicted_price,
            'predicted_return': predicted_return,
            'confidence': confidence,
            'training_score': train_score,
            'validation_score': val_score,
            'volatility': market_metrics['volatility'],
            'beta': market_metrics['beta']
        }
        
    except Exception as e:
        print(f"Error in testing {symbol}: {str(e)}")
        return None

def main():
    print("Starting Deep Learning Stock Analysis Test")
    print("=" * 50)
    
    stocks_to_test = ["AAPL", "MSFT", "GOOGL"]
    results = []
    
    for symbol in stocks_to_test:
        result = test_single_stock(symbol)
        if result:
            results.append(result)
            
            print("\nSummary for", symbol)
            print("-" * 30)
            print(f"Current Price: ${result['current_price']:.2f}")
            print(f"Predicted Price: ${result['predicted_price']:.2f}")
            print(f"Expected Return: {result['predicted_return']:.2%}")
            print(f"Confidence: {result['confidence']:.2%}")
            if not np.isnan(result['volatility']):
                print(f"Volatility: {result['volatility']:.2%}")
            if not np.isnan(result['beta']):
                print(f"Beta: {result['beta']:.2f}")
            
        print("\nPress Enter to continue...")
        input()

if __name__ == "__main__":
    main()