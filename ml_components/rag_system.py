"""
RAG System - Retrieval Augmented Generation for Financial Knowledge

This module implements a knowledge retrieval system that augments
the investment bot with financial domain knowledge, market data,
news analysis, and structured financial information.
"""

import logging
import json
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import re

class FinancialKnowledgeRAG:
    """
    Retrieval Augmented Generation system for financial knowledge.
    
    This system provides:
    1. Financial knowledge retrieval
    2. News and research analysis
    3. Structured financial data lookups
    4. Market context enhancement
    """
    
    def __init__(self, data_path: Optional[str] = None, embedding_dim: int = 384):
        """
        Initialize the RAG system.
        
        Args:
            data_path: Optional path to pre-loaded data
            embedding_dim: Dimension of the embedding vectors
        """
        self.logger = logging.getLogger(__name__)
        self.data_path = data_path
        self.embedding_dim = embedding_dim
        
        # Initialize knowledge stores
        self.financial_terms = self._load_financial_terms()
        self.metric_descriptions = self._load_metric_descriptions()
        self.industry_profiles = self._load_industry_profiles()
        self.embeddings = {}
        
        # Knowledge sources
        self.knowledge_sources = {
            "financial_terms": self.financial_terms,
            "metric_descriptions": self.metric_descriptions,
            "industry_profiles": self.industry_profiles
        }
        
    def retrieve_context(self, query: str, market_data: Dict = None, 
                        fundamental_data: Dict = None, k: int = 5) -> Dict:
        """
        Retrieve relevant context for the given query.
        
        Args:
            query: The query to retrieve context for
            market_data: Optional market data for enhancing context
            fundamental_data: Optional fundamental data for enhancing context
            k: Number of results to return
            
        Returns:
            Dictionary of relevant context information
        """
        try:
            self.logger.info(f"Retrieving context for query: {query}")
            
            # Extract key terms from query
            terms = self._extract_key_terms(query)
            
            # Retrieve relevant context from knowledge sources
            financial_context = self._retrieve_financial_terms(terms)
            metric_context = self._retrieve_metric_descriptions(terms)
            industry_context = self._retrieve_industry_context(fundamental_data)
            
            # Extract company-specific information from data if available
            company_context = self._extract_company_context(
                fundamental_data, market_data
            )
            
            # Augment with news if available
            news_context = self._retrieve_news_context(query, market_data)
            
            # Build comprehensive context
            context = {
                "query": query,
                "financial_terms": financial_context,
                "metrics": metric_context,
                "industry": industry_context,
                "company": company_context,
                "news": news_context,
                "timestamp": datetime.now().isoformat()
            }
            
            return context
            
        except Exception as e:
            self.logger.error(f"Error retrieving context: {e}")
            return {"query": query, "error": str(e), "timestamp": datetime.now().isoformat()}
    
    def retrieve_financial_knowledge(self, topic: str) -> Dict:
        """
        Retrieve specific financial knowledge about a topic.
        
        Args:
            topic: Financial topic to retrieve information about
            
        Returns:
            Dictionary containing relevant financial knowledge
        """
        try:
            # Direct lookup in financial terms
            if topic.lower() in self.financial_terms:
                return {
                    "topic": topic,
                    "definition": self.financial_terms[topic.lower()],
                    "source": "financial_terms"
                }
            
            # Check metric descriptions
            if topic.lower() in self.metric_descriptions:
                return {
                    "topic": topic,
                    "definition": self.metric_descriptions[topic.lower()]["description"],
                    "calculation": self.metric_descriptions[topic.lower()].get("calculation", ""),
                    "source": "metric_descriptions"
                }
            
            # Check industry profiles
            if topic.lower() in self.industry_profiles:
                return {
                    "topic": topic,
                    "profile": self.industry_profiles[topic.lower()],
                    "source": "industry_profiles"
                }
            
            # No exact match, return closest terms
            terms = self._extract_key_terms(topic)
            financial_context = self._retrieve_financial_terms(terms)
            
            return {
                "topic": topic,
                "related_terms": financial_context,
                "source": "similar_terms"
            }
            
        except Exception as e:
            self.logger.error(f"Error retrieving financial knowledge for {topic}: {e}")
            return {"topic": topic, "error": str(e)}
    
    def analyze_news_sentiment(self, symbol: str, news_data: List[Dict]) -> Dict:
        """
        Analyze sentiment from news articles.
        
        Args:
            symbol: Stock ticker symbol
            news_data: List of news article data
            
        Returns:
            Dictionary containing sentiment analysis results
        """
        # Placeholder for news sentiment analysis
        # This would ideally use a language model for actual sentiment analysis
        return {
            "symbol": symbol,
            "sentiment_score": 50,  # Neutral
            "article_count": len(news_data) if news_data else 0,
            "latest_date": datetime.now().isoformat(),
            "top_topics": []
        }
    
    def _extract_key_terms(self, text: str) -> List[str]:
        """Extract key financial terms from text."""
        terms = []
        
        # Simple tokenization for demo purposes
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        
        # Filter for financial terms
        financial_keywords = [
            'stock', 'bond', 'market', 'equity', 'asset', 'portfolio',
            'investment', 'dividend', 'yield', 'eps', 'revenue', 'income',
            'balance', 'cash', 'flow', 'ratio', 'roi', 'pe', 'profit',
            'margin', 'growth', 'valuation', 'analyst', 'sector', 'industry',
            'capital', 'risk', 'return', 'volatility', 'bullish', 'bearish',
            'debt', 'leverage', 'liquidity', 'ebitda', 'fcf', 'rotc',
            'profitability', 'recommendation'
        ]
        
        # Add terms that are in our financial keywords list
        terms.extend([word for word in words if word in financial_keywords])
        
        # Add any multi-word financial terms
        multi_word_terms = [
            'price to earnings', 'price-to-earnings', 'p/e ratio',
            'return on equity', 'return on assets', 'return on investment',
            'return on tangible capital', 'rotc', 'free cash flow',
            'debt to equity', 'profit margin', 'gross margin', 'net margin',
            'operating margin', 'compound annual growth rate', 'cagr',
            'dividend yield', 'earnings per share', 'book value',
            'price to book', 'price-to-book', 'p/b ratio',
            'enterprise value', 'market capitalization', 'market cap',
            'income statement', 'balance sheet', 'cash flow statement'
        ]
        
        for term in multi_word_terms:
            if term.lower() in text.lower():
                terms.append(term)
        
        return list(set(terms))  # Deduplicate
    
    def _retrieve_financial_terms(self, terms: List[str]) -> Dict[str, str]:
        """Retrieve definitions for financial terms."""
        result = {}
        
        for term in terms:
            if term in self.financial_terms:
                result[term] = self.financial_terms[term]
        
        return result
    
    def _retrieve_metric_descriptions(self, terms: List[str]) -> Dict[str, Dict]:
        """Retrieve descriptions for financial metrics."""
        result = {}
        
        for term in terms:
            if term in self.metric_descriptions:
                result[term] = self.metric_descriptions[term]
        
        return result
    
    def _retrieve_industry_context(self, fundamental_data: Optional[Dict]) -> Dict:
        """Retrieve industry context based on fundamental data."""
        if not fundamental_data:
            return {}
            
        industry = fundamental_data.get("industry", "")
        sector = fundamental_data.get("sector", "")
        
        result = {}
        
        if industry.lower() in self.industry_profiles:
            result["industry"] = self.industry_profiles[industry.lower()]
            
        if sector.lower() in self.industry_profiles:
            result["sector"] = self.industry_profiles[sector.lower()]
            
        return result
    
    def _extract_company_context(self, fundamental_data: Optional[Dict], 
                               market_data: Optional[Dict]) -> Dict:
        """Extract relevant company context from data."""
        if not fundamental_data:
            return {}
            
        company_context = {}
        
        # Basic company information
        company_context["name"] = fundamental_data.get("name", "")
        company_context["sector"] = fundamental_data.get("sector", "")
        company_context["industry"] = fundamental_data.get("industry", "")
        
        # Extract key financial metrics if available
        metrics = {}
        
        # Balance sheet metrics
        balance_sheet = fundamental_data.get("balance_sheet", {})
        if balance_sheet:
            metrics["total_assets"] = balance_sheet.get("totalAssets")
            metrics["total_debt"] = balance_sheet.get("totalDebt")
            metrics["cash_and_equivalents"] = balance_sheet.get("cash")
            metrics["total_equity"] = balance_sheet.get("totalStockholderEquity")
            
        # Income statement metrics
        income_stmt = fundamental_data.get("income_statement", {})
        if income_stmt:
            metrics["revenue"] = income_stmt.get("totalRevenue")
            metrics["net_income"] = income_stmt.get("netIncome")
            metrics["ebitda"] = income_stmt.get("ebitda")
            
        # Filter out None values
        metrics = {k: v for k, v in metrics.items() if v is not None}
        company_context["key_metrics"] = metrics
        
        # Add market data context if available
        if market_data:
            market_context = {}
            market_context["last_price"] = market_data.get("last_price")
            market_context["volume"] = market_data.get("volume")
            market_context["market_cap"] = market_data.get("market_cap")
            
            # Filter out None values
            market_context = {k: v for k, v in market_context.items() if v is not None}
            company_context["market_data"] = market_context
            
        return company_context
    
    def _retrieve_news_context(self, query: str, market_data: Optional[Dict]) -> List[Dict]:
        """Retrieve relevant news context."""
        # This is a placeholder - in a real implementation, this would
        # retrieve and analyze actual news articles
        if not market_data or "news" not in market_data:
            return []
            
        news_data = market_data.get("news", [])
        
        # Extract relevant news based on query terms
        terms = self._extract_key_terms(query)
        relevant_news = []
        
        for article in news_data[:10]:  # Limit to 10 most recent articles
            article_text = article.get("headline", "") + " " + article.get("summary", "")
            
            # Check if any term appears in the article
            if any(term in article_text.lower() for term in terms):
                relevant_news.append({
                    "headline": article.get("headline", ""),
                    "summary": article.get("summary", ""),
                    "date": article.get("date", ""),
                    "url": article.get("url", "")
                })
                
        return relevant_news[:5]  # Return up to 5 most relevant articles
    
    def _load_financial_terms(self) -> Dict[str, str]:
        """Load financial terms dictionary."""
        # This is a placeholder with a small set of terms
        # In a real implementation, this would load from a file or database
        return {
            "rotc": "Return on Tangible Capital (ROTC) measures a company's efficiency in generating profits from its tangible capital. It is calculated as NOPAT (Net Operating Profit After Tax) divided by Tangible Capital.",
            "nopat": "Net Operating Profit After Tax (NOPAT) represents a company's potential cash earnings if it had no debt and held no financial assets. It excludes the effects of financial leverage and non-operating items.",
            "tangible capital": "Tangible Capital is the physical and financial capital used in a business, excluding intangible assets like goodwill, patents, and trademarks.",
            "pe ratio": "The Price-to-Earnings Ratio (P/E) is calculated by dividing a company's share price by its earnings per share. It indicates how much investors are willing to pay for a dollar of earnings.",
            "ps ratio": "The Price-to-Sales Ratio (P/S) is calculated by dividing a company's market capitalization by its total revenue. It helps evaluate companies that don't yet have positive earnings.",
            "ev/ebitda": "Enterprise Value to EBITDA (EV/EBITDA) is a ratio used to determine the value of a company. It compares the company's enterprise value to its earnings before interest, taxes, depreciation, and amortization.",
            "debt to equity": "The Debt to Equity Ratio measures a company's financial leverage by dividing its total liabilities by stockholders' equity, indicating the proportion of debt and equity used to finance assets.",
            "current ratio": "The Current Ratio is calculated by dividing a company's current assets by its current liabilities, measuring the company's ability to pay short-term obligations.",
            "profit margin": "Profit Margin is a profitability ratio calculated as net income divided by revenue, showing the percentage of each dollar of revenue that represents profit.",
            "free cash flow": "Free Cash Flow (FCF) represents the cash a company generates after accounting for cash outflows to support operations and maintain capital assets."
        }
    
    def _load_metric_descriptions(self) -> Dict[str, Dict]:
        """Load financial metric descriptions."""
        # This is a placeholder with a small set of metrics
        # In a real implementation, this would load from a file or database
        return {
            "rotc": {
                "description": "Return on Tangible Capital (ROTC) measures a company's efficiency in generating profits from its tangible capital.",
                "calculation": "ROTC = NOPAT / Tangible Capital",
                "interpretation": "Higher ROTC indicates better efficiency in using tangible capital to generate profits.",
                "typical_range": "Good ROTC values are typically above 10%, with excellent being above 15%."
            },
            "pe ratio": {
                "description": "The Price-to-Earnings Ratio (P/E) indicates how much investors are willing to pay for a dollar of earnings.",
                "calculation": "P/E Ratio = Share Price / Earnings Per Share",
                "interpretation": "A higher P/E suggests investors expect higher growth in the future.",
                "typical_range": "The average P/E ratio for S&P 500 companies historically ranges from 15 to 25."
            },
            "ev/ebitda": {
                "description": "Enterprise Value to EBITDA (EV/EBITDA) is used to determine the value of a company, accounting for debt.",
                "calculation": "EV/EBITDA = Enterprise Value / EBITDA",
                "interpretation": "Lower values indicate potentially undervalued companies.",
                "typical_range": "Healthy companies typically have EV/EBITDA ratios between 6 and 12."
            }
        }
    
    def _load_industry_profiles(self) -> Dict[str, Dict]:
        """Load industry profile information."""
        # This is a placeholder with a small set of industries
        # In a real implementation, this would load from a file or database
        return {
            "technology": {
                "description": "The technology sector includes companies that primarily develop software, manufacture electronics, create computer hardware, or provide technology services.",
                "key_metrics": ["R&D Spending", "Revenue Growth", "Gross Margin"],
                "typical_pe": "Technology companies often trade at higher P/E ratios (25-40) due to growth expectations.",
                "typical_rotc": "Well-managed technology companies typically have ROTC values of 15-25%.",
                "growth_profile": "The sector typically shows above-average growth rates but can be cyclical."
            },
            "financial services": {
                "description": "The financial services sector includes banks, insurance companies, investment firms, and other businesses that manage money.",
                "key_metrics": ["Net Interest Margin", "Return on Equity", "Loan Loss Provisions", "Capital Adequacy"],
                "typical_pe": "Financial companies typically trade at lower P/E ratios (10-15) than other sectors.",
                "typical_rotc": "Well-managed financial companies typically have ROTC values of 8-15%.",
                "growth_profile": "Growth is often tied to economic cycles and interest rate environments."
            },
            "healthcare": {
                "description": "The healthcare sector includes pharmaceutical companies, biotechnology firms, medical device manufacturers, healthcare providers, and insurers.",
                "key_metrics": ["R&D Pipeline", "Margins", "Patent Expiry Dates", "Approval Rates"],
                "typical_pe": "Healthcare companies often trade at moderate to high P/E ratios (20-30) depending on growth prospects.",
                "typical_rotc": "Well-managed healthcare companies typically have ROTC values of 12-20%.",
                "growth_profile": "Growth tends to be stable with demographic tailwinds but regulatory risks."
            }
        }