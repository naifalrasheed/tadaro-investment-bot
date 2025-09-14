# Investment Bot Mobile App Integration

## Overview

This document provides specifications for integrating the Investment Bot platform into iOS and Android mobile applications. The Investment Bot provides comprehensive stock analysis, portfolio management, and AI-powered investment recommendations through a combination of traditional ML models and large language models (LLMs).

## System Architecture

The mobile apps will use a client-server architecture:

1. **Backend API**: RESTful API endpoints exposed by the Flask server
2. **Mobile Clients**: Native iOS and Android applications
3. **LLM Integration**: Hybrid approach using Claude API and custom ML models
4. **Data Storage**: SQLite for local caching, server-side PostgreSQL for user data

### Key Components

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Mobile Clients │────►│  Backend API    │────►│  Database       │
│  (iOS/Android)  │◄────│  (Flask Server) │◄────│  (PostgreSQL)   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │   ▲
                               │   │
                               ▼   │
                         ┌─────────────────┐     ┌─────────────────┐
                         │  LLM Services   │────►│  Claude API     │
                         │  (Hybrid AI)    │◄────│  (Anthropic)    │
                         └─────────────────┘     └─────────────────┘
                               │   ▲
                               │   │
                               ▼   │
                         ┌─────────────────┐
                         │  Custom ML      │
                         │  Models         │
                         └─────────────────┘
```

## API Endpoints

### Authentication Endpoints

- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/refresh` - Refresh authentication token
- `POST /api/auth/logout` - User logout

### Stock Analysis Endpoints

- `GET /api/stocks/{symbol}` - Get stock overview data
- `GET /api/stocks/{symbol}/analysis` - Get comprehensive stock analysis
- `GET /api/stocks/{symbol}/technical` - Get technical analysis
- `GET /api/stocks/{symbol}/fundamental` - Get fundamental analysis
- `GET /api/stocks/{symbol}/sentiment` - Get sentiment analysis

### Portfolio Endpoints

- `GET /api/portfolio` - Get user portfolios
- `GET /api/portfolio/{id}` - Get specific portfolio
- `POST /api/portfolio` - Create new portfolio
- `PUT /api/portfolio/{id}` - Update portfolio
- `DELETE /api/portfolio/{id}` - Delete portfolio
- `POST /api/portfolio/{id}/stocks` - Add stock to portfolio
- `DELETE /api/portfolio/{id}/stocks/{symbol}` - Remove stock from portfolio
- `GET /api/portfolio/{id}/analysis` - Get portfolio analysis

### Chat & AI Endpoints

- `POST /api/chat` - Send message to chatbot
- `GET /api/chat/history` - Get chat history
- `POST /api/chat/clear` - Clear chat history
- `GET /api/ml/status` - Get ML model status
- `POST /api/ml/train` - Train ML model
- `POST /api/ml/feedback` - Provide ML feedback
- `POST /api/ml/reset` - Reset ML model

## Data Models

### User Model

```
{
  "id": integer,
  "email": string,
  "name": string,
  "created_at": datetime,
  "risk_profile": string,
  "preferences": object
}
```

### Portfolio Model

```
{
  "id": integer,
  "user_id": integer,
  "name": string,
  "description": string,
  "created_at": datetime,
  "last_updated": datetime,
  "stocks": [
    {
      "symbol": string,
      "shares": number,
      "purchase_price": number,
      "purchase_date": datetime
    }
  ]
}
```

### Stock Analysis Model

```
{
  "symbol": string,
  "company_name": string,
  "current_price": number,
  "price_change": number,
  "technical_analysis": {
    "technical_score": number,
    "ml_prediction": number,
    "confidence": number,
    "predicted_price": number
  },
  "fundamental_analysis": {
    "pe_ratio": number,
    "rotc": number,
    "growth_rate": number,
    "debt_to_equity": number
  },
  "sentiment_analysis": {
    "sentiment_score": number,
    "sentiment_label": string,
    "components": object
  },
  "naif_model_criteria": {
    "meets_criteria": boolean,
    "failing_criteria": array
  }
}
```

## Mobile App Features

### Core Features

1. **User Authentication**
   - Login/Registration
   - Profile management
   - Risk profile assessment

2. **Stock Analysis**
   - Search and analyze stocks
   - Technical analysis with charts
   - CFA-level fundamental analysis
   - Advanced ratio analysis
   - Sentiment analysis
   - Naif Al-Rasheed model evaluation
   - Fixed income analysis and valuations

3. **Portfolio Management**
   - Create/edit portfolios
   - Track performance
   - View portfolio composition
   - Factor exposure analysis
   - Risk-based portfolio construction
   - Performance attribution
   - Efficient frontier optimization
   - Risk budgeting tools

4. **Behavioral Finance**
   - Cognitive and emotional bias detection
   - Decision-making framework
   - Investment thesis builder
   - Bias profile tracking
   - Debiasing strategies
   - Decision quality monitoring
   - Behavioral coaching

