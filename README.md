# Hexaware AI-Powered Question Builder

A comprehensive AI-powered application that automatically generates intelligent assessments from curriculum data using advanced NLP and Machine Learning techniques.

## 🚀 Features

### Core Functionality
- **AI-Powered Question Generation**: Generate MCQs, coding challenges, and case studies using NLP/ML
- **Curriculum Processing**: Upload and process CSV/Excel curriculum files
- **Smart Topic Extraction**: Automatically identify key topics from curriculum content
- **Multiple Question Types**: Support for multiple choice, coding, and case study questions
- **Difficulty Levels**: Easy, Medium, and Hard question generation
- **Role-Based Access Control**: Admin, Trainer, and Employee roles with different permissions

### AI & Machine Learning
- **Natural Language Processing**: Topic extraction and content analysis
- **Curriculum Mapping**: Intelligent mapping of content to skills and competencies
- **Feedback Analysis**: Sentiment analysis and insight extraction from user feedback
- **Personalized Learning Plans**: AI-generated learning paths based on performance

### Reports & Export
- **Question Banks**: Export in Excel format with detailed formatting
- **Learning Plans**: Generate personalized DOCX learning plans
- **Feedback Reports**: Comprehensive PDF reports with sentiment analysis
- **Assessment Reports**: Detailed completion and performance reports
- **Curriculum Mapping**: DOCX documents showing skill mappings

### Notifications
- **Email Notifications**: Automated email alerts for key events
- **In-App Notifications**: Real-time notifications within the application
- **Event Types**: Question bank ready, feedback acknowledgment, progress reminders, new resources

## 🛠 Technology Stack

- **Backend**: Python Flask with SQLAlchemy ORM
- **Frontend**: Bootstrap 5 with responsive design
- **Database**: SQLite (development) / PostgreSQL (production)
- **AI/ML**: scikit-learn, NLTK, Transformers (Hugging Face)
- **Document Generation**: ReportLab (PDF), python-docx (DOCX), openpyxl (Excel)
- **Email**: Flask-Mail with HTML templates
- **Authentication**: Flask-Login with role-based access control

## 📋 Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Git

## 🔧 Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd hexaware
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Download NLTK data**
   ```python
   python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"
   ```

5. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env file with your configuration
   ```

6. **Initialize database**
   ```bash
   python run.py
   ```

## 🚀 Running the Application

1. **Start the application**
   ```bash
   python run.py
   ```

2. **Access the application**
   - Open your browser and go to `http://localhost:5000`
   - Default admin credentials: `admin` / `admin123`

## 👥 User Roles

### Administrator
- Full system access
- User management
- System configuration
- All report generation
- Curriculum oversight

### Trainer
- Curriculum upload and management
- Question generation
- Assessment creation
- Performance reports
- Student progress tracking

### Employee
- View assigned curricula
- Take assessments
- View personal progress
- Access learning plans
- Provide feedback

## 📊 Usage Guide

### 1. Upload Curriculum
1. Navigate to **Curriculum > Upload**
2. Select CSV or Excel file with curriculum content
3. Provide curriculum name and description
4. AI will automatically extract topics and process content

### 2. Generate Questions
1. Go to **Questions > Generate**
2. Select processed curriculum
3. Choose topics, difficulty level, and question types
4. AI generates questions based on your specifications
5. Download question bank in Excel format

### 3. Create Assessments
1. Use generated question banks to create assessments
2. Assign to employees or groups
3. Track completion and performance
4. Generate detailed reports

### 4. View Reports
1. **Feedback Reports**: Analyze user feedback with sentiment analysis
2. **Assessment Reports**: Track completion rates and scores
3. **Curriculum Mapping**: View AI-generated skill mappings
4. **Learning Plans**: Generate personalized learning paths

## 🔧 Configuration

### Email Settings
Configure email settings in `.env` for notifications:
```env
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
```

### Database Configuration
- **Development**: SQLite (default)
- **Production**: PostgreSQL recommended
```env
DATABASE_URL=postgresql://user:password@localhost/hexaware_qb
```

### AI Model Configuration
- Models are downloaded automatically on first use
- Cache directory: `ai_cache/`
- Supports offline operation after initial download

## 📁 Project Structure

```
hexaware/
├── app.py                 # Main Flask application
├── run.py                 # Application entry point
├── config.py              # Configuration settings
├── models.py              # Database models
├── auth.py                # Authentication blueprint
├── routes.py              # Main application routes
├── ai_services.py         # AI/ML services
├── report_generator.py    # Report generation
├── notification_service.py # Notification system
├── file_processor.py      # File upload/processing
├── requirements.txt       # Python dependencies
├── templates/             # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── auth/
│   ├── dashboard/
│   ├── curriculum/
│   └── questions/
├── uploads/               # Uploaded files
└── ai_cache/             # AI model cache
```

## 🧪 Testing

Run tests with:
```bash
python -m pytest tests/
```

## 🚀 Deployment

### Production Deployment
1. Set environment to production:
   ```env
   FLASK_ENV=production
   FLASK_CONFIG=production
   ```

2. Use a production WSGI server:
   ```bash
   gunicorn -w 4 -b 0.0.0.0:5000 run:app
   ```

3. Set up reverse proxy (nginx recommended)
4. Configure SSL certificates
5. Set up database backups

## 🔒 Security Features

- **Password Hashing**: Werkzeug security for password protection
- **CSRF Protection**: Flask-WTF CSRF tokens
- **Role-Based Access**: Granular permission system
- **File Upload Security**: Secure filename handling and type validation
- **SQL Injection Protection**: SQLAlchemy ORM prevents SQL injection

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Contact the development team
- Check the documentation

## 🔄 Version History

- **v1.0.0**: Initial release with core functionality
- AI-powered question generation
- Multi-format report generation
- Role-based access control
- Comprehensive notification system

---

**Hexaware Question Builder** - Transforming education through AI-powered assessment generation.
