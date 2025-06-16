# routes/users.py - Complete User Management System
from flask import Blueprint,render_template,request,redirect,url_for,flash,session,jsonify
from models.database import db
from functools import wraps
from datetime import datetime
import hashlib

# Create blueprint
users_bp = Blueprint('users',__name__,url_prefix='/users')

# User roles and permissions configuration
ROLES = {
    'Super Admin': {
        'description': 'Full system access',
        'permissions': ['all']
    },
    'Admin': {
        'description': 'Administrative access',
        'permissions': ['students','rooms','assignments','payments','reports','users_view','users_add','users_edit']
    },
    'Manager': {
        'description': 'Management level access',
        'permissions': ['students','rooms','assignments','payments','reports_view']
    },
    'Staff': {
        'description': 'Staff level access',
        'permissions': ['students_view','rooms_view','assignments','payments_view']
    },
    'Receptionist': {
        'description': 'Front desk operations',
        'permissions': ['students','assignments_view','payments_view']
    },
    'Accountant': {
        'description': 'Financial operations',
        'permissions': ['students_view','payments','reports_financial']
    },
    'User': {
        'description': 'Self service user',
        'permissions': ['book_room','rooms_view']
    },
    'Read Only': {
        'description': 'View only access',
        'permissions': ['students_view','rooms_view','assignments_view','payments_view','reports_view']
    }
}


def require_auth(f):
    """Decorator to require authentication"""

    @wraps(f)
    def decorated_function(*args,**kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page','error')
            return redirect(url_for('login'))
        return f(*args,**kwargs)

    return decorated_function


def require_permission(permission):
    """Decorator to require specific permission"""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args,**kwargs):
            if 'user_id' not in session:
                flash('Please log in to access this page','error')
                return redirect(url_for('login'))

            user_role = session.get('role','Read Only')
            if not has_permission(user_role,permission):
                flash('You do not have permission to access this page','error')
                return redirect(url_for('dashboard'))

            return f(*args,**kwargs)

        return decorated_function

    return decorator


def has_permission(role,permission):
    """Check if a role has a specific permission"""
    if role not in ROLES:
        return False

    role_permissions = ROLES[role]['permissions']

    # Super admin has all permissions
    if 'all' in role_permissions:
        return True

    # Check exact permission match
    if permission in role_permissions:
        return True

    # Check if user has full access to a module (e.g., 'students' includes 'students_view')
    module = permission.split('_')[0]
    if module in role_permissions:
        return True

    return False


def get_user_permissions(role):
    """Get all permissions for a role"""
    if role not in ROLES:
        return []

    permissions = ROLES[role]['permissions']
    if 'all' in permissions:
        # Super admin gets all possible permissions
        all_perms = []
        for r in ROLES.values():
            all_perms.extend(r['permissions'])
        return list(set(all_perms))

    return permissions


@users_bp.route('/')
@require_permission('users_view')
def list_users():
    """List all users"""
    try:
        if not db or not db.test_connection():
            flash('Database connection error','error')
            return redirect(url_for('dashboard'))

        # Get all users
        users = db.execute_query("""
                                 SELECT user_id,
                                        username,
                                        full_name,
                                        email,
                                        role,
                                        status,
                                        last_login,
                                        created_at
                                 FROM users
                                 ORDER BY created_at DESC
                                 """)

        # Get user activity statistics
        stats = get_user_statistics()

        return render_template('users/list.html',users=users,stats=stats,roles=ROLES)

    except Exception as e:
        print(f"Error listing users: {e}")
        flash('Error loading users','error')
        return redirect(url_for('dashboard'))


@users_bp.route('/add',methods=['GET','POST'])
@require_permission('users_add')
def add_user():
    """Add new user"""
    if request.method == 'POST':
        try:
            # Get form data
            username = request.form.get('username','').strip()
            full_name = request.form.get('full_name','').strip()
            email = request.form.get('email','').strip()
            password = request.form.get('password','').strip()
            role = request.form.get('role','Read Only')
            status = request.form.get('status','Active')

            # Validation
            if not all([username,full_name,email,password]):
                flash('All fields are required','error')
                return render_template('users/add.html',roles=ROLES)

            if len(password) < 6:
                flash('Password must be at least 6 characters','error')
                return render_template('users/add.html',roles=ROLES)

            # Check if username exists
            existing = db.execute_query("SELECT user_id FROM users WHERE username = %s",(username,))
            if existing:
                flash('Username already exists','error')
                return render_template('users/add.html',roles=ROLES)

            # Check if email exists
            existing = db.execute_query("SELECT user_id FROM users WHERE email = %s",(email,))
            if existing:
                flash('Email already exists','error')
                return render_template('users/add.html',roles=ROLES)

            # Hash password (simple hash - in production use bcrypt)
            password_hash = hashlib.sha256(password.encode()).hexdigest()

            # Insert user
            user_id = db.execute_insert("""
                                        INSERT INTO users (username, password, full_name, email, role, status, created_by)
                                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                                        """,(username,password_hash,full_name,email,role,status,session.get('user_id')))

            if user_id:
                flash(f'User {username} created successfully','success')
                return redirect(url_for('users.list_users'))
            else:
                flash('Error creating user','error')

        except Exception as e:
            print(f"Error adding user: {e}")
            flash('Error creating user','error')

    return render_template('users/add.html',roles=ROLES)


