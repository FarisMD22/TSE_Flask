from flask import Blueprint,render_template,request,redirect,url_for,flash,session
from models.database import db,StudentDB
from datetime import datetime

students_bp = Blueprint('students',__name__,url_prefix='/students')


def require_login():
    """Check if user is logged in"""
    if 'user_id' not in session:
        flash('Please log in to access this page.','error')
        return redirect(url_for('login'))
    return None


@students_bp.route('/')
def list_students():
    """Display list of all students with search and filter functionality"""
    login_check = require_login()
    if login_check:
        return login_check

    # Get search parameters
    search = request.args.get('search','').strip()
    status_filter = request.args.get('status','all')

    try:
        if StudentDB:
            # Use StudentDB class if available
            students = StudentDB.search_students(search,status_filter)
        else:
            # Direct database query fallback
            if search and status_filter != 'all':
                query = """
                        SELECT s.student_id, \
                               s.student_number, \
                               s.first_name, \
                               s.last_name, \
                               s.email, \
                               s.phone,
                               s.address, \
                               s.guardian_name, \
                               s.guardian_phone, \
                               s.course, \
                               s.year_of_study,
                               s.date_joined, \
                               s.status, \
                               s.created_at, \
                               r.room_number
                        FROM students s
                                 LEFT JOIN room_assignments ra ON s.student_id = ra.student_id AND ra.status = 'Active'
                                 LEFT JOIN rooms r ON ra.room_id = r.room_id
                        WHERE (s.first_name LIKE %s OR s.last_name LIKE %s OR s.student_number LIKE %s OR \
                               s.email LIKE %s)
                          AND s.status = %s
                        ORDER BY s.created_at DESC \
                        """
                search_term = f"%{search}%"
                students = db.execute_query(query,(search_term,search_term,search_term,search_term,status_filter))
            elif search:
                query = """
                        SELECT s.student_id, \
                               s.student_number, \
                               s.first_name, \
                               s.last_name, \
                               s.email, \
                               s.phone,
                               s.address, \
                               s.guardian_name, \
                               s.guardian_phone, \
                               s.course, \
                               s.year_of_study,
                               s.date_joined, \
                               s.status, \
                               s.created_at, \
                               r.room_number
                        FROM students s
                                 LEFT JOIN room_assignments ra ON s.student_id = ra.student_id AND ra.status = 'Active'
                                 LEFT JOIN rooms r ON ra.room_id = r.room_id
                        WHERE s.first_name LIKE %s \
                           OR s.last_name LIKE %s \
                           OR s.student_number LIKE %s \
                           OR s.email LIKE %s
                        ORDER BY s.created_at DESC \
                        """
                search_term = f"%{search}%"
                students = db.execute_query(query,(search_term,search_term,search_term,search_term))
            elif status_filter != 'all':
                query = """
                        SELECT s.student_id, \
                               s.student_number, \
                               s.first_name, \
                               s.last_name, \
                               s.email, \
                               s.phone,
                               s.address, \
                               s.guardian_name, \
                               s.guardian_phone, \
                               s.course, \
                               s.year_of_study,
                               s.date_joined, \
                               s.status, \
                               s.created_at, \
                               r.room_number
                        FROM students s
                                 LEFT JOIN room_assignments ra ON s.student_id = ra.student_id AND ra.status = 'Active'
                                 LEFT JOIN rooms r ON ra.room_id = r.room_id
                        WHERE s.status = %s
                        ORDER BY s.created_at DESC \
                        """
                students = db.execute_query(query,(status_filter,))
            else:
                query = """
                        SELECT s.student_id, \
                               s.student_number, \
                               s.first_name, \
                               s.last_name, \
                               s.email, \
                               s.phone,
                               s.address, \
                               s.guardian_name, \
                               s.guardian_phone, \
                               s.course, \
                               s.year_of_study,
                               s.date_joined, \
                               s.status, \
                               s.created_at, \
                               r.room_number
                        FROM students s
                                 LEFT JOIN room_assignments ra ON s.student_id = ra.student_id AND ra.status = 'Active'
                                 LEFT JOIN rooms r ON ra.room_id = r.room_id
                        ORDER BY s.created_at DESC \
                        """
                students = db.execute_query(query)

        print(f"✅ Found {len(students) if students else 0} students")
        return render_template('students/list.html',
                               students=students or [],
                               search=search,
                               status_filter=status_filter)

    except Exception as e:
        print(f"❌ Error loading students: {e}")
        flash('Error loading student data. Please try again.','error')
        return render_template('students/list.html',
                               students=[],
                               search=search,
                               status_filter=status_filter)

