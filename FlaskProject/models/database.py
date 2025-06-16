import mysql.connector
from mysql.connector import Error
from config import Config


class Database:
    def __init__(self):
        """Initialize database connection parameters from :class:`Config`."""
        self.host = Config.DB_HOST
        self.user = Config.DB_USER
        self.password = Config.DB_PASSWORD
        self.database = Config.DB_NAME
        self.connection = None

    def connect(self):
        """Create database connection"""
        try:
            if self.connection is None or not self.connection.is_connected():
                self.connection = mysql.connector.connect(
                    host=self.host,
                    user=self.user,
                    password=self.password,
                    database=self.database,
                    autocommit=True,
                    charset='utf8mb4'
                )
                print("✅ Database connected successfully!")
            return self.connection
        except Error as e:
            print(f"❌ Error connecting to MySQL: {e}")
            self.connection = None
            return None

    def disconnect(self):
        """Close database connection"""
        try:
            if self.connection and self.connection.is_connected():
                self.connection.close()
                self.connection = None
                print("Database connection closed")
        except Error as e:
            print(f"Error closing connection: {e}")

    def execute_query(self,query,params=None):
        """Execute a query and return results"""
        try:
            # Ensure we have a valid connection
            if not self.connection or not self.connection.is_connected():
                self.connect()

            if not self.connection:
                print("❌ No database connection available")
                return []

            cursor = self.connection.cursor()
            cursor.execute(query,params or ())
            result = cursor.fetchall()
            cursor.close()
            return result

        except Error as e:
            print(f"❌ Error executing query: {e}")
            print(f"Query: {query}")
            print(f"Params: {params}")
            # Try to reconnect
            self.connect()
            return []
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return []

    def execute_insert(self,query,params=None):
        """Execute insert query and return last insert id"""
        try:
            # Ensure we have a valid connection
            if not self.connection or not self.connection.is_connected():
                self.connect()

            if not self.connection:
                print("❌ No database connection available")
                return None

            cursor = self.connection.cursor()
            cursor.execute(query,params or ())
            self.connection.commit()
            insert_id = cursor.lastrowid
            cursor.close()
            return insert_id

        except Error as e:
            print(f"❌ Error executing insert: {e}")
            if self.connection:
                self.connection.rollback()
            # Try to reconnect
            self.connect()
            return None
        except Exception as e:
            print(f"❌ Unexpected error in insert: {e}")
            return None

    def execute_update(self,query,params=None):
        """Execute update/delete query and return affected rows"""
        try:
            # Ensure we have a valid connection
            if not self.connection or not self.connection.is_connected():
                self.connect()

            if not self.connection:
                print("❌ No database connection available")
                return 0

            cursor = self.connection.cursor()
            cursor.execute(query,params or ())
            self.connection.commit()
            affected_rows = cursor.rowcount
            cursor.close()
            return affected_rows

        except Error as e:
            print(f"❌ Error executing update: {e}")
            if self.connection:
                self.connection.rollback()
            # Try to reconnect
            self.connect()
            return 0
        except Exception as e:
            print(f"❌ Unexpected error in update: {e}")
            return 0

    def test_connection(self):
        """Test if database connection is working"""
        try:
            result = self.execute_query("SELECT 1")
            return len(result) > 0
        except:
            return False


