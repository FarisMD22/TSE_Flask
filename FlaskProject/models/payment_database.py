from models.database import Database
from datetime import datetime,date
from decimal import Decimal
import mysql.connector
from typing import List,Tuple,Dict,Optional


class PaymentDB:
    """Database operations for payment management"""

    @staticmethod
    def get_all_payment_categories() -> List[tuple]:
        """Get all active payment categories"""
        db = Database()
        try:
            db.connect()
            query = """
                    SELECT category_id, \
                           category_name, \
                           description, \
                           is_recurring,
                           default_amount, \
                           is_active, \
                           created_at
                    FROM payment_categories
                    WHERE is_active = TRUE
                    ORDER BY category_name \
                    """
            return db.execute_query(query,())
        finally:
            db.disconnect()

    @staticmethod
    def get_fee_structure_by_room_type(room_type: str) -> List[tuple]:
        """Get fee structure for specific room type"""
        db = Database()
        try:
            db.connect()
            query = """
                    SELECT fs.fee_id, \
                           fs.room_type, \
                           fs.amount, \
                           pc.category_name,
                           pc.category_id, \
                           fs.effective_date
                    FROM fee_structure fs
                             INNER JOIN payment_categories pc ON fs.category_id = pc.category_id
                    WHERE fs.room_type = %s \
                      AND fs.is_active = TRUE \
                      AND pc.is_active = TRUE
                    ORDER BY pc.category_name \
                    """
            return db.execute_query(query,(room_type,))
        finally:
            db.disconnect()

    @staticmethod
    def add_payment(payment_data: dict) -> Tuple[bool,str]:
        """Add new payment record"""
        db = Database()
        try:
            db.connect()

            # Generate reference number if not provided
            if not payment_data.get('reference_number'):
                payment_data['reference_number'] = PaymentDB._generate_reference_number()

            # Generate receipt number if not provided
            if not payment_data.get('receipt_number'):
                payment_data['receipt_number'] = PaymentDB._generate_receipt_number()

            query = """
                    INSERT INTO payments (student_id, assignment_id, category_id, amount,
                                          payment_date, payment_method, payment_status,
                                          reference_number, receipt_number, due_date,
                                          late_fee, notes, processed_by)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) \
                    """

            params = (
                payment_data['student_id'],
                payment_data.get('assignment_id'),
                payment_data['category_id'],
                payment_data['amount'],
                payment_data['payment_date'],
                payment_data['payment_method'],
                payment_data.get('payment_status','Completed'),
                payment_data['reference_number'],
                payment_data['receipt_number'],
                payment_data.get('due_date'),
                payment_data.get('late_fee',0.00),
                payment_data.get('notes',''),
                payment_data.get('processed_by','System')
            )

            payment_id = db.execute_insert(query,params)

            # Update outstanding dues if applicable
            if payment_data.get('due_id'):
                PaymentDB._mark_due_as_paid(payment_data['due_id'],payment_id)

            return True,f"Payment recorded successfully. Payment ID: {payment_id}"

        except mysql.connector.Error as e:
            return False,f"Database error: {str(e)}"
        finally:
            db.disconnect()

    @staticmethod
    def get_student_payments(student_id: int,limit: int = 50) -> List[tuple]:
        """Get payment history for a student"""
        db = Database()
        try:
            db.connect()
            query = """
                    SELECT p.payment_id, \
                           p.amount, \
                           p.payment_date, \
                           p.payment_method,
                           p.payment_status, \
                           p.reference_number, \
                           p.receipt_number,
                           pc.category_name, \
                           s.first_name, \
                           s.last_name, \
                           s.student_number,
                           p.notes, \
                           p.late_fee, \
                           p.created_at
                    FROM payments p
                             INNER JOIN payment_categories pc ON p.category_id = pc.category_id
                             INNER JOIN students s ON p.student_id = s.student_id
                    WHERE p.student_id = %s
                    ORDER BY p.payment_date DESC, p.created_at DESC
                        LIMIT %s \
                    """
            return db.execute_query(query,(student_id,limit))
        finally:
            db.disconnect()

    @staticmethod
    def get_all_payments(limit: int = 100,status_filter: str = None) -> List[tuple]:
        """Get all payments with optional status filter"""
        db = Database()
        try:
            db.connect()
            base_query = """
                         SELECT p.payment_id, \
                                p.amount, \
                                p.payment_date, \
                                p.payment_method,
                                p.payment_status, \
                                p.reference_number, \
                                p.receipt_number,
                                pc.category_name, \
                                s.first_name, \
                                s.last_name, \
                                s.student_number,
                                p.notes, \
                                p.late_fee, \
                                p.created_at, \
                                s.student_id
                         FROM payments p
                                  INNER JOIN payment_categories pc ON p.category_id = pc.category_id
                                  INNER JOIN students s ON p.student_id = s.student_id \
                         """

            if status_filter and status_filter != 'All':
                query = base_query + " WHERE p.payment_status = %s"
                params = (status_filter,limit)
            else:
                query = base_query
                params = (limit,)

            query += " ORDER BY p.payment_date DESC, p.created_at DESC LIMIT %s"

            return db.execute_query(query,params)
        finally:
            db.disconnect()

    @staticmethod
    def get_outstanding_dues(student_id: int = None) -> List[tuple]:
        """Get outstanding dues for all students or specific student"""
        db = Database()
        try:
            db.connect()
            base_query = """
                         SELECT od.due_id, \
                                od.amount_due, \
                                od.due_date, \
                                od.month_year,
                                od.late_fee_applied, \
                                s.student_id, \
                                s.first_name, \
                                s.last_name,
                                s.student_number, \
                                pc.category_name, \
                                od.is_paid,
                                r.room_number, \
                                r.room_type
                         FROM outstanding_dues od
                                  INNER JOIN students s ON od.student_id = s.student_id
                                  INNER JOIN payment_categories pc ON od.category_id = pc.category_id
                                  LEFT JOIN room_assignments ra ON od.assignment_id = ra.assignment_id
                                  LEFT JOIN rooms r ON ra.room_id = r.room_id \
                         """

            if student_id:
                query = base_query + " WHERE od.student_id = %s AND od.is_paid = FALSE"
                params = (student_id,)
            else:
                query = base_query + " WHERE od.is_paid = FALSE"
                params = ()

            query += " ORDER BY od.due_date ASC, s.last_name, s.first_name"

            return db.execute_query(query,params)
        finally:
            db.disconnect()

    @staticmethod
    def create_monthly_dues(month_year: str) -> Tuple[bool,str]:
        """Generate monthly dues for all active assignments"""
        db = Database()
        try:
            db.connect()

            # Get all active assignments with room and fee information
            query = """
                    SELECT DISTINCT ra.student_id, \
                                    ra.assignment_id, \
                                    r.room_type,
                                    fs.category_id, \
                                    fs.amount
                    FROM room_assignments ra
                             INNER JOIN rooms r ON ra.room_id = r.room_id
                             INNER JOIN fee_structure fs ON r.room_type = fs.room_type
                             INNER JOIN payment_categories pc ON fs.category_id = pc.category_id
                    WHERE ra.status = 'Active'
                      AND fs.is_active = TRUE
                      AND pc.is_recurring = TRUE
                      AND pc.is_active = TRUE \
                    """

            assignments = db.execute_query(query,())

            # Calculate due date (15th of the month)
            year,month = month_year.split('-')
            due_date = f"{year}-{month}-15"

            dues_created = 0

            for assignment in assignments:
                student_id,assignment_id,room_type,category_id,amount = assignment

                # Check if due already exists for this month
                check_query = """
                              SELECT due_id \
                              FROM outstanding_dues
                              WHERE student_id = %s \
                                AND category_id = %s \
                                AND month_year = %s \
                              """
                existing = db.execute_query(check_query,(student_id,category_id,month_year))

                if not existing:
                    # Create new due
                    insert_query = """
                                   INSERT INTO outstanding_dues (student_id, assignment_id, category_id,
                                                                 amount_due, due_date, month_year)
                                   VALUES (%s, %s, %s, %s, %s, %s) \
                                   """

                    db.execute_insert(insert_query,(
                        student_id,assignment_id,category_id,
                        amount,due_date,month_year
                    ))
                    dues_created += 1

            return True,f"Created {dues_created} monthly dues for {month_year}"

        except mysql.connector.Error as e:
            return False,f"Database error: {str(e)}"
        finally:
            db.disconnect()

    @staticmethod
    def get_payment_summary() -> dict:
        """Get payment summary statistics"""
        db = Database()
        try:
            db.connect()

            # Total payments this month
            month_query = """
                          SELECT COALESCE(SUM(amount), 0) as total_month
                          FROM payments
                          WHERE MONTH (payment_date) = MONTH (CURRENT_DATE)
                            AND YEAR (payment_date) = YEAR (CURRENT_DATE)
                            AND payment_status = 'Completed' \
                          """
            month_total = db.execute_query(month_query,())[0][0]

            # Outstanding dues
            dues_query = """
                         SELECT COALESCE(SUM(amount_due + late_fee_applied), 0) as total_dues
                         FROM outstanding_dues
                         WHERE is_paid = FALSE \
                         """
            outstanding_dues = db.execute_query(dues_query,())[0][0]

            # Total students with pending payments
            students_query = """
                             SELECT COUNT(DISTINCT student_id) as pending_students
                             FROM outstanding_dues
                             WHERE is_paid = FALSE \
                             """
            pending_students = db.execute_query(students_query,())[0][0]

            # Payment methods distribution
            methods_query = """
                            SELECT payment_method, COUNT(*) as count, SUM(amount) as total
                            FROM payments
                            WHERE payment_status = 'Completed'
                              AND MONTH (payment_date) = MONTH (CURRENT_DATE)
                              AND YEAR (payment_date) = YEAR (CURRENT_DATE)
                            GROUP BY payment_method \
                            """
            payment_methods = db.execute_query(methods_query,())

            return {
                'month_total': float(month_total),
                'outstanding_dues': float(outstanding_dues),
                'pending_students': pending_students,
                'payment_methods': payment_methods
            }

        finally:
            db.disconnect()

    @staticmethod
    def _generate_reference_number() -> str:
        """Generate unique reference number"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"PAY{timestamp}"

    @staticmethod
    def _generate_receipt_number() -> str:
        """Generate unique receipt number"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"RCP{timestamp}"

    @staticmethod
    def _mark_due_as_paid(due_id: int,payment_id: int) -> bool:
        """Mark outstanding due as paid"""
        db = Database()
        try:
            db.connect()
            query = """
                    UPDATE outstanding_dues
                    SET is_paid    = TRUE, \
                        payment_id = %s, \
                        updated_at = CURRENT_TIMESTAMP
                    WHERE due_id = %s \
                    """
            db.execute_update(query,(payment_id,due_id))
            return True
        except mysql.connector.Error:
            return False
        finally:
            db.disconnect()