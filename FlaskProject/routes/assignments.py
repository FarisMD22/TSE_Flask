from flask import Blueprint,render_template,request,redirect,url_for,flash,session
from models.database import db,AssignmentDB,StudentDB
from datetime import datetime,date

# Create assignments blueprint
assignments_bp = Blueprint('assignments',__name__,url_prefix='/assignments')


@assignments_bp.route('/')
def list_assignments():
    """Display all room assignments"""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    try:
        # Get filter parameters
        status_filter = request.args.get('status','all')
        search = request.args.get('search','').strip()

        if status_filter == 'active':
            assignments = AssignmentDB.get_active_assignments()
        else:
            assignments = AssignmentDB.get_all_assignments()

        # Apply search filter
        if search:
            assignments = [a for a in assignments if (
                    search.lower() in f"{a[7]} {a[8]}".lower() or  # student name
                    search.lower() in a[6].lower() or  # student number
                    search.lower() in a[11].lower()  # room number
            )]

        # FIX: Convert date objects to strings for template
        processed_assignments = []
        for assignment in assignments:
            assignment_dict = {
                'assignment_id': assignment[0],
                'student_id': assignment[1],
                'room_id': assignment[2],
                'assigned_date': assignment[3].strftime('%Y-%m-%d') if assignment[3] else None,
                'checkout_date': assignment[4].strftime('%Y-%m-%d') if assignment[4] else None,
                'status': assignment[5],
                'student_number': assignment[6],
                'first_name': assignment[7],
                'last_name': assignment[8],
                'email': assignment[9],
                'phone': assignment[10],
                'room_number': assignment[11],
                'room_type': assignment[12],
                'capacity': assignment[13],
                'rent_amount': assignment[14],
                'created_at': assignment[15].strftime('%Y-%m-%d %H:%M:%S') if assignment[15] else None
            }
            processed_assignments.append(assignment_dict)

        # Get statistics
        stats = AssignmentDB.get_occupancy_statistics()

        return render_template('assignments/list.html',
                               assignments=processed_assignments,
                               stats=stats,
                               status_filter=status_filter,
                               search=search)
    except Exception as e:
        print(f"Error in list_assignments: {e}")
        flash('Error loading assignments','error')
        return redirect(url_for('dashboard'))


@assignments_bp.route('/assign',methods=['GET','POST'])
# Debug the assignment form issue
# Add this debug code to your assign_student() method in assignments.py

@assignments_bp.route('/assign',methods=['GET','POST'])
def assign_student():
    """Assign a student to a room"""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        try:
            # DEBUG: Print all form data to see what we're receiving
            print("=== FORM DATA DEBUG ===")
            print(f"All form data: {dict(request.form)}")
            print(f"Form keys: {list(request.form.keys())}")

            student_id = request.form.get('student_id')
            room_id = request.form.get('room_id')
            assigned_date = request.form.get('assigned_date')

            # DEBUG: Print individual field values
            print(f"student_id: '{student_id}' (type: {type(student_id)})")
            print(f"room_id: '{room_id}' (type: {type(room_id)})")
            print(f"assigned_date: '{assigned_date}' (type: {type(assigned_date)})")
            print("=====================")

            # Check for empty strings and None values
            if not student_id or student_id.strip() == '':
                print("ERROR: student_id is empty or None")
            if not room_id or room_id.strip() == '':
                print("ERROR: room_id is empty or None")
            if not assigned_date or assigned_date.strip() == '':
                print("ERROR: assigned_date is empty or None")

            # Validation - check for both None and empty strings
            if not all([student_id,room_id,assigned_date]) or not all(
                    [str(student_id).strip(),str(room_id).strip(),str(assigned_date).strip()]):
                print("VALIDATION FAILED: One or more fields are empty")
                flash('All fields are required','error')
                return render_template('assignments/assign.html',
                                       unassigned_students=AssignmentDB.get_unassigned_students(),
                                       available_rooms=AssignmentDB.get_available_rooms(),
                                       today=date.today().strftime('%Y-%m-%d'))

            # Convert date - FIX: Better date handling
            try:
                assigned_date_obj = datetime.strptime(assigned_date,'%Y-%m-%d').date()

                # Validate date is not in the past
                if assigned_date_obj < date.today():
                    flash('Assignment date cannot be in the past','error')
                    return render_template('assignments/assign.html',
                                           unassigned_students=AssignmentDB.get_unassigned_students(),
                                           available_rooms=AssignmentDB.get_available_rooms(),
                                           today=date.today().strftime('%Y-%m-%d'))

            except ValueError as ve:
                print(f"DATE PARSING ERROR: {ve}")
                flash('Invalid date format','error')
                return render_template('assignments/assign.html',
                                       unassigned_students=AssignmentDB.get_unassigned_students(),
                                       available_rooms=AssignmentDB.get_available_rooms(),
                                       today=date.today().strftime('%Y-%m-%d'))

            # Make assignment
            print(f"ATTEMPTING ASSIGNMENT: student_id={student_id}, room_id={room_id}, date={assigned_date_obj}")
            success,message = AssignmentDB.assign_student_to_room(
                int(student_id),int(room_id),assigned_date_obj
            )

            if success:
                flash(message,'success')
                return redirect(url_for('assignments.list_assignments'))
            else:
                flash(message,'error')

        except Exception as e:
            print(f"EXCEPTION in assign_student: {e}")
            import traceback
            traceback.print_exc()
            flash('Error creating assignment','error')

    # GET request - show assignment form
    try:
        unassigned_students = AssignmentDB.get_unassigned_students()
        available_rooms = AssignmentDB.get_available_rooms()

        print(f"DEBUG: Found {len(unassigned_students)} unassigned students")
        print(f"DEBUG: Found {len(available_rooms)} available rooms")

        return render_template('assignments/assign.html',
                               unassigned_students=unassigned_students,
                               available_rooms=available_rooms,
                               today=date.today().strftime('%Y-%m-%d'))
    except Exception as e:
        print(f"Error loading assignment form: {e}")
        flash('Error loading assignment form','error')
        return redirect(url_for('assignments.list_assignments'))