class StudentDB:
    """Student database operations class"""

    @staticmethod
    def get_all_students(limit=None):
        """Get all students with room information"""
        try:
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
            if limit:
                query += f" LIMIT {limit}"

            return db.execute_query(query)
        except Exception as e:
            print(f"Error getting students: {e}")
            return []

    @staticmethod
    def get_student_by_id(student_id):
        """Get student by ID with room information"""
        try:
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
            return result[0] if result else None
        except Exception as e:
            print(f"Error getting student by ID: {e}")
            return None

    @staticmethod
    def search_students(search_term,status_filter='all'):
        """Search students with filters"""
        try:
            base_query = """
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
                         WHERE 1 = 1 \
                         """

            params = []

            if search_term:
                base_query += """ AND (s.first_name LIKE %s OR s.last_name LIKE %s 
                                     OR s.student_number LIKE %s OR s.email LIKE %s)"""
                search_pattern = f"%{search_term}%"
                params.extend([search_pattern,search_pattern,search_pattern,search_pattern])

            if status_filter != 'all':
                base_query += " AND s.status = %s"
                params.append(status_filter)

            base_query += " ORDER BY s.created_at DESC"

            return db.execute_query(base_query,params)
        except Exception as e:
            print(f"Error searching students: {e}")
            return []

    @staticmethod
    def add_student(student_data):
        """Add new student"""
        try:
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
            return db.execute_insert(query,values)
        except Exception as e:
            print(f"Error adding student: {e}")
            return None

    @staticmethod
    def update_student(student_id,student_data):
        """Update student information"""
        try:
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
            return db.execute_update(query,values) > 0
        except Exception as e:
            print(f"Error updating student: {e}")
            return False

    @staticmethod
    def delete_student(student_id):
        """Delete student"""
        try:
            return db.execute_update("DELETE FROM students WHERE student_id = %s",(student_id,)) > 0
        except Exception as e:
            print(f"Error deleting student: {e}")
            return False

    @staticmethod
    def get_student_payments(student_id,limit=5):
        """Get student payment history"""
        try:
            query = """
                    SELECT payment_id, amount, payment_date, payment_type, payment_method, receipt_number, status
                    FROM fee_payments
                    WHERE student_id = %s
                    ORDER BY payment_date DESC \
                    """
            if limit:
                query += f" LIMIT {limit}"

            return db.execute_query(query,(student_id,))
        except Exception as e:
            print(f"Error getting student payments: {e}")
            return []

    @staticmethod
    def assign_room(student_id,room_id,assigned_date):
        """Assign room to student"""
        try:
            # Check if student already has an active room assignment
            existing = db.execute_query(
                "SELECT assignment_id FROM room_assignments WHERE student_id = %s AND status = 'Active'",
                (student_id,)
            )
            if existing:
                return False,"Student already has an active room assignment"

            # Check if room is available
            room_check = db.execute_query(
                "SELECT capacity, current_occupancy FROM rooms WHERE room_id = %s",
                (room_id,)
            )
            if not room_check:
                return False,"Room not found"

            capacity,current_occupancy = room_check[0]
            if current_occupancy >= capacity:
                return False,"Room is full"

            # Assign room
            assignment_id = db.execute_insert(
                "INSERT INTO room_assignments (student_id, room_id, assigned_date) VALUES (%s, %s, %s)",
                (student_id,room_id,assigned_date)
            )

            if assignment_id:
                # Update room occupancy
                db.execute_update(
                    "UPDATE rooms SET current_occupancy = current_occupancy + 1, status = CASE WHEN current_occupancy + 1 >= capacity THEN 'Occupied' ELSE 'Available' END WHERE room_id = %s",
                    (room_id,)
                )
                return True,"Room assigned successfully"

            return False,"Failed to assign room"
        except Exception as e:
            print(f"Error assigning room: {e}")
            return False,f"Error: {e}"


# Add this new class to your existing models/database.py file
# Place it after the StudentDB class and before the global db instance

# ADD THIS CLASS TO YOUR EXISTING models/database.py FILE
# Place it after the StudentDB class and before the global db instance

