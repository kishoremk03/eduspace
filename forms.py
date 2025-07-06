from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from models import User

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Role', choices=[('student', 'Student'), ('admin', 'Admin')], default='student')
    submit = SubmitField('Register')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')

class SoftSkillTestForm(FlaskForm):
    test_name = StringField('Test Name', validators=[DataRequired()], default='Soft Skills Assessment')
    
    communication_response = TextAreaField(
        'Communication: Describe a time when you had to explain a complex topic to someone. How did you ensure they understood?',
        validators=[DataRequired(), Length(min=50, max=1000)],
        render_kw={"rows": 4, "placeholder": "Share your experience with clear communication..."}
    )
    
    empathy_response = TextAreaField(
        'Empathy: Tell us about a situation where you had to understand and support someone going through a difficult time.',
        validators=[DataRequired(), Length(min=50, max=1000)],
        render_kw={"rows": 4, "placeholder": "Describe how you showed empathy and understanding..."}
    )
    
    collaboration_response = TextAreaField(
        'Collaboration: Describe a successful team project you were part of. What was your role and how did you contribute?',
        validators=[DataRequired(), Length(min=50, max=1000)],
        render_kw={"rows": 4, "placeholder": "Share your collaborative experience..."}
    )
    
    leadership_response = TextAreaField(
        'Leadership: Give an example of when you took initiative or led others towards a common goal.',
        validators=[DataRequired(), Length(min=50, max=1000)],
        render_kw={"rows": 4, "placeholder": "Describe your leadership experience..."}
    )
    
    problem_solving_response = TextAreaField(
        'Problem Solving: Describe a challenging problem you faced and how you approached solving it.',
        validators=[DataRequired(), Length(min=50, max=1000)],
        render_kw={"rows": 4, "placeholder": "Explain your problem-solving approach..."}
    )
    
    submit = SubmitField('Submit Test')

class AIDetectionForm(FlaskForm):
    content = TextAreaField(
        'Text Content',
        validators=[DataRequired(), Length(min=50, max=5000)],
        render_kw={"rows": 10, "placeholder": "Paste or type the text you want to analyze for AI-generated content..."}
    )
    submit = SubmitField('Analyze Content')