@assignments_bp.route('/checkout/<int:assignment_id>',methods=['POST'])
def checkout_student(assignment_id):
    """Check out a student from their room"""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    try:
        checkout_date_str = request.form.get('checkout_date')

        if not checkout_date_str:
            checkout_date = date.today()
        else:
            try:
                checkout_date = datetime.strptime(checkout_date_str,'%Y-%m-%d').date()
            except ValueError:
                flash('Invalid checkout date format','error')
                return redirect(url_for('assignments.list_assignments'))

        # Validate checkout date is not in the future
        if checkout_date > date.today():
            flash('Checkout date cannot be in the future','error')
            return redirect(url_for('assignments.list_assignments'))

        success,message = AssignmentDB.checkout_student(assignment_id,checkout_date)

        if success:
            flash(message,'success')
        else:
            flash(message,'error')

    except Exception as e:
        print(f"Error checking out student: {e}")
        flash('Error checking out student','error')

    return redirect(url_for('assignments.list_assignments'))


@assignments_bp.route('/transfer/<int:assignment_id>',methods=['GET','POST'])
def transfer_student(assignment_id):
    """Transfer a student to a different room"""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Get current assignment details
    try:
        current_assignment = db.execute_query(
            """SELECT ra.assignment_id,
                      ra.student_id,
                      ra.room_id,
                      ra.assigned_date,
                      s.student_number,
                      s.first_name,
                      s.last_name,
                      r.room_number,
                      r.room_type
               FROM room_assignments ra
                        INNER JOIN students s ON ra.student_id = s.student_id
                        INNER JOIN rooms r ON ra.room_id = r.room_id
               WHERE ra.assignment_id = %s
                 AND ra.status = 'Active'""",
            (assignment_id,)
        )

        if not current_assignment:
            flash('Assignment not found or not active','error')
            return redirect(url_for('assignments.list_assignments'))

        assignment = current_assignment[0]

        # FIX: Convert assignment data to dictionary with proper date handling
        assignment_dict = {
            'assignment_id': assignment[0],
            'student_id': assignment[1],
            'room_id': assignment[2],
            'assigned_date': assignment[3].strftime('%Y-%m-%d') if assignment[3] else None,
            'student_number': assignment[4],
            'first_name': assignment[5],
            'last_name': assignment[6],
            'room_number': assignment[7],
            'room_type': assignment[8]
        }

    except Exception as e:
        print(f"Error getting assignment details: {e}")
        flash('Error loading assignment details','error')
        return redirect(url_for('assignments.list_assignments'))

    if request.method == 'POST':
        try:
            new_room_id = request.form.get('new_room_id')
            transfer_date_str = request.form.get('transfer_date')

            if not all([new_room_id,transfer_date_str]):
                flash('All fields are required','error')
                return render_template('assignments/transfer.html',
                                       assignment=assignment_dict,
                                       available_rooms=AssignmentDB.get_available_rooms(),
                                       today=date.today().strftime('%Y-%m-%d'))

            # Convert and validate transfer date
            try:
                transfer_date = datetime.strptime(transfer_date_str,'%Y-%m-%d').date()

                # Validate transfer date
                if transfer_date < date.today():
                    flash('Transfer date cannot be in the past','error')
                    return render_template('assignments/transfer.html',
                                           assignment=assignment_dict,
                                           available_rooms=AssignmentDB.get_available_rooms(),
                                           today=date.today().strftime('%Y-%m-%d'))

            except ValueError:
                flash('Invalid date format','error')
                return render_template('assignments/transfer.html',
                                       assignment=assignment_dict,
                                       available_rooms=AssignmentDB.get_available_rooms(),
                                       today=date.today().strftime('%Y-%m-%d'))

            # Make transfer
            success,message = AssignmentDB.transfer_student(
                assignment_id,int(new_room_id),transfer_date
            )

            if success:
                flash(message,'success')
                return redirect(url_for('assignments.list_assignments'))
            else:
                flash(message,'error')

        except Exception as e:
            print(f"Error transferring student: {e}")
            flash('Error transferring student','error')

    # GET request or error - show transfer form
    try:
        # Get available rooms (excluding current room)
        available_rooms = [room for room in AssignmentDB.get_available_rooms()
                           if room[0] != assignment_dict['room_id']]  # Exclude current room_id

        return render_template('assignments/transfer.html',
                               assignment=assignment_dict,
                               available_rooms=available_rooms,
                               today=date.today().strftime('%Y-%m-%d'))
    except Exception as e:
        print(f"Error loading transfer form: {e}")
        flash('Error loading transfer form','error')
        return redirect(url_for('assignments.list_assignments'))


