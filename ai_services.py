import nltk
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
import torch
import re
import json
from typing import List, Dict, Any
import random

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

class QuestionGenerator:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.question_templates = {
            'mcq': [
                "What is {concept}?",
                "Which of the following best describes {concept}?",
                "In the context of {topic}, {concept} refers to:",
                "What are the key characteristics of {concept}?",
                "How does {concept} relate to {topic}?"
            ],
            'coding': [
                "Write a function to implement {concept} in {language}.",
                "Create a program that demonstrates {concept}.",
                "Implement {concept} using {framework} framework.",
                "Debug the following code that implements {concept}:",
                "Optimize the given {concept} implementation."
            ],
            'case_study': [
                "Analyze a scenario where {concept} is applied in {domain}.",
                "Design a solution using {concept} for the following business problem:",
                "Evaluate the implementation of {concept} in this real-world case:",
                "Compare different approaches to {concept} in {industry}.",
                "Propose improvements to this {concept} implementation:"
            ]
        }
        
    def extract_topics_from_curriculum(self, curriculum_data: pd.DataFrame) -> List[str]:
        """Extract topics from curriculum data using NLP techniques"""
        text_columns = curriculum_data.select_dtypes(include=['object']).columns
        all_text = ""
        
        for col in text_columns:
            all_text += " ".join(curriculum_data[col].astype(str).values)
        
        # Clean and tokenize text
        sentences = nltk.sent_tokenize(all_text.lower())
        
        # Use TF-IDF to find important terms
        vectorizer = TfidfVectorizer(max_features=100, stop_words='english', ngram_range=(1, 3))
        tfidf_matrix = vectorizer.fit_transform(sentences)
        
        # Get feature names (topics)
        feature_names = vectorizer.get_feature_names_out()
        
        # Calculate importance scores
        importance_scores = np.mean(tfidf_matrix.toarray(), axis=0)
        
        # Get top topics
        top_indices = np.argsort(importance_scores)[-20:]
        topics = [feature_names[i] for i in top_indices]
        
        return topics
    
    def generate_mcq_question(self, topic: str, difficulty: str) -> Dict[str, Any]:
        """Generate MCQ question for a given topic"""
        template = random.choice(self.question_templates['mcq'])
        question_text = template.format(concept=topic, topic=topic)
        
        # Generate options based on difficulty
        if difficulty == 'easy':
            options = [
                f"Basic definition of {topic}",
                f"Simple application of {topic}",
                f"Common example of {topic}",
                f"Incorrect definition of {topic}"
            ]
        elif difficulty == 'medium':
            options = [
                f"Advanced concept related to {topic}",
                f"Practical implementation of {topic}",
                f"Theoretical framework of {topic}",
                f"Common misconception about {topic}"
            ]
        else:  # hard
            options = [
                f"Complex theoretical aspect of {topic}",
                f"Advanced implementation strategy for {topic}",
                f"Expert-level application of {topic}",
                f"Subtle distinction in {topic}"
            ]
        
        random.shuffle(options)
        correct_answer = 0  # First option is correct
        
        return {
            'type': 'mcq',
            'question': question_text,
            'options': options,
            'correct_answer': correct_answer,
            'difficulty': difficulty,
            'topic': topic,
            'explanation': f"This question tests understanding of {topic} at {difficulty} level."
        }
    
    def generate_coding_question(self, topic: str, difficulty: str) -> Dict[str, Any]:
        """Generate coding question for a given topic"""
        template = random.choice(self.question_templates['coding'])
        languages = ['Python', 'Java', 'JavaScript', 'C++']
        language = random.choice(languages)
        
        question_text = template.format(concept=topic, language=language, framework='React' if language == 'JavaScript' else 'Spring')
        
        # Generate sample solution based on difficulty
        if difficulty == 'easy':
            sample_code = f"# Basic {topic} implementation\ndef {topic.replace(' ', '_').lower()}():\n    # TODO: Implement basic {topic}\n    pass"
        elif difficulty == 'medium':
            sample_code = f"# Intermediate {topic} implementation\nclass {topic.replace(' ', '').title()}:\n    def __init__(self):\n        # TODO: Initialize {topic}\n        pass\n    \n    def process(self):\n        # TODO: Implement {topic} logic\n        pass"
        else:  # hard
            sample_code = f"# Advanced {topic} implementation\n# Consider edge cases, optimization, and error handling\n# TODO: Implement comprehensive {topic} solution"
        
        return {
            'type': 'coding',
            'question': question_text,
            'language': language,
            'sample_code': sample_code,
            'difficulty': difficulty,
            'topic': topic,
            'test_cases': [
                {'input': 'sample_input', 'expected_output': 'sample_output'},
                {'input': 'edge_case_input', 'expected_output': 'edge_case_output'}
            ]
        }
    
    def generate_case_study_question(self, topic: str, difficulty: str) -> Dict[str, Any]:
        """Generate case study question for a given topic"""
        template = random.choice(self.question_templates['case_study'])
        domains = ['Healthcare', 'Finance', 'E-commerce', 'Manufacturing', 'Education']
        domain = random.choice(domains)
        
        question_text = template.format(concept=topic, domain=domain, industry=domain)
        
        # Generate scenario based on difficulty
        if difficulty == 'easy':
            scenario = f"A {domain.lower()} company wants to implement {topic}. Describe the basic steps and considerations."
        elif difficulty == 'medium':
            scenario = f"A {domain.lower()} organization is facing challenges with {topic}. Analyze the situation and propose solutions."
        else:  # hard
            scenario = f"A multinational {domain.lower()} corporation needs to optimize their {topic} strategy across different markets. Provide a comprehensive analysis."
        
        return {
            'type': 'case_study',
            'question': question_text,
            'scenario': scenario,
            'domain': domain,
            'difficulty': difficulty,
            'topic': topic,
            'evaluation_criteria': [
                'Problem identification',
                'Solution approach',
                'Implementation strategy',
                'Risk assessment',
                'Expected outcomes'
            ]
        }
    
    def generate_questions(self, topics: List[str], num_questions: int, difficulty: str, question_types: List[str]) -> List[Dict[str, Any]]:
        """Generate questions based on specified parameters"""
        questions = []
        questions_per_type = num_questions // len(question_types)
        
        for q_type in question_types:
            for i in range(questions_per_type):
                topic = random.choice(topics)
                
                if q_type == 'mcq':
                    question = self.generate_mcq_question(topic, difficulty)
                elif q_type == 'coding':
                    question = self.generate_coding_question(topic, difficulty)
                elif q_type == 'case_study':
                    question = self.generate_case_study_question(topic, difficulty)
                
                questions.append(question)
        
        # Fill remaining questions if needed
        remaining = num_questions - len(questions)
        for i in range(remaining):
            topic = random.choice(topics)
            q_type = random.choice(question_types)
            
            if q_type == 'mcq':
                question = self.generate_mcq_question(topic, difficulty)
            elif q_type == 'coding':
                question = self.generate_coding_question(topic, difficulty)
            elif q_type == 'case_study':
                question = self.generate_case_study_question(topic, difficulty)
            
            questions.append(question)
        
        return questions

