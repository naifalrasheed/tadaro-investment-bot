# src/user_profiling/questionnaire.py

from typing import Dict, List, Tuple
import json

class InvestmentQuestionnaire:
    def __init__(self):
        self.questions = self._load_questions()
        self.responses = {}
        self.risk_scores = {
            'time_horizon': 0,
            'risk_tolerance': 0,
            'investment_knowledge': 0,
            'income_stability': 0,
            'loss_attitude': 0
        }

    def _load_questions(self) -> Dict:
        """Load questions from configuration"""
        return {
            'time_horizon': [
                {
                    'id': 'th_1',
                    'question': 'When do you expect to start withdrawing money from your investment account?',
                    'options': [
                        ('Less than 1 year', 1),
                        ('1-3 years', 2),
                        ('3-5 years', 3),
                        ('5-10 years', 4),
                        ('More than 10 years', 5)
                    ]
                },
                {
                    'id': 'th_2',
                    'question': 'Once you begin withdrawing money, how long do you expect to continue withdrawing?',
                    'options': [
                        ('Less than 1 year', 5),
                        ('1-3 years', 4),
                        ('3-5 years', 3),
                        ('5-10 years', 2),
                        ('More than 10 years', 1)
                    ]
                }
            ],
            'risk_tolerance': [
                {
                    'id': 'rt_1',
                    'question': 'Which statement best describes your investment attitude?',
                    'options': [
                        ('I cannot tolerate any investment losses', 1),
                        ('I can tolerate small losses occasionally', 2),
                        ('I can accept moderate losses in pursuit of higher returns', 3),
                        ('I can accept significant volatility for maximum returns', 4),
                        ('I view volatility as an opportunity', 5)
                    ]
                },
                {
                    'id': 'rt_2',
                    'question': 'If your investment dropped 20% in one month, what would you do?',
                    'options': [
                        ('Sell everything immediately', 1),
                        ('Sell some investments', 2),
                        ('Do nothing and wait it out', 3),
                        ('Buy a little more', 4),
                        ('Buy a lot more', 5)
                    ]
                }
            ],
            'investment_knowledge': [
                {
                    'id': 'ik_1',
                    'question': 'How would you rate your investment knowledge?',
                    'options': [
                        ('None', 1),
                        ('Limited', 2),
                        ('Good', 3),
                        ('Extensive', 4),
                        ('Professional', 5)
                    ]
                }
            ],
            'income_stability': [
                {
                    'id': 'is_1',
                    'question': 'How stable is your current and future income?',
                    'options': [
                        ('Very unstable', 1),
                        ('Somewhat unstable', 2),
                        ('Mostly stable', 3),
                        ('Very stable', 4),
                        ('Guaranteed stable', 5)
                    ]
                }
            ],
            'loss_attitude': [
                {
                    'id': 'la_1',
                    'question': 'What is the maximum loss you could tolerate in one year?',
                    'options': [
                        ('0-5%', 1),
                        ('5-10%', 2),
                        ('10-15%', 3),
                        ('15-25%', 4),
                        ('More than 25%', 5)
                    ]
                }
            ]
        }

    def conduct_questionnaire(self) -> Dict:
        """Run the interactive questionnaire"""
        print("\n=== Investment Profile Questionnaire ===\n")
        
        for category, questions in self.questions.items():
            category_title = category.replace('_', ' ').title()
            print(f"\n{category_title}:")
            print("-" * 40)
            
            for question in questions:
                self._ask_question(question, category)
        
        self._calculate_scores()
        return self.risk_scores

    def _ask_question(self, question: Dict, category: str):
        """Present a question and collect response"""
        while True:
            # Clear display for each attempt
            print(f"\n{question['question']}")
            
            # Display options clearly numbered
            for i, (option, _) in enumerate(question['options'], 1):
                print(f"{i}. {option}")
            
            # Get input with clear prompt
            choice = input("\nEnter your choice (1-5): ").strip()
            
            # Validate input
            if choice.isdigit():
                response = int(choice)
                if 1 <= response <= 5:
                    self.responses[question['id']] = response
                    break
                else:
                    print("Please enter a number between 1 and 5")
            else:
                print("Please enter a valid number")

    def _calculate_scores(self):
        """Calculate risk scores for each category"""
        for category, questions in self.questions.items():
            category_score = 0
            for question in questions:
                response_index = self.responses[question['id']] - 1
                score = question['options'][response_index][1]
                category_score += score
            
            # Normalize score to 0-100 range
            max_possible = len(questions) * 5
            self.risk_scores[category] = (category_score / max_possible) * 100

    def get_result_summary(self) -> str:
        """Generate a summary of the questionnaire results"""
        summary = "\n=== Investment Profile Summary ===\n"
        
        for category, score in self.risk_scores.items():
            summary += f"\n{category.replace('_', ' ').title()}: {score:.1f}/100"
            summary += f"\n{self._get_category_interpretation(category, score)}"
            
        return summary

    def _get_category_interpretation(self, category: str, score: float) -> str:
        """Interpret the score for each category"""
        if score < 20:
            return "Very Conservative"
        elif score < 40:
            return "Conservative"
        elif score < 60:
            return "Moderate"
        elif score < 80:
            return "Aggressive"
        else:
            return "Very Aggressive"