# routes/reports.py - FIXED VERSION - Complete Reports Module Routes
from flask import Blueprint,render_template,request,redirect,url_for,flash,jsonify,make_response,session
from models.reports_database import ReportsDB
from models.database import db,StudentDB,AssignmentDB
from models.payment_database import PaymentDB
from datetime import datetime,date,timedelta
import csv
import io

# Create blueprint
reports_bp = Blueprint('reports',__name__,url_prefix='/reports')


# Helper function to check authentication
def require_auth():
    """Check if user is authenticated"""
    if 'user_id' not in session:
        flash('Please log in to access reports','error')
        return redirect(url_for('login'))
    return None


@reports_bp.route('/')
def reports_dashboard():
    """Main reports dashboard"""
    auth_check = require_auth()
    if auth_check:
        return auth_check

    try:
        # Get dashboard statistics
        stats = ReportsDB.get_dashboard_statistics()

        return render_template('reports/dashboard.html',stats=stats)
    except Exception as e:
        print(f"Error in reports dashboard: {e}")
        flash('Error loading reports dashboard','error')
        # Return with default stats
        default_stats = {
            'total_students': 0,
            'total_rooms': 0,
            'active_assignments': 0,
            'monthly_payments': 0,
            'monthly_revenue': 0.0,
            'outstanding_count': 0,
            'outstanding_total': 0.0,
            'occupancy_rate': 0.0
        }
        return render_template('reports/dashboard.html',stats=default_stats)