5. **AI Assistant**
   - Natural language chat interface
   - Stock analysis commands
   - Portfolio management commands
   - Investment recommendations
   - ML-powered personalized insights
   - CFA concept explanations

6. **Investment Policy Management**
   - IPS creation and management
   - Goal-based portfolio construction
   - Risk constraint implementation
   - Rebalancing policy management
   - Performance evaluation criteria

7. **Notifications**
   - Price alerts
   - Recommendation notifications
   - Portfolio performance updates
   - Behavioral bias alerts
   - Decision framework reminders

### Advanced Features

1. **Offline Mode**
   - Cache recent analyses
   - Save portfolios locally
   - Queue commands for sync

2. **Biometric Authentication**
   - Face ID / Touch ID integration
   - Secure login

3. **Custom Watchlists**
   - Create and manage watchlists
   - Set alerts and notifications

4. **Social Sharing**
   - Share analyses
   - Export reports as PDF

## AI & ML Engine Integration

### Transformative Learning Approach

The mobile app will implement a hybrid AI approach combining:

1. **Custom ML Models**:
   - Personalized stock scoring based on user preferences
   - Feature weight adaptation through feedback
   - Sector preference tracking
   - Prediction accuracy monitoring
   - Behavioral bias detection algorithms
   - Risk-adjusted portfolio optimization

2. **LLM Integration with CFA Knowledge**:
   - Claude API for natural language understanding
   - CFA curriculum integration for advanced analysis
   - Behavioral finance pattern recognition
   - Investment thesis evaluation
   - Context preservation across sessions
   - Response generation with visualizations
   - Command pattern recognition

3. **Continuous Learning with Behavioral Insights**:
   - Store user interactions in secured database
   - Track decision-making patterns for bias detection
   - Develop personalized behavioral coaching strategies
   - Periodic retraining of ML models
   - Preference tracking across devices
   - Feature importance re-weighting
   - Cognitive bias profile adaptation

4. **CFA-Level Portfolio Analytics**:
   - Factor model analysis and exposures
   - Performance attribution (Brinson-Fachler)
   - Risk budgeting and risk-based allocation
   - Alternative investments evaluation
   - Fixed income analysis and optimization

### Data Collection & Storage

User data will be collected to improve personalization and behavioral insights:

- **Stock Preferences**: Liked/disliked stocks
- **Viewing Patterns**: Time spent analyzing specific stocks/sectors
- **Feature Weights**: Importance of different metrics
- **Feedback Data**: Explicit feedback on recommendations
- **Sector Preferences**: Sectors user shows interest in
- **Decision Records**: History of investment decisions with rationales
- **Bias Profiles**: Detected behavioral biases and patterns
- **Risk Preferences**: User-specific risk tolerance profiles
- **Portfolio Constraints**: User's specific portfolio constraints
- **Trading Behavior**: Transaction patterns (timing, frequency, emotional context)
- **Decision Framework Usage**: How users interact with decision frameworks
- **Investment Thesis Records**: Historical investment theses and outcomes

All data collection will be:
- Opt-in (requires user consent)
- Transparent (user can view collected data)
- Secure (encrypted in transit and at rest)
- Deletable (user can request data deletion)
- Educational (users can learn from their own patterns)
- Non-judgmental (focuses on improvement, not criticism)

## Implementation Guidelines

### iOS Implementation

- Swift 5.5+
- SwiftUI for modern UI components
- Combine for reactive programming
- Core ML for on-device models
- MVVM architecture
- Keychain for secure storage

See `/mobile_app/ios/` directory for iOS-specific implementation files.

### Android Implementation

- Kotlin 1.5+
- Jetpack Compose for UI
- Coroutines for async operations
- TensorFlow Lite for on-device models
- MVVM architecture with Repository pattern
- AndroidX components

See `/mobile_app/android/` directory for Android-specific implementation files.

## Authentication & Security

- JWT-based authentication
- Refresh token rotation
- API rate limiting
- HTTPS for all communications
- Biometric authentication integration
- Secure local storage for sensitive data

## Testing Strategy

1. **Unit Testing**
   - API service mocks
   - UI component tests
   - ML model input/output validation

2. **Integration Testing**
   - API integration tests
   - Database integration tests
   - Third-party service integration tests

3. **UI Testing**
   - Automated UI flows
   - Device compatibility tests
   - Accessibility testing

4. **Performance Testing**
   - Response time benchmarks
   - Memory usage monitoring
   - Battery consumption analysis

## Getting Started

1. Clone the repository
2. Set up environment variables (see `.env.example`)
3. Choose platform directory (`ios` or `android`)
4. Follow platform-specific setup instructions

## API Keys & Configuration

The mobile app requires several API keys:

1. Claude API (Anthropic) for chatbot functionality
2. Alpha Vantage for financial data
3. News API for sentiment analysis
4. Firebase for notifications

Configuration should be stored in platform-specific secure storage, not hardcoded.

## Contributing

Follow the standard GitHub workflow:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

Please adhere to the coding standards defined in each platform directory.

## License

[MIT License](LICENSE)

## Contact

For questions or support, please contact: [your-email@example.com]