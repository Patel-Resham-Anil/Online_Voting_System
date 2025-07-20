from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_socketio import SocketIO, emit
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, EqualTo
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
import uuid
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///voting_system.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*")
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    votes = db.relationship('Vote', backref='voter', lazy=True)

class Election(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    candidates = db.relationship('Candidate', backref='election', lazy=True, cascade='all, delete-orphan')
    votes = db.relationship('Vote', backref='election', lazy=True)

class Candidate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    election_id = db.Column(db.Integer, db.ForeignKey('election.id'), nullable=False)
    votes_received = db.relationship('Vote', backref='candidate', lazy=True)

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    voter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    election_id = db.Column(db.Integer, db.ForeignKey('election.id'), nullable=False)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidate.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))
    session_id = db.Column(db.String(100))

# Forms
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class ElectionForm(FlaskForm):
    title = StringField('Election Title', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    start_date = StringField('Start Date (YYYY-MM-DD HH:MM)', validators=[DataRequired()])
    end_date = StringField('End Date (YYYY-MM-DD HH:MM)', validators=[DataRequired()])
    submit = SubmitField('Create Election')

class CandidateForm(FlaskForm):
    name = StringField('Candidate Name', validators=[DataRequired()])
    description = TextAreaField('Description')
    submit = SubmitField('Add Candidate')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    active_elections = Election.query.filter_by(is_active=True).filter(
        Election.start_date <= datetime.utcnow(),
        Election.end_date >= datetime.utcnow()
    ).all()
    return render_template('index.html', elections=active_elections)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=hashed_password
        )
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/progress')
@login_required
def progress():
    # Get user's voting history
    user_votes = Vote.query.filter_by(voter_id=current_user.id).all()
    
    # Get all elections the user has participated in with vote timestamps
    participated_elections = []
    election_vote_times = {}
    for vote in user_votes:
        election = Election.query.get(vote.election_id)
        if election and election not in participated_elections:
            participated_elections.append(election)
            election_vote_times[election.id] = vote.timestamp
    
    # Get active elections
    active_elections = Election.query.filter_by(is_active=True).filter(
        Election.start_date <= datetime.utcnow(),
        Election.end_date >= datetime.utcnow()
    ).all()
    
    # Calculate statistics
    total_elections = Election.query.count()
    total_votes_cast = len(user_votes)
    participation_rate = (len(participated_elections) / total_elections * 100) if total_elections > 0 else 0
    
    return render_template('progress.html', 
                         user_votes=user_votes,
                         participated_elections=participated_elections,
                         election_vote_times=election_vote_times,
                         active_elections=active_elections,
                         total_elections=total_elections,
                         total_votes_cast=total_votes_cast,
                         participation_rate=participation_rate)

@app.route('/election/<int:election_id>')
@login_required
def election_detail(election_id):
    election = Election.query.get_or_404(election_id)
    has_voted = Vote.query.filter_by(voter_id=current_user.id, election_id=election_id).first() is not None
    now = datetime.utcnow()
    return render_template('election_detail.html', election=election, has_voted=has_voted, now=now)

@app.route('/vote/<int:election_id>/<int:candidate_id>', methods=['POST'])
@login_required
def vote(election_id, candidate_id):
    # Check if user has already voted
    existing_vote = Vote.query.filter_by(voter_id=current_user.id, election_id=election_id).first()
    if existing_vote:
        return jsonify({'success': False, 'message': 'You have already voted in this election'})
    
    # Check if election is active
    election = Election.query.get_or_404(election_id)
    if not election.is_active or datetime.utcnow() < election.start_date or datetime.utcnow() > election.end_date:
        return jsonify({'success': False, 'message': 'Election is not active'})
    
    # Create vote
    vote = Vote(
        voter_id=current_user.id,
        election_id=election_id,
        candidate_id=candidate_id,
        ip_address=request.remote_addr,
        session_id=str(uuid.uuid4())
    )
    db.session.add(vote)
    db.session.commit()
    
    # Emit real-time update
    socketio.emit('vote_update', {
        'election_id': election_id,
        'candidate_id': candidate_id,
        'total_votes': len(election.votes)
    })
    
    return jsonify({'success': True, 'message': 'Vote cast successfully!'})

@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    
    elections = Election.query.all()
    users = User.query.all()
    
    # Calculate total votes
    total_votes = Vote.query.count()
    
    return render_template('admin_dashboard.html', elections=elections, users=users, total_votes=total_votes)

@app.route('/admin/election/create', methods=['GET', 'POST'])
@login_required
def create_election():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    
    form = ElectionForm()
    if form.validate_on_submit():
        try:
            start_date = datetime.strptime(form.start_date.data, '%Y-%m-%d %H:%M')
            end_date = datetime.strptime(form.end_date.data, '%Y-%m-%d %H:%M')
            
            election = Election(
                title=form.title.data,
                description=form.description.data,
                start_date=start_date,
                end_date=end_date,
                created_by=current_user.id
            )
            db.session.add(election)
            db.session.commit()
            flash('Election created successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
        except ValueError:
            flash('Invalid date format. Use YYYY-MM-DD HH:MM', 'error')
    
    return render_template('create_election.html', form=form)

@app.route('/admin/election/<int:election_id>/candidates', methods=['GET', 'POST'])
@login_required
def manage_candidates(election_id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    
    election = Election.query.get_or_404(election_id)
    form = CandidateForm()
    
    if form.validate_on_submit():
        candidate = Candidate(
            name=form.name.data,
            description=form.description.data,
            election_id=election_id
        )
        db.session.add(candidate)
        db.session.commit()
        flash('Candidate added successfully!', 'success')
        return redirect(url_for('manage_candidates', election_id=election_id))
    
    return render_template('manage_candidates.html', election=election, form=form)

@app.route('/admin/election/<int:election_id>/results')
@login_required
def election_results(election_id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    
    election = Election.query.get_or_404(election_id)
    results = {}
    
    for candidate in election.candidates:
        vote_count = Vote.query.filter_by(candidate_id=candidate.id).count()
        results[candidate.name] = vote_count
    
    total_votes = sum(results.values())
    return render_template('election_results.html', election=election, results=results, total_votes=total_votes)

@app.route('/api/election/<int:election_id>/results')
def api_election_results(election_id):
    election = Election.query.get_or_404(election_id)
    results = {}
    
    for candidate in election.candidates:
        vote_count = Vote.query.filter_by(candidate_id=candidate.id).count()
        results[candidate.name] = vote_count
    
    return jsonify(results)

# Socket.IO events
@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('join_election')
def handle_join_election(data):
    election_id = data['election_id']
    # Join the room for this election
    from flask_socketio import join_room
    join_room(f'election_{election_id}')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Create admin user if none exists
        admin = User.query.filter_by(is_admin=True).first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@votingsystem.com',
                password_hash=generate_password_hash('admin123'),
                is_admin=True,
                is_verified=True
            )
            db.session.add(admin)
            db.session.commit()
            print("Admin user created: username='admin', password='admin123'")
    
    socketio.run(app, debug=True, host='0.0.0.0', port=5000) 