from ml_components.improved_ml_engine import ImprovedMLEngine
import yfinance as yf
import pandas as pd

def test_new_features(symbol: str = "AAPL"):
    print(f"\nTesting Improved ML with New Features for {symbol}")
    print("-" * 50)

    ml_engine = ImprovedMLEngine()

    # Fetch data
    end_date = pd.Timestamp.now()
    start_date = end_date - pd.Timedelta(days=750)  # 2 years of data
    stock = yf.Ticker(symbol)
    data = stock.history(start=start_date, end=end_date)

    if data.empty:
        print("Error: No data retrieved!")
        return

    print(f"Retrieved {len(data)} days of data.")

    # Prepare features
    features_df = ml_engine.prepare_features(data)
    if features_df.empty:
        print("Error: No features prepared!")
        return

    print(f"Features prepared: {features_df.columns.tolist()}")

    # Train and predict
    training_features = features_df.iloc[:-1].values
    training_targets = data['Close'].pct_change().shift(-1).iloc[1:-1].values
    latest_features = features_df.iloc[-1:].values

    if len(training_features) < 200:
        print("Error: Insufficient training data.")
        return

    print(f"Training with {len(training_features)} samples.")
    training_results = ml_engine.train_model(training_features, training_targets)

    print("\nTraining Results:")
    for metric, value in training_results.items():
        print(f"{metric}: {value:.4f}" if isinstance(value, float) else f"{metric}: {value}")

    prediction, confidence = ml_engine.predict(latest_features)

    print("\nPrediction Results:")
    print(f"Current Price: ${data['Close'].iloc[-1]:.2f}")
    print(f"Predicted Price: ${data['Close'].iloc[-1] * (1 + prediction):.2f}")
    print(f"Expected Return: {prediction:.2%}")
    print(f"Prediction Confidence: {confidence:.2f}%")

if __name__ == "__main__":
    test_new_features("AAPL")