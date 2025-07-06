from flask import render_template, flash, redirect, url_for, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.urls import url_parse
from app import app, db
from models import User, SoftSkillTest, Submission, Feedback
from forms import LoginForm, RegistrationForm, SoftSkillTestForm, AIDetectionForm
from ai_engine.skill_evaluator import evaluate_all_skills
from ai_engine.ai_detector import analyze_text_for_ai
import json
import logging

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', title='Home')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password', 'danger')
            return redirect(url_for('login'))
        
        login_user(user)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('dashboard')
        
        flash(f'Welcome back, {user.username}!', 'success')
        return redirect(next_page)
    
    return render_template('login.html', title='Sign In', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data, role=form.role.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        
        flash('Congratulations, you are now registered!', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', title='Register', form=form)

@app.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Get user's recent test results
    recent_tests = SoftSkillTest.query.filter_by(user_id=current_user.id).order_by(SoftSkillTest.completed_at.desc()).limit(5).all()
    
    # Get user's recent submissions
    recent_submissions = Submission.query.filter_by(user_id=current_user.id).order_by(Submission.submitted_at.desc()).limit(5).all()
    
    # Calculate some basic stats
    total_tests = SoftSkillTest.query.filter_by(user_id=current_user.id).count()
    total_submissions = Submission.query.filter_by(user_id=current_user.id).count()
    
    avg_score = 0
    if recent_tests:
        avg_score = sum(test.total_score for test in recent_tests) / len(recent_tests)
    
    return render_template('dashboard.html', 
                         title='Dashboard',
                         recent_tests=recent_tests,
                         recent_submissions=recent_submissions,
                         total_tests=total_tests,
                         total_submissions=total_submissions,
                         avg_score=avg_score)

@app.route('/skill_test', methods=['GET', 'POST'])
@login_required
def skill_test():
    form = SoftSkillTestForm()
    if form.validate_on_submit():
        # Create new test record
        test = SoftSkillTest(
            user_id=current_user.id,
            test_name=form.test_name.data,
            communication_response=form.communication_response.data,
            empathy_response=form.empathy_response.data,
            collaboration_response=form.collaboration_response.data,
            leadership_response=form.leadership_response.data,
            problem_solving_response=form.problem_solving_response.data
        )
        
        # Prepare responses for evaluation
        responses = {
            'communication_response': form.communication_response.data,
            'empathy_response': form.empathy_response.data,
            'collaboration_response': form.collaboration_response.data,
            'leadership_response': form.leadership_response.data,
            'problem_solving_response': form.problem_solving_response.data
        }
        
        try:
            # Evaluate all skills
            results = evaluate_all_skills(responses)
            
            # Store scores in the test record
            test.communication_score = results['communication']['score']
            test.empathy_score = results['empathy']['score']
            test.collaboration_score = results['collaboration']['score']
            test.leadership_score = results['leadership']['score']
            test.problem_solving_score = results['problem_solving']['score']
            
            # Calculate total score
            test.calculate_total_score()
            
            # Save to database
            db.session.add(test)
            db.session.commit()
            
            # Create feedback records
            for skill, result in results.items():
                feedback = Feedback(
                    user_id=current_user.id,
                    test_id=test.id,
                    feedback_type='skill_test',
                    content=f"{skill.title()}: {result['feedback']}"
                )
                db.session.add(feedback)
            
            db.session.commit()
            
            flash('Soft skills test completed successfully!', 'success')
            return redirect(url_for('test_results', test_id=test.id))
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error evaluating skills: {e}")
            flash('Error processing your test. Please try again.', 'danger')
            return redirect(url_for('skill_test'))
    
    return render_template('skill_test.html', title='Soft Skills Test', form=form)

@app.route('/test_results/<int:test_id>')
@login_required
def test_results(test_id):
    test = SoftSkillTest.query.filter_by(id=test_id, user_id=current_user.id).first_or_404()
    feedbacks = Feedback.query.filter_by(test_id=test_id, user_id=current_user.id).all()
    
    # Prepare skill data for visualization
    skills_data = {
        'Communication': test.communication_score,
        'Empathy': test.empathy_score,
        'Collaboration': test.collaboration_score,
        'Leadership': test.leadership_score,
        'Problem Solving': test.problem_solving_score
    }
    
    return render_template('test_results.html', 
                         title='Test Results',
                         test=test,
                         skills_data=skills_data,
                         feedbacks=feedbacks)

@app.route('/integrity_checker', methods=['GET', 'POST'])
@login_required
def integrity_checker():
    form = AIDetectionForm()
    if form.validate_on_submit():
        try:
            # Analyze the content for AI generation
            analysis = analyze_text_for_ai(form.content.data)
            
            # Create submission record
            submission = Submission(
                user_id=current_user.id,
                content=form.content.data,
                ai_probability=analysis['probability'],
                is_ai_generated=analysis['probability'] >= 0.7,
                analysis_details=json.dumps(analysis)
            )
            
            db.session.add(submission)
            db.session.commit()
            
            # Create feedback record
            feedback_content = f"AI Detection Analysis: {analysis.get('analysis', 'Analysis completed')}"
            feedback = Feedback(
                user_id=current_user.id,
                submission_id=submission.id,
                feedback_type='ai_detection',
                content=feedback_content
            )
            db.session.add(feedback)
            db.session.commit()
            
            flash('Content analysis completed!', 'success')
            return render_template('integrity_checker.html', 
                                 title='AI Integrity Checker',
                                 form=AIDetectionForm(),  # Fresh form
                                 analysis=analysis,
                                 submission=submission)
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error analyzing content: {e}")
            flash('Error analyzing content. Please try again.', 'danger')
    
    return render_template('integrity_checker.html', 
                         title='AI Integrity Checker',
                         form=form)

@app.route('/admin_panel')
@login_required
def admin_panel():
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get statistics
    total_users = User.query.count()
    total_tests = SoftSkillTest.query.count()
    total_submissions = Submission.query.count()
    
    # Get recent activity
    recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()
    recent_tests = SoftSkillTest.query.order_by(SoftSkillTest.completed_at.desc()).limit(10).all()
    recent_submissions = Submission.query.order_by(Submission.submitted_at.desc()).limit(10).all()
    
    # AI Detection Statistics
    high_risk_submissions = Submission.query.filter(Submission.ai_probability >= 0.7).count()
    medium_risk_submissions = Submission.query.filter(
        Submission.ai_probability >= 0.4, 
        Submission.ai_probability < 0.7
    ).count()
    low_risk_submissions = Submission.query.filter(Submission.ai_probability < 0.4).count()
    
    # Average scores by skill
    avg_scores = {}
    if total_tests > 0:
        avg_scores = {
            'communication': db.session.query(db.func.avg(SoftSkillTest.communication_score)).scalar() or 0,
            'empathy': db.session.query(db.func.avg(SoftSkillTest.empathy_score)).scalar() or 0,
            'collaboration': db.session.query(db.func.avg(SoftSkillTest.collaboration_score)).scalar() or 0,
            'leadership': db.session.query(db.func.avg(SoftSkillTest.leadership_score)).scalar() or 0,
            'problem_solving': db.session.query(db.func.avg(SoftSkillTest.problem_solving_score)).scalar() or 0
        }
    
    return render_template('admin_panel.html',
                         title='Admin Panel',
                         total_users=total_users,
                         total_tests=total_tests,
                         total_submissions=total_submissions,
                         recent_users=recent_users,
                         recent_tests=recent_tests,
                         recent_submissions=recent_submissions,
                         high_risk_submissions=high_risk_submissions,
                         medium_risk_submissions=medium_risk_submissions,
                         low_risk_submissions=low_risk_submissions,
                         avg_scores=avg_scores)

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
