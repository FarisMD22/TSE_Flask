from flask import Flask,render_template,redirect,url_for,session,flash,request
from models.database import db,StudentDB,AssignmentDB
import os
import hashlib

print("🚀 Starting Hostel Management System...")

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'

# Import configuration
try:
    from config import Config

    app.config.from_object(Config)
    print("✅ Configuration loaded successfully")
except ImportError as e:
    print(f"⚠️  Config not found: {e}")

# Import room routes
try:
    from routes.rooms import rooms_bp

    app.register_blueprint(rooms_bp)
    print("✅ Room routes loaded successfully")
except ImportError as e:
    print(f"⚠️  Room routes not found: {e}")
    rooms_bp = None

# Import assignment routes
try:
    from routes.assignments import assignments_bp

    app.register_blueprint(assignments_bp)
    print("✅ Assignment routes registered successfully")
except ImportError as e:
    print(f"⚠️  Assignment routes not found: {e}")

# Import payment routes
try:
    from routes.payments import payments_bp

    app.register_blueprint(payments_bp)
    print("✅ Payment routes registered successfully")
except ImportError as e:
    print(f"⚠️  Payment routes not found: {e}")

# Import student routes
try:
    from routes.students import students_bp

    app.register_blueprint(students_bp)
    print("✅ Student routes registered successfully")
except ImportError as e:
    print(f"⚠️  Student routes not found: {e}")

# Import reports routes
try:
    from routes.reports import reports_bp

    app.register_blueprint(reports_bp)
    print("✅ Reports routes registered successfully")
except ImportError as e:
    print(f"⚠️  Reports routes not found: {e}")

# NEW: Import user management routes
try:
    from routes.users import users_bp,initialize_user_tables,create_default_admin,has_permission

    app.register_blueprint(users_bp)
    print("✅ User management routes registered successfully")
except ImportError as e:
    print(f"⚠️  User management routes not found: {e}")
    users_bp = None
    has_permission = lambda role,perm: True  # Fallback function

# Import database models
try:
    from models.database import db,StudentDB,AssignmentDB

    print("✅ Database models loaded successfully")
except ImportError as e:
    print(f"⚠️  Database models not found: {e}")
    AssignmentDB = None

# Import payment database
try:
    from models.payment_database import PaymentDB

    print("✅ Payment database models loaded successfully")
except ImportError as e:
    print(f"⚠️  Payment database models not found: {e}")
    PaymentDB = None

# Import reports database
try:
    from models.reports_database import ReportsDB

    print("✅ Reports database models loaded successfully")
except ImportError as e:
    print(f"⚠️  Reports database models not found: {e}")
    ReportsDB = None

# Initialize database connection when app starts
if db:
    with app.app_context():
        try:
            db.connect()
            print("✅ Database connection successful!")

            # Initialize user management tables
            if users_bp:
                initialize_user_tables()
                create_default_admin()

        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            print("📝 App will run in demo mode")


# Add template globals for user permissions
@app.template_global()
def user_has_permission(permission):
    """Template function to check user permissions"""
    if 'role' not in session:
        return False
    return has_permission(session.get('role','Read Only'),permission)


@app.template_global()
def get_current_user():
    """Template function to get current user info"""
    return {
        'user_id': session.get('user_id'),
        'username': session.get('username'),
        'full_name': session.get('full_name'),
        'role': session.get('role','Read Only')
    }


@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('dashboard'))


