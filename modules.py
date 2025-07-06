from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    role = db.Column(db.String(20), default='student')  # 'student' or 'admin'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    skill_tests = db.relationship('SoftSkillTest', backref='user', lazy=True)
    submissions = db.relationship('Submission', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.role == 'admin'

class SoftSkillTest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    test_name = db.Column(db.String(100), nullable=False)
    
    # Skill scores (0-100)
    communication_score = db.Column(db.Integer, default=0)
    empathy_score = db.Column(db.Integer, default=0)
    collaboration_score = db.Column(db.Integer, default=0)
    leadership_score = db.Column(db.Integer, default=0)
    problem_solving_score = db.Column(db.Integer, default=0)
    
    total_score = db.Column(db.Integer, default=0)
    
    # Test responses
    communication_response = db.Column(db.Text)
    empathy_response = db.Column(db.Text)
    collaboration_response = db.Column(db.Text)
    leadership_response = db.Column(db.Text)
    problem_solving_response = db.Column(db.Text)
    
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def calculate_total_score(self):
        scores = [
            self.communication_score or 0,
            self.empathy_score or 0,
            self.collaboration_score or 0,
            self.leadership_score or 0,
            self.problem_solving_score or 0
        ]
        self.total_score = sum(scores) // len(scores)
        return self.total_score

class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    ai_probability = db.Column(db.Float, default=0.0)  # 0.0 to 1.0
    is_ai_generated = db.Column(db.Boolean, default=False)
    analysis_details = db.Column(db.Text)  # JSON string with detailed analysis
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_ai_status(self):
        if self.ai_probability >= 0.7:
            return "High Risk - Likely AI Generated"
        elif self.ai_probability >= 0.4:
            return "Medium Risk - Possibly AI Generated"
        else:
            return "Low Risk - Likely Human Written"
    
    def get_status_class(self):
        if self.ai_probability >= 0.7:
            return "danger"
        elif self.ai_probability >= 0.4:
            return "warning"
        else:
            return "success"

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    test_id = db.Column(db.Integer, db.ForeignKey('soft_skill_test.id'), nullable=True)
    submission_id = db.Column(db.Integer, db.ForeignKey('submission.id'), nullable=True)
    feedback_type = db.Column(db.String(50))  # 'skill_test' or 'ai_detection'
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='feedbacks')
    test = db.relationship('SoftSkillTest', backref='feedbacks')
    submission = db.relationship('Submission', backref='feedbacks')
