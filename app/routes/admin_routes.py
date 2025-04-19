from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import User, Download  # Import the Download model
from werkzeug.security import generate_password_hash
from app.extensions import db
from functools import wraps

admin_bp = Blueprint('admin_routes', __name__)

def admin_required(f):
    @wraps(f)
    @login_required
    def wrap(*args, **kwargs):
        if current_user.role != 'Admin':
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('web_routes.home'))
        return f(*args, **kwargs)
    return wrap

@admin_bp.route('/admin', methods=['GET'])
@admin_required
def admin():
    users = User.query.all()
    return render_template('admin.html', users=users)

@admin_bp.route('/admin/add', methods=['GET', 'POST'])
@admin_required
def add_user():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        role = request.form.get('role')
        status = request.form.get('status')

        if not username or not password or not email or not role or not status:
            flash('All fields are required.', 'danger')
            return redirect(url_for('admin_routes.add_user'))

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists.', 'danger')
            return redirect(url_for('admin_routes.add_user'))

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, password=hashed_password, email=email, role=role, status=status)

        try:
            db.session.add(new_user)
            db.session.commit()
            flash('User added successfully!', 'success')
            return redirect(url_for('admin_routes.admin'))
        except Exception as e:
            db.session.rollback()
            flash('Error adding user. Please try again.', 'danger')
            return redirect(url_for('admin_routes.add_user'))

    return render_template('add_user.html')

@admin_bp.route('/admin/edit/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        user.username = request.form.get('username')
        user.email = request.form.get('email')
        user.role = request.form.get('role')
        user.status = request.form.get('status')

        if request.form.get('password'):
            user.password = generate_password_hash(request.form.get('password'), method='pbkdf2:sha256')

        try:
            db.session.commit()
            flash('User updated successfully!', 'success')
            return redirect(url_for('admin_routes.admin'))
        except Exception as e:
            db.session.rollback()
            flash('Error updating user. Please try again.', 'danger')
            return redirect(url_for('admin_routes.edit_user', user_id=user_id))

    return render_template('edit_user.html', user=user)

@admin_bp.route('/admin/delete/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    print(f"Attempting to delete user: {user.username}")

    try:
        # Delete related records in the downloads table
        db.session.query(Download).filter_by(user_id=user_id).delete()
        
        # Delete the user
        db.session.delete(user)
        db.session.commit()
        flash('User deleted successfully!', 'success')
        print(f"User {user.username} deleted successfully.")
    except Exception as e:
        db.session.rollback()
        flash('Error deleting user. Please try again.', 'danger')
        print(f"Error deleting user: {e}")

    return redirect(url_for('admin_routes.admin'))