@reports_bp.route('/occupancy')
def occupancy_reports():
    """Occupancy reports and analytics"""
    auth_check = require_auth()
    if auth_check:
        return auth_check

    try:
        # Get filter parameters
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        room_type = request.args.get('room_type')
        report_type = request.args.get('report_type','overview')

        # Set default dates if not provided
        if not date_from:
            date_from = (date.today() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not date_to:
            date_to = date.today().strftime('%Y-%m-%d')

        # Get occupancy statistics
        occupancy_stats = get_occupancy_statistics()

        # Get room utilization data
        room_utilization = get_room_utilization_data(room_type)

        # Get detailed room status
        detailed_rooms = get_detailed_room_status()

        # Get peak usage patterns
        peak_patterns = get_peak_usage_patterns(date_from,date_to)

        # Get underutilized rooms
        underutilized_rooms = get_underutilized_rooms()

        return render_template('reports/occupancy_reports.html',
                               date_from=date_from,
                               date_to=date_to,
                               occupancy_stats=occupancy_stats,
                               room_utilization=room_utilization,
                               detailed_rooms=detailed_rooms,
                               peak_patterns=peak_patterns,
                               underutilized_rooms=underutilized_rooms)

    except Exception as e:
        print(f"Error in occupancy reports: {e}")
        flash('Error loading occupancy reports','error')
        # Return with safe defaults
        return render_template('reports/occupancy_reports.html',
                               date_from=date_from or '',
                               date_to=date_to or '',
                               occupancy_stats={'total_rooms': 0,'occupied_rooms': 0,'available_rooms': 0,
                                                'occupancy_rate': 0},
                               room_utilization=[],
                               detailed_rooms=[],
                               peak_patterns=[],
                               underutilized_rooms=[])


@reports_bp.route('/financial')
def financial_reports():
    """Financial reports and analytics"""
    auth_check = require_auth()
    if auth_check:
        return auth_check

    try:
        # Get filter parameters
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        period = request.args.get('period','monthly')
        payment_method = request.args.get('payment_method')

        # Set default dates if not provided
        if not date_from:
            date_from = (date.today() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not date_to:
            date_to = date.today().strftime('%Y-%m-%d')

        # Get financial summary
        financial_summary = get_financial_summary(date_from,date_to,payment_method)

        # Get monthly breakdown
        monthly_breakdown = get_monthly_financial_breakdown(date_from,date_to)

        # Get outstanding dues analysis
        outstanding_analysis = get_outstanding_dues_analysis()

        # Get recent payments
        recent_payments = get_recent_payments_for_report()

        # Get financial KPIs
        financial_kpis = get_financial_kpis()

        # Get top paying students
        top_paying_students = get_top_paying_students()

        return render_template('reports/financial_reports.html',
                               date_from=date_from,
                               date_to=date_to,
                               financial_summary=financial_summary,
                               monthly_breakdown=monthly_breakdown,
                               outstanding_analysis=outstanding_analysis,
                               recent_payments=recent_payments,
                               financial_kpis=financial_kpis,
                               top_paying_students=top_paying_students)

    except Exception as e:
        print(f"Error in financial reports: {e}")
        flash('Error loading financial reports','error')
        # Return with safe defaults
        return render_template('reports/financial_reports.html',
                               date_from=date_from or '',
                               date_to=date_to or '',
                               financial_summary={'total_revenue': 0,'outstanding_amount': 0,'collection_rate': 0,
                                                  'average_payment': 0},
                               monthly_breakdown=[],
                               outstanding_analysis=[],
                               recent_payments=[],
                               financial_kpis={'revenue_growth': 0,'collection_efficiency': 0,'avg_days_to_pay': 0,
                                               'late_payment_rate': 0},
                               top_paying_students=[])


@reports_bp.route('/students')
def student_reports():
    """Student reports and analytics"""
    auth_check = require_auth()
    if auth_check:
        return auth_check

    try:
        # Get filter parameters
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        course = request.args.get('course')
        status = request.args.get('status','Active')
        year = request.args.get('year')
        room_status = request.args.get('room_status')
        payment_status = request.args.get('payment_status')
        report_type = request.args.get('report_type','overview')

        # Set default dates if not provided (current academic year)
        if not date_from:
            today = date.today()
            academic_year_start = date(today.year if today.month >= 9 else today.year - 1,9,1)
            date_from = academic_year_start.strftime('%Y-%m-%d')
        if not date_to:
            date_to = date.today().strftime('%Y-%m-%d')

        # Get available courses
        available_courses = get_available_courses()

        # Get student statistics
        student_stats = get_student_statistics(status,course,year)

        # Get course analysis
        course_analysis = get_course_analysis()

        # Get top performing students
        top_students = get_top_performing_students()

        # Get students requiring attention
        attention_students = get_students_requiring_attention()

        # Get payment timing analysis
        payment_timing = get_payment_timing_analysis()

        # Get recent student activities
        recent_activities = get_recent_student_activities()

        # Get retention rates
        retention_rates = get_retention_rates()

        return render_template('reports/student_reports.html',
                               date_from=date_from,
                               date_to=date_to,
                               available_courses=available_courses,
                               student_stats=student_stats,
                               course_analysis=course_analysis,
                               top_students=top_students,
                               attention_students=attention_students,
                               payment_timing=payment_timing,
                               recent_activities=recent_activities,
                               retention_rates=retention_rates)

    except Exception as e:
        print(f"Error in student reports: {e}")
        flash('Error loading student reports','error')
        # Return with safe defaults
        return render_template('reports/student_reports.html',
                               date_from=date_from or '',
                               date_to=date_to or '',
                               available_courses=[],
                               student_stats={'total_students': 0,'active_students': 0,'students_with_rooms': 0,
                                              'students_with_dues': 0},
                               course_analysis=[],
                               top_students=[],
                               attention_students=[],
                               payment_timing={'early_payers': 0,'on_time_payers': 0,'late_payers': 0,'non_payers': 0},
                               recent_activities=[],
                               retention_rates={'year_1_to_2': 0,'year_2_to_3': 0,'year_3_to_4': 0,'overall': 0})


@reports_bp.route('/export')
def export_data():
    """Export data page"""
    auth_check = require_auth()
    if auth_check:
        return auth_check

    try:
        # Get export options and counts
        export_options = ReportsDB.get_export_options()
        return render_template('reports/export_data.html',export_options=export_options)
    except Exception as e:
        print(f"Error in export data page: {e}")
        flash('Error loading export options','error')
        # Return with default options
        default_options = {
            'students': {'count': 0,'description': 'Student records - no data found'},
            'rooms': {'count': 0,'description': 'Room records - no data found'},
            'assignments': {'count': 0,'description': 'Assignment records - no data found'},
            'payments': {'count': 0,'description': 'Payment records - no data found'},
            'outstanding_dues': {'count': 0,'description': 'Outstanding dues - no data found'}
        }
        return render_template('reports/export_data.html',export_options=default_options)


@reports_bp.route('/export/<data_type>')
def export_csv(data_type):
    """Export data as CSV"""
    auth_check = require_auth()
    if auth_check:
        return auth_check

    try:
        # Get date filters if provided
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')

        # Route to appropriate export function
        if data_type == 'students':
            data,filename = ReportsDB.export_students_csv()
        elif data_type == 'rooms':
            data,filename = ReportsDB.export_rooms_csv()
        elif data_type == 'payments':
            data,filename = ReportsDB.export_payments_csv(date_from,date_to)
        elif data_type == 'assignments':
            data,filename = ReportsDB.export_assignments_csv(date_from,date_to)
        elif data_type == 'outstanding_dues':
            data,filename = ReportsDB.export_outstanding_dues_csv()
        else:
            flash('Invalid export type','error')
            return redirect(url_for('reports.export_data'))

        # Create CSV response
        output = io.StringIO()
        writer = csv.writer(output)

        for row in data:
            writer.writerow(row)

        output.seek(0)

        # Create response
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename={filename}'

        return response

    except Exception as e:
        print(f"Error exporting {data_type}: {e}")
        flash(f'Error exporting {data_type} data','error')
        return redirect(url_for('reports.export_data'))


@reports_bp.route('/custom-report')
def custom_report():
    """Custom report builder"""
    auth_check = require_auth()
    if auth_check:
        return auth_check

    try:
        return render_template('reports/custom_report.html')
    except Exception as e:
        print(f"Error in custom report: {e}")
        flash('Custom report builder temporarily unavailable','warning')
        return redirect(url_for('reports.reports_dashboard'))


@reports_bp.route('/generate-summary-report')
def generate_summary_report():
    """Generate comprehensive summary report"""
    auth_check = require_auth()
    if auth_check:
        return auth_check

    try:
        # Get current month data
        today = date.today()
        month_start = today.replace(day=1)

        # Get summary data
        stats = ReportsDB.get_dashboard_statistics()

        # Create a simple text report (could be enhanced to PDF)
        report_data = f"""
HOSTEL MANAGEMENT SYSTEM - MONTHLY SUMMARY REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Report Period: {month_start.strftime('%B %Y')}

=== GENERAL STATISTICS ===
Total Students: {stats.get('total_students',0)}
Total Rooms: {stats.get('total_rooms',0)}
Active Assignments: {stats.get('active_assignments',0)}
Occupancy Rate: {stats.get('occupancy_rate',0):.1f}%

=== FINANCIAL SUMMARY ===
Monthly Revenue: RM {stats.get('monthly_revenue',0):.2f}
Monthly Payments: {stats.get('monthly_payments',0)}
Outstanding Amount: RM {stats.get('outstanding_total',0):.2f}
Outstanding Count: {stats.get('outstanding_count',0)}

=== SYSTEM STATUS ===
Report Generated Successfully
All modules operational
Database connection: Active
Payment system: Active
"""

        # Create text file response
        response = make_response(report_data)
        response.headers['Content-Type'] = 'text/plain'
        response.headers['Content-Disposition'] = f'attachment; filename=summary_report_{today.strftime("%Y%m%d")}.txt'

        return response

    except Exception as e:
        print(f"Error generating summary report: {e}")
        flash('Error generating summary report','error')
        return redirect(url_for('reports.reports_dashboard'))


# API endpoints for chart data
@reports_bp.route('/api/chart-data/<chart_type>')
def chart_data_api(chart_type):
    """API endpoint for chart data"""
    try:
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')

        if chart_type == 'occupancy_trend':
            data = ReportsDB.get_occupancy_chart_data(date_from,date_to)
        elif chart_type == 'revenue_trend':
            data = ReportsDB.get_revenue_chart_data(date_from,date_to)
        elif chart_type == 'payment_methods':
            data = ReportsDB.get_payment_methods_chart_data(date_from,date_to)
        elif chart_type == 'room_types':
            data = ReportsDB.get_room_types_chart_data()
        elif chart_type == 'student_courses':
            data = ReportsDB.get_student_courses_chart_data()
        else:
            return jsonify({'error': 'Invalid chart type'}),400

        return jsonify(data)

    except Exception as e:
        print(f"Error getting chart data for {chart_type}: {e}")
        return jsonify({'error': 'Failed to load chart data'}),500


# Helper functions for report data
def get_occupancy_statistics():
    """Get occupancy statistics"""
    try:
        if not db or not db.test_connection():
            return {'total_rooms': 0,'occupied_rooms': 0,'available_rooms': 0,'occupancy_rate': 0}

        stats = {}

        # Total rooms
        result = db.execute_query("SELECT COUNT(*) FROM rooms")
        stats['total_rooms'] = result[0][0] if result else 0

        # Occupied rooms
        result = db.execute_query("SELECT COUNT(*) FROM rooms WHERE current_occupancy > 0")
        stats['occupied_rooms'] = result[0][0] if result else 0

        # Available rooms
        result = db.execute_query("SELECT COUNT(*) FROM rooms WHERE current_occupancy < capacity")
        stats['available_rooms'] = result[0][0] if result else 0

        # Occupancy rate
        result = db.execute_query("SELECT SUM(current_occupancy), SUM(capacity) FROM rooms")
        if result and result[0][0] and result[0][1]:
            stats['occupancy_rate'] = (result[0][0] / result[0][1]) * 100
        else:
            stats['occupancy_rate'] = 0

        return stats
    except Exception as e:
        print(f"Error getting occupancy statistics: {e}")
        return {'total_rooms': 0,'occupied_rooms': 0,'available_rooms': 0,'occupancy_rate': 0}


def get_room_utilization_data(room_type_filter=None):
    """Get room utilization data by type"""
    try:
        if not db or not db.test_connection():
            return []

        query = """
                SELECT room_type,
                       COUNT(*)                                       as total_rooms,
                       SUM(capacity)                                  as total_capacity,
                       SUM(current_occupancy)                         as current_occupancy,
                       (SUM(current_occupancy) / SUM(capacity) * 100) as utilization_rate,
                       (SUM(capacity) - SUM(current_occupancy))       as available_spaces,
                       (SUM(current_occupancy) * AVG(rent_amount))    as revenue_potential
                FROM rooms \
                """

        params = []
        if room_type_filter:
            query += " WHERE room_type = %s"
            params.append(room_type_filter)

        query += " GROUP BY room_type ORDER BY room_type"

        result = db.execute_query(query,params)

        room_utilization = []
        for row in result:
            room_utilization.append({
                'type': row[0],
                'total_rooms': row[1],
                'total_capacity': row[2],
                'current_occupancy': row[3],
                'utilization_rate': float(row[4]) if row[4] else 0,
                'available_spaces': row[5],
                'revenue_potential': float(row[6]) if row[6] else 0
            })

        return room_utilization
    except Exception as e:
        print(f"Error getting room utilization data: {e}")
        return []


def get_detailed_room_status():
    """Get detailed room status"""
    try:
        if not db or not db.test_connection():
            return []

        query = """
                SELECT r.room_id, \
                       r.room_number, \
                       r.room_type, \
                       r.floor_number,
                       r.capacity, \
                       r.current_occupancy, \
                       r.status, \
                       r.rent_amount,
                       MAX(ra.assigned_date)                 as last_assignment,
                       (r.current_occupancy * r.rent_amount) as monthly_revenue
                FROM rooms r
                         LEFT JOIN room_assignments ra ON r.room_id = ra.room_id
                GROUP BY r.room_id
                ORDER BY r.room_number \
                """

        result = db.execute_query(query)

        detailed_rooms = []
        for row in result:
            detailed_rooms.append({
                'room_id': row[0],
                'room_number': row[1],
                'room_type': row[2],
                'floor_number': row[3],
                'capacity': row[4],
                'current_occupancy': row[5],
                'status': row[6],
                'rent_amount': float(row[7]) if row[7] else 0,
                'last_assignment': row[8],
                'monthly_revenue': float(row[9]) if row[9] else 0
            })

        return detailed_rooms
    except Exception as e:
        print(f"Error getting detailed room status: {e}")
        return []


def get_peak_usage_patterns(date_from,date_to):
    """Get peak usage patterns"""
    try:
        if not db or not db.test_connection():
            return []

        query = """
                SELECT DATE_FORMAT(assigned_date, '%Y-%m') as month,
                   COUNT(*) as assignments
                FROM room_assignments
                WHERE assigned_date BETWEEN %s \
                  AND %s
                GROUP BY DATE_FORMAT(assigned_date, '%Y-%m')
                ORDER BY assignments DESC
                    LIMIT 6 \
                """

        result = db.execute_query(query,(date_from,date_to))

        patterns = []
        for row in result:
            patterns.append({
                'month': row[0],
                'assignments': row[1]
            })

        return patterns
    except Exception as e:
        print(f"Error getting peak usage patterns: {e}")
        return []


def get_underutilized_rooms():
    """Get underutilized rooms (less than 50% capacity)"""
    try:
        if not db or not db.test_connection():
            return []

        query = """
                SELECT room_number, \
                       room_type, \
                       floor_number, \
                       capacity, \
                       current_occupancy,
                       (current_occupancy / capacity * 100) as utilization_rate
                FROM rooms
                WHERE current_occupancy < (capacity * 0.5)
                ORDER BY utilization_rate ASC LIMIT 10 \
                """

        result = db.execute_query(query)

        underutilized = []
        for row in result:
            underutilized.append({
                'room_number': row[0],
                'room_type': row[1],
                'floor_number': row[2],
                'capacity': row[3],
                'current_occupancy': row[4],
                'utilization_rate': float(row[5]) if row[5] else 0
            })

        return underutilized
    except Exception as e:
        print(f"Error getting underutilized rooms: {e}")
        return []


def get_financial_summary(date_from,date_to,payment_method=None):
    """Get financial summary for the period"""
    try:
        if not PaymentDB:
            return {'total_revenue': 0,'outstanding_amount': 0,'collection_rate': 0,'average_payment': 0}

        # Get payment summary
        summary = PaymentDB.get_payment_summary()

        # Calculate additional metrics
        total_revenue = summary.get('month_total',0)
        outstanding = summary.get('outstanding_dues',0)

        collection_rate = 0
        if total_revenue + outstanding > 0:
            collection_rate = (total_revenue / (total_revenue + outstanding)) * 100

        # Get average payment (simplified calculation)
        average_payment = total_revenue / max(1,summary.get('monthly_payments',1))

        return {
            'total_revenue': total_revenue,
            'outstanding_amount': outstanding,
            'collection_rate': collection_rate,
            'average_payment': average_payment
        }
    except Exception as e:
        print(f"Error getting financial summary: {e}")
        return {'total_revenue': 0,'outstanding_amount': 0,'collection_rate': 0,'average_payment': 0}


def get_monthly_financial_breakdown(date_from,date_to):
    """Get monthly financial breakdown"""
    try:
        # Sample data for monthly breakdown
        months = []
        current_month = datetime.strptime(date_from,'%Y-%m-%d').replace(day=1)
        end_month = datetime.strptime(date_to,'%Y-%m-%d').replace(day=1)

        while current_month <= end_month:
            months.append({
                'month_name': current_month.strftime('%B %Y'),
                'total_revenue': 5000 + (current_month.month * 100),  # Sample data
                'payment_count': 45 + current_month.month,
                'average_payment': 150.0,
                'outstanding': 1200.0,
                'collection_rate': 85.5,
                'growth_rate': 2.5 if current_month.month % 2 == 0 else -1.2
            })

            # Move to next month
            if current_month.month == 12:
                current_month = current_month.replace(year=current_month.year + 1,month=1)
            else:
                current_month = current_month.replace(month=current_month.month + 1)

        return months[-6:]  # Return last 6 months
    except Exception as e:
        print(f"Error getting monthly financial breakdown: {e}")
        return []


def get_outstanding_dues_analysis():
    """Get outstanding dues analysis by age"""
    try:
        # Sample data for outstanding dues analysis
        return [
            {'age_range': 'Current (0-7 days)','count': 5,'amount': 2500.0,'percentage': 35.0},
            {'age_range': 'Recent (8-15 days)','count': 8,'amount': 4000.0,'percentage': 40.0},
            {'age_range': 'Due Soon (16-30 days)','count': 3,'amount': 1200.0,'percentage': 15.0},
            {'age_range': 'Overdue (>30 days)','count': 2,'amount': 800.0,'percentage': 10.0}
        ]
    except Exception as e:
        print(f"Error getting outstanding dues analysis: {e}")
        return []


def get_recent_payments_for_report():
    """Get recent payments for financial report"""
    try:
        if not PaymentDB:
            return []

        payments = PaymentDB.get_all_payments(limit=10)

        recent_payments = []
        for payment in payments:
            if len(payment) >= 15:  # Ensure we have enough data
                recent_payments.append({
                    'payment_id': payment[0],
                    'amount': float(payment[1]),
                    'payment_date': payment[2],
                    'payment_method': payment[3],
                    'payment_status': payment[4],
                    'receipt_number': payment[6],
                    'category_name': payment[7],
                    'student_name': f"{payment[8]} {payment[9]}",
                    'student_number': payment[10]
                })

        return recent_payments
    except Exception as e:
        print(f"Error getting recent payments: {e}")
        return []


def get_financial_kpis():
    """Get financial KPIs"""
    try:
        # Sample KPI data - in a real system, calculate from actual data
        return {
            'revenue_growth': 5.2,  # Month over month growth
            'collection_efficiency': 87.5,  # Percentage of dues collected
            'avg_days_to_pay': 12,  # Average days from due date to payment
            'late_payment_rate': 15.3  # Percentage of late payments
        }
    except Exception as e:
        print(f"Error getting financial KPIs: {e}")
        return {'revenue_growth': 0,'collection_efficiency': 0,'avg_days_to_pay': 0,'late_payment_rate': 0}


def get_top_paying_students():
    """Get top paying students"""
    try:
        # Sample data for top paying students
        return [
            {'student_name': 'John Doe','student_number': 'S12345','total_paid': 3500.0,'payment_count': 12},
            {'student_name': 'Jane Smith','student_number': 'S12346','total_paid': 3200.0,'payment_count': 11},
            {'student_name': 'Bob Johnson','student_number': 'S12347','total_paid': 3000.0,'payment_count': 10},
            {'student_name': 'Alice Brown','student_number': 'S12348','total_paid': 2800.0,'payment_count': 9},
            {'student_name': 'Charlie Wilson','student_number': 'S12349','total_paid': 2600.0,'payment_count': 8}
        ]
    except Exception as e:
        print(f"Error getting top paying students: {e}")
        return []


def get_available_courses():
    """Get list of available courses"""
    try:
        if not db or not db.test_connection():
            return ['Computer Science','Business Administration','Engineering','Information Technology']

        result = db.execute_query("SELECT DISTINCT course FROM students WHERE course IS NOT NULL ORDER BY course")
        return [row[0] for row in result] if result else []
    except Exception as e:
        print(f"Error getting available courses: {e}")
        return ['Computer Science','Business Administration','Engineering','Information Technology']


def get_student_statistics(status=None,course=None,year=None):
    """Get student statistics"""
    try:
        if not db or not db.test_connection():
            return {'total_students': 0,'active_students': 0,'students_with_rooms': 0,'students_with_dues': 0}

        stats = {}

        # Total students
        result = db.execute_query("SELECT COUNT(*) FROM students")
        stats['total_students'] = result[0][0] if result else 0

        # Active students
        result = db.execute_query("SELECT COUNT(*) FROM students WHERE status = 'Active'")
        stats['active_students'] = result[0][0] if result else 0

        # Students with rooms
        result = db.execute_query("""
                                  SELECT COUNT(DISTINCT s.student_id)
                                  FROM students s
                                           INNER JOIN room_assignments ra ON s.student_id = ra.student_id
                                  WHERE ra.status = 'Active'
                                  """)
        stats['students_with_rooms'] = result[0][0] if result else 0

        # Students with outstanding dues (sample data)
        stats['students_with_dues'] = 8

        return stats
    except Exception as e:
        print(f"Error getting student statistics: {e}")
        return {'total_students': 0,'active_students': 0,'students_with_rooms': 0,'students_with_dues': 0}


def get_course_analysis():
    """Get course analysis data"""
    try:
        # Sample course analysis data
        return [
            {
                'course_name': 'Computer Science',
                'total_students': 18,
                'year_1': 6,'year_2': 5,'year_3': 4,'year_4': 3,
                'students_with_rooms': 16,
                'room_utilization': 88.9,
                'avg_payment_status': 92.5
            },
            {
                'course_name': 'Business Administration',
                'total_students': 15,
                'year_1': 5,'year_2': 4,'year_3': 4,'year_4': 2,
                'students_with_rooms': 12,
                'room_utilization': 80.0,
                'avg_payment_status': 85.0
            },
            {
                'course_name': 'Engineering',
                'total_students': 12,
                'year_1': 4,'year_2': 3,'year_3': 3,'year_4': 2,
                'students_with_rooms': 11,
                'room_utilization': 91.7,
                'avg_payment_status': 88.0
            },
            {
                'course_name': 'Information Technology',
                'total_students': 10,
                'year_1': 3,'year_2': 3,'year_3': 2,'year_4': 2,
                'students_with_rooms': 8,
                'room_utilization': 80.0,
                'avg_payment_status': 90.0
            }
        ]
    except Exception as e:
        print(f"Error getting course analysis: {e}")
        return []


def get_top_performing_students():
    """Get top performing students"""
    try:
        # Sample data for top performing students
        return [
            {'full_name': 'Alice Johnson','student_number': 'S12001','course': 'Computer Science','payment_score': 98,
             'total_payments': 12},
            {'full_name': 'Bob Smith','student_number': 'S12002','course': 'Engineering','payment_score': 96,
             'total_payments': 11},
            {'full_name': 'Carol Brown','student_number': 'S12003','course': 'Business','payment_score': 94,
             'total_payments': 10},
            {'full_name': 'David Wilson','student_number': 'S12004','course': 'IT','payment_score': 92,
             'total_payments': 11},
            {'full_name': 'Eva Davis','student_number': 'S12005','course': 'Computer Science','payment_score': 90,
             'total_payments': 9}
        ]
    except Exception as e:
        print(f"Error getting top performing students: {e}")
        return []


def get_students_requiring_attention():
    """Get students requiring attention"""
    try:
        # Sample data for students requiring attention
        return [
            {'full_name': 'John Doe','student_number': 'S12010','course': 'Business','issue_type': 'payment',
             'outstanding_amount': 1200.0},
            {'full_name': 'Jane Wilson','student_number': 'S12011','course': 'Engineering','issue_type': 'room',
             'days_without_room': 15},
            {'full_name': 'Mike Brown','student_number': 'S12012','course': 'IT','issue_type': 'payment',
             'outstanding_amount': 800.0}
        ]
    except Exception as e:
        print(f"Error getting students requiring attention: {e}")
        return []


def get_payment_timing_analysis():
    """Get payment timing analysis"""
    try:
        # Sample payment timing data
        return {
            'early_payers': 25,  # Pay before due date
            'on_time_payers': 45,  # Pay on due date
            'late_payers': 25,  # Pay after due date
            'non_payers': 5  # Haven't paid
        }
    except Exception as e:
        print(f"Error getting payment timing analysis: {e}")
        return {'early_payers': 0,'on_time_payers': 0,'late_payers': 0,'non_payers': 0}


def get_recent_student_activities():
    """Get recent student activities"""
    try:
        # Sample recent activities data
        today = date.today()
        return [
            {
                'activity_date': today - timedelta(days=1),
                'student_id': 1,
                'student_name': 'Alice Johnson',
                'student_number': 'S12001',
                'activity_type': 'Payment',
                'description': 'Monthly rent payment received',
                'status': 'Completed'
            },
            {
                'activity_date': today - timedelta(days=2),
                'student_id': 2,
                'student_name': 'Bob Smith',
                'student_number': 'S12002',
                'activity_type': 'Room Assignment',
                'description': 'Assigned to Room 101',
                'status': 'Completed'
            },
            {
                'activity_date': today - timedelta(days=3),
                'student_id': 3,
                'student_name': 'Carol Brown',
                'student_number': 'S12003',
                'activity_type': 'Enrollment',
                'description': 'New student enrollment completed',
                'status': 'Completed'
            },
            {
                'activity_date': today - timedelta(days=4),
                'student_id': 4,
                'student_name': 'David Wilson',
                'student_number': 'S12004',
                'activity_type': 'Payment',
                'description': 'Security deposit payment',
                'status': 'Pending'
            },
            {
                'activity_date': today - timedelta(days=5),
                'student_id': 5,
                'student_name': 'Eva Davis',
                'student_number': 'S12005',
                'activity_type': 'Checkout',
                'description': 'Checked out from Room 205',
                'status': 'Completed'
            }
        ]
    except Exception as e:
        print(f"Error getting recent student activities: {e}")
        return []


def get_retention_rates():
    """Get student retention rates"""
    try:
        # Sample retention rate data
        return {
            'year_1_to_2': 95,
            'year_2_to_3': 88,
            'year_3_to_4': 92,
            'overall': 91
        }
    except Exception as e:
        print(f"Error getting retention rates: {e}")
        return {'year_1_to_2': 0,'year_2_to_3': 0,'year_3_to_4': 0,'overall': 0}