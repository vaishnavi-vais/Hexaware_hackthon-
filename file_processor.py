import pandas as pd
import os
from werkzeug.utils import secure_filename
from typing import Dict, List, Any, Tuple
import json
from models import Curriculum, db
from ai_services import QuestionGenerator

class FileProcessor:
    def __init__(self, upload_folder: str):
        self.upload_folder = upload_folder
        self.allowed_extensions = {'csv', 'xlsx', 'xls'}
        self.question_generator = QuestionGenerator()
        
    def allowed_file(self, filename: str) -> bool:
        """Check if file extension is allowed"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.allowed_extensions
    
    def save_uploaded_file(self, file, user_id: int) -> Tuple[bool, str, str]:
        """Save uploaded file and return success status, message, and file path"""
        if not file or file.filename == '':
            return False, "No file selected", ""
        
        if not self.allowed_file(file.filename):
            return False, f"File type not allowed. Supported formats: {', '.join(self.allowed_extensions)}", ""
        
        try:
            filename = secure_filename(file.filename)
            # Add timestamp to avoid conflicts
            timestamp = str(int(pd.Timestamp.now().timestamp()))
            name, ext = os.path.splitext(filename)
            unique_filename = f"{name}_{timestamp}{ext}"
            
            file_path = os.path.join(self.upload_folder, unique_filename)
            file.save(file_path)
            
            return True, "File uploaded successfully", file_path
            
        except Exception as e:
            return False, f"Error saving file: {str(e)}", ""
    
    def process_curriculum_file(self, file_path: str, curriculum_name: str, description: str, user_id: int) -> Tuple[bool, str, Curriculum]:
        """Process uploaded curriculum file and extract topics"""
        try:
            # Read file based on extension
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext == '.csv':
                df = pd.read_csv(file_path)
            elif file_ext in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
            else:
                return False, "Unsupported file format", None
            
            # Validate file structure
            if df.empty:
                return False, "File is empty", None
            
            # Extract topics using AI
            topics = self.question_generator.extract_topics_from_curriculum(df)
            
            # Create curriculum record
            curriculum = Curriculum(
                name=curriculum_name,
                description=description,
                file_path=file_path,
                file_type=file_ext[1:],  # Remove the dot
                uploaded_by=user_id,
                processed=True,
                topics_extracted=topics
            )
            
            db.session.add(curriculum)
            db.session.commit()
            
            return True, f"Curriculum processed successfully. {len(topics)} topics extracted.", curriculum
            
        except Exception as e:
            return False, f"Error processing file: {str(e)}", None
    
    def get_curriculum_preview(self, file_path: str, rows: int = 5) -> Dict[str, Any]:
        """Get preview of curriculum file"""
        try:
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext == '.csv':
                df = pd.read_csv(file_path, nrows=rows)
            elif file_ext in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path, nrows=rows)
            else:
                return {'error': 'Unsupported file format'}
            
            return {
                'columns': df.columns.tolist(),
                'data': df.to_dict('records'),
                'total_rows': len(df),
                'shape': df.shape
            }
            
        except Exception as e:
            return {'error': f"Error reading file: {str(e)}"}
    
    def validate_curriculum_structure(self, file_path: str) -> Dict[str, Any]:
        """Validate curriculum file structure and content"""
        try:
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext == '.csv':
                df = pd.read_csv(file_path)
            elif file_ext in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
            else:
                return {'valid': False, 'errors': ['Unsupported file format']}
            
            errors = []
            warnings = []
            
            # Check if file is empty
            if df.empty:
                errors.append("File is empty")
                return {'valid': False, 'errors': errors}
            
            # Check for minimum columns
            if len(df.columns) < 2:
                warnings.append("File has fewer than 2 columns. Consider adding more descriptive content.")
            
            # Check for missing values
            missing_percentage = (df.isnull().sum().sum() / (df.shape[0] * df.shape[1])) * 100
            if missing_percentage > 50:
                warnings.append(f"File has {missing_percentage:.1f}% missing values")
            
            # Check for text content
            text_columns = df.select_dtypes(include=['object']).columns
            if len(text_columns) == 0:
                warnings.append("No text columns found. Topics extraction may be limited.")
            
            # Check row count
            if len(df) < 5:
                warnings.append("File has fewer than 5 rows. Consider adding more content for better topic extraction.")
            
            return {
                'valid': len(errors) == 0,
                'errors': errors,
                'warnings': warnings,
                'stats': {
                    'rows': len(df),
                    'columns': len(df.columns),
                    'text_columns': len(text_columns),
                    'missing_percentage': missing_percentage
                }
            }
            
        except Exception as e:
            return {'valid': False, 'errors': [f"Error validating file: {str(e)}"]}
    
    def extract_curriculum_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from curriculum file"""
        try:
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext == '.csv':
                df = pd.read_csv(file_path)
            elif file_ext in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
            else:
                return {'error': 'Unsupported file format'}
            
            # Basic statistics
            metadata = {
                'file_size': os.path.getsize(file_path),
                'rows': len(df),
                'columns': len(df.columns),
                'column_names': df.columns.tolist(),
                'data_types': df.dtypes.to_dict(),
                'memory_usage': df.memory_usage(deep=True).sum(),
                'missing_values': df.isnull().sum().to_dict()
            }
            
            # Content analysis
            text_columns = df.select_dtypes(include=['object']).columns
            if len(text_columns) > 0:
                # Sample content from text columns
                sample_content = {}
                for col in text_columns[:3]:  # First 3 text columns
                    sample_values = df[col].dropna().head(3).tolist()
                    sample_content[col] = sample_values
                
                metadata['sample_content'] = sample_content
                metadata['text_columns'] = text_columns.tolist()
            
            # Numeric analysis
            numeric_columns = df.select_dtypes(include=['number']).columns
            if len(numeric_columns) > 0:
                metadata['numeric_summary'] = df[numeric_columns].describe().to_dict()
            
            return metadata
            
        except Exception as e:
            return {'error': f"Error extracting metadata: {str(e)}"}
    
    def cleanup_old_files(self, days_old: int = 30) -> int:
        """Clean up old uploaded files"""
        import time
        
        current_time = time.time()
        cutoff_time = current_time - (days_old * 24 * 60 * 60)
        
        cleaned_count = 0
        
        try:
            for filename in os.listdir(self.upload_folder):
                file_path = os.path.join(self.upload_folder, filename)
                
                if os.path.isfile(file_path):
                    file_time = os.path.getmtime(file_path)
                    
                    if file_time < cutoff_time:
                        os.remove(file_path)
                        cleaned_count += 1
            
            return cleaned_count
            
        except Exception as e:
            print(f"Error cleaning up files: {str(e)}")
            return 0