class AssignmentDB:
    """Room assignment database operations class"""

    @staticmethod
    def get_all_assignments():
        """Get all active room assignments with student and room details"""
        try:
            query = """
            SELECT ra.assignment_id, ra.student_id, ra.room_id, ra.assigned_date, 
                   ra.checkout_date, ra.status,
                   s.student_number, s.first_name, s.last_name, s.email, s.phone,
                   r.room_number, r.room_type, r.capacity, r.rent_amount,
                   ra.created_at
            FROM room_assignments ra
            INNER JOIN students s ON ra.student_id = s.student_id
            INNER JOIN rooms r ON ra.room_id = r.room_id
            ORDER BY ra.assigned_date DESC, ra.created_at DESC
            """
            return db.execute_query(query)
        except Exception as e:
            print(f"Error getting assignments: {e}")
            return []

    @staticmethod
    def get_active_assignments():
        """Get only active room assignments"""
        try:
            query = """
            SELECT ra.assignment_id, ra.student_id, ra.room_id, ra.assigned_date, 
                   ra.checkout_date, ra.status,
                   s.student_number, s.first_name, s.last_name, s.email, s.phone,
                   r.room_number, r.room_type, r.capacity, r.rent_amount,
                   ra.created_at
            FROM room_assignments ra
            INNER JOIN students s ON ra.student_id = s.student_id
            INNER JOIN rooms r ON ra.room_id = r.room_id
            WHERE ra.status = 'Active'
            ORDER BY r.room_number, ra.assigned_date
            """
            return db.execute_query(query)
        except Exception as e:
            print(f"Error getting active assignments: {e}")
            return []

    @staticmethod
    def get_unassigned_students():
        """Get students who don't have active room assignments"""
        try:
            query = """
            SELECT s.student_id, s.student_number, s.first_name, s.last_name, 
                   s.email, s.phone, s.course, s.year_of_study, s.status
            FROM students s
            LEFT JOIN room_assignments ra ON s.student_id = ra.student_id AND ra.status = 'Active'
            WHERE ra.assignment_id IS NULL AND s.status = 'Active'
            ORDER BY s.first_name, s.last_name
            """
            return db.execute_query(query)
        except Exception as e:
            print(f"Error getting unassigned students: {e}")
            return []

    @staticmethod
    def get_available_rooms():
        """Get rooms that have available space"""
        try:
            query = """
            SELECT r.room_id, r.room_number, r.room_type, r.capacity, 
                   r.current_occupancy, r.rent_amount, r.floor_number,
                   (r.capacity - r.current_occupancy) as available_spaces
            FROM rooms r
            WHERE r.status IN ('Available', 'Occupied') 
            AND r.current_occupancy < r.capacity
            ORDER BY r.room_number
            """
            return db.execute_query(query)
        except Exception as e:
            print(f"Error getting available rooms: {e}")
            return []

    @staticmethod
    def assign_student_to_room(student_id, room_id, assigned_date, notes=""):
        """Assign a student to a room"""
        try:
            # Check if student already has an active assignment
            existing = db.execute_query(
                "SELECT assignment_id FROM room_assignments WHERE student_id = %s AND status = 'Active'",
                (student_id,)
            )
            if existing:
                return False, "Student already has an active room assignment"

            # Check if room has available space
            room_check = db.execute_query(
                "SELECT capacity, current_occupancy, status FROM rooms WHERE room_id = %s",
                (room_id,)
            )
            if not room_check:
                return False, "Room not found"

            capacity, current_occupancy, room_status = room_check[0]
            if room_status not in ['Available', 'Occupied']:
                return False, f"Room is not available for assignment (Status: {room_status})"

            if current_occupancy >= capacity:
                return False, "Room is at full capacity"

            # Create the assignment
            assignment_id = db.execute_insert(
                """INSERT INTO room_assignments (student_id, room_id, assigned_date, status)
                   VALUES (%s, %s, %s, 'Active')""",
                (student_id, room_id, assigned_date)
            )

            if assignment_id:
                # Update room occupancy and status
                new_occupancy = current_occupancy + 1
                new_status = 'Occupied' if new_occupancy >= capacity else 'Available'

                db.execute_update(
                    """UPDATE rooms SET current_occupancy = %s, 
                       status = CASE WHEN %s >= capacity THEN 'Occupied' ELSE status END
                       WHERE room_id = %s""",
                    (new_occupancy, new_occupancy, room_id)
                )

                return True, f"Student successfully assigned to room"

            return False, "Failed to create assignment"

        except Exception as e:
            print(f"Error assigning student to room: {e}")
            return False, f"Database error: {e}"

    # ADD THESE METHODS to your AssignmentDB class in models/database.py
    # Add them after your existing methods in the AssignmentDB class

    @staticmethod
    def checkout_student(assignment_id,checkout_date):
        """Check out a student from their room"""
        try:
            # Get current assignment details
            assignment = db.execute_query(
                """SELECT ra.student_id, ra.room_id, r.capacity, r.current_occupancy
                   FROM room_assignments ra
                            INNER JOIN rooms r ON ra.room_id = r.room_id
                   WHERE ra.assignment_id = %s
                     AND ra.status = 'Active'""",
                (assignment_id,)
            )

            if not assignment:
                return False,"Assignment not found or not active"

            student_id,room_id,capacity,current_occupancy = assignment[0]

            # Update assignment status and checkout date
            updated = db.execute_update(
                """UPDATE room_assignments
                   SET status        = 'Completed',
                       checkout_date = %s
                   WHERE assignment_id = %s""",
                (checkout_date,assignment_id)
            )

            if updated:
                # Update room occupancy
                new_occupancy = max(0,current_occupancy - 1)

                db.execute_update(
                    """UPDATE rooms
                       SET current_occupancy = %s,
                           status            = CASE
                                                   WHEN %s = 0 THEN 'Available'
                                                   WHEN %s < capacity THEN 'Available'
                                                   ELSE 'Occupied' END
                       WHERE room_id = %s""",
                    (new_occupancy,new_occupancy,new_occupancy,room_id)
                )

                return True,"Student checked out successfully"

            return False,"Failed to check out student"

        except Exception as e:
            print(f"Error checking out student: {e}")
            return False,f"Database error: {e}"

    @staticmethod
    def transfer_student(assignment_id,new_room_id,transfer_date):
        """Transfer student to a different room"""
        try:
            # Get current assignment
            current = db.execute_query(
                """SELECT ra.student_id, ra.room_id, ra.assigned_date
                   FROM room_assignments ra
                   WHERE ra.assignment_id = %s
                     AND ra.status = 'Active'""",
                (assignment_id,)
            )

            if not current:
                return False,"Assignment not found or not active"

            student_id,old_room_id,assigned_date = current[0]

            # Check new room availability
            room_check = db.execute_query(
                "SELECT capacity, current_occupancy FROM rooms WHERE room_id = %s",
                (new_room_id,)
            )

            if not room_check:
                return False,"New room not found"

            capacity,current_occupancy = room_check[0]
            if current_occupancy >= capacity:
                return False,"New room is at full capacity"

            # Close old assignment
            db.execute_update(
                """UPDATE room_assignments
                   SET status        = 'Transferred',
                       checkout_date = %s
                   WHERE assignment_id = %s""",
                (transfer_date,assignment_id)
            )

            # Create new assignment
            new_assignment_id = db.execute_insert(
                """INSERT INTO room_assignments (student_id, room_id, assigned_date, status)
                   VALUES (%s, %s, %s, 'Active')""",
                (student_id,new_room_id,transfer_date)
            )

            if new_assignment_id:
                # Update old room occupancy
                db.execute_update(
                    """UPDATE rooms
                       SET current_occupancy = current_occupancy - 1,
                           status            = CASE
                                                   WHEN current_occupancy - 1 = 0 THEN 'Available'
                                                   WHEN current_occupancy - 1 < capacity THEN 'Available'
                                                   ELSE 'Occupied' END
                       WHERE room_id = %s""",
                    (old_room_id,)
                )

                # Update new room occupancy
                db.execute_update(
                    """UPDATE rooms
                       SET current_occupancy = current_occupancy + 1,
                           status            = CASE
                                                   WHEN current_occupancy + 1 >= capacity THEN 'Occupied'
                                                   ELSE 'Available' END
                       WHERE room_id = %s""",
                    (new_room_id,)
                )

                return True,"Student transferred successfully"

            return False,"Failed to create new assignment"

        except Exception as e:
            print(f"Error transferring student: {e}")
            return False,f"Database error: {e}"

    @staticmethod
    def get_assignment_history(student_id=None,room_id=None,limit=50):
        """Get assignment history with optional filters"""
        try:
            query = """
                    SELECT ra.assignment_id, \
                           ra.student_id, \
                           ra.room_id, \
                           ra.assigned_date,
                           ra.checkout_date, \
                           ra.status, \
                           ra.created_at,
                           s.student_number, \
                           s.first_name, \
                           s.last_name,
                           r.room_number, \
                           r.room_type
                    FROM room_assignments ra
                             INNER JOIN students s ON ra.student_id = s.student_id
                             INNER JOIN rooms r ON ra.room_id = r.room_id
                    WHERE 1 = 1 \
                    """

            params = []

            if student_id:
                query += " AND ra.student_id = %s"
                params.append(student_id)

            if room_id:
                query += " AND ra.room_id = %s"
                params.append(room_id)

            query += " ORDER BY ra.created_at DESC"

            if limit:
                query += f" LIMIT {limit}"

            return db.execute_query(query,params)

        except Exception as e:
            print(f"Error getting assignment history: {e}")
            return []

    @staticmethod
    def get_occupancy_statistics():
        """Get overall occupancy statistics"""
        try:
            stats = {}

            # Total assignments
            result = db.execute_query("SELECT COUNT(*) FROM room_assignments WHERE status = 'Active'")
            stats['total_active_assignments'] = result[0][0] if result else 0

            # Unassigned students
            result = db.execute_query("""
                SELECT COUNT(*) FROM students s
                LEFT JOIN room_assignments ra ON s.student_id = ra.student_id AND ra.status = 'Active'
                WHERE ra.assignment_id IS NULL AND s.status = 'Active'
            """)
            stats['unassigned_students'] = result[0][0] if result else 0

            # Available bed spaces
            result = db.execute_query("""
                SELECT SUM(capacity - current_occupancy) FROM rooms 
                WHERE status IN ('Available', 'Occupied')
            """)
            stats['available_spaces'] = result[0][0] if result and result[0][0] else 0

            # Room utilization by type
            result = db.execute_query("""
                SELECT room_type, 
                       COUNT(*) as total_rooms,
                       SUM(current_occupancy) as occupied_spaces,
                       SUM(capacity) as total_capacity
                FROM rooms 
                GROUP BY room_type
                ORDER BY room_type
            """)
            stats['utilization_by_type'] = result if result else []

            return stats

        except Exception as e:
            print(f"Error getting occupancy statistics: {e}")
            return {}


