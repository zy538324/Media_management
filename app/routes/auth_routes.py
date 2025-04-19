from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, current_user, logout_user
from app.models import User
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import CSRFProtect
from app.extensions import db

# Initialize CSRF protection if not done globally in __init__.py
csrf = CSRFProtect()

auth_bp = Blueprint('auth_routes', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
@csrf.exempt  # Add this if using CSRFProtect at the blueprint level or app level
def register():
    if current_user.is_authenticated:
        return redirect(url_for('web_routes.home'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')

        if not username or not password or not email:
            flash('All fields are required.', 'danger')
            return redirect(url_for('auth_routes.register'))

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists.', 'danger')
            return redirect(url_for('auth_routes.register'))

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        # Check if this is the first user
        if User.query.count() == 0:
            role = 'Admin'
        else:
            role = 'User'

        new_user = User(username=username, password=hashed_password, email=email, role=role, status='Active')

        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('auth_routes.login'))
        except Exception as e:
            db.session.rollback()
            flash('Error creating user. Please try again.', 'danger')
            return redirect(url_for('auth_routes.register'))

    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
@csrf.exempt  # Add this if using CSRFProtect at the blueprint level or app level
def login():
    if current_user.is_authenticated:
        return redirect(url_for('web_routes.home'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Login successful!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('web_routes.home'))
        else:
            flash('Invalid username or password', 'danger')

    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth_routes.login'))