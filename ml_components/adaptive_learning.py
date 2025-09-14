"""
Adaptive Learning System for Investment Bot

This module implements a learning system that adapts to user preferences
and improves stock recommendations based on user feedback and historical performance.
"""

import os
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import pickle
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from typing import Dict, List, Any, Optional, Tuple
import logging
import faiss  # Import FAISS for vector storage (comment out if not installed)
from collections import deque

class AdaptiveLearningSystem:
    """
    A system that learns from user feedback and adapts recommendations
    to match the user's investment methodology and preferences.
    
    Enhanced with advanced memory capabilities:
    - Short-term context window (recent analyses)
    - Long-term vector memory (historical decisions)
    - Episodic memory (decision outcomes)
    - Personalized relevance-based retrieval
    """
    
    def __init__(self, user_id: str, data_dir: str = 'adaptive_data', 
                vector_dim: int = 128, short_term_size: int = 20):
        """
        Initialize the adaptive learning system.
        
        Args:
            user_id: Unique identifier for the user
            data_dir: Directory to store user preference and model data
            vector_dim: Dimension of vector embeddings for memory
            short_term_size: Size of short-term memory window
        """
        self.logger = logging.getLogger(__name__)
        self.user_id = user_id
        self.data_dir = data_dir
        self.user_dir = os.path.join(data_dir, f'user_{user_id}')
        self.vector_dim = vector_dim
        self.short_term_size = short_term_size
        
        # Create data directories if they don't exist
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        if not os.path.exists(self.user_dir):
            os.makedirs(self.user_dir)
            
        # Paths for storing user data
        self.preferences_path = os.path.join(self.user_dir, 'stock_preferences.json')
        self.feature_weights_path = os.path.join(self.user_dir, 'feature_weights.json')
        self.model_path = os.path.join(self.user_dir, 'user_model.pkl')
        self.performance_path = os.path.join(self.user_dir, 'performance_history.json')
        self.memory_path = os.path.join(self.user_dir, 'vector_memory.pkl')
        self.episodic_memory_path = os.path.join(self.user_dir, 'episodic_memory.json')
        
        # Initialize or load user data
        self.stock_preferences = self._load_stock_preferences()
        self.feature_weights = self._load_feature_weights()
        self.performance_history = self._load_performance_history()
        self.user_model = self._load_model()
        
        # Initialize feature scaling
        self.scaler = StandardScaler()
        
        # Initialize memory systems
        self.short_term_memory = deque(maxlen=short_term_size)  # Recent analyses
        self.vector_memory, self.memory_data = self._load_vector_memory()
        self.episodic_memory = self._load_episodic_memory()  # Decision outcomes
        
    def _load_stock_preferences(self):
        """Load user's stock preferences history or create if doesn't exist."""
        if os.path.exists(self.preferences_path):
            with open(self.preferences_path, 'r') as f:
                return json.load(f)
        else:
            # Initialize with empty preference history
            return {
                "liked_stocks": [],      # Stocks user explicitly liked
                "disliked_stocks": [],   # Stocks user explicitly disliked
                "viewed_stocks": [],     # Stocks user has viewed
                "purchased_stocks": [],  # Stocks user has purchased
                "time_spent": {},        # Time spent viewing each stock
                "sector_preferences": {} # Sector preference scores
            }
    
    def _load_feature_weights(self):
        """Load feature weights or initialize with default values."""
        if os.path.exists(self.feature_weights_path):
            with open(self.feature_weights_path, 'r') as f:
                return json.load(f)
        else:
            # Initialize with default equal weighting
            return {
                "price_momentum": 0.2,
                "weekly_range": 0.1, 
                "ytd_performance": 0.2,
                "news_sentiment": 0.1,
                "rotc": 0.1,
                "pe_ratio": 0.1,
                "dividend_yield": 0.1,
                "volume_change": 0.05,
                "market_cap": 0.05
            }
    
    def _load_performance_history(self):
        """Load prediction performance history or create if doesn't exist."""
        if os.path.exists(self.performance_path):
            with open(self.performance_path, 'r') as f:
                return json.load(f)
        else:
            return {
                "predictions": [],
                "accuracy": 0.0,
                "last_updated": datetime.now().isoformat()
            }
    
    def _load_model(self):
        """Load the user's personalized model or create a new one."""
        if os.path.exists(self.model_path):
            with open(self.model_path, 'rb') as f:
                return pickle.load(f)
        else:
            # Initialize a new model
            return RandomForestClassifier(n_estimators=100, random_state=42)
    
    def _save_stock_preferences(self):
        """Save user stock preferences to file."""
        with open(self.preferences_path, 'w') as f:
            json.dump(self.stock_preferences, f, indent=2)
    
    def _save_feature_weights(self):
        """Save feature weights to file."""
        with open(self.feature_weights_path, 'w') as f:
            json.dump(self.feature_weights, f, indent=2)
    
    def _save_model(self):
        """Save the user's personalized model."""
        with open(self.model_path, 'wb') as f:
            pickle.dump(self.user_model, f)
    
    def _save_performance_history(self):
        """Save prediction performance history."""
        with open(self.performance_path, 'w') as f:
            json.dump(self.performance_history, f, indent=2)
    
    def record_stock_view(self, stock_symbol, view_duration=None):
        """
        Record that a user viewed a particular stock.
        
        Args:
            stock_symbol (str): The stock symbol that was viewed
            view_duration (float, optional): Time spent viewing in seconds
        """
        timestamp = datetime.now().isoformat()
        
        if stock_symbol not in self.stock_preferences["viewed_stocks"]:
            self.stock_preferences["viewed_stocks"].append(stock_symbol)
        
        if view_duration:
            self.stock_preferences["time_spent"][stock_symbol] = \
                self.stock_preferences["time_spent"].get(stock_symbol, 0) + view_duration
        
        self._save_stock_preferences()
        
    def record_feedback(self, stock_symbol, reaction, stock_data=None, sector=None):
        """
        Record user's explicit feedback about a stock.
        
        Args:
            stock_symbol (str): The stock symbol
            reaction (str): 'like', 'dislike', or 'purchase'
            stock_data (dict, optional): Stock metrics and features
            sector (str, optional): The stock's sector
        """
        timestamp = datetime.now().isoformat()
        
        if reaction == 'like' and stock_symbol not in self.stock_preferences["liked_stocks"]:
            self.stock_preferences["liked_stocks"].append(stock_symbol)
            # Remove from disliked if it was there
            if stock_symbol in self.stock_preferences["disliked_stocks"]:
                self.stock_preferences["disliked_stocks"].remove(stock_symbol)
                
        elif reaction == 'dislike' and stock_symbol not in self.stock_preferences["disliked_stocks"]:
            self.stock_preferences["disliked_stocks"].append(stock_symbol)
            # Remove from liked if it was there
            if stock_symbol in self.stock_preferences["liked_stocks"]:
                self.stock_preferences["liked_stocks"].remove(stock_symbol)
                
        elif reaction == 'purchase':
            purchase_record = {
                "symbol": stock_symbol,
                "date": timestamp,
                "price": stock_data.get("current_price") if stock_data else None
            }
            self.stock_preferences["purchased_stocks"].append(purchase_record)
        
        # Update sector preferences if sector is provided
        if sector:
            current_score = self.stock_preferences["sector_preferences"].get(sector, 0)
            if reaction == 'like' or reaction == 'purchase':
                self.stock_preferences["sector_preferences"][sector] = current_score + 1
            elif reaction == 'dislike':
                self.stock_preferences["sector_preferences"][sector] = current_score - 1
        
        # If we have stock data, use it to update our learning model
        if stock_data:
            self._update_learning_model(stock_symbol, reaction, stock_data)
        
        self._save_stock_preferences()
    
    def _update_learning_model(self, stock_symbol, reaction, stock_data):
        """
        Update the learning model based on user feedback.
        
        Args:
            stock_symbol (str): The stock symbol
            reaction (str): User's reaction ('like', 'dislike', 'purchase')
            stock_data (dict): Stock metrics and features
        """
        # Convert stock data to features
        features = self._extract_features(stock_data)
        
        # Prepare training data
        X = np.array(features).reshape(1, -1)
        y = np.array([1 if reaction in ('like', 'purchase') else 0])
        
        # Update model (simple update for demonstration)
        # In a real system, you would accumulate data and retrain periodically
        try:
            self.user_model.fit(X, y)
            self._save_model()
        except Exception as e:
            print(f"Error updating model: {e}")
    
    def _extract_features(self, stock_data):
        """
        Extract relevant features from stock data.
        
        Args:
            stock_data (dict): Stock metrics and features
            
        Returns:
            list: Extracted features
        """
        # These are placeholder features - adjust based on your actual data structure
        features = [
            stock_data.get('price_momentum', 0),
            stock_data.get('52_week_range_position', 0),
            stock_data.get('ytd_performance', 0),
            stock_data.get('news_sentiment', 0),
            stock_data.get('rotc', 0),
            stock_data.get('pe_ratio', 0),
            stock_data.get('dividend_yield', 0),
            stock_data.get('volume_change', 0),
            stock_data.get('market_cap', 0)
        ]
        return features
    
    def adjust_feature_weights(self):
        """
        Adjust feature weights based on user preferences and model importance.
        This uses the machine learning model's feature importance to update weights.
        """
        if hasattr(self.user_model, 'feature_importances_'):
            # Get feature importances from the model
            importances = self.user_model.feature_importances_
            
            # Map to feature names (ensure same order as in _extract_features)
            feature_names = list(self.feature_weights.keys())
            
            # Update weights with a blend of current and new weights
            for i, feature in enumerate(feature_names):
                if i < len(importances):
                    # Blend: 70% old weight, 30% new importance
                    self.feature_weights[feature] = 0.7 * self.feature_weights[feature] + 0.3 * importances[i]
            
            # Normalize to sum to 1
            total = sum(self.feature_weights.values())
            for feature in self.feature_weights:
                self.feature_weights[feature] /= total
                
            self._save_feature_weights()
            return True
        return False
    
    def predict_stock_preference(self, stock_data):
        """
        Predict if a user would like a given stock based on their preference history.
        
        Args:
            stock_data (dict): Stock metrics and features
            
        Returns:
            dict: Prediction results with probability and rationale
        """
        features = self._extract_features(stock_data)
        X = np.array(features).reshape(1, -1)
        
        # Make prediction
        try:
            probability = self.user_model.predict_proba(X)[0][1]  # Probability of positive class
            prediction = 1 if probability >= 0.5 else 0
            
            # Get top contributing features
            if hasattr(self.user_model, 'feature_importances_'):
                feature_names = list(self.feature_weights.keys())
                importances = self.user_model.feature_importances_
                
                # Get top 3 features
                indices = np.argsort(importances)[-3:][::-1]
                top_features = [feature_names[i] for i in indices if i < len(feature_names)]
            else:
                top_features = []
                
            return {
                "predicted_like": bool(prediction),
                "probability": float(probability),
                "top_features": top_features
            }
        except Exception as e:
            print(f"Prediction error: {e}")
            return {
                "predicted_like": None,
                "probability": 0.5,  # Neutral
                "top_features": [],
                "error": str(e)
            }
    
    def record_prediction_outcome(self, stock_symbol, predicted_performance, actual_performance):
        """
        Record and track the accuracy of price/performance predictions.
        
        Args:
            stock_symbol (str): The stock symbol
            predicted_performance (float): Predicted performance (e.g., price change %)
            actual_performance (float): Actual performance
            
        Returns:
            float: Updated prediction accuracy
        """
        # Calculate prediction error
        error = abs(predicted_performance - actual_performance)
        
        # Record prediction
        prediction = {
            "symbol": stock_symbol,
            "date": datetime.now().isoformat(),
            "predicted": predicted_performance,
            "actual": actual_performance,
            "error": error
        }
        
        self.performance_history["predictions"].append(prediction)
        
        # Update overall accuracy (using mean absolute error)
        if len(self.performance_history["predictions"]) > 0:
            errors = [p["error"] for p in self.performance_history["predictions"]]
            self.performance_history["accuracy"] = float(np.mean(errors))
        
        self.performance_history["last_updated"] = datetime.now().isoformat()
        self._save_performance_history()
        
        return self.performance_history["accuracy"]
    
    def get_personalized_sentiment(self, stock_data, default_sentiment):
        """
        Calculate a personalized sentiment score based on user preferences.
        
        Args:
            stock_data (dict): Stock metrics and features
            default_sentiment (float): The default sentiment score (-100 to 100)
            
        Returns:
            float: Personalized sentiment score
        """
        # Extract basic features
        features = {}
        for key in self.feature_weights:
            features[key] = stock_data.get(key, 0)
        
        # Apply personalized weights
        weighted_sum = sum(self.feature_weights[feature] * value 
                         for feature, value in features.items())
        
        # Blend with default sentiment (50% each)
        normalized_default = default_sentiment / 100  # Convert to -1 to 1 scale
        personalized_sentiment = 0.5 * normalized_default + 0.5 * weighted_sum
        
        # Convert back to -100 to 100 scale
        return personalized_sentiment * 100
    
    def get_recommended_stocks(self, available_stocks, top_n=5):
        """
        Get stocks recommended for the user based on their preferences.
        
        Args:
            available_stocks (list): List of dictionaries with stock data
            top_n (int): Number of stocks to recommend
            
        Returns:
            list: Top recommended stocks
        """
        recommendations = []
        
        for stock in available_stocks:
            # Skip already purchased stocks
            purchased_symbols = [p["symbol"] for p in self.stock_preferences["purchased_stocks"]]
            if stock["symbol"] in purchased_symbols:
                continue
                
            # Get preference prediction
            prediction = self.predict_stock_preference(stock)
            
            # Add prediction data to stock
            stock_with_prediction = {**stock, "preference_prediction": prediction}
            recommendations.append(stock_with_prediction)
        
        # Sort by preference probability
        sorted_recommendations = sorted(
            recommendations, 
            key=lambda x: x["preference_prediction"]["probability"], 
            reverse=True
        )
        
        return sorted_recommendations[:top_n]
    
    def _load_vector_memory(self) -> Tuple[Any, List[Dict]]:
        """Load vector memory or initialize a new one."""
        try:
            if os.path.exists(self.memory_path):
                with open(self.memory_path, 'rb') as f:
                    saved_data = pickle.load(f)
                    return saved_data['index'], saved_data['data']
                    
            # Initialize new vector index
            try:
                # Create a new FAISS index
                index = faiss.IndexFlatL2(self.vector_dim)
                return index, []
            except (NameError, ImportError):
                # If FAISS is not available, use a simple list for demo purposes
                self.logger.warning("FAISS not available, using simple list storage for vectors")
                return [], []
                
        except Exception as e:
            self.logger.error(f"Error loading vector memory: {e}")
            return [], []
            
    def _save_vector_memory(self):
        """Save vector memory to disk."""
        try:
            with open(self.memory_path, 'wb') as f:
                data_to_save = {
                    'index': self.vector_memory,
                    'data': self.memory_data
                }
                pickle.dump(data_to_save, f)
        except Exception as e:
            self.logger.error(f"Error saving vector memory: {e}")
            
    def _load_episodic_memory(self) -> Dict:
        """Load episodic memory or create a new one."""
        if os.path.exists(self.episodic_memory_path):
            try:
                with open(self.episodic_memory_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Error loading episodic memory: {e}")
                return {"episodes": [], "indexes": {}}
        else:
            return {"episodes": [], "indexes": {}}
            
    def _save_episodic_memory(self):
        """Save episodic memory to disk."""
        try:
            with open(self.episodic_memory_path, 'w') as f:
                json.dump(self.episodic_memory, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving episodic memory: {e}")

    def store_in_memory(self, data: Dict, vector: Optional[np.ndarray] = None) -> int:
        """
        Store data in long-term vector memory.
        
        Args:
            data: The data to store
            vector: Optional vector representation (if not provided, will be generated)
            
        Returns:
            Index of stored data
        """
        try:
            # Add timestamp
            data["timestamp"] = datetime.now().isoformat()
            
            # Generate vector if not provided
            if vector is None:
                vector = self._generate_vector(data)
                
            # Store in vector memory
            if isinstance(self.vector_memory, list):
                # Simple list storage
                index = len(self.vector_memory)
                self.vector_memory.append(vector)
                self.memory_data.append(data)
            else:
                # FAISS index
                index = len(self.memory_data)
                self.vector_memory.add(np.array([vector], dtype=np.float32))
                self.memory_data.append(data)
                
            # Add to short-term memory as well
            self.short_term_memory.append(data)
            
            # Save to disk
            self._save_vector_memory()
            
            return index
            
        except Exception as e:
            self.logger.error(f"Error storing in memory: {e}")
            return -1
            
    def _generate_vector(self, data: Dict) -> np.ndarray:
        """
        Generate a vector representation of data.
        
        Args:
            data: The data to generate a vector for
            
        Returns:
            numpy array of vector representation
        """
        # This is a placeholder implementation
        # In a real system, this would use an embedding model
        vector = np.zeros(self.vector_dim, dtype=np.float32)
        
        # Fill with some semi-meaningful values based on data
        if "symbol" in data:
            # Use simple hash of symbol to populate some elements
            symbol_hash = hash(data["symbol"]) % 1000
            vector[0:10] = np.array([int(d) for d in str(symbol_hash).zfill(10)]) / 10.0
            
        if "recommendation" in data and isinstance(data["recommendation"], dict):
            rec = data["recommendation"]
            if "score" in rec:
                vector[10] = rec["score"]
            if "confidence" in rec:
                vector[11] = rec["confidence"]
                
        if "agent_insights" in data:
            insights = data["agent_insights"]
            if "technical" in insights and "sentiment" in insights["technical"]:
                sentiment = insights["technical"]["sentiment"]
                vector[20] = 1.0 if sentiment == "bullish" else 0.0 if sentiment == "neutral" else -1.0
                
        # Ensure vector is normalized
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
            
        return vector
        
    def retrieve_from_memory(self, query: Dict, k: int = 5) -> List[Dict]:
        """
        Retrieve relevant data from memory.
        
        Args:
            query: The query to search for
            k: Number of results to return
            
        Returns:
            List of relevant data items
        """
        try:
            # First check short-term memory
            if not self.short_term_memory:
                return []
                
            # Generate query vector
            query_vector = self._generate_vector(query)
            
            # Search in vector memory
            if isinstance(self.vector_memory, list):
                if not self.vector_memory:
                    return []
                    
                # Simple distance calculation for list
                distances = []
                for i, vec in enumerate(self.vector_memory):
                    dist = np.sum((vec - query_vector) ** 2)
                    distances.append((dist, i))
                    
                # Get top k results
                distances.sort()
                results = [self.memory_data[idx] for _, idx in distances[:k]]
                
            else:
                # FAISS search
                if self.vector_memory.ntotal == 0:
                    return []
                    
                distances, indices = self.vector_memory.search(
                    np.array([query_vector], dtype=np.float32), k
                )
                results = [self.memory_data[idx] for idx in indices[0] if idx < len(self.memory_data)]
                
            return results
            
        except Exception as e:
            self.logger.error(f"Error retrieving from memory: {e}")
            return []
            
    def store_episode(self, episode_data: Dict) -> str:
        """
        Store an episode in episodic memory.
        
        Args:
            episode_data: The episode data to store
            
        Returns:
            Episode ID
        """
        try:
            # Generate episode ID
            episode_id = f"ep_{datetime.now().strftime('%Y%m%d%H%M%S')}_{len(self.episodic_memory['episodes'])}"
            
            # Add timestamp and ID
            episode_data["timestamp"] = datetime.now().isoformat()
            episode_data["episode_id"] = episode_id
            
            # Add to episodes
            self.episodic_memory["episodes"].append(episode_data)
            
            # Create indexes for efficient retrieval
            if "symbol" in episode_data:
                symbol = episode_data["symbol"]
                if symbol not in self.episodic_memory["indexes"]:
                    self.episodic_memory["indexes"][symbol] = []
                self.episodic_memory["indexes"][symbol].append(episode_id)
                
            # Save to disk
            self._save_episodic_memory()
            
            return episode_id
            
        except Exception as e:
            self.logger.error(f"Error storing episode: {e}")
            return ""
            
    def retrieve_episodes(self, symbol: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """
        Retrieve episodes from episodic memory.
        
        Args:
            symbol: Optional symbol to filter by
            limit: Maximum number of episodes to return
            
        Returns:
            List of episodes
        """
        try:
            episodes = self.episodic_memory["episodes"]
            
            # Filter by symbol if provided
            if symbol and symbol in self.episodic_memory["indexes"]:
                episode_ids = self.episodic_memory["indexes"][symbol]
                filtered_episodes = []
                for episode in episodes:
                    if episode.get("episode_id") in episode_ids:
                        filtered_episodes.append(episode)
                episodes = filtered_episodes
                
            # Sort by timestamp (newest first)
            episodes.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            
            # Limit results
            return episodes[:limit]
            
        except Exception as e:
            self.logger.error(f"Error retrieving episodes: {e}")
            return []

    def get_user_profile_summary(self) -> Dict:
        """
        Generate a summary of the user's investment profile based on preferences.
        
        Returns:
            dict: Summary of user preferences and tendencies
        """
        # Count stock interactions
        liked_count = len(self.stock_preferences["liked_stocks"])
        disliked_count = len(self.stock_preferences["disliked_stocks"])
        purchased_count = len(self.stock_preferences["purchased_stocks"])
        
        # Get top sectors (if any)
        top_sectors = []
        if self.stock_preferences["sector_preferences"]:
            sorted_sectors = sorted(
                self.stock_preferences["sector_preferences"].items(),
                key=lambda x: x[1],
                reverse=True
            )
            top_sectors = [sector for sector, score in sorted_sectors[:3] if score > 0]
        
        # Get feature importance
        feature_importance = {}
        if hasattr(self.user_model, 'feature_importances_'):
            feature_names = list(self.feature_weights.keys())
            importances = self.user_model.feature_importances_
            for i, feature in enumerate(feature_names):
                if i < len(importances):
                    feature_importance[feature] = float(importances[i])
        
        # Get recent memory summary
        recent_activity = []
        for item in list(self.short_term_memory)[-3:]:  # Last 3 items
            if "symbol" in item:
                recent_activity.append({
                    "symbol": item["symbol"],
                    "timestamp": item.get("timestamp", ""),
                    "type": item.get("type", "analysis")
                })
        
        return {
            "interaction_stats": {
                "liked_stocks": liked_count,
                "disliked_stocks": disliked_count,
                "purchased_stocks": purchased_count,
                "total_viewed": len(self.stock_preferences["viewed_stocks"])
            },
            "preferred_sectors": top_sectors,
            "feature_importance": feature_importance,
            "personalized_weights": self.feature_weights,
            "prediction_accuracy": self.performance_history["accuracy"],
            "memory_stats": {
                "short_term_items": len(self.short_term_memory),
                "long_term_items": len(self.memory_data),
                "episodes": len(self.episodic_memory["episodes"]),
                "recent_activity": recent_activity
            },
            "risk_tolerance": self._determine_risk_tolerance()
        }
        
    def _determine_risk_tolerance(self) -> str:
        """Determine user's risk tolerance based on preferences."""
        # Simple heuristic based on liked stocks
        high_risk_count = 0
        low_risk_count = 0
        
        for stock in self.stock_preferences["liked_stocks"]:
            # Check if we have episodic data about this stock
            episodes = self.retrieve_episodes(symbol=stock)
            for episode in episodes:
                if "agent_insights" in episode and "risk" in episode["agent_insights"]:
                    risk_level = episode["agent_insights"]["risk"].get("risk_level", "moderate")
                    if risk_level in ["high", "very high"]:
                        high_risk_count += 1
                    elif risk_level in ["low", "very low"]:
                        low_risk_count += 1
        
        # Determine risk tolerance
        if high_risk_count > low_risk_count * 2:
            return "high"
        elif low_risk_count > high_risk_count * 2:
            return "low"
        else:
            return "moderate"