# Add this PaymentDB class to your models/database.py file
# Place it after the AssignmentDB class

class PaymentDB:
    """Payment management database operations class"""

    @staticmethod
    def get_payment_categories():
        """Get all active payment categories"""
        try:
            query = """
                    SELECT category_id, category_name, description, is_recurring, default_amount
                    FROM payment_categories
                    WHERE is_active = TRUE
                    ORDER BY category_name \
                    """
            return db.execute_query(query)
        except Exception as e:
            print(f"Error getting payment categories: {e}")
            return []

    @staticmethod
    def get_fee_structure(room_type=None):
        """Get fee structure, optionally filtered by room type"""
        try:
            query = """
                    SELECT fs.fee_id, fs.room_type, fs.amount, pc.category_name, pc.category_id
                    FROM fee_structure fs
                             INNER JOIN payment_categories pc ON fs.category_id = pc.category_id
                    WHERE fs.is_active = TRUE \
                    """
            params = []

            if room_type:
                query += " AND fs.room_type = %s"
                params.append(room_type)

            query += " ORDER BY fs.room_type, pc.category_name"

            return db.execute_query(query,params)
        except Exception as e:
            print(f"Error getting fee structure: {e}")
            return []

    @staticmethod
    def record_payment(payment_data):
        """Record a new payment"""
        try:
            # Generate reference number if not provided
            if not payment_data.get('reference_number'):
                # Get next payment ID to generate reference
                next_id_query = "SELECT AUTO_INCREMENT FROM information_schema.TABLES WHERE TABLE_SCHEMA = 'hostel_management' AND TABLE_NAME = 'payments'"
                result = db.execute_query(next_id_query)
                next_id = result[0][0] if result else 1
                payment_data['reference_number'] = f"PAY{next_id:06d}"

            # Generate receipt number if not provided
            if not payment_data.get('receipt_number'):
                payment_data['receipt_number'] = f"RCP{payment_data['reference_number'][3:]}"

            query = """
                    INSERT INTO payments (student_id, assignment_id, category_id, amount, payment_date,
                                          payment_method, payment_status, reference_number, receipt_number,
                                          due_date, late_fee, notes, processed_by)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) \
                    """

            values = (
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
                payment_data.get('notes'),
                payment_data.get('processed_by','System')
            )

            payment_id = db.execute_insert(query,values)

            if payment_id:
                # Update outstanding dues if this payment covers a due
                PaymentDB._update_outstanding_dues(payment_data,payment_id)
                return True,f"Payment recorded successfully. Receipt: {payment_data['receipt_number']}"

            return False,"Failed to record payment"

        except Exception as e:
            print(f"Error recording payment: {e}")
            return False,f"Database error: {e}"

    @staticmethod
    def _update_outstanding_dues(payment_data,payment_id):
        """Update outstanding dues when payment is made"""
        try:
            # Find matching outstanding due
            due_query = """
                        SELECT due_id \
                        FROM outstanding_dues
                        WHERE student_id = %s \
                          AND category_id = %s \
                          AND is_paid = FALSE
                        ORDER BY due_date ASC LIMIT 1 \
                        """

            dues = db.execute_query(due_query,(payment_data['student_id'],payment_data['category_id']))

            if dues:
                # Mark the due as paid
                update_query = """
                               UPDATE outstanding_dues
                               SET is_paid    = TRUE, \
                                   payment_id = %s, \
                                   updated_at = CURRENT_TIMESTAMP
                               WHERE due_id = %s \
                               """
                db.execute_update(update_query,(payment_id,dues[0][0]))

        except Exception as e:
            print(f"Error updating outstanding dues: {e}")

    @staticmethod
    def get_student_payments(student_id,limit=None):
        """Get payment history for a student"""
        try:
            query = """
                    SELECT p.payment_id, \
                           p.amount, \
                           p.payment_date, \
                           p.payment_method, \
                           p.payment_status,
                           p.reference_number, \
                           p.receipt_number, \
                           p.late_fee, \
                           p.notes, \
                           p.created_at,
                           pc.category_name, \
                           r.room_number
                    FROM payments p
                             INNER JOIN payment_categories pc ON p.category_id = pc.category_id
                             LEFT JOIN room_assignments ra ON p.assignment_id = ra.assignment_id
                             LEFT JOIN rooms r ON ra.room_id = r.room_id
                    WHERE p.student_id = %s
                    ORDER BY p.payment_date DESC, p.created_at DESC \
                    """

            if limit:
                query += f" LIMIT {limit}"

            return db.execute_query(query,(student_id,))
        except Exception as e:
            print(f"Error getting student payments: {e}")
            return []

    @staticmethod
    def get_all_payments(limit=50,status_filter=None,date_from=None,date_to=None):
        """Get all payments with optional filters"""
        try:
            query = """
                    SELECT p.payment_id, \
                           p.student_id, \
                           p.amount, \
                           p.payment_date, \
                           p.payment_method,
                           p.payment_status, \
                           p.reference_number, \
                           p.receipt_number, \
                           p.late_fee,
                           s.student_number, \
                           s.first_name, \
                           s.last_name, \
                           s.email,
                           pc.category_name, \
                           r.room_number
                    FROM payments p
                             INNER JOIN students s ON p.student_id = s.student_id
                             INNER JOIN payment_categories pc ON p.category_id = pc.category_id
                             LEFT JOIN room_assignments ra ON p.assignment_id = ra.assignment_id
                             LEFT JOIN rooms r ON ra.room_id = r.room_id
                    WHERE 1 = 1 \
                    """

            params = []

            if status_filter:
                query += " AND p.payment_status = %s"
                params.append(status_filter)

            if date_from:
                query += " AND p.payment_date >= %s"
                params.append(date_from)

            if date_to:
                query += " AND p.payment_date <= %s"
                params.append(date_to)

            query += " ORDER BY p.payment_date DESC, p.created_at DESC"

            if limit:
                query += f" LIMIT {limit}"

            return db.execute_query(query,params)
        except Exception as e:
            print(f"Error getting all payments: {e}")
            return []

    @staticmethod
    def get_outstanding_dues(student_id=None,overdue_only=False):
        """Get outstanding dues, optionally for specific student or overdue only"""
        try:
            query = """
                    SELECT od.due_id, \
                           od.student_id, \
                           od.amount_due, \
                           od.due_date, \
                           od.month_year,
                           od.late_fee_applied, \
                           od.created_at,
                           s.student_number, \
                           s.first_name, \
                           s.last_name, \
                           s.email,
                           pc.category_name, \
                           r.room_number
                    FROM outstanding_dues od
                             INNER JOIN students s ON od.student_id = s.student_id
                             INNER JOIN payment_categories pc ON od.category_id = pc.category_id
                             LEFT JOIN room_assignments ra ON od.assignment_id = ra.assignment_id
                             LEFT JOIN rooms r ON ra.room_id = r.room_id
                    WHERE od.is_paid = FALSE \
                    """

            params = []

            if student_id:
                query += " AND od.student_id = %s"
                params.append(student_id)

            if overdue_only:
                query += " AND od.due_date < CURDATE()"

            query += " ORDER BY od.due_date ASC, s.last_name, s.first_name"

            return db.execute_query(query,params)
        except Exception as e:
            print(f"Error getting outstanding dues: {e}")
            return []

    @staticmethod
    def generate_monthly_dues():
        """Generate monthly dues for all active assignments"""
        try:
            from datetime import datetime,timedelta

            # Get current month/year
            now = datetime.now()
            month_year = now.strftime('%Y-%m')
            due_date = (now.replace(day=1) + timedelta(days=32)).replace(day=5)  # 5th of next month

            # Get all active assignments with room types
            assignments_query = """
                                SELECT ra.assignment_id, ra.student_id, r.room_type
                                FROM room_assignments ra
                                         INNER JOIN rooms r ON ra.room_id = r.room_id
                                WHERE ra.status = 'Active' \
                                """

            assignments = db.execute_query(assignments_query)

            dues_created = 0

            for assignment in assignments:
                assignment_id,student_id,room_type = assignment

                # Get rent amount for this room type
                fee_query = """
                            SELECT fs.amount, fs.category_id
                            FROM fee_structure fs
                                     INNER JOIN payment_categories pc ON fs.category_id = pc.category_id
                            WHERE fs.room_type = %s \
                              AND pc.category_name = 'Monthly Rent' \
                              AND fs.is_active = TRUE LIMIT 1 \
                            """

                fee_result = db.execute_query(fee_query,(room_type,))

                if fee_result:
                    amount,category_id = fee_result[0]

                    # Insert due if not already exists for this month
                    insert_due_query = """
                                       INSERT \
                                       IGNORE INTO outstanding_dues 
                    (student_id, assignment_id, category_id, amount_due, due_date, month_year)
                    VALUES ( \
                                       %s, \
                                       %s, \
                                       %s, \
                                       %s, \
                                       %s, \
                                       %s \
                                       ) \
                                       """

                    result = db.execute_update(insert_due_query,(
                        student_id,assignment_id,category_id,amount,due_date,month_year
                    ))

                    if result > 0:
                        dues_created += 1

            return True,f"Generated {dues_created} monthly dues for {month_year}"

        except Exception as e:
            print(f"Error generating monthly dues: {e}")
            return False,f"Error generating dues: {e}"

    @staticmethod
    def get_payment_statistics():
        """Get payment statistics for dashboard"""
        try:
            stats = {}

            # Total payments this month
            result = db.execute_query("""
                                      SELECT COUNT(*) as count, COALESCE(SUM(amount), 0) as total
                                      FROM payments
                                      WHERE payment_date >= DATE_FORMAT(CURDATE()
                                          , '%Y-%m-01')
                                        AND payment_status = 'Completed'
                                      """)
            stats['monthly_payments'] = {'count': result[0][0],'total': float(result[0][1])} if result else {'count': 0,
                                                                                                             'total': 0.0}

            # Outstanding dues
            result = db.execute_query("""
                                      SELECT COUNT(*) as count, COALESCE(SUM(amount_due + late_fee_applied), 0) as total
                                      FROM outstanding_dues
                                      WHERE is_paid = FALSE
                                      """)
            stats['outstanding_dues'] = {'count': result[0][0],'total': float(result[0][1])} if result else {'count': 0,
                                                                                                             'total': 0.0}

            # Overdue payments
            result = db.execute_query("""
                                      SELECT COUNT(*) as count, COALESCE(SUM(amount_due + late_fee_applied), 0) as total
                                      FROM outstanding_dues
                                      WHERE is_paid = FALSE AND due_date < CURDATE()
                                      """)
            stats['overdue_payments'] = {'count': result[0][0],'total': float(result[0][1])} if result else {'count': 0,
                                                                                                             'total': 0.0}

            # Payment methods breakdown
            result = db.execute_query("""
                                      SELECT payment_method, COUNT(*) as count, SUM(amount) as total
                                      FROM payments
                                      WHERE payment_date >= DATE_FORMAT(CURDATE()
                                          , '%Y-%m-01')
                                        AND payment_status = 'Completed'
                                      GROUP BY payment_method
                                      ORDER BY total DESC
                                      """)
            stats['payment_methods'] = result if result else []

            # Recent payments
            result = db.execute_query("""
                                      SELECT p.payment_id,
                                             p.amount,
                                             p.payment_date,
                                             p.payment_method,
                                             s.first_name,
                                             s.last_name,
                                             pc.category_name
                                      FROM payments p
                                               INNER JOIN students s ON p.student_id = s.student_id
                                               INNER JOIN payment_categories pc ON p.category_id = pc.category_id
                                      WHERE p.payment_status = 'Completed'
                                      ORDER BY p.payment_date DESC, p.created_at DESC LIMIT 10
                                      """)
            stats['recent_payments'] = result if result else []

            return stats

        except Exception as e:
            print(f"Error getting payment statistics: {e}")
            return {}

    @staticmethod
    def search_payments(search_term,status_filter=None):
        """Search payments by student name, receipt number, or reference number"""
        try:
            query = """
                    SELECT p.payment_id, \
                           p.student_id, \
                           p.amount, \
                           p.payment_date, \
                           p.payment_method,
                           p.payment_status, \
                           p.reference_number, \
                           p.receipt_number, \
                           p.late_fee,
                           s.student_number, \
                           s.first_name, \
                           s.last_name, \
                           s.email,
                           pc.category_name, \
                           r.room_number
                    FROM payments p
                             INNER JOIN students s ON p.student_id = s.student_id
                             INNER JOIN payment_categories pc ON p.category_id = pc.category_id
                             LEFT JOIN room_assignments ra ON p.assignment_id = ra.assignment_id
                             LEFT JOIN rooms r ON ra.room_id = r.room_id
                    WHERE (s.first_name LIKE %s OR s.last_name LIKE %s OR s.student_number LIKE %s
                        OR p.reference_number LIKE %s OR p.receipt_number LIKE %s) \
                    """

            search_pattern = f"%{search_term}%"
            params = [search_pattern] * 5

            if status_filter:
                query += " AND p.payment_status = %s"
                params.append(status_filter)

            query += " ORDER BY p.payment_date DESC"

            return db.execute_query(query,params)
        except Exception as e:
            print(f"Error searching payments: {e}")
            return []

