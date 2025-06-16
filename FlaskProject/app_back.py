from flask import Flask,render_template,redirect,url_for,session,flash,request
# Update this import in your app.py
from models.database import db, StudentDB, AssignmentDB
import os

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
# ADD THIS IMPORT after your existing imports
try:
    from routes.rooms import rooms_bp
    print("✅ Room routes loaded successfully")
except ImportError as e:
    print(f"⚠️  Room routes not found: {e}")
    rooms_bp = None

try:
    from routes.assignments import assignments_bp
    app.register_blueprint(assignments_bp)
    print("✅ Assignment routes registered successfully")
except ImportError as e:
    print(f"⚠️  Assignment routes not found: {e}")

# Also import the AssignmentDB class
try:
    from models.database import db, StudentDB, AssignmentDB
    print("✅ Assignment database models loaded successfully")
except ImportError as e:
    print(f"⚠️  Assignment database models not found: {e}")
    AssignmentDB = None

# ADD THIS BLUEPRINT REGISTRATION after your students blueprint registration
if rooms_bp:
    app.register_blueprint(rooms_bp)
    print("✅ Room routes registered successfully")

# Import database
try:
    from models.database import db,StudentDB

    print("✅ Database module loaded successfully")
except ImportError as e:
    print(f"⚠️  Database module not found: {e}")
    db = None
    StudentDB = None

# Import and register blueprints
try:
    from routes.students import students_bp

    app.register_blueprint(students_bp)
    print("✅ Student routes registered successfully")
except ImportError as e:
    print(f"⚠️  Student routes not found: {e}")