@app.route('/login',methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Hash the password for database comparison
        password_hash = hashlib.sha256(password.encode()).hexdigest()

        # Try database authentication first
        if db:
            try:
                query = """
                        SELECT user_id, username, role, full_name, status
                        FROM users
                        WHERE username = %s \
                          AND password = %s \
                          AND status = 'Active' \
                        """
                user = db.execute_query(query,(username,password_hash))

                if user:
                    user_data = user[0]
                    session['user_id'] = user_data[0]
                    session['username'] = user_data[1]
                    session['role'] = user_data[2]
                    session['full_name'] = user_data[3]

                    # Update last login
                    db.execute_update(
                        "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE user_id = %s",
                        (user_data[0],)
                    )

                    flash('Login successful!','success')
                    return redirect(url_for('dashboard'))
                else:
                    flash('Invalid username or password!','error')
            except Exception as e:
                print(f"Database authentication failed: {e}")
                flash('Database error during login','error')

        # Fallback authentication for development
        if username == 'admin' and password == 'admin123':
            session['user_id'] = 1
            session['username'] = username
            session['role'] = 'Super Admin'
            session['full_name'] = 'System Administrator'
            flash('Login successful! (Fallback mode)','success')
            return redirect(url_for('dashboard'))

    # Try to render login template
    try:
        return render_template('auth/login.html')
    except Exception as e:
        print(f"⚠️  Login template not found: {e}")
        # Return enhanced login form
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Login - Hostel Management</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
            <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        </head>
        <body class="bg-light">
            <div class="container">
                <div class="row justify-content-center mt-5">
                    <div class="col-md-6">
                        <div class="card shadow">
                            <div class="card-header bg-primary text-white text-center">
                                <h3><i class="fas fa-building"></i> Hostel Management System</h3>
                            </div>
                            <div class="card-body">
                                ''' + (''.join([f'<div class="alert alert-{cat}">{msg}</div>' for cat,msg in
                                                get_flashed_messages(with_categories=True)])) + '''
                                <form method="POST">
                                    <div class="mb-3">
                                        <label class="form-label"><i class="fas fa-user"></i> Username</label>
                                        <input type="text" class="form-control" name="username" required>
                                    </div>
                                    <div class="mb-3">
                                        <label class="form-label"><i class="fas fa-lock"></i> Password</label>
                                        <input type="password" class="form-control" name="password" required>
                                    </div>
                                    <button type="submit" class="btn btn-primary w-100">
                                        <i class="fas fa-sign-in-alt"></i> Login
                                    </button>
                                </form>
                                <div class="mt-3 text-center">
                                    <small class="text-muted">Default: admin / admin123</small>
                                </div>
                                <div class="mt-3">
                                    <h6>Available Roles:</h6>
                                    <small class="text-muted">
                                        • Super Admin - Full system access<br>
                                        • Admin - Administrative access<br>
                                        • Manager - Management level access<br>
                                        • Staff - Staff level operations<br>
                                        • Receptionist - Front desk operations<br>
                                        • Accountant - Financial operations<br>
                                        • Read Only - View only access
                                    </small>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        '''


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Initialize statistics with default values
    stats = {
        'total_students': 0,
        'total_rooms': 5,
        'available_rooms': 3,
        'occupied_rooms': 2,
        'recent_activities': [],
        'monthly_revenue': 0,
        'outstanding_dues': 0,
        'overdue_payments': 0,
        'pending_students': 0,
        'total_users': 0,
        'active_users': 0
    }

    # Try to get real statistics from database
    if db and db.test_connection():
        try:
            # Existing statistics
            result = db.execute_query("SELECT COUNT(*) FROM students WHERE status = 'Active'")
            if result and len(result) > 0:
                stats['total_students'] = result[0][0]

            result = db.execute_query("SELECT COUNT(*) FROM rooms")
            if result and len(result) > 0:
                stats['total_rooms'] = result[0][0]

            result = db.execute_query("SELECT COUNT(*) FROM rooms WHERE status = 'Available'")
            if result and len(result) > 0:
                stats['available_rooms'] = result[0][0]

            result = db.execute_query("SELECT COUNT(*) FROM rooms WHERE status = 'Occupied'")
            if result and len(result) > 0:
                stats['occupied_rooms'] = result[0][0]

            # User statistics
            result = db.execute_query("SELECT COUNT(*) FROM users")
            if result and len(result) > 0:
                stats['total_users'] = result[0][0]

            result = db.execute_query("SELECT COUNT(*) FROM users WHERE status = 'Active'")
            if result and len(result) > 0:
                stats['active_users'] = result[0][0]

            # Payment statistics
            if PaymentDB:
                try:
                    payment_summary = PaymentDB.get_payment_summary()
                    stats['monthly_revenue'] = payment_summary.get('month_total',0)
                    stats['outstanding_dues'] = payment_summary.get('outstanding_dues',0)
                    stats['pending_students'] = payment_summary.get('pending_students',0)

                    # Get recent payments for activities
                    recent_payments = PaymentDB.get_all_payments(limit=3)
                    for payment in recent_payments:
                        if len(payment) >= 10:  # Ensure we have enough data
                            stats['recent_activities'].append(
                                f"Payment RM {payment[1]:.2f} from {payment[8]} {payment[9]}"
                            )
                except Exception as pe:
                    print(f"Payment stats error: {pe}")

            # Recent activities from students
            if StudentDB:
                recent_students = StudentDB.get_all_students(limit=3)
                if recent_students:
                    for student in recent_students[:2]:  # Limit to avoid too many activities
                        stats['recent_activities'].append(
                            f"Student {student[2]} {student[3]} registered"
                        )

            print("✅ Dashboard stats loaded from database")

        except Exception as e:
            print(f"❌ Dashboard error: {e}")
            flash('Using demo data - database connection issue','warning')
    else:
        flash('Running in demo mode - connect database for real data','info')

    # Try to render dashboard template
    try:
        return render_template('dashboard.html',stats=stats)
    except Exception as e:
        print(f"⚠️  Dashboard template not found: {e}")
        # Return enhanced HTML dashboard with user management
        user_role = session.get('role','Read Only')
        user_name = session.get('full_name',session.get('username'))

        return f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Dashboard - Hostel Management</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
            <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        </head>
        <body>
            <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
                <div class="container">
                    <span class="navbar-brand"><i class="fas fa-building"></i> Hostel Management System</span>

                    <div class="navbar-nav me-auto">
                        <div class="nav-item dropdown">
                            <a class="nav-link dropdown-toggle text-white" href="#" role="button" data-bs-toggle="dropdown">
                                <i class="fas fa-money-bill-wave"></i> Payments
                            </a>
                            <ul class="dropdown-menu">
                                <li><a class="dropdown-item" href="/payments"><i class="fas fa-list"></i> All Payments</a></li>
                                <li><a class="dropdown-item" href="/payments/add"><i class="fas fa-plus"></i> Add Payment</a></li>
                                <li><a class="dropdown-item" href="/payments/dues"><i class="fas fa-exclamation-triangle"></i> Outstanding Dues</a></li>
                            </ul>
                        </div>

                        <div class="nav-item dropdown">
                            <a class="nav-link dropdown-toggle text-white" href="#" role="button" data-bs-toggle="dropdown">
                                <i class="fas fa-chart-bar"></i> Reports
                            </a>
                            <ul class="dropdown-menu">
                                <li><a class="dropdown-item" href="/reports"><i class="fas fa-dashboard"></i> Reports Dashboard</a></li>
                                <li><a class="dropdown-item" href="/reports/occupancy"><i class="fas fa-bed"></i> Occupancy Reports</a></li>
                                <li><a class="dropdown-item" href="/reports/financial"><i class="fas fa-dollar-sign"></i> Financial Reports</a></li>
                                <li><a class="dropdown-item" href="/reports/students"><i class="fas fa-users"></i> Student Reports</a></li>
                            </ul>
                        </div>

                        {"" if user_role not in ['Super Admin','Admin'] else '''
                        <div class="nav-item dropdown">
                            <a class="nav-link dropdown-toggle text-white" href="#" role="button" data-bs-toggle="dropdown">
                                <i class="fas fa-users-cog"></i> Users
                            </a>
                            <ul class="dropdown-menu">
                                <li><a class="dropdown-item" href="/users"><i class="fas fa-list"></i> All Users</a></li>
                                <li><a class="dropdown-item" href="/users/add"><i class="fas fa-user-plus"></i> Add User</a></li>
                                <li><a class="dropdown-item" href="/users/activity"><i class="fas fa-history"></i> User Activity</a></li>
                            </ul>
                        </div>
                        '''}
                    </div>

                    <div class="navbar-nav">
                        <div class="nav-item dropdown">
                            <a class="nav-link dropdown-toggle text-white" href="#" role="button" data-bs-toggle="dropdown">
                                <i class="fas fa-user"></i> {user_name} ({user_role})
                            </a>
                            <ul class="dropdown-menu">
                                <li><a class="dropdown-item" href="/users/profile"><i class="fas fa-user-circle"></i> My Profile</a></li>
                                <li><a class="dropdown-item" href="/users/change-password"><i class="fas fa-key"></i> Change Password</a></li>
                                <li><hr class="dropdown-divider"></li>
                                <li><a class="dropdown-item" href="/logout"><i class="fas fa-sign-out-alt"></i> Logout</a></li>
                            </ul>
                        </div>
                    </div>
                </div>
            </nav>

            <div class="container mt-4">
                <div class="d-flex justify-content-between align-items-center mb-4">
                    <div>
                        <h2><i class="fas fa-tachometer-alt"></i> Dashboard</h2>
                        <p class="text-muted mb-0">Welcome back, {user_name}! Here's your system overview.</p>
                    </div>
                    <div class="badge bg-{('success' if user_role == 'Super Admin' else 'primary' if user_role == 'Admin' else 'info')} fs-6">
                        {user_role}
                    </div>
                </div>

                <!-- System Statistics Cards Row 1 -->
                <div class="row mt-4">
                    <div class="col-md-3">
                        <div class="card text-white bg-primary">
                            <div class="card-body text-center">
                                <h5><i class="fas fa-users"></i> Total Students</h5>
                                <h2>{stats['total_students']}</h2>
                                <small class="opacity-75">Active students</small>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card text-white bg-success">
                            <div class="card-body text-center">
                                <h5><i class="fas fa-bed"></i> Total Rooms</h5>
                                <h2>{stats['total_rooms']}</h2>
                                <small class="opacity-75">All rooms</small>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card text-white bg-warning">
                            <div class="card-body text-center">
                                <h5><i class="fas fa-door-open"></i> Available</h5>
                                <h2>{stats['available_rooms']}</h2>
                                <small class="opacity-75">Ready for assignment</small>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card text-white bg-info">
                            <div class="card-body text-center">
                                <h5><i class="fas fa-user-check"></i> Occupied</h5>
                                <h2>{stats['occupied_rooms']}</h2>
                                <small class="opacity-75">Currently occupied</small>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Financial & User Statistics Cards Row 2 -->
                <div class="row mt-3">
                    <div class="col-md-3">
                        <div class="card text-white bg-success">
                            <div class="card-body text-center">
                                <h5><i class="fas fa-money-bill-wave"></i> Monthly Revenue</h5>
                                <h2>RM {stats['monthly_revenue']:.2f}</h2>
                                <small class="opacity-75">This month</small>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card text-white bg-danger">
                            <div class="card-body text-center">
                                <h5><i class="fas fa-exclamation-triangle"></i> Outstanding</h5>
                                <h2>RM {stats['outstanding_dues']:.2f}</h2>
                                <small class="opacity-75">Pending payments</small>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card text-white bg-secondary">
                            <div class="card-body text-center">
                                <h5><i class="fas fa-users-cog"></i> Total Users</h5>
                                <h2>{stats['total_users']}</h2>
                                <small class="opacity-75">System users</small>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card text-white bg-dark">
                            <div class="card-body text-center">
                                <h5><i class="fas fa-user-check"></i> Active Users</h5>
                                <h2>{stats['active_users']}</h2>
                                <small class="opacity-75">Currently active</small>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Quick Actions and Recent Activities -->
                <div class="row mt-4">
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header">
                                <h5><i class="fas fa-bolt"></i> Quick Actions</h5>
                            </div>
                            <div class="card-body">
                                <div class="d-grid gap-2">
                                    <a href="/students" class="btn btn-primary">
                                        <i class="fas fa-users"></i> Manage Students
                                    </a>
                                    <a href="/rooms" class="btn btn-success">
                                        <i class="fas fa-bed"></i> Manage Rooms
                                    </a>
                                    <a href="/assignments" class="btn btn-info">
                                        <i class="fas fa-home"></i> Room Assignments
                                    </a>
                                    <a href="/payments" class="btn btn-warning">
                                        <i class="fas fa-dollar-sign"></i> Payment Management
                                    </a>
                                    {"" if user_role not in ['Super Admin','Admin'] else '''
                                    <a href="/users" class="btn btn-secondary">
                                        <i class="fas fa-users-cog"></i> User Management
                                    </a>
                                    '''}
                                    <a href="/reports" class="btn btn-dark">
                                        <i class="fas fa-chart-bar"></i> Reports & Analytics
                                    </a>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header">
                                <h5><i class="fas fa-clock"></i> Recent Activities</h5>
                            </div>
                            <div class="card-body">
                                {"".join([f"<div class='mb-2'><i class='fas fa-check-circle text-success'></i> {activity}</div>" for activity in stats['recent_activities'][:5]]) if stats['recent_activities'] else "<p class='text-muted'>No recent activities</p>"}
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Alerts and Notifications -->
                {f'''
                <div class="row mt-3">
                    <div class="col-12">
                        <div class="alert alert-warning">
                            <i class="fas fa-exclamation-triangle"></i>
                            <strong>Payment Alert:</strong> {stats['pending_students']} students have outstanding dues totaling RM {stats['outstanding_dues']:.2f}
                            <a href="/payments/dues" class="btn btn-sm btn-outline-warning ms-2">View Details</a>
                        </div>
                    </div>
                </div>
                ''' if stats['outstanding_dues'] > 0 else ''}

                <!-- User Role Information -->
                <div class="row mt-3">
                    <div class="col-12">
                        <div class="alert alert-info">
                            <i class="fas fa-info-circle"></i>
                            <strong>Your Access Level:</strong> You are logged in as <strong>{user_role}</strong>. 
                            {"You have full system access." if user_role == "Super Admin" else
        "You have administrative access to most system functions." if user_role == "Admin" else
        "You have limited access based on your role permissions."}
                            <a href="/users/profile" class="btn btn-sm btn-outline-info ms-2">View Profile</a>
                        </div>
                    </div>
                </div>
            </div>

            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        </body>
        </html>
        '''


@app.route('/logout')
def logout():
    username = session.get('username','User')
    session.clear()
    flash(f'Goodbye {username}! You have been logged out.','info')
    return redirect(url_for('login'))


# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return '''
    <div class="container mt-5 text-center">
        <h1><i class="fas fa-exclamation-triangle text-warning"></i> 404</h1>
        <h4>Page Not Found</h4>
        <p>The page you're looking for doesn't exist.</p>
        <a href="/" class="btn btn-primary"><i class="fas fa-home"></i> Go Home</a>
    </div>
    ''',404


@app.errorhandler(500)
def internal_error(error):
    return '''
    <div class="container mt-5 text-center">
        <h1><i class="fas fa-server text-danger"></i> 500</h1>
        <h4>Internal Server Error</h4>
        <p>Something went wrong. Please try again.</p>
        <a href="/" class="btn btn-primary"><i class="fas fa-home"></i> Go Home</a>
    </div>
    ''',500


if __name__ == '__main__':
    print("=" * 60)
    print("🏢 HOSTEL MANAGEMENT SYSTEM WITH USER MANAGEMENT")
    print("=" * 60)
    print("🔗 URLs to access:")
    print("   📱 Main: http://127.0.0.1:5000")
    print("   🔐 Login: http://127.0.0.1:5000/login")
    print("   📊 Dashboard: http://127.0.0.1:5000/dashboard")
    print("   👨‍🎓 Students: http://127.0.0.1:5000/students")
    print("   🏠 Rooms: http://127.0.0.1:5000/rooms")
    print("   🏡 Assignments: http://127.0.0.1:5000/assignments")
    print("   💰 Payments: http://127.0.0.1:5000/payments")
    print("   📈 Reports: http://127.0.0.1:5000/reports")
    print("   👥 Users: http://127.0.0.1:5000/users")  # NEW
    print("=" * 60)
    print("🔑 Default login credentials:")
    print("   Username: admin")
    print("   Password: admin123")
    print("   Role: Super Admin")
    print("=" * 60)
    print("👥 User Management Features:")
    print("   📋 User List: /users")
    print("   ➕ Add User: /users/add")
    print("   ✏️  Edit User: /users/edit/<id>")
    print("   👤 User Profile: /users/profile")
    print("   🔑 Change Password: /users/change-password")
    print("   📊 User Activity: /users/activity")
    print("=" * 60)


    try:
        app.run(host='127.0.0.1',port=5000,debug=True)
    except OSError as e:
        if "Address already in use" in str(e):
            print("❌ Port 5000 is in use, trying 5001...")
            app.run(host='127.0.0.1',port=5001,debug=True)
        else:
            print(f"❌ Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")