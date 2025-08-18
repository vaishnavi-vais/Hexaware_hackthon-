from flask_mail import Message
from models import Notification, User, db
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json

class NotificationService:
    def __init__(self, mail_instance):
        self.mail = mail_instance
        
    def create_notification(self, user_id: int, title: str, message: str, notification_type: str, send_email: bool = True) -> Notification:
        """Create a new notification for a user"""
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            type=notification_type
        )
        
        db.session.add(notification)
        db.session.commit()
        
        if send_email:
            self.send_email_notification(notification)
        
        return notification
    
    def send_email_notification(self, notification: Notification) -> bool:
        """Send email notification to user"""
        try:
            user = User.query.get(notification.user_id)
            if not user or not user.email:
                return False
            
            msg = Message(
                subject=f"Hexaware Question Builder - {notification.title}",
                sender="noreply@hexaware-qb.com",
                recipients=[user.email]
            )
            
            msg.html = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <div style="background: linear-gradient(135deg, #2E86AB, #A23B72); color: white; padding: 20px; border-radius: 8px 8px 0 0;">
                            <h1 style="margin: 0; font-size: 24px;">Hexaware Question Builder</h1>
                        </div>
                        
                        <div style="background: #f9f9f9; padding: 20px; border-radius: 0 0 8px 8px; border: 1px solid #ddd;">
                            <h2 style="color: #2E86AB; margin-top: 0;">{notification.title}</h2>
                            <p style="font-size: 16px; margin-bottom: 20px;">{notification.message}</p>
                            
                            <div style="background: white; padding: 15px; border-radius: 5px; border-left: 4px solid #A23B72;">
                                <p style="margin: 0; font-size: 14px; color: #666;">
                                    <strong>Notification Type:</strong> {notification.type.replace('_', ' ').title()}<br>
                                    <strong>Date:</strong> {notification.created_at.strftime('%Y-%m-%d %H:%M:%S')}
                                </p>
                            </div>
                            
                            <div style="margin-top: 20px; text-align: center;">
                                <a href="http://localhost:5000/dashboard" 
                                   style="background: #2E86AB; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">
                                    View in Dashboard
                                </a>
                            </div>
                        </div>
                        
                        <div style="text-align: center; margin-top: 20px; font-size: 12px; color: #666;">
                            <p>This is an automated message from Hexaware Question Builder System.</p>
                        </div>
                    </div>
                </body>
            </html>
            """
            
            self.mail.send(msg)
            notification.email_sent = True
            db.session.commit()
            return True
            
        except Exception as e:
            print(f"Failed to send email notification: {str(e)}")
            return False
    
    def notify_question_bank_ready(self, user_id: int, question_bank_name: str, num_questions: int):
        """Notify user that question bank is ready"""
        title = "Question Bank Generated Successfully"
        message = f"Your question bank '{question_bank_name}' with {num_questions} questions has been generated and is ready for download."
        
        return self.create_notification(user_id, title, message, "question_bank_ready")
    
    def notify_feedback_acknowledgment(self, user_id: int, feedback_type: str):
        """Notify user that their feedback has been acknowledged"""
        title = "Feedback Received"
        message = f"Thank you for your {feedback_type} feedback. We have received and processed your input to improve our services."
        
        return self.create_notification(user_id, title, message, "feedback_ack")
    
    def notify_progress_reminder(self, user_id: int, assessment_name: str, days_remaining: int):
        """Send progress reminder to user"""
        title = "Assessment Progress Reminder"
        message = f"Reminder: You have {days_remaining} days remaining to complete the '{assessment_name}' assessment. Please log in to continue your progress."
        
        return self.create_notification(user_id, title, message, "progress_reminder")
    
    def notify_new_resource(self, user_ids: List[int], resource_name: str, resource_type: str):
        """Notify multiple users about new resources"""
        title = "New Learning Resource Available"
        message = f"A new {resource_type} '{resource_name}' has been added to your learning materials. Check it out in your dashboard."
        
        notifications = []
        for user_id in user_ids:
            notification = self.create_notification(user_id, title, message, "new_resource")
            notifications.append(notification)
        
        return notifications
    
    def notify_curriculum_processed(self, user_id: int, curriculum_name: str, topics_count: int):
        """Notify user that curriculum has been processed"""
        title = "Curriculum Processing Complete"
        message = f"Your curriculum '{curriculum_name}' has been successfully processed. {topics_count} topics have been identified and are ready for question generation."
        
        return self.create_notification(user_id, title, message, "curriculum_processed")
    
    def notify_assessment_completed(self, user_id: int, assessment_name: str, score: float):
        """Notify user about assessment completion"""
        title = "Assessment Completed"
        message = f"Congratulations! You have completed the '{assessment_name}' assessment with a score of {score:.1f}%. Your results and feedback are now available."
        
        return self.create_notification(user_id, title, message, "assessment_completed")
    
    def notify_learning_plan_ready(self, user_id: int, plan_name: str):
        """Notify user that personalized learning plan is ready"""
        title = "Personalized Learning Plan Ready"
        message = f"Your personalized learning plan '{plan_name}' has been generated based on your performance and preferences. Download it from your dashboard."
        
        return self.create_notification(user_id, title, message, "learning_plan_ready")
    
    def get_user_notifications(self, user_id: int, unread_only: bool = False, limit: int = 50) -> List[Notification]:
        """Get notifications for a specific user"""
        query = Notification.query.filter_by(user_id=user_id)
        
        if unread_only:
            query = query.filter_by(read=False)
        
        return query.order_by(Notification.created_at.desc()).limit(limit).all()
    
    def mark_notification_read(self, notification_id: int, user_id: int) -> bool:
        """Mark a notification as read"""
        notification = Notification.query.filter_by(id=notification_id, user_id=user_id).first()
        
        if notification:
            notification.read = True
            db.session.commit()
            return True
        
        return False
    
    def mark_all_notifications_read(self, user_id: int) -> int:
        """Mark all notifications as read for a user"""
        count = Notification.query.filter_by(user_id=user_id, read=False).update({'read': True})
        db.session.commit()
        return count
    
    def get_notification_stats(self, user_id: int) -> Dict[str, int]:
        """Get notification statistics for a user"""
        total = Notification.query.filter_by(user_id=user_id).count()
        unread = Notification.query.filter_by(user_id=user_id, read=False).count()
        
        # Count by type
        type_counts = {}
        notifications = Notification.query.filter_by(user_id=user_id).all()
        
        for notification in notifications:
            type_counts[notification.type] = type_counts.get(notification.type, 0) + 1
        
        return {
            'total': total,
            'unread': unread,
            'read': total - unread,
            'by_type': type_counts
        }
    
    def send_bulk_notification(self, user_ids: List[int], title: str, message: str, notification_type: str) -> List[Notification]:
        """Send notification to multiple users"""
        notifications = []
        
        for user_id in user_ids:
            notification = self.create_notification(user_id, title, message, notification_type)
            notifications.append(notification)
        
        return notifications
    
    def cleanup_old_notifications(self, days_old: int = 30) -> int:
        """Clean up notifications older than specified days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        count = Notification.query.filter(Notification.created_at < cutoff_date).delete()
        db.session.commit()
        return count