@assignments_bp.route('/history')
# REPLACE your assignment_history() method in assignments.py with this fixed version:

@assignments_bp.route('/history')
def assignment_history():
    """View assignment history"""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    try:
        student_id = request.args.get('student_id')
        room_id = request.args.get('room_id')
        limit = request.args.get('limit',50)

        history_raw = AssignmentDB.get_assignment_history(
            student_id=int(student_id) if student_id else None,
            room_id=int(room_id) if room_id else None,
            limit=int(limit) if limit else None
        )

        print(f"DEBUG: Retrieved {len(history_raw)} history records")
        if history_raw:
            print(f"DEBUG: First history record: {history_raw[0]}")
            print(f"DEBUG: History record length: {len(history_raw[0])}")

        # DON'T convert to dictionaries - keep as tuples for the template
        # The template expects tuples with this structure:
        # [0]assignment_id, [1]student_id, [2]room_id, [3]assigned_date,
        # [4]checkout_date, [5]status, [6]created_at,
        # [7]student_number, [8]first_name, [9]last_name,
        # [10]room_number, [11]room_type

        # Just handle date formatting for display
        processed_history = []
        for record in history_raw:
            try:
                # Convert to list so we can modify dates for display
                record_list = list(record)

                # Format dates for display (indices 3, 4, 6)
                if record_list[3]:  # assigned_date
                    record_list[3] = record_list[3].strftime('%Y-%m-%d')
                if record_list[4]:  # checkout_date
                    record_list[4] = record_list[4].strftime('%Y-%m-%d')
                if record_list[6]:  # created_at
                    record_list[6] = record_list[6].strftime('%Y-%m-%d %H:%M:%S')

                # Convert back to tuple for template compatibility
                processed_history.append(tuple(record_list))

            except Exception as e:
                print(f"Error processing history record {record}: {e}")
                # Skip malformed records
                continue

        print(f"DEBUG: Processed {len(processed_history)} history records successfully")

        return render_template('assignments/history.html',history=processed_history)

    except Exception as e:
        print(f"Error loading assignment history: {e}")
        import traceback
        traceback.print_exc()
        flash('Error loading assignment history','error')
        return redirect(url_for('assignments.list_assignments'))

@assignments_bp.route('/dashboard')
# REPLACE your assignment_dashboard() method with this corrected version:

