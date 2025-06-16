from flask import Blueprint,render_template,session,redirect,url_for
from models.database import db

dashboard_bp = Blueprint('dashboard',__name__)


@dashboard_bp.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    # Get statistics for dashboard
    stats = {}

    try:
        # Total students
        result = db.execute_query("SELECT COUNT(*) FROM students WHERE status = 'Active'")
        stats['total_students'] = result[0][0] if result else 0

        # Total rooms
        result = db.execute_query("SELECT COUNT(*) FROM rooms")
        stats['total_rooms'] = result[0][0] if result else 0

        # Available rooms
        result = db.execute_query("SELECT COUNT(*) FROM rooms WHERE status = 'Available'")
        stats['available_rooms'] = result[0][0] if result else 0

        # Occupied rooms
        result = db.execute_query("SELECT COUNT(*) FROM rooms WHERE status = 'Occupied'")
        stats['occupied_rooms'] = result[0][0] if result else 0

        # Pending payments (example)
        result = db.execute_query("SELECT COUNT(*) FROM fee_payments WHERE status = 'Pending'")
        stats['pending_payments'] = result[0][0] if result else 0

        # Recent activities (last 5 activities)
        recent_activities = []

        # Get recent student registrations
        student_activities = db.execute_query("""
                                              SELECT CONCAT(first_name, ' ', last_name) as name,
                                                     DATE_FORMAT(created_at, '%Y-%m-%d %H:%i') as date,
                   'Student Registration' as activity_type
                                              FROM students
                                              ORDER BY created_at DESC
                                                  LIMIT 3
                                              """)

        if student_activities:
            for activity in student_activities:
                recent_activities.append({
                    'description': f"{activity[0]} registered as new student",
                    'date': activity[1],
                    'type': 'success'
                })

        # Get recent payments
        payment_activities = db.execute_query("""
                                              SELECT CONCAT(s.first_name, ' ', s.last_name) as name,
                                                     fp.amount,
                                                     DATE_FORMAT(fp.created_at, '%Y-%m-%d %H:%i') as date
                                              FROM fee_payments fp
                                                  JOIN students s
                                              ON fp.student_id = s.student_id
                                              ORDER BY fp.created_at DESC
                                                  LIMIT 2
                                              """)

        if payment_activities:
            for payment in payment_activities:
                recent_activities.append({
                    'description': f"Payment of ${payment[1]} received from {payment[0]}",
                    'date': payment[2],
                    'type': 'info'
                })

        stats['recent_activities'] = recent_activities

    except Exception as e:
        print(f"Error getting dashboard stats: {e}")
        stats = {
            'total_students': 0,
            'total_rooms': 0,
            'available_rooms': 0,
            'occupied_rooms': 0,
            'pending_payments': 0,
            'recent_activities': []
        }

    return render_template('dashboard.html',stats=stats)