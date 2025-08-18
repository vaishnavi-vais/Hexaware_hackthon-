from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, send_file, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
import json
from datetime import datetime, timedelta
import pandas as pd

from models import (User, Curriculum, QuestionRequest, QuestionBank, Assessment, 
                   LearningPlan, Notification, Report, UserRole, DifficultyLevel, 
                   QuestionType, db)
from auth import role_required
from ai_services import QuestionGenerator, CurriculumMapper, FeedbackAnalyzer
from report_generator import ReportGenerator
from notification_service import NotificationService
from file_processor import FileProcessor

# Services will be initialized within routes

# Create blueprints
main_bp = Blueprint('main', __name__)
dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')
curriculum_bp = Blueprint('curriculum', __name__, url_prefix='/curriculum')
questions_bp = Blueprint('questions', __name__, url_prefix='/questions')
assessments_bp = Blueprint('assessments', __name__, url_prefix='/assessments')
reports_bp = Blueprint('reports', __name__, url_prefix='/reports')
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Main routes
@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    return render_template('index.html')

@main_bp.route('/about')
def about():
    return render_template('about.html')

# Dashboard routes
@dashboard_bp.route('/')
@login_required
def index():
    # Get user statistics
    stats = {
        'curricula_count': Curriculum.query.filter_by(uploaded_by=current_user.id).count(),
        'question_requests': QuestionRequest.query.filter_by(user_id=current_user.id).count(),
        'assessments_completed': Assessment.query.filter_by(user_id=current_user.id).filter(Assessment.completed_at.isnot(None)).count(),
        'notifications_unread': Notification.query.filter_by(user_id=current_user.id, read=False).count()
    }
    
    # Get recent activities
    recent_curricula = Curriculum.query.filter_by(uploaded_by=current_user.id).order_by(Curriculum.uploaded_at.desc()).limit(5).all()
    recent_requests = QuestionRequest.query.filter_by(user_id=current_user.id).order_by(QuestionRequest.created_at.desc()).limit(5).all()
    recent_notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).limit(5).all()
    
    return render_template('dashboard/index.html', 
                         stats=stats, 
                         recent_curricula=recent_curricula,
                         recent_requests=recent_requests,
                         recent_notifications=recent_notifications)

@dashboard_bp.route('/notifications')
@login_required
def notifications():
    page = request.args.get('page', 1, type=int)
    notifications = Notification.query.filter_by(user_id=current_user.id)\
                                    .order_by(Notification.created_at.desc())\
                                    .paginate(page=page, per_page=20, error_out=False)
    
    return render_template('dashboard/notifications.html', notifications=notifications)

# Curriculum routes
@curriculum_bp.route('/')
@login_required
def index():
    curricula = Curriculum.query.filter_by(uploaded_by=current_user.id).order_by(Curriculum.uploaded_at.desc()).all()
    return render_template('curriculum/index.html', curricula=curricula)

@curriculum_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        curriculum_name = request.form.get('name')
        description = request.form.get('description', '')
        
        if not curriculum_name:
            flash('Curriculum name is required', 'error')
            return redirect(request.url)
        
        # Initialize services
        file_processor = FileProcessor(current_app.config['UPLOAD_FOLDER'])
        
        # Save file
        success, message, file_path = file_processor.save_uploaded_file(file, current_user.id)
        
        if not success:
            flash(message, 'error')
            return redirect(request.url)
        
        # Process curriculum
        success, message, curriculum = file_processor.process_curriculum_file(
            file_path, curriculum_name, description, current_user.id
        )
        
        if success:
            # Send notification
            notification_service = NotificationService(current_app.extensions['mail'])
            notification_service.notify_curriculum_processed(
                current_user.id, curriculum_name, len(curriculum.topics_extracted)
            )
            
            flash(message, 'success')
            return redirect(url_for('curriculum.view', id=curriculum.id))
        else:
            flash(message, 'error')
            return redirect(request.url)
    
    return render_template('curriculum/upload.html')

