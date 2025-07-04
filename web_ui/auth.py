from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from functools import wraps
from .database import User

auth_bp = Blueprint('auth', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({"status": "error", "message": "Unauthorized: Login required."}), 401
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def super_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'super_admin':
            if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({"status": "error", "message": "Forbidden: Super admin access required."}), 403
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['logged_in'] = True
            session['permanent'] = True
            session['username'] = username
            session['role'] = user.role
            flash('Logged in successfully.', 'success')
            return redirect(url_for('main.index'))
        else:
            flash('Invalid username or password.', 'danger')
            return render_template('login.html', error='Invalid Credentials')
    return render_template('login.html')

@auth_bp.before_app_request
def check_for_first_user():
    if not User.query.first():
        if request.endpoint and request.endpoint not in ['auth.register', 'static']:
            return redirect(url_for('auth.register'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    is_first_user = not User.query.first()

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if not is_first_user and User.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
            return render_template('register.html', is_first_user=is_first_user)
        
        new_user = User(username=username)
        new_user.set_password(password)
        
        if is_first_user:
            new_user.role = 'super_admin'
        
        from .database import db # Import db here to avoid circular dependency
        db.session.add(new_user)
        db.session.commit()
        
        if is_first_user:
            flash('Super admin account created successfully. Please log in.', 'success')
        else:
            flash('Registration successful. Please log in.', 'success')
            
        return redirect(url_for('auth.login'))
        
    return render_template('register.html', is_first_user=is_first_user)

@auth_bp.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))