# ADD THESE METHODS to your AssignmentDB class in models/database.py
# Place these after your existing methods in the AssignmentDB class

@staticmethod
def checkout_student(assignment_id,checkout_date):
    """Check out a student from their room"""
    try:
        # Get current assignment details
        assignment = db.execute_query(
            """SELECT ra.student_id, ra.room_id, r.capacity, r.current_occupancy
               FROM room_assignments ra
                        INNER JOIN rooms r ON ra.room_id = r.room_id
               WHERE ra.assignment_id = %s
                 AND ra.status = 'Active'""",
            (assignment_id,)
        )

        if not assignment:
            return False,"Assignment not found or not active"

        student_id,room_id,capacity,current_occupancy = assignment[0]

        # Update assignment status and checkout date
        updated = db.execute_update(
            """UPDATE room_assignments
               SET status        = 'Completed',
                   checkout_date = %s
               WHERE assignment_id = %s""",
            (checkout_date,assignment_id)
        )

        if updated:
            # Update room occupancy
            new_occupancy = max(0,current_occupancy - 1)

            db.execute_update(
                """UPDATE rooms
                   SET current_occupancy = %s,
                       status            = CASE
                                               WHEN %s = 0 THEN 'Available'
                                               WHEN %s < capacity THEN 'Available'
                                               ELSE 'Occupied' END
                   WHERE room_id = %s""",
                (new_occupancy,new_occupancy,new_occupancy,room_id)
            )

            return True,"Student checked out successfully"

        return False,"Failed to check out student"

    except Exception as e:
        print(f"Error checking out student: {e}")
        return False,f"Database error: {e}"