@curriculum_bp.route('/<int:id>')
@login_required
def view(id):
    curriculum = Curriculum.query.filter_by(id=id, uploaded_by=current_user.id).first_or_404()
    
    # Get curriculum mapping
    if curriculum.processed and curriculum.file_path:
        try:
            curriculum_mapper = CurriculumMapper()
            df = pd.read_csv(curriculum.file_path) if curriculum.file_type == 'csv' else pd.read_excel(curriculum.file_path)
            mapping = curriculum_mapper.map_curriculum_to_skills(df)
        except:
            mapping = {}
    else:
        mapping = {}
    
    return render_template('curriculum/view.html', curriculum=curriculum, mapping=mapping)

# Questions routes
@questions_bp.route('/')
@login_required
def index():
    requests = QuestionRequest.query.filter_by(user_id=current_user.id).order_by(QuestionRequest.created_at.desc()).all()
    return render_template('questions/index.html', requests=requests)

@questions_bp.route('/generate', methods=['GET', 'POST'])
@login_required
def generate():
    if request.method == 'POST':
        curriculum_id = request.form.get('curriculum_id', type=int)
        topics = request.form.getlist('topics')
        num_questions = request.form.get('num_questions', type=int)
        difficulty = request.form.get('difficulty')
        question_types = request.form.getlist('question_types')
        
        # Validation
        if not curriculum_id or not topics or not num_questions or not difficulty or not question_types:
            flash('All fields are required', 'error')
            return redirect(request.url)
        
        curriculum = Curriculum.query.filter_by(id=curriculum_id, uploaded_by=current_user.id).first()
        if not curriculum:
            flash('Invalid curriculum selected', 'error')
            return redirect(request.url)
        
        # Create question request
        question_request = QuestionRequest(
            user_id=current_user.id,
            curriculum_id=curriculum_id,
            topics=topics,
            num_questions=num_questions,
            difficulty_level=DifficultyLevel(difficulty),
            question_types=question_types,
            status='processing'
        )
        
        db.session.add(question_request)
        db.session.commit()
        
        try:
            # Initialize services
            question_generator = QuestionGenerator()
            report_generator = ReportGenerator()
            
            # Generate questions
            questions = question_generator.generate_questions(topics, num_questions, difficulty, question_types)
            
            # Create question bank
            question_bank = QuestionBank(
                request_id=question_request.id,
                curriculum_id=curriculum_id,
                name=f"Question Bank - {curriculum.name} - {datetime.now().strftime('%Y%m%d_%H%M%S')}",
                questions=questions
            )
            
            db.session.add(question_bank)
            
            # Update request status
            question_request.status = 'completed'
            question_request.completed_at = datetime.utcnow()
            
            db.session.commit()
            
            # Generate Excel file
            filename = f"question_bank_{question_bank.id}.xlsx"
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            report_generator.generate_question_bank_excel(questions, file_path)
            question_bank.file_path = file_path
            db.session.commit()
            
            # Send notification
            notification_service = NotificationService(current_app.extensions['mail'])
            notification_service.notify_question_bank_ready(
                current_user.id, question_bank.name, num_questions
            )
            
            flash('Questions generated successfully!', 'success')
            return redirect(url_for('questions.view', id=question_bank.id))
            
        except Exception as e:
            question_request.status = 'failed'
            db.session.commit()
            flash(f'Error generating questions: {str(e)}', 'error')
            return redirect(request.url)
    
    # Get user's curricula for the form
    curricula = Curriculum.query.filter_by(uploaded_by=current_user.id, processed=True).all()
    return render_template('questions/generate.html', curricula=curricula)

@questions_bp.route('/<int:id>')
@login_required
def view(id):
    question_bank = QuestionBank.query.join(QuestionRequest)\
                                    .filter(QuestionBank.id == id, QuestionRequest.user_id == current_user.id)\
                                    .first_or_404()
    
    return render_template('questions/view.html', question_bank=question_bank)

@questions_bp.route('/<int:id>/download')
@login_required
def download(id):
    question_bank = QuestionBank.query.join(QuestionRequest)\
                                    .filter(QuestionBank.id == id, QuestionRequest.user_id == current_user.id)\
                                    .first_or_404()
    
    if question_bank.file_path and os.path.exists(question_bank.file_path):
        return send_file(question_bank.file_path, as_attachment=True, 
                        download_name=f"{question_bank.name}.xlsx")
    else:
        flash('File not found', 'error')
        return redirect(url_for('questions.view', id=id))

