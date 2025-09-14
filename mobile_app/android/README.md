# Investment Bot Android App

## Setup Instructions

### Requirements

- Android Studio Giraffe (2023.1.1) or newer
- Kotlin 1.8.0+
- Gradle 8.0+
- Android 8.0+ (API level 26+)

### Installation

1. Clone the repository
2. Open the project in Android Studio
3. Sync Gradle files
4. Build and run the project

## Project Structure

```
app/
├── src/
│   ├── main/
│   │   ├── java/com/investmentbot/
│   │   │   ├── application/
│   │   │   │   └── InvestmentBotApplication.kt
│   │   │   ├── data/
│   │   │   │   ├── api/
│   │   │   │   ├── database/
│   │   │   │   ├── model/
│   │   │   │   └── repository/
│   │   │   ├── di/
│   │   │   │   └── AppModule.kt
│   │   │   ├── domain/
│   │   │   │   ├── model/
│   │   │   │   ├── repository/
│   │   │   │   └── usecase/
│   │   │   ├── presentation/
│   │   │   │   ├── auth/
│   │   │   │   ├── chat/
│   │   │   │   ├── portfolio/
│   │   │   │   ├── settings/
│   │   │   │   └── stocks/
│   │   │   └── util/
│   │   │       ├── extensions/
│   │   │       └── Constants.kt
│   │   └── res/
│   │       ├── drawable/
│   │       ├── layout/
│   │       ├── navigation/
│   │       ├── values/
│   │       └── xml/
│   └── test/
│       ├── java/
│       └── androidTest/
├── build.gradle
└── proguard-rules.pro
```

## Architecture

The app follows Clean Architecture principles with MVVM pattern:

```
┌───────────────┐      ┌───────────────┐      ┌───────────────┐
│ Presentation  │ ───► │    Domain     │ ◄─── │     Data      │
│   (MVVM)      │      │   (Use Cases) │      │ (Repositories)│
└───────────────┘      └───────────────┘      └───────────────┘
```

- **Presentation Layer**: UI components (Activities, Fragments, Composables)
- **Domain Layer**: Business logic and use cases
- **Data Layer**: API and database implementations

## Key Technologies

- **Jetpack Compose**: Modern UI toolkit
- **Kotlin Coroutines**: Asynchronous programming
- **Kotlin Flow**: Reactive data streams
- **Hilt**: Dependency injection
- **Room**: Local database
- **Retrofit**: API communication
- **TensorFlow Lite**: ML model integration
- **Material Design 3**: UI components
- **Navigation Component**: In-app navigation
- **Biometric Authentication**: Secure login

## Key Features

1. **Authentication**
   - JWT-based auth with refresh tokens
   - Biometric authentication
   - Auto-login capabilities

2. **Stock Analysis**
   - Stock search with prediction scores
   - Technical analysis charts
   - Fundamental data visualization
   - ML-enhanced insights

3. **Portfolio Management**
   - Holdings tracker
   - Performance metrics
   - Allocation visualization
   - Rebalancing suggestions

4. **AI Chat Assistant**
   - Natural language interface
   - Context-aware responses
   - Stock command recognition
   - Portfolio insights

5. **Personalization**
   - User preference tracking
   - ML model adaptation
   - Customizable dashboards
   - Risk profile settings

## API Integration

The app communicates with the Investment Bot API:

```kotlin
interface InvestmentBotApi {
    // Authentication endpoints
    @POST("auth/login")
    suspend fun login(@Body request: LoginRequest): Response<AuthResponse>
    
    @POST("auth/refresh")
    suspend fun refreshToken(@Body request: RefreshTokenRequest): Response<AuthResponse>
    
    // Stock endpoints
    @GET("stocks/{symbol}")
    suspend fun getStockData(@Path("symbol") symbol: String): Response<StockResponse>
    
    @GET("stocks/{symbol}/analysis")
    suspend fun getStockAnalysis(@Path("symbol") symbol: String): Response<AnalysisResponse>
    
    // Portfolio endpoints
    @GET("portfolio")
    suspend fun getPortfolios(): Response<List<PortfolioResponse>>
    
    @POST("portfolio")
    suspend fun createPortfolio(@Body request: CreatePortfolioRequest): Response<PortfolioResponse>
    
    // Chat endpoints
    @POST("chat")
    suspend fun sendChatMessage(@Body request: ChatRequest): Response<ChatResponse>
    
    @GET("chat/history")
    suspend fun getChatHistory(): Response<ChatHistoryResponse>
    
    // ML endpoints
    @POST("ml/train")
    suspend fun trainMlModel(): Response<MlTrainingResponse>
    
    @POST("ml/feedback")
    suspend fun provideFeedback(@Body request: FeedbackRequest): Response<FeedbackResponse>
}
```

## ML Integration

The app uses a hybrid approach for ML features:

1. **TensorFlow Lite Models**:
   - On-device stock scoring
   - Basic technical analysis
   - Local feature extraction

2. **Server-side ML**:
   - Complex analysis models
   - User preference learning
   - LLM-powered chat responses

## Configuration

Create a `local.properties` file with:

```properties
api.base.url=https://your-api-base-url.com
api.version=v1
anthropic.api.key=your_api_key_here
```

## Testing

The app includes multiple testing layers:

- **Unit Tests**: Business logic, view models, repositories
- **Integration Tests**: API integration, database operations
- **UI Tests**: User flows, component interactions

Run tests with:

```bash
./gradlew test           # Unit tests
./gradlew connectedCheck # Integration and UI tests
```

## Performance Considerations

- **Offline Support**: Local caching for essential data
- **Lazy Loading**: Paginated data loading
- **Image Optimization**: Efficient caching and resizing
- **Background Processing**: WorkManager for long-running tasks

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

Please adhere to the project's coding standards:

- Follow Kotlin coding conventions
- Use architectural components as designed
- Add tests for new features
- Document public APIs

## License

This project is licensed under the MIT License - see the LICENSE file for details.