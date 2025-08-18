from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from models import User, UserRole, db
from functools import wraps

auth_bp = Blueprint('auth', __name__)

def role_required(*roles):
    """Decorator to require specific roles for access"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            if current_user.role not in roles:
                flash('Access denied. Insufficient permissions.', 'error')
                return redirect(url_for('dashboard.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        username = data.get('username')
        password = data.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            if user.is_active:
                login_user(user, remember=True)
                user.last_login = db.func.now()
                db.session.commit()
                
                if request.is_json:
                    return jsonify({
                        'success': True,
                        'message': 'Login successful',
                        'user': {
                            'id': user.id,
                            'username': user.username,
                            'role': user.role.value,
                            'department': user.department
                        }
                    })
                else:
                    flash('Login successful!', 'success')
                    return redirect(url_for('dashboard.index'))
            else:
                message = 'Account is deactivated. Please contact administrator.'
        else:
            message = 'Invalid username or password.'
        
        if request.is_json:
            return jsonify({'success': False, 'message': message}), 401
        else:
            flash(message, 'error')
            return render_template('auth/login.html')
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        department = data.get('department')
        role = data.get('role', 'employee')
        
        # Validation
        if User.query.filter_by(username=username).first():
            message = 'Username already exists.'
        elif User.query.filter_by(email=email).first():
            message = 'Email already registered.'
        elif len(password) < 6:
            message = 'Password must be at least 6 characters long.'
        else:
            # Create new user
            user = User(
                username=username,
                email=email,
                password_hash=generate_password_hash(password),
                department=department,
                role=UserRole(role)
            )
            
            db.session.add(user)
            db.session.commit()
            
            if request.is_json:
                return jsonify({
                    'success': True,
                    'message': 'Registration successful',
                    'user_id': user.id
                })
            else:
                flash('Registration successful! Please login.', 'success')
                return redirect(url_for('auth.login'))
        
        if request.is_json:
            return jsonify({'success': False, 'message': message}), 400
        else:
            flash(message, 'error')
            return render_template('auth/register.html')
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile')
@login_required
def profile():
    return render_template('auth/profile.html', user=current_user)

@auth_bp.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    data = request.get_json() if request.is_json else request.form
    
    current_user.department = data.get('department', current_user.department)
    
    # Only allow password change if current password is provided
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    
    if current_password and new_password:
        if check_password_hash(current_user.password_hash, current_password):
            if len(new_password) >= 6:
                current_user.password_hash = generate_password_hash(new_password)
            else:
                message = 'New password must be at least 6 characters long.'
                if request.is_json:
                    return jsonify({'success': False, 'message': message}), 400
                else:
                    flash(message, 'error')
                    return redirect(url_for('auth.profile'))
        else:
            message = 'Current password is incorrect.'
            if request.is_json:
                return jsonify({'success': False, 'message': message}), 400
            else:
                flash(message, 'error')
                return redirect(url_for('auth.profile'))
    
    db.session.commit()
    
    if request.is_json:
        return jsonify({'success': True, 'message': 'Profile updated successfully'})
    else:
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('auth.profile'))

# Admin-only routes
@auth_bp.route('/admin/users')
@login_required
@role_required(UserRole.ADMIN)
def admin_users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@auth_bp.route('/admin/users/<int:user_id>/toggle_status', methods=['POST'])
@login_required
@role_required(UserRole.ADMIN)
def toggle_user_status(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()
    
    status = 'activated' if user.is_active else 'deactivated'
    
    if request.is_json:
        return jsonify({
            'success': True,
            'message': f'User {user.username} has been {status}',
            'is_active': user.is_active
        })
    else:
        flash(f'User {user.username} has been {status}.', 'success')
        return redirect(url_for('auth.admin_users'))

@auth_bp.route('/admin/users/<int:user_id>/change_role', methods=['POST'])
@login_required
@role_required(UserRole.ADMIN)
def change_user_role(user_id):
    user = User.query.get_or_404(user_id)
    data = request.get_json() if request.is_json else request.form
    new_role = data.get('role')
    
    if new_role in [role.value for role in UserRole]:
        user.role = UserRole(new_role)
        db.session.commit()
        
        if request.is_json:
            return jsonify({
                'success': True,
                'message': f'User {user.username} role changed to {new_role}',
                'role': new_role
            })
        else:
            flash(f'User {user.username} role changed to {new_role}.', 'success')
            return redirect(url_for('auth.admin_users'))
    else:
        message = 'Invalid role specified.'
        if request.is_json:
            return jsonify({'success': False, 'message': message}), 400
        else:
            flash(message, 'error')
            return redirect(url_for('auth.admin_users'))
