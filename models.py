from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from enum import Enum

db = SQLAlchemy()

class UserRole(Enum):
    ADMIN = "admin"
    TRAINER = "trainer"
    EMPLOYEE = "employee"

class DifficultyLevel(Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

class QuestionType(Enum):
    MCQ = "mcq"
    CODING = "coding"
    CASE_STUDY = "case_study"

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum(UserRole), nullable=False, default=UserRole.EMPLOYEE)
    department = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    curricula = db.relationship('Curriculum', backref='uploaded_by_user', lazy=True)
    question_requests = db.relationship('QuestionRequest', backref='requested_by', lazy=True)
    notifications = db.relationship('Notification', backref='user', lazy=True)

class Curriculum(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    file_path = db.Column(db.String(500), nullable=False)
    file_type = db.Column(db.String(10), nullable=False)  # csv, xlsx
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed = db.Column(db.Boolean, default=False)
    topics_extracted = db.Column(db.JSON)  # Store extracted topics as JSON
    
    # Relationships
    question_banks = db.relationship('QuestionBank', backref='curriculum', lazy=True)

class QuestionRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    curriculum_id = db.Column(db.Integer, db.ForeignKey('curriculum.id'), nullable=False)
    topics = db.Column(db.JSON, nullable=False)  # List of topics
    num_questions = db.Column(db.Integer, nullable=False)
    difficulty_level = db.Column(db.Enum(DifficultyLevel), nullable=False)
    question_types = db.Column(db.JSON, nullable=False)  # List of question types
    status = db.Column(db.String(20), default='pending')  # pending, processing, completed, failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    # Relationships
    question_bank = db.relationship('QuestionBank', backref='request', uselist=False)

class QuestionBank(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('question_request.id'), nullable=False)
    curriculum_id = db.Column(db.Integer, db.ForeignKey('curriculum.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    questions = db.Column(db.JSON, nullable=False)  # Store questions as JSON
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    file_path = db.Column(db.String(500))  # Path to generated file
    
    # Relationships
    assessments = db.relationship('Assessment', backref='question_bank', lazy=True)

class Assessment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_bank_id = db.Column(db.Integer, db.ForeignKey('question_bank.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    score = db.Column(db.Float)
    total_questions = db.Column(db.Integer, nullable=False)
    correct_answers = db.Column(db.Integer, default=0)
    time_taken = db.Column(db.Integer)  # in minutes
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    feedback = db.Column(db.Text)
    
    # Relationships
    user_assessment = db.relationship('User', backref='assessments')

class LearningPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    curriculum_id = db.Column(db.Integer, db.ForeignKey('curriculum.id'), nullable=False)
    plan_data = db.Column(db.JSON, nullable=False)  # Personalized learning plan
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    file_path = db.Column(db.String(500))  # Path to generated DOCX/PDF
    
    # Relationships
    plan_user = db.relationship('User', backref='learning_plans')
    plan_curriculum = db.relationship('Curriculum', backref='learning_plans')

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), nullable=False)  # question_bank_ready, feedback_ack, progress_reminder, new_resource
    read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    email_sent = db.Column(db.Boolean, default=False)

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # feedback, curriculum_mapping, issue_resolution, assessment_completion
    generated_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    generator = db.relationship('User', backref='generated_reports')