@staticmethod
def transfer_student(assignment_id,new_room_id,transfer_date):
    """Transfer student to a different room"""
    try:
        # Get current assignment
        current = db.execute_query(
            """SELECT ra.student_id, ra.room_id, ra.assigned_date
               FROM room_assignments ra
               WHERE ra.assignment_id = %s
                 AND ra.status = 'Active'""",
            (assignment_id,)
        )

        if not current:
            return False,"Assignment not found or not active"

        student_id,old_room_id,assigned_date = current[0]

        # Check new room availability
        room_check = db.execute_query(
            "SELECT capacity, current_occupancy FROM rooms WHERE room_id = %s",
            (new_room_id,)
        )

        if not room_check:
            return False,"New room not found"

        capacity,current_occupancy = room_check[0]
        if current_occupancy >= capacity:
            return False,"New room is at full capacity"

        # Close old assignment
        db.execute_update(
            """UPDATE room_assignments
               SET status        = 'Transferred',
                   checkout_date = %s
               WHERE assignment_id = %s""",
            (transfer_date,assignment_id)
        )

        # Create new assignment
        new_assignment_id = db.execute_insert(
            """INSERT INTO room_assignments (student_id, room_id, assigned_date, status)
               VALUES (%s, %s, %s, 'Active')""",
            (student_id,new_room_id,transfer_date)
        )

        if new_assignment_id:
            # Update old room occupancy
            db.execute_update(
                """UPDATE rooms
                   SET current_occupancy = current_occupancy - 1,
                       status            = CASE
                                               WHEN current_occupancy - 1 = 0 THEN 'Available'
                                               WHEN current_occupancy - 1 < capacity THEN 'Available'
                                               ELSE 'Occupied' END
                   WHERE room_id = %s""",
                (old_room_id,)
            )

            # Update new room occupancy
            db.execute_update(
                """UPDATE rooms
                   SET current_occupancy = current_occupancy + 1,
                       status            = CASE
                                               WHEN current_occupancy + 1 >= capacity THEN 'Occupied'
                                               ELSE 'Available' END
                   WHERE room_id = %s""",
                (new_room_id,)
            )

            return True,"Student transferred successfully"

        return False,"Failed to create new assignment"

    except Exception as e:
        print(f"Error transferring student: {e}")
        return False,f"Database error: {e}"