@assignments_bp.route('/dashboard')
def assignment_dashboard():
    """Assignment overview dashboard"""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    try:
        # Get comprehensive statistics
        stats = AssignmentDB.get_occupancy_statistics()

        # Get recent assignments with debug info
        try:
            recent_assignments_raw = AssignmentDB.get_assignment_history(limit=10)
            print(f"DEBUG: Retrieved {len(recent_assignments_raw)} recent assignments")

            if recent_assignments_raw:
                print(f"DEBUG: First assignment: {recent_assignments_raw[0]}")
                print(f"DEBUG: Assignment tuple length: {len(recent_assignments_raw[0])}")

        except Exception as e:
            print(f"Error getting recent assignments: {e}")
            recent_assignments_raw = []

        unassigned_count = len(AssignmentDB.get_unassigned_students())
        available_rooms_count = len(AssignmentDB.get_available_rooms())

        # FIX: Safely process recent assignments - match the get_assignment_history structure
        processed_recent = []
        for assignment in recent_assignments_raw:
            try:
                # Based on get_assignment_history query, the structure should be:
                # [0]assignment_id, [1]student_id, [2]room_id, [3]assigned_date,
                # [4]checkout_date, [5]status, [6]created_at,
                # [7]student_number, [8]first_name, [9]last_name,
                # [10]room_number, [11]room_type

                assignment_dict = {
                    'assignment_id': assignment[0],
                    'student_id': assignment[1],
                    'room_id': assignment[2],
                    'assigned_date': assignment[3].strftime('%Y-%m-%d') if assignment[3] else None,
                    'checkout_date': assignment[4].strftime('%Y-%m-%d') if assignment[4] else None,
                    'status': assignment[5],
                    'created_at': assignment[6].strftime('%Y-%m-%d %H:%M:%S') if assignment[6] else None,
                    'student_number': assignment[7] if len(assignment) > 7 else 'N/A',
                    'first_name': assignment[8] if len(assignment) > 8 else 'Unknown',
                    'last_name': assignment[9] if len(assignment) > 9 else 'Student',
                    'room_number': assignment[10] if len(assignment) > 10 else 'N/A',
                    'room_type': assignment[11] if len(assignment) > 11 else 'N/A'
                }
                processed_recent.append(assignment_dict)

            except IndexError as ie:
                print(f"IndexError processing assignment {assignment}: {ie}")
                print(f"Assignment length: {len(assignment)}")
                # Skip malformed assignments
                continue
            except Exception as e:
                print(f"Error processing assignment {assignment}: {e}")
                continue

        stats.update({
            'unassigned_students': unassigned_count,
            'available_rooms': available_rooms_count,
            'recent_assignments': processed_recent
        })

        print(f"DEBUG: Processed {len(processed_recent)} assignments successfully")
        return render_template('assignments/dashboard.html',stats=stats)

    except Exception as e:
        print(f"Error loading assignment dashboard: {e}")
        import traceback
        traceback.print_exc()
        flash('Error loading assignment dashboard','error')
        return redirect(url_for('dashboard'))

# Quick assignment from student or room pages
@assignments_bp.route('/quick-assign')
def quick_assign():
    """Quick assignment with pre-selected student or room"""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    student_id = request.args.get('student_id')
    room_id = request.args.get('room_id')

    try:
        unassigned_students = AssignmentDB.get_unassigned_students()
        available_rooms = AssignmentDB.get_available_rooms()

        # Pre-select if provided
        selected_student = None
        selected_room = None

        if student_id:
            selected_student = next((s for s in unassigned_students if s[0] == int(student_id)),None)

        if room_id:
            selected_room = next((r for r in available_rooms if r[0] == int(room_id)),None)

        return render_template('assignments/assign.html',
                               unassigned_students=unassigned_students,
                               available_rooms=available_rooms,
                               selected_student=selected_student,
                               selected_room=selected_room,
                               today=date.today().strftime('%Y-%m-%d'))  # FIX: Add today's date

    except Exception as e:
        print(f"Error in quick assign: {e}")
        flash('Error loading quick assignment','error')
        return redirect(url_for('assignments.assign_student'))


# FIX: Add date filter for templates
@assignments_bp.app_template_filter('dateformat')
def dateformat(value,format='%Y-%m-%d'):
    """Format date objects for templates"""
    if value is None:
        return ""
    if isinstance(value,str):
        return value
    if isinstance(value,(datetime,date)):
        return value.strftime(format)
    return str(value)