@students_bp.route('/add',methods=['GET','POST'])
def add_student():
    """Add new student"""
    login_check = require_login()
    if login_check:
        return login_check

    if request.method == 'POST':
        try:
            # Get form data
            student_data = {
                'student_number': request.form.get('student_number','').strip(),
                'first_name': request.form.get('first_name','').strip(),
                'last_name': request.form.get('last_name','').strip(),
                'email': request.form.get('email','').strip(),
                'phone': request.form.get('phone','').strip(),
                'address': request.form.get('address','').strip(),
                'guardian_name': request.form.get('guardian_name','').strip(),
                'guardian_phone': request.form.get('guardian_phone','').strip(),
                'course': request.form.get('course','').strip(),
                'year_of_study': request.form.get('year_of_study') or None,
                'date_joined': request.form.get('date_joined') or datetime.now().date().isoformat(),
                'status': request.form.get('status','Active')
            }

            # Validate required fields
            if not all([student_data['student_number'],student_data['first_name'],
                        student_data['last_name'],student_data['email']]):
                flash('Please fill in all required fields.','error')
                return render_template('students/add.html',student=student_data)

            # Check if student number already exists
            existing = db.execute_query(
                "SELECT student_id FROM students WHERE student_number = %s",
                (student_data['student_number'],)
            )
            if existing:
                flash('Student number already exists. Please use a different number.','error')
                return render_template('students/add.html',student=student_data)

            # Check if email already exists
            existing = db.execute_query(
                "SELECT student_id FROM students WHERE email = %s",
                (student_data['email'],)
            )
            if existing:
                flash('Email already exists. Please use a different email.','error')
                return render_template('students/add.html',student=student_data)

            # Insert student
            if StudentDB:
                student_id = StudentDB.add_student(student_data)
            else:
                query = """
                        INSERT INTO students (student_number, first_name, last_name, email, phone, address,
                                              guardian_name, guardian_phone, course, year_of_study, date_joined, status)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) \
                        """
                values = (
                    student_data['student_number'],student_data['first_name'],student_data['last_name'],
                    student_data['email'],student_data['phone'],student_data['address'],
                    student_data['guardian_name'],student_data['guardian_phone'],student_data['course'],
                    int(student_data['year_of_study']) if student_data['year_of_study'] else None,
                    student_data['date_joined'],student_data['status']
                )
                student_id = db.execute_insert(query,values)

            if student_id:
                flash(f'Student {student_data["first_name"]} {student_data["last_name"]} added successfully!','success')
                return redirect(url_for('students.view_student',student_id=student_id))
            else:
                flash('Error adding student. Please try again.','error')

        except Exception as e:
            print(f"Error adding student: {e}")
            flash('Error adding student. Please check your input and try again.','error')

    return render_template('students/add.html',student={})


@students_bp.route('/<int:student_id>')
def view_student(student_id):
    """View student details"""
    login_check = require_login()
    if login_check:
        return login_check

    try:
        # Get student details with room information
        if StudentDB:
            student = StudentDB.get_student_by_id(student_id)
        else:
            query = """
                    SELECT s.student_id, \
                           s.student_number, \
                           s.first_name, \
                           s.last_name, \
                           s.email, \
                           s.phone,
                           s.address, \
                           s.guardian_name, \
                           s.guardian_phone, \
                           s.course, \
                           s.year_of_study,
                           s.date_joined, \
                           s.status, \
                           s.created_at, \
                           r.room_number, \
                           ra.assigned_date
                    FROM students s
                             LEFT JOIN room_assignments ra ON s.student_id = ra.student_id AND ra.status = 'Active'
                             LEFT JOIN rooms r ON ra.room_id = r.room_id
                    WHERE s.student_id = %s \
                    """
            result = db.execute_query(query,(student_id,))
            student = result[0] if result else None

        if not student:
            flash('Student not found.','error')
            return redirect(url_for('students.list_students'))

        # Get payment history
        payment_query = """
                        SELECT payment_id, amount, payment_date, payment_type, payment_method, receipt_number, status
                        FROM fee_payments
                        WHERE student_id = %s
                        ORDER BY payment_date DESC LIMIT 5 \
                        """
        payments = db.execute_query(payment_query,(student_id,))

        return render_template('students/view.html',student=student,payments=payments or [])

    except Exception as e:
        print(f"Error loading student: {e}")
        flash('Error loading student details.','error')
        return redirect(url_for('students.list_students'))


@students_bp.route('/debug')
def debug_students():
    """Debug route to test if students blueprint is working"""
    try:
        # Test database connection
        result = db.execute_query("SELECT COUNT(*) FROM students")
        count = result[0][0] if result else 0

        return f"""
        <h1>Debug Students Route</h1>
        <p>Blueprint is working!</p>
        <p>Students in database: {count}</p>
        <p><a href="/students">Try students list</a></p>
        <p><a href="/students/1">Try student view</a></p>
        """
    except Exception as e:
        return f"Error: {e}"