@staticmethod
def get_assignment_history(student_id=None,room_id=None,limit=50):
    """Get assignment history with optional filters"""
    try:
        query = """
                SELECT ra.assignment_id, \
                       ra.student_id, \
                       ra.room_id, \
                       ra.assigned_date,
                       ra.checkout_date, \
                       ra.status, \
                       ra.created_at,
                       s.student_number, \
                       s.first_name, \
                       s.last_name,
                       r.room_number, \
                       r.room_type
                FROM room_assignments ra
                         INNER JOIN students s ON ra.student_id = s.student_id
                         INNER JOIN rooms r ON ra.room_id = r.room_id
                WHERE 1 = 1 \
                """

        params = []

        if student_id:
            query += " AND ra.student_id = %s"
            params.append(student_id)

        if room_id:
            query += " AND ra.room_id = %s"
            params.append(room_id)

        query += " ORDER BY ra.created_at DESC"

        if limit:
            query += f" LIMIT {limit}"

        return db.execute_query(query,params)

    except Exception as e:
        print(f"Error getting assignment history: {e}")
        return []
# Create global database instance
db = Database()

# Test the connection on import (optional)
if __name__ == "__main__":
    print("Testing database connection...")
    try:
        db.connect()
        result = db.execute_query("SELECT COUNT(*) FROM students")
        print(f"✅ Connection successful! Students count: {result[0][0] if result else 0}")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("💡 Make sure MySQL is running and password is correct")