# Assessment routes
@assessments_bp.route('/')
@login_required
def index():
    assessments = Assessment.query.filter_by(user_id=current_user.id)\
                                .order_by(Assessment.started_at.desc()).all()
    return render_template('assessments/index.html', assessments=assessments)

@assessments_bp.route('/<int:id>')
@login_required
def view(id):
    assessment = Assessment.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    return render_template('assessments/view.html', assessment=assessment)

# Reports routes
@reports_bp.route('/')
@login_required
@role_required(UserRole.ADMIN, UserRole.TRAINER)
def index():
    reports = Report.query.filter_by(generated_by=current_user.id)\
                         .order_by(Report.created_at.desc()).all()
    return render_template('reports/index.html', reports=reports)

@reports_bp.route('/generate', methods=['GET', 'POST'])
@login_required
@role_required(UserRole.ADMIN, UserRole.TRAINER)
def generate():
    if request.method == 'POST':
        report_type = request.form.get('report_type')
        
        if report_type == 'feedback':
            # Initialize services
            feedback_analyzer = FeedbackAnalyzer()
            report_generator = ReportGenerator()
            
            # Generate feedback report
            assessments = Assessment.query.filter(Assessment.feedback.isnot(None)).all()
            feedback_data = []
            
            for assessment in assessments:
                if assessment.feedback:
                    analysis = feedback_analyzer.analyze_feedback(assessment.feedback)
                    feedback_data.append(analysis)
            
            filename = f"feedback_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            report_generator.generate_feedback_report_pdf(feedback_data, file_path)
            
        elif report_type == 'assessment_completion':
            # Initialize services if not already done
            if 'report_generator' not in locals():
                report_generator = ReportGenerator()
                
            # Generate assessment completion report
            assessments = Assessment.query.all()
            assessment_data = []
            
            for assessment in assessments:
                assessment_data.append({
                    'username': assessment.user_assessment.username,
                    'score': assessment.score or 0,
                    'total_questions': assessment.total_questions,
                    'correct_answers': assessment.correct_answers,
                    'time_taken': assessment.time_taken,
                    'completed_at': assessment.completed_at
                })
            
            filename = f"assessment_completion_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            report_generator.generate_assessment_completion_report_pdf(assessment_data, file_path)
        
        # Create report record
        report = Report(
            name=f"{report_type.replace('_', ' ').title()} Report",
            type=report_type,
            generated_by=current_user.id,
            file_path=file_path
        )
        
        db.session.add(report)
        db.session.commit()
        
        flash('Report generated successfully!', 'success')
        return redirect(url_for('reports.view', id=report.id))
    
    return render_template('reports/generate.html')

@reports_bp.route('/<int:id>')
@login_required
@role_required(UserRole.ADMIN, UserRole.TRAINER)
def view(id):
    report = Report.query.filter_by(id=id, generated_by=current_user.id).first_or_404()
    return render_template('reports/view.html', report=report)

@reports_bp.route('/<int:id>/download')
@login_required
@role_required(UserRole.ADMIN, UserRole.TRAINER)
def download(id):
    report = Report.query.filter_by(id=id, generated_by=current_user.id).first_or_404()
    
    if report.file_path and os.path.exists(report.file_path):
        return send_file(report.file_path, as_attachment=True)
    else:
        flash('File not found', 'error')
        return redirect(url_for('reports.view', id=id))

# API routes
@api_bp.route('/notifications/mark_read/<int:notification_id>', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    notification = Notification.query.filter_by(id=notification_id, user_id=current_user.id).first()
    
    if notification:
        notification.read = True
        db.session.commit()
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'message': 'Notification not found'}), 404

@api_bp.route('/curriculum/<int:id>/topics')
@login_required
def get_curriculum_topics(id):
    curriculum = Curriculum.query.filter_by(id=id, uploaded_by=current_user.id).first()
    
    if curriculum and curriculum.topics_extracted:
        return jsonify({'topics': curriculum.topics_extracted})
    
    return jsonify({'topics': []})