@users_bp.route('/edit/<int:user_id>',methods=['GET','POST'])
@require_permission('users_edit')
def edit_user(user_id):
    """Edit user"""
    try:
        # Get user data
        user = db.execute_query("""
                                SELECT user_id, username, full_name, email, role, status, created_at
                                FROM users
                                WHERE user_id = %s
                                """,(user_id,))

        if not user:
            flash('User not found','error')
            return redirect(url_for('users.list_users'))

        user = user[0]

        if request.method == 'POST':
            # Get form data
            full_name = request.form.get('full_name','').strip()
            email = request.form.get('email','').strip()
            role = request.form.get('role','Read Only')
            status = request.form.get('status','Active')
            new_password = request.form.get('new_password','').strip()

            # Validation
            if not all([full_name,email]):
                flash('Full name and email are required','error')
                return render_template('users/edit.html',user=user,roles=ROLES)

            # Check if email exists (excluding current user)
            existing = db.execute_query(
                "SELECT user_id FROM users WHERE email = %s AND user_id != %s",
                (email,user_id)
            )
            if existing:
                flash('Email already exists','error')
                return render_template('users/edit.html',user=user,roles=ROLES)

            # Update user
            if new_password:
                if len(new_password) < 6:
                    flash('Password must be at least 6 characters','error')
                    return render_template('users/edit.html',user=user,roles=ROLES)

                password_hash = hashlib.sha256(new_password.encode()).hexdigest()
                updated = db.execute_update("""
                                            UPDATE users
                                            SET full_name  = %s,
                                                email      = %s,
                                                role       = %s,
                                                status     = %s,
                                                password   = %s,
                                                updated_at = CURRENT_TIMESTAMP
                                            WHERE user_id = %s
                                            """,(full_name,email,role,status,password_hash,user_id))
            else:
                updated = db.execute_update("""
                                            UPDATE users
                                            SET full_name  = %s,
                                                email      = %s,
                                                role       = %s,
                                                status     = %s,
                                                updated_at = CURRENT_TIMESTAMP
                                            WHERE user_id = %s
                                            """,(full_name,email,role,status,user_id))

            if updated:
                flash('User updated successfully','success')
                return redirect(url_for('users.list_users'))
            else:
                flash('Error updating user','error')

        return render_template('users/edit.html',user=user,roles=ROLES)

    except Exception as e:
        print(f"Error editing user: {e}")
        flash('Error editing user','error')
        return redirect(url_for('users.list_users'))


@users_bp.route('/delete/<int:user_id>',methods=['POST'])
@require_permission('users_delete')
def delete_user(user_id):
    """Delete user"""
    try:
        # Prevent self-deletion
        if user_id == session.get('user_id'):
            flash('You cannot delete your own account','error')
            return redirect(url_for('users.list_users'))

        # Get user info
        user = db.execute_query("SELECT username FROM users WHERE user_id = %s",(user_id,))
        if not user:
            flash('User not found','error')
            return redirect(url_for('users.list_users'))

        username = user[0][0]

        # Delete user
        deleted = db.execute_update("DELETE FROM users WHERE user_id = %s",(user_id,))

        if deleted:
            flash(f'User {username} deleted successfully','success')
        else:
            flash('Error deleting user','error')

    except Exception as e:
        print(f"Error deleting user: {e}")
        flash('Error deleting user','error')

    return redirect(url_for('users.list_users'))


@users_bp.route('/profile')
@require_auth
def profile():
    """User profile page"""
    try:
        user_id = session.get('user_id')
        user = db.execute_query("""
                                SELECT user_id,
                                       username,
                                       full_name,
                                       email,
                                       role,
                                       status,
                                       last_login,
                                       created_at
                                FROM users
                                WHERE user_id = %s
                                """,(user_id,))

        if not user:
            flash('User not found','error')
            return redirect(url_for('login'))

        user = user[0]
        user_permissions = get_user_permissions(user[4])  # role is at index 4

        return render_template('users/profile.html',user=user,
                               permissions=user_permissions,roles=ROLES)

    except Exception as e:
        print(f"Error loading profile: {e}")
        flash('Error loading profile','error')
        return redirect(url_for('dashboard'))


