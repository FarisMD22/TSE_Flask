from flask import Blueprint,render_template,request,redirect,url_for,flash,session
from models.payment_database import PaymentDB
from models.database import StudentDB,AssignmentDB
from datetime import datetime,date
from decimal import Decimal

payments_bp = Blueprint('payments',__name__,url_prefix='/payments')


@payments_bp.route('/')
def payment_list():
    """Display all payments"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    status_filter = request.args.get('status','All')
    payments = PaymentDB.get_all_payments(limit=100,status_filter=status_filter)

    # Format payments for display
    formatted_payments = []
    for payment in payments:
        formatted_payments.append({
            'payment_id': payment[0],
            'amount': float(payment[1]),
            'payment_date': payment[2].strftime('%Y-%m-%d') if payment[2] else None,
            'payment_method': payment[3],
            'payment_status': payment[4],
            'reference_number': payment[5],
            'receipt_number': payment[6],
            'category_name': payment[7],
            'student_name': f"{payment[8]} {payment[9]}",
            'student_number': payment[10],
            'notes': payment[11],
            'late_fee': float(payment[12]),
            'created_at': payment[13].strftime('%Y-%m-%d %H:%M') if payment[13] else None,
            'student_id': payment[14]
        })

    return render_template('payments/list.html',
                           payments=formatted_payments,
                           current_filter=status_filter)


@payments_bp.route('/add',methods=['GET','POST'])
def add_payment():
    """Add new payment"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    if request.method == 'GET':
        # Get data for form
        students = StudentDB.get_all_students()
        categories = PaymentDB.get_all_payment_categories()
        assignments = AssignmentDB.get_active_assignments()

        return render_template('payments/add.html',
                               students=students,
                               categories=categories,
                               assignments=assignments)

    # Handle POST request
    try:
        payment_data = {
            'student_id': int(request.form.get('student_id')),
            'assignment_id': int(request.form.get('assignment_id')) if request.form.get('assignment_id') else None,
            'category_id': int(request.form.get('category_id')),
            'amount': float(request.form.get('amount')),
            'payment_date': request.form.get('payment_date'),
            'payment_method': request.form.get('payment_method'),
            'payment_status': request.form.get('payment_status','Completed'),
            'due_date': request.form.get('due_date') if request.form.get('due_date') else None,
            'late_fee': float(request.form.get('late_fee',0)),
            'notes': request.form.get('notes',''),
            'processed_by': session.get('full_name','Staff')
        }

        # Validate required fields
        if not all([payment_data['student_id'],payment_data['category_id'],
                    payment_data['amount'],payment_data['payment_date'],
                    payment_data['payment_method']]):
            flash('All required fields must be filled','error')
            return redirect(url_for('payments.add_payment'))

        success,message = PaymentDB.add_payment(payment_data)

        if success:
            flash(message,'success')
            return redirect(url_for('payments.payment_list'))
        else:
            flash(message,'error')
            return redirect(url_for('payments.add_payment'))

    except (ValueError,TypeError) as e:
        flash(f'Invalid data provided: {str(e)}','error')
        return redirect(url_for('payments.add_payment'))


