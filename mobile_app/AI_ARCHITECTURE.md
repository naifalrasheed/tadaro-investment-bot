# Investment Bot AI Architecture

## Hybrid AI Approach

The Investment Bot implements a hybrid AI architecture combining custom ML models with Large Language Models (LLMs) to deliver personalized investment insights while maintaining natural language understanding capabilities.

## Architecture Overview

```
┌────────────────────────────────────────────────────────────┐
│                  Investment Bot AI System                  │
├────────────────┬─────────────────────┬────────────────────┤
│                │                     │                    │
│  Custom ML     │  Transformative     │  LLM Integration   │
│  Components    │  Learning Engine    │  (Claude/LLAMA/X)  │
│                │                     │                    │
└────────┬───────┴──────────┬──────────┴──────────┬─────────┘
         │                  │                     │
         ▼                  ▼                     ▼
┌────────────────┐ ┌────────────────────┐ ┌────────────────────┐
│                │ │                    │ │                    │
│ Stock Scoring  │ │ User Interaction   │ │ Natural Language   │
│ Algorithms     │ │ Database           │ │ Understanding      │
│                │ │                    │ │                    │
└────────────────┘ └────────────────────┘ └────────────────────┘
```

## 1. Custom ML Components

### Feature-Based Stock Scoring

The core of our custom ML approach uses a weighted feature scoring system:

```python
def calculate_stock_score(stock_data, feature_weights):
    score = 0
    
    # Price momentum scoring
    if 'price_momentum' in stock_data:
        score += stock_data['price_momentum'] * feature_weights.get('price_momentum', 0.1)
        
    # 52-week range position scoring
    if '52_week_range_position' in stock_data:
        score += stock_data['52_week_range_position'] * 100 * feature_weights.get('weekly_range', 0.1)
        
    # YTD performance scoring
    if 'ytd_performance' in stock_data:
        score += stock_data['ytd_performance'] * feature_weights.get('ytd_performance', 0.1)
        
    # News sentiment scoring
    if 'news_sentiment' in stock_data:
        score += stock_data['news_sentiment'] * 100 * feature_weights.get('news_sentiment', 0.1)
        
    # ROTC scoring
    if 'rotc' in stock_data:
        score += stock_data['rotc'] * feature_weights.get('rotc', 0.1)
        
    # P/E ratio scoring (lower is better, so invert)
    if 'pe_ratio' in stock_data and stock_data['pe_ratio'] > 0:
        pe_score = 25 / max(stock_data['pe_ratio'], 1) * feature_weights.get('pe_ratio', 0.1)
        score += pe_score
        
    # Dividend yield scoring
    if 'dividend_yield' in stock_data:
        score += stock_data['dividend_yield'] * feature_weights.get('dividend_yield', 0.1)
        
    # Sector preference bonus (20%)
    if 'sector' in stock_data and stock_data['sector'] in preferred_sectors:
        score *= 1.2
    
    return score
```

### Sector Preference Tracking

```python
def update_sector_preference(user_id, sector, score_change):
    """
    Update sector preference based on user behavior.
    
    Args:
        user_id: User identifier
        sector: Stock sector (e.g., "Technology")
        score_change: Positive or negative score change based on interaction
    """
    # Retrieve current preference
    current_pref = get_sector_preference(user_id, sector)
    
    # Apply bounded update
    new_score = current_pref + score_change
    # Bound between -10 and +10
    new_score = max(min(new_score, 10), -10)
    
    # Save updated preference
    save_sector_preference(user_id, sector, new_score)
```

### Technical Analysis Models

Our system implements multiple technical analysis models:

1. **RandomForestRegressor**: Price prediction based on technical indicators
2. **GradientBoostingClassifier**: Signal classification (Buy/Sell/Hold)
3. **LSTM Neural Network**: Time series prediction for short-term price movement

## 2. Transformative Learning Engine

### User Feedback Loop