# Initialize database connection when app starts
if db:
    with app.app_context():
        try:
            db.connect()
            print("✅ Database connection successful!")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            print("📝 App will run in demo mode")


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

        # Try database authentication first
        if db:
            try:
                query = "SELECT user_id, username, role, full_name FROM users WHERE username = %s AND password = %s AND status = 'Active'"
                user = db.execute_query(query,(username,password))

                if user:
                    user_data = user[0]
                    session['user_id'] = user_data[0]
                    session['username'] = user_data[1]
                    session['role'] = user_data[2]
                    session['full_name'] = user_data[3]
                    flash('Login successful!','success')
                    return redirect(url_for('dashboard'))
            except Exception as e:
                print(f"Database authentication failed: {e}")

        # Fallback authentication
        if username == 'admin' and password == 'admin123':
            session['user_id'] = 1
            session['username'] = username
            session['role'] = 'Admin'
            session['full_name'] = 'System Administrator'
            flash('Login successful!','success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password!','error')

    # Try to render login template
    try:
        return render_template('auth/login.html')
    except Exception as e:
        print(f"⚠️  Login template not found: {e}")
        # Return basic HTML login form
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
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        '''


# UPDATE YOUR DASHBOARD ROUTE to include room statistics
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Get statistics for dashboard
    stats = {
        'total_students': 0,
        'total_rooms': 5,
        'available_rooms': 3,
        'occupied_rooms': 2,
        'recent_activities': [],
        'monthly_revenue': 0,  # NEW
        'outstanding_dues': 0,  # NEW
        'overdue_payments': 0
    }

    # Try to get real statistics from database
    if db and db.test_connection():
        try:
            # Total students
            result = db.execute_query("SELECT COUNT(*) FROM students WHERE status = 'Active'")
            if result and len(result) > 0:
                stats['total_students'] = result[0][0]

            # Total rooms
            result = db.execute_query("SELECT COUNT(*) FROM rooms")
            if result and len(result) > 0:
                stats['total_rooms'] = result[0][0]

            # Available rooms
            result = db.execute_query("SELECT COUNT(*) FROM rooms WHERE status = 'Available'")
            if result and len(result) > 0:
                stats['available_rooms'] = result[0][0]

            # Occupied rooms
            result = db.execute_query("SELECT COUNT(*) FROM rooms WHERE status = 'Occupied'")
            if result and len(result) > 0:
                stats['occupied_rooms'] = result[0][0]

            # Recent activities
            if StudentDB:
                recent_students = StudentDB.get_all_students(limit=5)
                if recent_students:
                    stats['recent_activities'] = [
                        f"Student {student[2]} {student[3]} registered" for student in recent_students[:3]
                    ]

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
        # Return updated HTML dashboard with room management link
        return f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Dashboard - Hostel Management</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
            <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        </head>
        <body>
            <nav class="navbar navbar-dark bg-primary">
                <div class="container">
                    <span class="navbar-brand"><i class="fas fa-building"></i> Hostel Management System</span>
                    <div>
                        <span class="text-white me-3">Welcome, {session.get('full_name',session.get('username'))}</span>
                        <a href="/logout" class="btn btn-outline-light btn-sm">Logout</a>
                    </div>
                </div>
            </nav>
            <div class="container mt-4">
                <h2><i class="fas fa-tachometer-alt"></i> Dashboard</h2>
                <div class="row mt-4">
                    <div class="col-md-3">
                        <div class="card text-white bg-primary">
                            <div class="card-body text-center">
                                <h5><i class="fas fa-users"></i> Total Students</h5>
                                <h2>{stats['total_students']}</h2>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card text-white bg-success">
                            <div class="card-body text-center">
                                <h5><i class="fas fa-bed"></i> Total Rooms</h5>
                                <h2>{stats['total_rooms']}</h2>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card text-white bg-warning">
                            <div class="card-body text-center">
                                <h5><i class="fas fa-door-open"></i> Available</h5>
                                <h2>{stats['available_rooms']}</h2>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card text-white bg-info">
                            <div class="card-body text-center">
                                <h5><i class="fas fa-user-check"></i> Occupied</h5>
                                <h2>{stats['occupied_rooms']}</h2>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="mt-4">
                    <div class="card">
                        <div class="card-body">
                            <h5><i class="fas fa-bolt"></i> Quick Actions</h5>
                            <a href="/students" class="btn btn-primary me-2">
                                <i class="fas fa-users"></i> Manage Students
                            </a>
                            <a href="{{ url_for('rooms.list_rooms') }}" class="btn btn-success me-2">
                                <i class="fas fa-bed"></i> Manage Rooms
                            </a>
                            <button class="btn btn-warning" onclick="alert('Payment system coming soon!')">
                                <i class="fas fa-dollar-sign"></i> Payments
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        '''

        # Try to get real statistics from database
        if db and db.test_connection():
            try:
                # Existing stats
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

                # NEW: Payment statistics
                if PaymentDB:
                    payment_stats = PaymentDB.get_payment_statistics()
                    stats['monthly_revenue'] = payment_stats.get('monthly_payments',{}).get('total',0)
                    stats['outstanding_dues'] = payment_stats.get('outstanding_dues',{}).get('total',0)
                    stats['overdue_payments'] = payment_stats.get('overdue_payments',{}).get('total',0)

                # Recent activities
                if StudentDB:
                    recent_students = StudentDB.get_all_students(limit=5)
                    if recent_students:
                        stats['recent_activities'] = [
                            f"Student {student[2]} {student[3]} registered" for student in recent_students[:3]
                        ]

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
            # Return updated HTML dashboard with payment management link
            return f'''
            <!DOCTYPE html>
            <html>
            <head>
                <title>Dashboard - Hostel Management</title>
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
                <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
            </head>
            <body>
                <nav class="navbar navbar-dark bg-primary">
                    <div class="container">
                        <span class="navbar-brand"><i class="fas fa-building"></i> Hostel Management System</span>
                        <div>
                            <span class="text-white me-3">Welcome, {session.get('full_name',session.get('username'))}</span>
                            <a href="/logout" class="btn btn-outline-light btn-sm">Logout</a>
                        </div>
                    </div>
                </nav>
                <div class="container mt-4">
                    <h2><i class="fas fa-tachometer-alt"></i> Dashboard</h2>
                    <div class="row mt-4">
                        <div class="col-md-3">
                            <div class="card text-white bg-primary">
                                <div class="card-body text-center">
                                    <h5><i class="fas fa-users"></i> Total Students</h5>
                                    <h2>{stats['total_students']}</h2>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="card text-white bg-success">
                                <div class="card-body text-center">
                                    <h5><i class="fas fa-bed"></i> Total Rooms</h5>
                                    <h2>{stats['total_rooms']}</h2>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="card text-white bg-warning">
                                <div class="card-body text-center">
                                    <h5><i class="fas fa-dollar-sign"></i> Monthly Revenue</h5>
                                    <h2>RM {stats['monthly_revenue']:.2f}</h2>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="card text-white bg-danger">
                                <div class="card-body text-center">
                                    <h5><i class="fas fa-exclamation-triangle"></i> Outstanding</h5>
                                    <h2>RM {stats['outstanding_dues']:.2f}</h2>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="mt-4">
                        <div class="card">
                            <div class="card-body">
                                <h5><i class="fas fa-bolt"></i> Quick Actions</h5>
                                <a href="/students" class="btn btn-primary me-2">
                                    <i class="fas fa-users"></i> Manage Students
                                </a>
                                <a href="/rooms" class="btn btn-success me-2">
                                    <i class="fas fa-bed"></i> Manage Rooms
                                </a>
                                <a href="/assignments" class="btn btn-info me-2">
                                    <i class="fas fa-home"></i> Assignments
                                </a>
                                <a href="/payments" class="btn btn-warning">
                                    <i class="fas fa-dollar-sign"></i> Payments
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            '''

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out!','info')
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



# UPDATE THE STARTUP MESSAGE to include room management
if __name__ == '__main__':
    print("=" * 60)
    print("🏢 HOSTEL MANAGEMENT SYSTEM")
    print("=" * 60)
    print("🔗 URLs to access:")
    print("   📱 Main: http://127.0.0.1:5000")
    print("   🔐 Login: http://127.0.0.1:5000/login")
    print("   📊 Dashboard: http://127.0.0.1:5000/dashboard")
    print("   👨‍🎓 Students: http://127.0.0.1:5000/students")
    print("   🏠 Rooms: http://127.0.0.1:5000/rooms")  # NEW
    print("=" * 60)
    print("🔑 Default login credentials:")
    print("   Username: admin")
    print("   Password: admin123")
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