class CurriculumMapper:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        
    def map_curriculum_to_skills(self, curriculum_data: pd.DataFrame) -> Dict[str, Any]:
        """Map curriculum content to skills and competencies"""
        text_columns = curriculum_data.select_dtypes(include=['object']).columns
        all_text = []
        
        for _, row in curriculum_data.iterrows():
            row_text = " ".join([str(row[col]) for col in text_columns])
            all_text.append(row_text)
        
        # Vectorize curriculum content
        tfidf_matrix = self.vectorizer.fit_transform(all_text)
        
        # Cluster similar content
        n_clusters = min(5, len(all_text))
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        clusters = kmeans.fit_predict(tfidf_matrix)
        
        # Map clusters to skill categories
        skill_mapping = {}
        feature_names = self.vectorizer.get_feature_names_out()
        
        for cluster_id in range(n_clusters):
            cluster_center = kmeans.cluster_centers_[cluster_id]
            top_features = np.argsort(cluster_center)[-10:]
            cluster_keywords = [feature_names[i] for i in top_features]
            
            skill_mapping[f"Skill_Category_{cluster_id + 1}"] = {
                'keywords': cluster_keywords,
                'content_items': [i for i, c in enumerate(clusters) if c == cluster_id],
                'difficulty_estimate': self._estimate_difficulty(cluster_keywords)
            }
        
        return skill_mapping
    
    def _estimate_difficulty(self, keywords: List[str]) -> str:
        """Estimate difficulty based on keywords complexity"""
        complex_terms = ['advanced', 'complex', 'optimization', 'algorithm', 'architecture', 'framework']
        basic_terms = ['introduction', 'basic', 'simple', 'overview', 'fundamentals']
        
        complex_count = sum(1 for keyword in keywords if any(term in keyword.lower() for term in complex_terms))
        basic_count = sum(1 for keyword in keywords if any(term in keyword.lower() for term in basic_terms))
        
        if complex_count > basic_count:
            return 'hard'
        elif basic_count > complex_count:
            return 'easy'
        else:
            return 'medium'

class FeedbackAnalyzer:
    def __init__(self):
        self.sentiment_analyzer = pipeline("sentiment-analysis", model="cardiffnlp/twitter-roberta-base-sentiment-latest")
        
    def analyze_feedback(self, feedback_text: str) -> Dict[str, Any]:
        """Analyze feedback sentiment and extract insights"""
        if not feedback_text:
            return {'sentiment': 'neutral', 'confidence': 0.0, 'insights': []}
        
        # Analyze sentiment
        sentiment_result = self.sentiment_analyzer(feedback_text)[0]
        
        # Extract key phrases
        sentences = nltk.sent_tokenize(feedback_text)
        insights = []
        
        for sentence in sentences:
            if len(sentence.split()) > 5:  # Only consider substantial sentences
                insights.append(sentence.strip())
        
        return {
            'sentiment': sentiment_result['label'].lower(),
            'confidence': sentiment_result['score'],
            'insights': insights[:5],  # Top 5 insights
            'word_count': len(feedback_text.split()),
            'suggestions': self._generate_suggestions(sentiment_result['label'], insights)
        }
    
    def _generate_suggestions(self, sentiment: str, insights: List[str]) -> List[str]:
        """Generate improvement suggestions based on feedback analysis"""
        suggestions = []
        
        if sentiment.lower() == 'negative':
            suggestions.extend([
                "Consider reviewing the difficulty level of questions",
                "Provide more detailed explanations for answers",
                "Include more practical examples",
                "Improve question clarity and formatting"
            ])
        elif sentiment.lower() == 'positive':
            suggestions.extend([
                "Maintain current question quality standards",
                "Consider expanding similar question types",
                "Share successful patterns with other curricula"
            ])
        else:  # neutral
            suggestions.extend([
                "Gather more specific feedback",
                "Consider A/B testing different question formats",
                "Review engagement metrics for improvements"
            ])
        
        return suggestions[:3]  # Top 3 suggestions