@payments_bp.route('/dues')
def outstanding_dues():
    """Outstanding dues page with embedded HTML"""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Sample outstanding dues data (replace with real database queries)
    sample_dues = [
        {
            'due_id': 1,
            'student_id': 1,
            'student_name': 'John Smith',
            'student_number': 'STU001',
            'room_number': 'R101',
            'room_type': 'Single Room',
            'category_name': 'Monthly Rent',
            'month_year': 'November 2024',
            'amount_due': 450.00,
            'due_date': '2024-11-30',
            'late_fee': 45.00,
            'is_overdue': True
        },
        {
            'due_id': 2,
            'student_id': 2,
            'student_name': 'Sarah Johnson',
            'student_number': 'STU002',
            'room_number': 'R102',
            'room_type': 'Double Room',
            'category_name': 'Monthly Rent',
            'month_year': 'December 2024',
            'amount_due': 350.00,
            'due_date': '2024-12-31',
            'late_fee': 0.00,
            'is_overdue': False
        },
        {
            'due_id': 3,
            'student_id': 3,
            'student_name': 'Mike Davis',
            'student_number': 'STU003',
            'room_number': 'D301',
            'room_type': 'Dormitory',
            'category_name': 'Utilities',
            'month_year': 'November 2024',
            'amount_due': 75.00,
            'due_date': '2024-11-15',
            'late_fee': 15.00,
            'is_overdue': True
        }
    ]

    # Calculate statistics
    total_outstanding = sum(due['amount_due'] + due['late_fee'] for due in sample_dues)
    overdue_count = sum(1 for due in sample_dues if due['is_overdue'])
    students_with_dues = len(sample_dues)
    total_late_fees = sum(due['late_fee'] for due in sample_dues)

    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Outstanding Dues - Hostel Management</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    </head>
    <body>
        <!-- Navigation -->
        <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
            <div class="container">
                <span class="navbar-brand"><i class="fas fa-building"></i> Hostel Management System</span>

                <div class="navbar-nav me-auto">
                    <a class="nav-link text-white" href="/students"><i class="fas fa-users"></i> Students</a>
                    <a class="nav-link text-white" href="/rooms"><i class="fas fa-bed"></i> Rooms</a>
                    <a class="nav-link text-white" href="/assignments"><i class="fas fa-home"></i> Assignments</a>
                    <a class="nav-link text-white" href="/payments"><i class="fas fa-money-bill"></i> Payments</a>
                    <a class="nav-link text-white" href="/reports"><i class="fas fa-chart-bar"></i> Reports</a>
                </div>

                <div class="navbar-nav">
                    <a class="nav-link text-white" href="/dashboard">
                        <i class="fas fa-tachometer-alt"></i> Dashboard
                    </a>
                    <a class="nav-link text-white" href="/logout">
                        <i class="fas fa-sign-out-alt"></i> Logout
                    </a>
                </div>
            </div>
        </nav>

        <div class="container-fluid mt-4">
            <!-- Page Header -->
            <div class="row">
                <div class="col-12">
                    <div class="d-flex justify-content-between align-items-center mb-4">
                        <div>
                            <h2><i class="fas fa-exclamation-triangle text-warning"></i> Outstanding Dues</h2>
                            <p class="text-muted mb-0">Manage overdue payments and collect outstanding fees</p>
                        </div>
                        <div>
                            <button type="button" class="btn btn-primary me-2" data-bs-toggle="modal" data-bs-target="#generateDuesModal">
                                <i class="fas fa-calendar-plus"></i> Generate Monthly Dues
                            </button>
                            <a href="/payments" class="btn btn-outline-secondary">
                                <i class="fas fa-arrow-left"></i> Back to Payments
                            </a>
                        </div>
                    </div>

                    <!-- Summary Cards -->
                    <div class="row mb-4">
                        <div class="col-md-3">
                            <div class="card text-white bg-warning">
                                <div class="card-body text-center">
                                    <h5><i class="fas fa-exclamation-triangle"></i> Total Outstanding</h5>
                                    <h3>RM {total_outstanding:.2f}</h3>
                                    <small class="opacity-75">Across all students</small>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="card text-white bg-danger">
                                <div class="card-body text-center">
                                    <h5><i class="fas fa-clock"></i> Overdue</h5>
                                    <h3>{overdue_count}</h3>
                                    <small class="opacity-75">Past due date</small>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="card text-white bg-info">
                                <div class="card-body text-center">
                                    <h5><i class="fas fa-users"></i> Students</h5>
                                    <h3>{students_with_dues}</h3>
                                    <small class="opacity-75">With outstanding dues</small>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="card text-white bg-secondary">
                                <div class="card-body text-center">
                                    <h5><i class="fas fa-percentage"></i> Late Fees</h5>
                                    <h3>RM {total_late_fees:.2f}</h3>
                                    <small class="opacity-75">Additional charges</small>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Outstanding Dues Table -->
                    <div class="card">
                        <div class="card-header">
                            <h5 class="mb-0"><i class="fas fa-list"></i> Outstanding Payment Details</h5>
                        </div>
                        <div class="card-body">
                            <div class="table-responsive">
                                <table class="table table-striped table-hover">
                                    <thead class="table-dark">
                                        <tr>
                                            <th>Student</th>
                                            <th>Room</th>
                                            <th>Category</th>
                                            <th>Month/Year</th>
                                            <th>Amount Due</th>
                                            <th>Due Date</th>
                                            <th>Late Fee</th>
                                            <th>Total</th>
                                            <th>Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {''.join([f'''
                                        <tr class="{'table-danger' if due['is_overdue'] else 'table-warning' if due['due_date'] >= '2024-12-01' else ''}">
                                            <td>
                                                <div>
                                                    <strong>{due['student_name']}</strong><br>
                                                    <small class="text-muted">{due['student_number']}</small>
                                                </div>
                                            </td>
                                            <td>
                                                {due['room_number']}<br>
                                                <small class="text-muted">{due['room_type']}</small>
                                            </td>
                                            <td>{due['category_name']}</td>
                                            <td>{due['month_year']}</td>
                                            <td>RM {due['amount_due']:.2f}</td>
                                            <td>
                                                {due['due_date']}
                                                {'<br><small class="text-danger">Overdue</small>' if due['is_overdue'] else '<br><small class="text-warning">Due Soon</small>' if due['due_date'] >= '2024-12-01' else ''}
                                            </td>
                                            <td>
                                                {'<span class="text-danger">RM ' + f"{due['late_fee']:.2f}" + '</span>' if due['late_fee'] > 0 else '<span class="text-muted">RM 0.00</span>'}
                                            </td>
                                            <td>
                                                <strong>RM {due['amount_due'] + due['late_fee']:.2f}</strong>
                                            </td>
                                            <td>
                                                <button class="btn btn-sm btn-success"
                                                        onclick="collectPayment({due['due_id']}, {due['student_id']}, '{due['student_name']}', {due['amount_due'] + due['late_fee']:.2f})"
                                                        title="Collect Payment">
                                                    <i class="fas fa-money-bill"></i>
                                                </button>
                                                <button class="btn btn-sm btn-outline-info" 
                                                        onclick="viewStudentPayments({due['student_id']}, '{due['student_name']}')"
                                                        title="View Student Payments">
                                                    <i class="fas fa-eye"></i>
                                                </button>
                                            </td>
                                        </tr>
                                        ''' for due in sample_dues])}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Generate Monthly Dues Modal -->
        <div class="modal fade" id="generateDuesModal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Generate Monthly Dues</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <form id="generateDuesForm" onsubmit="generateDues(event)">
                        <div class="modal-body">
                            <div class="mb-3">
                                <label for="month_year" class="form-label">Month/Year <span class="text-danger">*</span></label>
                                <input type="month" name="month_year" id="month_year" class="form-control" required>
                            </div>
                            <div class="mb-3">
                                <label for="due_date" class="form-label">Due Date <span class="text-danger">*</span></label>
                                <input type="date" name="due_date" id="due_date" class="form-control" required>
                            </div>
                            <div class="alert alert-info">
                                <i class="fas fa-info-circle"></i>
                                This will generate monthly dues for all active students based on their room assignments and fee structure.
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="submit" class="btn btn-primary">Generate Dues</button>
                        </div>
                    </form>
                </div>
            </div>
        </div>

        <!-- Collect Payment Modal -->
        <div class="modal fade" id="collectPaymentModal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Collect Payment</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <form id="collectPaymentForm" onsubmit="processPayment(event)">
                        <div class="modal-body">
                            <input type="hidden" name="due_id" id="modal_due_id">
                            <input type="hidden" name="student_id" id="modal_student_id">

                            <div class="mb-3">
                                <strong>Student:</strong> <span id="modal_student_name"></span>
                            </div>
                            <div class="mb-3">
                                <strong>Amount:</strong> RM <span id="modal_amount"></span>
                            </div>

                            <div class="mb-3">
                                <label for="modal_payment_method" class="form-label">Payment Method <span class="text-danger">*</span></label>
                                <select name="payment_method" id="modal_payment_method" class="form-select" required>
                                    <option value="">Select Payment Method</option>
                                    <option value="Cash">Cash</option>
                                    <option value="Card">Credit/Debit Card</option>
                                    <option value="Bank Transfer">Bank Transfer</option>
                                    <option value="Online">Online Payment</option>
                                </select>
                            </div>

                            <div class="mb-3">
                                <label for="modal_notes" class="form-label">Notes (Optional)</label>
                                <textarea name="notes" id="modal_notes" class="form-control" rows="2" placeholder="Payment notes or reference number"></textarea>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="submit" class="btn btn-success">
                                <i class="fas fa-money-bill"></i> Collect Payment
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>

        <!-- Student Payments Modal -->
        <div class="modal fade" id="studentPaymentsModal" tabindex="-1">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Student Payment History</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div id="studentPaymentsContent">
                            <p class="text-center text-muted">Loading payment history...</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        <script>
            function collectPayment(dueId, studentId, studentName, amount) {{
                document.getElementById('modal_due_id').value = dueId;
                document.getElementById('modal_student_id').value = studentId;
                document.getElementById('modal_student_name').textContent = studentName;
                document.getElementById('modal_amount').textContent = amount.toFixed(2);

                const modal = new bootstrap.Modal(document.getElementById('collectPaymentModal'));
                modal.show();
            }}

            function viewStudentPayments(studentId, studentName) {{
                document.querySelector('#studentPaymentsModal .modal-title').textContent = studentName + ' - Payment History';

                // Sample payment history
                const sampleHistory = `
                    <div class="table-responsive">
                        <table class="table table-sm">
                            <thead>
                                <tr>
                                    <th>Date</th>
                                    <th>Category</th>
                                    <th>Amount</th>
                                    <th>Method</th>
                                    <th>Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td>2024-10-30</td>
                                    <td>Monthly Rent</td>
                                    <td>RM 450.00</td>
                                    <td>Bank Transfer</td>
                                    <td><span class="badge bg-success">Paid</span></td>
                                </tr>
                                <tr>
                                    <td>2024-09-30</td>
                                    <td>Monthly Rent</td>
                                    <td>RM 450.00</td>
                                    <td>Cash</td>
                                    <td><span class="badge bg-success">Paid</span></td>
                                </tr>
                                <tr>
                                    <td>2024-08-30</td>
                                    <td>Monthly Rent</td>
                                    <td>RM 450.00</td>
                                    <td>Card</td>
                                    <td><span class="badge bg-success">Paid</span></td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                `;

                document.getElementById('studentPaymentsContent').innerHTML = sampleHistory;

                const modal = new bootstrap.Modal(document.getElementById('studentPaymentsModal'));
                modal.show();
            }}

            function generateDues(event) {{
                event.preventDefault();

                const monthYear = document.getElementById('month_year').value;
                const dueDate = document.getElementById('due_date').value;

                alert('Monthly dues generated for ' + monthYear + '\\nDue date: ' + dueDate + '\\n\\nThis is a demo - in a real system, this would create due records in the database.');

                bootstrap.Modal.getInstance(document.getElementById('generateDuesModal')).hide();
            }}

            function processPayment(event) {{
                event.preventDefault();

                const studentName = document.getElementById('modal_student_name').textContent;
                const amount = document.getElementById('modal_amount').textContent;
                const method = document.getElementById('modal_payment_method').value;

                alert('Payment collected successfully!\\n\\nStudent: ' + studentName + '\\nAmount: RM ' + amount + '\\nMethod: ' + method + '\\n\\nReceipt generated.');

                bootstrap.Modal.getInstance(document.getElementById('collectPaymentModal')).hide();

                // In a real system, you would refresh the page or update the table
                setTimeout(() => {{
                    location.reload();
                }}, 1000);
            }}

            // Set current month as default
            document.addEventListener('DOMContentLoaded', function() {{
                const now = new Date();
                const monthYear = now.getFullYear() + '-' + String(now.getMonth() + 1).padStart(2, '0');
                document.getElementById('month_year').value = monthYear;

                // Set due date to end of selected month
                const lastDay = new Date(now.getFullYear(), now.getMonth() + 1, 0);
                const dueDate = lastDay.getFullYear() + '-' + String(lastDay.getMonth() + 1).padStart(2, '0') + '-' + String(lastDay.getDate()).padStart(2, '0');
                document.getElementById('due_date').value = dueDate;
            }});
        </script>
    </body>
    </html>
    '''

@payments_bp.route('/generate-dues',methods=['POST'])
def generate_monthly_dues():
    """Generate monthly dues for all active students"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    month_year = request.form.get('month_year')

    if not month_year:
        flash('Month/Year is required','error')
        return redirect(url_for('payments.outstanding_dues'))

    success,message = PaymentDB.create_monthly_dues(month_year)

    if success:
        flash(message,'success')
    else:
        flash(message,'error')

    return redirect(url_for('payments.outstanding_dues'))


@payments_bp.route('/dashboard')
def payment_dashboard():
    """Payment dashboard with statistics"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    summary = PaymentDB.get_payment_summary()
    return render_template('payments/dashboard.html',summary=summary)


@payments_bp.route('/student/<int:student_id>')
def student_payments():
    """View payment history for specific student"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    student = StudentDB.get_student_by_id(student_id)
    if not student:
        flash('Student not found','error')
        return redirect(url_for('payments.payment_list'))

    payments = PaymentDB.get_student_payments(student_id,limit=50)
    dues = PaymentDB.get_outstanding_dues(student_id)

    # Format data for display
    formatted_payments = []
    for payment in payments:
        formatted_payments.append({
            'payment_id': payment[0],
            'amount': float(payment[1]),
            'payment_date': payment[2].strftime('%Y-%m-%d') if payment[2] else None,
            'payment_method': payment[3],
            'payment_status': payment[4],
            'reference_number': payment[5],
            'receipt_number': payment[6],
            'category_name': payment[7],
            'notes': payment[11],
            'late_fee': float(payment[12])
        })

    formatted_dues = []
    for due in dues:
        formatted_dues.append({
            'due_id': due[0],
            'amount_due': float(due[1]),
            'due_date': due[2].strftime('%Y-%m-%d') if due[2] else None,
            'month_year': due[3],
            'late_fee': float(due[4]),
            'category_name': due[9]
        })

    return render_template('payments/student_payments.html',
                           student=student,
                           payments=formatted_payments,
                           dues=formatted_dues)