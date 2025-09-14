# Adaptive Learning Implementation for Investment Bot

## Overview

We've implemented a comprehensive adaptive learning system that enables the Investment Bot to learn from user interactions and adapt to individual trading methodologies. This system fulfills the requirements for:

1. Collecting user feedback on stock recommendations
2. Storing historical stock preferences 
3. Recognizing patterns in preferred metrics/indicators
4. Implementing a reinforcement learning approach to adjust weightings
5. Tracking prediction accuracy to improve future recommendations

## Components Implemented

### 1. Core Adaptive Learning System
- `AdaptiveLearningSystem` class that manages learning and adaptation
- File-based storage for user preferences, feature weights, and performance history
- Machine learning model (RandomForestClassifier) to predict user preferences

### 2. Database Integration
- `AdaptiveLearningDB` class that provides database integration
- New database models:
  - `StockPreference` - Stores user interactions with stocks
  - `FeatureWeight` - Records personalized feature importance
  - `SectorPreference` - Tracks preferred sectors
  - `PredictionRecord` - Monitors prediction accuracy

### 3. Web Interface Components
- Feedback collection buttons on stock analysis pages
- View duration tracking to analyze user engagement
- Personalized stock analysis view that adjusts to user preferences
- Recommendations page based on learned preferences
- User preference profile page to visualize learned preferences

## Key Features

### Feedback Collection
- Users can express "like", "dislike", or "purchase interest" for any stock
- System collects view duration to measure engagement with certain stocks
- Web interface provides immediate feedback on user actions

### Preference Storage
- Stores liked/disliked/purchased stocks
- Records viewing patterns and time spent
- Maintains sector preferences based on interaction history
- Tracks feature weights that matter most to each user

### Pattern Recognition
- Identifies which metrics are common in stocks the user likes
- Gradually adjusts feature weights based on user preferences
- Builds a profile of user's sector preferences

### Reinforcement Learning
- Dynamically adjusts feature weights based on user feedback
- Increases weights for features present in liked stocks
- Decreases weights for features present in disliked stocks
- Normalizes weights to maintain proper distribution

### Prediction Tracking
- Records predictions about price changes and user preferences
- Compares predictions to actual outcomes
- Calculates error metrics to improve future predictions
- Visualizes prediction accuracy for user awareness

## Usage Flow

1. **Discovery Phase**
   - User analyzes various stocks
   - System records viewing patterns and collects explicit feedback
   - Initial feature weights are established

2. **Learning Phase**
   - System adjusts feature weights based on user feedback
   - Pattern recognition identifies preferred metrics and sectors
   - ML model is trained on user's historical preferences

3. **Personalization Phase**
   - Recommendations are tailored to user's preferences
   - Stock analyses include personalized sentiment scores
   - System highlights features that match user preferences

4. **Improvement Phase**
   - Prediction accuracy is tracked and visualized
   - System continues to refine its understanding of user preferences
   - Recommendations become increasingly personalized

## Technical Implementation

- Used SQLAlchemy models for database integration
- RandomForestClassifier from scikit-learn for preference prediction
- Flask routes for handling user interactions
- JavaScript for asynchronous feedback collection
- Jinja2 templates for displaying personalized content

## Future Enhancements

- Implement more sophisticated ML models (deep learning)
- Add collaborative filtering to leverage patterns across users
- Introduce A/B testing for recommendation strategies
- Develop time-based weighting (giving more weight to recent preferences)
- Add explainability features to help users understand recommendations