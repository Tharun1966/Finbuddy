from flask import Flask, request, jsonify, render_template, session, redirect, url_for, flash
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from finbuddy import FinBuddy
from smart_insights import SmartInsights
from werkzeug.security import generate_password_hash, check_password_hash
import logging
from functools import wraps
import secrets
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', secrets.token_hex(32))
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///finbuddy.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Initialize extensions
CORS(app, supports_credentials=True)
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

# User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def update_last_login(self):
        self.last_login = datetime.utcnow()
        db.session.commit()

    def __repr__(self):
        return f'<User {self.username}>'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Initialize FinBuddy instance
finbuddy = FinBuddy()

# Initialize SmartInsights engine
insights_engine = SmartInsights()

def handle_error(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {f.__name__}: {str(e)}")
            return jsonify({'status': 'error', 'message': 'An unexpected error occurred'}), 500
    return decorated_function

@app.route('/')
def home():
    if current_user.is_authenticated:
        return render_template('dashboard.html')
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
@handle_error
def login():
    if request.method == 'POST':
        try:
            data = request.get_json()
            logger.debug(f"Login attempt for user: {data.get('username')}")
            
            # Validate required fields
            if not all(k in data for k in ['username', 'password']):
                logger.warning("Login attempt with missing fields")
                return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400
            
            user = User.query.filter_by(username=data['username']).first()
            if user and user.check_password(data['password']):
                if not user.is_active:
                    return jsonify({'status': 'error', 'message': 'Account is disabled'}), 403
                
                login_user(user, remember=True)
                user.update_last_login()
                logger.info(f"User {user.username} logged in successfully")
                return jsonify({'status': 'success', 'redirect': url_for('dashboard')})
            
            logger.warning(f"Failed login attempt for user: {data.get('username')}")
            return jsonify({'status': 'error', 'message': 'Invalid username or password'}), 401
            
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return jsonify({'status': 'error', 'message': 'An error occurred during login'}), 500
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
@handle_error
def register():
    if request.method == 'POST':
        try:
            data = request.get_json()
            logger.debug(f"Registration attempt for user: {data.get('username')}")
            
            # Validate required fields
            if not all(k in data for k in ['username', 'email', 'password']):
                logger.warning("Registration attempt with missing fields")
                return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400
            
            # Validate email format
            if not re.match(r"[^@]+@[^@]+\.[^@]+", data['email']):
                return jsonify({'status': 'error', 'message': 'Invalid email format'}), 400
            
            # Validate password strength
            if len(data['password']) < 8:
                return jsonify({'status': 'error', 'message': 'Password must be at least 8 characters long'}), 400
            
            # Check if username exists
            if User.query.filter_by(username=data['username']).first():
                logger.warning(f"Registration attempt with existing username: {data['username']}")
                return jsonify({'status': 'error', 'message': 'Username already exists'}), 409
            
            # Check if email exists
            if User.query.filter_by(email=data['email']).first():
                logger.warning(f"Registration attempt with existing email: {data['email']}")
                return jsonify({'status': 'error', 'message': 'Email already registered'}), 409
            
            # Create new user
            new_user = User(
                username=data['username'],
                email=data['email']
            )
            new_user.set_password(data['password'])
            
            # Add to database
            db.session.add(new_user)
            db.session.commit()
            logger.info(f"New user registered successfully: {new_user.username}")
            
            # Log in the new user
            login_user(new_user)
            return jsonify({'status': 'success', 'redirect': url_for('dashboard')})
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Registration error: {str(e)}")
            return jsonify({'status': 'error', 'message': 'An error occurred during registration'}), 500
            
    return render_template('register.html')

@app.route('/dashboard')
@login_required
@handle_error
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/chat', methods=['POST'])
@login_required
@handle_error
def chat():
    try:
        data = request.get_json()
        message = data.get('message')
        if not message:
            return jsonify({'status': 'error', 'message': 'No message provided'}), 400
        
        response = finbuddy.process_message(message)
        return jsonify({'status': 'success', 'response': response})
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        return jsonify({'status': 'error', 'message': 'An error occurred while processing your message'}), 500

@app.route('/api/expenses', methods=['GET', 'POST'])
@login_required
def handle_expenses():
    try:
        if request.method == 'POST':
            data = request.get_json()
            response = finbuddy.handle_expense(data.get('message'), {})
            return jsonify({'status': 'success', 'response': response})
        
        # GET request to fetch expenses
        expenses = finbuddy.get_status()
        return jsonify({'status': 'success', 'expenses': expenses})
    except Exception as e:
        logger.error(f"Expenses error: {str(e)}")
        return jsonify({'status': 'error', 'message': 'An error occurred while handling expenses'})

@app.route('/api/budgets', methods=['GET', 'POST'])
@login_required
def handle_budgets():
    try:
        if request.method == 'POST':
            data = request.get_json()
            response = finbuddy.handle_budget(data.get('message'), {})
            return jsonify({'status': 'success', 'response': response})
        
        # GET request to fetch budgets
        budgets = finbuddy.get_status()
        return jsonify({'status': 'success', 'budgets': budgets})
    except Exception as e:
        logger.error(f"Budgets error: {str(e)}")
        return jsonify({'status': 'error', 'message': 'An error occurred while handling budgets'})

@app.route('/api/reminders', methods=['GET', 'POST'])
@login_required
def handle_reminders():
    try:
        if request.method == 'POST':
            data = request.get_json()
            response = finbuddy.handle_reminder(data.get('message'), {})
            return jsonify({'status': 'success', 'response': response})
        
        # GET request to fetch reminders
        return jsonify({'status': 'success', 'reminders': []})
    except Exception as e:
        logger.error(f"Reminders error: {str(e)}")
        return jsonify({'status': 'error', 'message': 'An error occurred while handling reminders'})

# ==================== Smart Insights API Endpoints ====================

@app.route('/api/insights/overview', methods=['GET'])
@login_required
@handle_error
def insights_overview():
    """Get spending overview and key metrics"""
    try:
        days = request.args.get('days', 30, type=int)
        overview = insights_engine.get_spending_overview(current_user.id, days=days)
        
        if overview:
            return jsonify({
                'status': 'success',
                'data': overview
            })
        return jsonify({
            'status': 'error',
            'message': 'Could not retrieve spending overview'
        }), 500
    except Exception as e:
        logger.error(f"Insights overview error: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/insights/recommendations', methods=['GET'])
@login_required
@handle_error
def insights_recommendations():
    """Get smart budgeting recommendations"""
    try:
        recommendations = insights_engine.get_smart_recommendations(current_user.id)
        
        return jsonify({
            'status': 'success',
            'recommendations': recommendations,
            'count': len(recommendations)
        })
    except Exception as e:
        logger.error(f"Insights recommendations error: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/insights/anomalies', methods=['GET'])
@login_required
@handle_error
def insights_anomalies():
    """Detect unusual spending patterns"""
    try:
        anomalies = insights_engine.detect_spending_anomalies(current_user.id)
        
        return jsonify({
            'status': 'success',
            'anomalies': anomalies,
            'count': len(anomalies)
        })
    except Exception as e:
        logger.error(f"Insights anomalies error: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/insights/savings-potential', methods=['GET'])
@login_required
@handle_error
def insights_savings():
    """Calculate savings potential"""
    try:
        savings_data = insights_engine.calculate_savings_potential(current_user.id)
        
        if savings_data:
            return jsonify({
                'status': 'success',
                'data': savings_data
            })
        return jsonify({
            'status': 'error',
            'message': 'Could not calculate savings potential'
        }), 500
    except Exception as e:
        logger.error(f"Insights savings error: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/insights/goals', methods=['GET'])
@login_required
@handle_error
def insights_goals():
    """Get financial goal progress"""
    try:
        goals = insights_engine.get_goal_progress(current_user.id)
        
        return jsonify({
            'status': 'success',
            'goals': goals,
            'count': len(goals)
        })
    except Exception as e:
        logger.error(f"Insights goals error: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/logout')
@login_required
@handle_error
def logout():
    logout_user()
    return redirect(url_for('home'))

if __name__ == '__main__':
    with app.app_context():
        try:
            # Create database tables
            db.create_all()
            logger.info("Database tables created successfully")
            
            # Test database connection
            test_user = User.query.first()
            logger.info("Database connection test successful")
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")
            raise
    
    # Run the application
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true') 