@users_bp.route('/change-password',methods=['GET','POST'])
@require_auth
def change_password():
    """Change user password"""
    if request.method == 'POST':
        try:
            current_password = request.form.get('current_password','').strip()
            new_password = request.form.get('new_password','').strip()
            confirm_password = request.form.get('confirm_password','').strip()

            # Validation
            if not all([current_password,new_password,confirm_password]):
                flash('All fields are required','error')
                return render_template('users/change_password.html')

            if new_password != confirm_password:
                flash('New passwords do not match','error')
                return render_template('users/change_password.html')

            if len(new_password) < 6:
                flash('Password must be at least 6 characters','error')
                return render_template('users/change_password.html')

            # Verify current password
            current_hash = hashlib.sha256(current_password.encode()).hexdigest()
            user = db.execute_query(
                "SELECT user_id FROM users WHERE user_id = %s AND password = %s",
                (session.get('user_id'),current_hash)
            )

            if not user:
                flash('Current password is incorrect','error')
                return render_template('users/change_password.html')

            # Update password
            new_hash = hashlib.sha256(new_password.encode()).hexdigest()
            updated = db.execute_update("""
                                        UPDATE users
                                        SET password   = %s,
                                            updated_at = CURRENT_TIMESTAMP
                                        WHERE user_id = %s
                                        """,(new_hash,session.get('user_id')))

            if updated:
                flash('Password changed successfully','success')
                return redirect(url_for('users.profile'))
            else:
                flash('Error changing password','error')

        except Exception as e:
            print(f"Error changing password: {e}")
            flash('Error changing password','error')

    return render_template('users/change_password.html')


@users_bp.route('/activity')
@require_permission('users_view')
def user_activity():
    """User activity log"""
    try:
        # Get recent user activities
        activities = db.execute_query("""
                                      SELECT u.username, u.full_name, u.last_login, u.role, u.status
                                      FROM users u
                                      ORDER BY u.last_login DESC LIMIT 50
                                      """)

        return render_template('users/activity.html',activities=activities)

    except Exception as e:
        print(f"Error loading user activity: {e}")
        flash('Error loading user activity','error')
        return redirect(url_for('users.list_users'))


@users_bp.route('/api/check-permission')
@require_auth
def check_permission():
    """API endpoint to check user permissions"""
    permission = request.args.get('permission')
    user_role = session.get('role','Read Only')

    return jsonify({
        'has_permission': has_permission(user_role,permission),
        'role': user_role,
        'permissions': get_user_permissions(user_role)
    })


# Helper functions
def get_user_statistics():
    """Get user statistics"""
    try:
        stats = {}

        # Total users
        result = db.execute_query("SELECT COUNT(*) FROM users")
        stats['total_users'] = result[0][0] if result else 0

        # Active users
        result = db.execute_query("SELECT COUNT(*) FROM users WHERE status = 'Active'")
        stats['active_users'] = result[0][0] if result else 0

        # Users by role
        result = db.execute_query("""
                                  SELECT role, COUNT(*) as count
                                  FROM users
                                  WHERE status = 'Active'
                                  GROUP BY role
                                  ORDER BY count DESC
                                  """)
        stats['users_by_role'] = result if result else []

        # Recent logins (last 7 days)
        result = db.execute_query("""
                                  SELECT COUNT(*)
                                  FROM users
                                  WHERE last_login >= DATE_SUB(CURRENT_DATE, INTERVAL 7 DAY)
                                  """)
        stats['recent_logins'] = result[0][0] if result else 0

        return stats

    except Exception as e:
        print(f"Error getting user statistics: {e}")
        return {
            'total_users': 0,
            'active_users': 0,
            'users_by_role': [],
            'recent_logins': 0
        }


def create_default_admin():
    """Create default admin user if none exists"""
    try:
        if not db or not db.test_connection():
            return False

        # Check if any admin exists
        admin_exists = db.execute_query("SELECT user_id FROM users WHERE role IN ('Super Admin', 'Admin') LIMIT 1")

        if not admin_exists:
            # Create default admin
            password_hash = hashlib.sha256('admin123'.encode()).hexdigest()

            admin_id = db.execute_insert("""
                                         INSERT INTO users (username, password, full_name, email, role, status)
                                         VALUES (%s, %s, %s, %s, %s, %s)
                                         """,('admin',password_hash,'System Administrator','admin@system.local',
                                              'Super Admin','Active'))

            if admin_id:
                print("✅ Default admin user created: admin / admin123")
                return True

        return False

    except Exception as e:
        print(f"Error creating default admin: {e}")
        return False


def initialize_user_tables():
    """Initialize user tables if they don't exist"""
    try:
        if not db or not db.test_connection():
            return False

        # Create users table
        db.execute_update("""
                          CREATE TABLE IF NOT EXISTS users
                          (
                              user_id
                              INT
                              AUTO_INCREMENT
                              PRIMARY
                              KEY,
                              username
                              VARCHAR
                          (
                              50
                          ) UNIQUE NOT NULL,
                              password VARCHAR
                          (
                              255
                          ) NOT NULL,
                              full_name VARCHAR
                          (
                              100
                          ) NOT NULL,
                              email VARCHAR
                          (
                              100
                          ) UNIQUE NOT NULL,
                              role VARCHAR
                          (
                              50
                          ) DEFAULT 'Read Only',
                              status VARCHAR
                          (
                              20
                          ) DEFAULT 'Active',
                              last_login DATETIME NULL,
                              created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                              updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                              created_by INT NULL,
                              INDEX idx_username
                          (
                              username
                          ),
                              INDEX idx_email
                          (
                              email
                          ),
                              INDEX idx_role
                          (
                              role
                          ),
                              INDEX idx_status
                          (
                              status
                          )
                              )
                          """)

        print("✅ User tables initialized")
        return True

    except Exception as e:
        print(f"Error initializing user tables: {e}")
        return False