```python
def record_feedback(user_id, stock_symbol, feedback_type, stock_data=None):
    """
    Record and process user feedback to continuously improve the model.
    
    Args:
        user_id: User identifier
        stock_symbol: Stock ticker symbol
        feedback_type: 'like', 'dislike', or 'purchase'
        stock_data: Optional stock metrics at time of feedback
    """
    # Store feedback in database
    store_feedback(user_id, stock_symbol, feedback_type, stock_data)
    
    # Update feature weights based on this feedback
    if stock_data:
        update_feature_weights(user_id, stock_data, feedback_type)
    
    # If sector information available, update sector preference
    if stock_data and 'sector' in stock_data:
        modifier = 1 if feedback_type in ('like', 'purchase') else -1
        update_sector_preference(user_id, stock_data['sector'], modifier)
```

### Feature Weight Adaptation

```python
def update_feature_weights(user_id, stock_data, feedback_type):
    """
    Adaptively update feature weights based on user feedback.
    
    Args:
        user_id: User identifier
        stock_data: Stock metrics and data
        feedback_type: 'like', 'dislike', or 'purchase'
    """
    # Get current weights
    weights = get_user_feature_weights(user_id)
    
    # Adjustment factor - stronger for purchases
    adjustment = 1.05 if feedback_type in ('like', 'purchase') else 0.95
    
    # For each feature, if it's strong and user liked it, increase weight
    # Or if it's weak and user disliked it, decrease weight
    if feedback_type in ('like', 'purchase'):
        # For positive feedback, increase weights of strong features
        if stock_data.get('price_momentum', 0) > 50:
            weights['price_momentum_weight'] *= adjustment
            
        if stock_data.get('52_week_range_position', 0) > 0.7:
            weights['weekly_range_weight'] *= adjustment
            
        if stock_data.get('ytd_performance', 0) > 15:
            weights['ytd_performance_weight'] *= adjustment
            
        if stock_data.get('news_sentiment', 0) > 0.6:
            weights['news_sentiment_weight'] *= adjustment
            
        if stock_data.get('rotc', 0) > 10:
            weights['rotc_weight'] *= adjustment
            
        if stock_data.get('pe_ratio', 100) < 20 and stock_data.get('pe_ratio', 0) > 0:
            weights['pe_ratio_weight'] *= adjustment
            
        if stock_data.get('dividend_yield', 0) > 2:
            weights['dividend_yield_weight'] *= adjustment
    else:
        # For negative feedback, decrease weights of weak features
        if stock_data.get('price_momentum', 0) < 30:
            weights['price_momentum_weight'] *= adjustment
            
        if stock_data.get('52_week_range_position', 0) < 0.3:
            weights['weekly_range_weight'] *= adjustment
            
        if stock_data.get('ytd_performance', 0) < 0:
            weights['ytd_performance_weight'] *= adjustment
            
        # Similar pattern for other features...
    
    # Normalize weights
    normalize_weights(weights)
    
    # Save updated weights
    save_user_feature_weights(user_id, weights)
```

### Collaborative Filtering Extension

Future implementation will include collaborative filtering across users:

```python
def get_collaborative_recommendations(user_id, top_n=5):
    """
    Find similar users and recommend stocks they like.
    
    Args:
        user_id: Target user identifier
        top_n: Number of recommendations to return
        
    Returns:
        List of recommended stocks with similarity scores
    """
    # Find users with similar feature weights and sector preferences
    similar_users = find_similar_users(user_id)
    
    # Get stocks liked by similar users that target user hasn't interacted with
    recommendations = []
    for similar_user, similarity_score in similar_users:
        liked_stocks = get_liked_stocks(similar_user)
        user_stocks = get_user_interactions(user_id)
        
        for stock in liked_stocks:
            if stock not in user_stocks:
                recommendations.append({
                    'symbol': stock,
                    'similarity_score': similarity_score,
                    'recommender_count': 1
                })
                
    # Aggregate multiple recommendations of the same stock
    aggregated = {}
    for rec in recommendations:
        if rec['symbol'] in aggregated:
            aggregated[rec['symbol']]['similarity_score'] += rec['similarity_score']
            aggregated[rec['symbol']]['recommender_count'] += 1
        else:
            aggregated[rec['symbol']] = rec
            
    # Sort by combined score and return top N
    sorted_recs = sorted(aggregated.values(), 
                         key=lambda x: x['similarity_score'] * x['recommender_count'],
                         reverse=True)
    
    return sorted_recs[:top_n]
```