@students_bp.route('/<int:student_id>/edit',methods=['GET','POST'])
def edit_student(student_id):
    """Edit student details"""
    login_check = require_login()
    if login_check:
        return login_check

    try:
        # Get current student data
        if StudentDB:
            student = StudentDB.get_student_by_id(student_id)
        else:
            query = """
                    SELECT student_id, \
                           student_number, \
                           first_name, \
                           last_name, \
                           email, \
                           phone, \
                           address,
                           guardian_name, \
                           guardian_phone, \
                           course, \
                           year_of_study, \
                           date_joined, \
                           status, \
                           created_at
                    FROM students \
                    WHERE student_id = %s \
                    """
            result = db.execute_query(query,(student_id,))
            student = result[0] if result else None

        if not student:
            flash('Student not found.','error')
            return redirect(url_for('students.list_students'))

        if request.method == 'POST':
            # Get form data
            student_data = {
                'student_number': request.form.get('student_number','').strip(),
                'first_name': request.form.get('first_name','').strip(),
                'last_name': request.form.get('last_name','').strip(),
                'email': request.form.get('email','').strip(),
                'phone': request.form.get('phone','').strip(),
                'address': request.form.get('address','').strip(),
                'guardian_name': request.form.get('guardian_name','').strip(),
                'guardian_phone': request.form.get('guardian_phone','').strip(),
                'course': request.form.get('course','').strip(),
                'year_of_study': request.form.get('year_of_study') or None,
                'status': request.form.get('status','Active')
            }

            # Validate required fields
            if not all([student_data['student_number'],student_data['first_name'],
                        student_data['last_name'],student_data['email']]):
                flash('Please fill in all required fields.','error')
                return render_template('students/edit.html',student=list(student_data.values()))

            # Check if student number exists for other students
            existing = db.execute_query(
                "SELECT student_id FROM students WHERE student_number = %s AND student_id != %s",
                (student_data['student_number'],student_id)
            )
            if existing:
                flash('Student number already exists. Please use a different number.','error')
                return render_template('students/edit.html',student=student)

            # Check if email exists for other students
            existing = db.execute_query(
                "SELECT student_id FROM students WHERE email = %s AND student_id != %s",
                (student_data['email'],student_id)
            )
            if existing:
                flash('Email already exists. Please use a different email.','error')
                return render_template('students/edit.html',student=student)

            # Update student
            if StudentDB:
                success = StudentDB.update_student(student_id,student_data)
            else:
                query = """
                        UPDATE students \
                        SET student_number = %s, \
                            first_name     = %s, \
                            last_name      = %s, \
                            email          = %s, \
                            phone          = %s, \
                            address        = %s, \
                            guardian_name  = %s, \
                            guardian_phone = %s, \
                            course         = %s, \
                            year_of_study  = %s, \
                            status         = %s
                        WHERE student_id = %s \
                        """
                values = (
                    student_data['student_number'],student_data['first_name'],student_data['last_name'],
                    student_data['email'],student_data['phone'],student_data['address'],
                    student_data['guardian_name'],student_data['guardian_phone'],student_data['course'],
                    int(student_data['year_of_study']) if student_data['year_of_study'] else None,
                    student_data['status'],student_id
                )
                success = db.execute_update(query,values)

            if success:
                flash(f'Student {student_data["first_name"]} {student_data["last_name"]} updated successfully!',
                      'success')
                return redirect(url_for('students.view_student',student_id=student_id))
            else:
                flash('Error updating student. Please try again.','error')

        return render_template('students/edit.html',student=student)

    except Exception as e:
        print(f"Error editing student: {e}")
        flash('Error loading student for editing.','error')
        return redirect(url_for('students.list_students'))


@students_bp.route('/<int:student_id>/delete',methods=['POST'])
def delete_student(student_id):
    """Delete student"""
    login_check = require_login()
    if login_check:
        return login_check

    try:
        # Get student name for confirmation message
        student_query = "SELECT first_name, last_name FROM students WHERE student_id = %s"
        result = db.execute_query(student_query,(student_id,))

        if not result:
            flash('Student not found.','error')
            return redirect(url_for('students.list_students'))

        student_name = f"{result[0][0]} {result[0][1]}"

        # Check if student has active room assignment
        room_check = db.execute_query(
            "SELECT room_id FROM room_assignments WHERE student_id = %s AND status = 'Active'",
            (student_id,)
        )

        if room_check:
            flash(
                f'Cannot delete {student_name}. Student has an active room assignment. Please check out the student first.',
                'error')
            return redirect(url_for('students.view_student',student_id=student_id))

        # Delete student (this will cascade delete related records due to foreign key constraints)
        if StudentDB:
            success = StudentDB.delete_student(student_id)
        else:
            success = db.execute_update("DELETE FROM students WHERE student_id = %s",(student_id,))

        if success:
            flash(f'Student {student_name} deleted successfully.','success')
        else:
            flash('Error deleting student. Please try again.','error')

    except Exception as e:
        print(f"Error deleting student: {e}")
        flash('Error deleting student. Please try again.','error')

    return redirect(url_for('students.list_students'))