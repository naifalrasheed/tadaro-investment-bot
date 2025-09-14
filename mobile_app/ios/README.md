# Investment Bot iOS App

## Setup Instructions

### Requirements

- Xcode 14.0+
- iOS 15.0+
- Swift 5.5+
- CocoaPods or Swift Package Manager

### Installation

1. Clone the repository
2. Navigate to the iOS directory
3. Run `pod install` (if using CocoaPods)
4. Open the `.xcworkspace` file in Xcode
5. Build and run the project

## Project Structure

```
InvestmentBot/
├── App/
│   ├── AppDelegate.swift
│   ├── SceneDelegate.swift
│   └── AppCoordinator.swift
├── Models/
│   ├── User.swift
│   ├── Stock.swift
│   ├── Portfolio.swift
│   └── Analysis.swift
├── Views/
│   ├── Authentication/
│   ├── StockAnalysis/
│   ├── Portfolio/
│   ├── Chat/
│   └── Settings/
├── ViewModels/
│   ├── AuthViewModel.swift
│   ├── StockViewModel.swift
│   ├── PortfolioViewModel.swift
│   └── ChatViewModel.swift
├── Services/
│   ├── NetworkService.swift
│   ├── APIService.swift
│   ├── UserService.swift
│   ├── StockService.swift
│   └── ChatService.swift
├── Utils/
│   ├── Extensions/
│   ├── Helpers/
│   └── Constants.swift
├── Resources/
│   ├── Assets.xcassets
│   ├── LaunchScreen.storyboard
│   └── Info.plist
└── Config/
    ├── Debug.xcconfig
    └── Release.xcconfig
```

## Key Features

1. **Authentication**
   - Secure login with biometrics
   - JWT token management

2. **Stock Analysis**
   - Stock search and detail views
   - Interactive charts using SwiftUI
   - Technical and fundamental analysis displays
   - ML-powered predictions

3. **Portfolio Management**
   - Multiple portfolio support
   - Holdings visualization
   - Performance tracking
   - Optimization suggestions

4. **Chat Interface**
   - Natural language processing
   - Command recognition
   - Context-aware responses
   - Markdown rendering

5. **Settings & Preferences**
   - Customize analysis preferences
   - Notification settings
   - ML model management

## Integration Points

### API Integration

The app uses the Investment Bot API for all data operations. See `APIService.swift` for implementation details.

### AI Features

The iOS app leverages both on-device ML models (using Core ML) and server-side AI for a balanced approach:

- On-device models for basic scoring and predictions
- Server-side processing for complex analyses and LLM features

### Security

- Keychain for secure token storage
- FaceID/TouchID for biometric authentication
- Certificate pinning for secure API communication

## Configuration

Create a `Config.xcconfig` file with the following variables:

```
API_BASE_URL = https://your-api-base-url.com
API_VERSION = v1
ANTHROPIC_API_KEY = your_api_key_here
```

## Contributing

Follow the standard iOS development guidelines:

1. Use SwiftLint for code style enforcement
2. Write unit tests for all new features
3. Follow MVVM architecture
4. Use Swift UI for new views when possible

## Testing

Run tests using the standard Xcode testing framework:

```bash
xcodebuild test -workspace InvestmentBot.xcworkspace -scheme InvestmentBot -destination 'platform=iOS Simulator,name=iPhone 14'
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.