## 3. LLM Integration

### Command Pattern Recognition

The system uses regular expressions to identify commands in natural language input:

```python
command_patterns = {
    'analyze_stock': re.compile(r'analyze\s+([A-Za-z0-9.]+)', re.IGNORECASE),
    'compare_stocks': re.compile(r'compare\s+([A-Za-z0-9.]+)\s+and\s+([A-Za-z0-9.]+)', re.IGNORECASE),
    'portfolio_summary': re.compile(r'portfolio\s+summary', re.IGNORECASE),
    'train_ml': re.compile(r'train\s+(?:ml|machine learning)(?:\s+on\s+(.+))?', re.IGNORECASE),
    'analyze_with_ml': re.compile(r'analyze\s+with\s+ml\s+([A-Za-z0-9.]+)', re.IGNORECASE),
    # Additional patterns...
}
```

### Hybrid Response Generation

```python
def process_message(user_id, message):
    """
    Process user message with hybrid AI approach.
    
    Args:
        user_id: User identifier
        message: User's text message
        
    Returns:
        Response text and optional visualizations
    """
    # Check if message matches any command patterns
    command_match = check_for_commands(message)
    
    if command_match:
        # Handle command with our custom ML
        command_name, args = command_match
        response, visualizations = execute_command(command_name, args)
        return response, visualizations
    else:
        # Use LLM for general conversation
        context = get_user_context(user_id)
        response = call_llm_api(message, context)
        
        # Store interaction for context preservation
        store_interaction(user_id, message, response)
        
        return response, None
```

### Context Management

```python
def get_user_context(user_id):
    """
    Retrieve conversation context for the user.
    
    Args:
        user_id: User identifier
        
    Returns:
        Context object with chat history and user preferences
    """
    # Get recent chat history
    chat_history = get_chat_history(user_id, limit=10)
    
    # Get user profile
    profile = get_user_profile(user_id)
    
    # Get user preferences
    preferences = get_user_preferences(user_id)
    
    # Create context object for LLM
    context = {
        'history': chat_history,
        'profile': profile,
        'preferences': preferences,
        'current_stocks': get_recently_viewed_stocks(user_id),
        'last_analysis': get_last_analysis(user_id)
    }
    
    return context
```

## 4. Data Storage & Privacy

### User Preference Storage Schema

```sql
CREATE TABLE user_stock_preferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    sector VARCHAR(50),
    view_count INTEGER DEFAULT 0,
    total_view_time FLOAT DEFAULT 0,
    liked BOOLEAN DEFAULT NULL,
    purchased BOOLEAN DEFAULT NULL,
    feedback_date TIMESTAMP,
    purchase_date TIMESTAMP,
    purchase_price FLOAT,
    metrics_at_feedback TEXT,
    last_viewed TIMESTAMP,
    UNIQUE(user_id, symbol)
);

CREATE TABLE user_sector_preferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    sector VARCHAR(50) NOT NULL,
    score INTEGER DEFAULT 0,
    last_updated TIMESTAMP,
    UNIQUE(user_id, sector)
);

CREATE TABLE user_feature_weights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    price_momentum_weight FLOAT DEFAULT 1.0,
    weekly_range_weight FLOAT DEFAULT 1.0,
    ytd_performance_weight FLOAT DEFAULT 1.0,
    news_sentiment_weight FLOAT DEFAULT 1.0,
    rotc_weight FLOAT DEFAULT 1.0,
    pe_ratio_weight FLOAT DEFAULT 1.0,
    dividend_yield_weight FLOAT DEFAULT 1.0,
    volume_weight FLOAT DEFAULT 1.0,
    market_cap_weight FLOAT DEFAULT 1.0,
    volatility_weight FLOAT DEFAULT 1.0,
    last_updated TIMESTAMP,
    UNIQUE(user_id)
);
```

### Privacy Considerations

1. **Data Minimization**: Only collect data necessary for personalization
2. **Opt-In Collection**: Users explicitly consent to data collection
3. **Local Processing**: Perform sensitive calculations on-device when possible
4. **Data Deletion**: Allow users to reset or delete their data
5. **Anonymization**: Use anonymized data for model improvements
6. **Encryption**: Encrypt sensitive data in transit and at rest

## 5. Benchmarking & Evaluation

### ML Model Evaluation Metrics

1. **Prediction Accuracy**: RMSE for price predictions
2. **Signal Accuracy**: F1-score for buy/sell signals
3. **User Satisfaction**: Explicit feedback scores
4. **Engagement Metrics**: Time spent, return rate, session frequency

### A/B Testing Framework

```python
def assign_experiment_variant(user_id):
    """
    Assign user to experiment variant for A/B testing.
    
    Args:
        user_id: User identifier
        
    Returns:
        Variant name ('control', 'experimental')
    """
    # Deterministic but evenly distributed assignment
    variant = 'experimental' if hash(str(user_id)) % 2 == 0 else 'control'
    record_experiment_assignment(user_id, variant)
    return variant

def track_experiment_metrics(user_id, metric_name, value):
    """
    Record metrics for experiment analysis.
    
    Args:
        user_id: User identifier
        metric_name: Name of metric to track
        value: Metric value
    """
    variant = get_user_experiment_variant(user_id)
    record_experiment_metric(user_id, variant, metric_name, value)
```

## 6. LLM Integration Options

The system supports multiple LLM options:

### Claude API Integration

```python
def call_claude_api(message, context):
    """
    Call Claude API with message and context.
    
    Args:
        message: User's message
        context: Conversation context
        
    Returns:
        Response from Claude API
    """
    client = Anthropic(api_key=CLAUDE_API_KEY)
    
    # Format context into message history
    messages = format_context_as_messages(context)
    
    # Add user's new message
    messages.append({"role": "user", "content": message})
    
    # Call Claude API
    response = client.messages.create(
        model="claude-3-sonnet-20240229",
        messages=messages,
        temperature=0.7,
        max_tokens=2000
    )
    
    return response.content[0].text
```

### LLAMA Integration

```python
def call_llama_api(message, context):
    """
    Call LLAMA API with message and context.
    
    Args:
        message: User's message
        context: Conversation context
        
    Returns:
        Response from LLAMA API
    """
    # Format context and message into LLAMA's expected format
    formatted_prompt = format_for_llama(context, message)
    
    # Call LLAMA API
    response = requests.post(
        LLAMA_API_ENDPOINT,
        json={
            "prompt": formatted_prompt,
            "temperature": 0.7,
            "max_tokens": 2000,
            "stop": ["Human:", "\n\n"]
        },
        headers={"Authorization": f"Bearer {LLAMA_API_KEY}"}
    )
    
    return response.json()["choices"][0]["text"]
```

### X.AI Integration

```python
def call_xai_api(message, context):
    """
    Call X.AI (Grok) API with message and context.
    
    Args:
        message: User's message
        context: Conversation context
        
    Returns:
        Response from X.AI API
    """
    # Format context and message for X.AI API
    formatted_data = {
        "messages": format_context_for_xai(context),
        "new_message": message,
        "temperature": 0.7,
        "max_tokens": 2000
    }
    
    # Call X.AI API
    response = requests.post(
        XAI_API_ENDPOINT,
        json=formatted_data,
        headers={"Authorization": f"Bearer {XAI_API_KEY}"}
    )
    
    return response.json()["response"]
```

## 7. Future Development

1. **Multimodal Input**: Process images of charts and financial documents
2. **Real-time Feedback**: Update models in real-time based on user interactions
3. **Cross-Device Learning**: Sync learning profiles across devices
4. **Explainable AI**: Provide more detailed explanations of recommendations
5. **Advanced Visualization**: Interactive 3D portfolio visualizations
6. **Voice Interface**: Voice commands and conversational responses
7. **Market Regime Detection**: Automatically detect and adapt to changing market conditions

## Contact

For technical questions about the AI architecture, please contact the development team at [your-email@example.com].