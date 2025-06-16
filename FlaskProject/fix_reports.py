import mysql.connector


def fix_reports_data():
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='password',  # Your password
            database='hostel_management'
        )

        cursor = conn.cursor()

        print("Adding sample data for reports...")

        # Add students if needed
        cursor.execute("""
                       INSERT
                       IGNORE INTO students (student_number, first_name, last_name, email, course, date_joined, status) VALUES
            ('CS001', 'Ahmed', 'Rahman', 'ahmed@student.mmu.edu.my', 'Computer Science', '2025-05-15', 'Active'),
            ('CS002', 'Siti', 'Nurhaliza', 'siti@student.mmu.edu.my', 'Computer Science', '2025-05-20', 'Active'),
            ('BA001', 'Michael', 'Tan', 'michael@student.mmu.edu.my', 'Business', '2025-05-25', 'Active')
                       """)

        # Add assignments
        cursor.execute("""
                       INSERT
                       IGNORE INTO room_assignments (student_id, room_id, assigned_date, status) VALUES
            (1, 1, '2025-05-15', 'Active'),
            (2, 2, '2025-05-20', 'Active'),
            (3, 3, '2025-05-25', 'Active')
                       """)

        # Add payments
        cursor.execute("""
                       INSERT
                       IGNORE INTO payments (student_id, category_id, amount, payment_date, payment_method, payment_status, reference_number, receipt_number, processed_by) VALUES
            (1, 1, 800.00, '2025-05-15', 'Bank Transfer', 'Completed', 'PAY001', 'RCP001', 'Admin'),
            (2, 1, 600.00, '2025-05-20', 'Cash', 'Completed', 'PAY002', 'RCP002', 'Admin'),
            (3, 1, 500.00, '2025-05-25', 'Card', 'Completed', 'PAY003', 'RCP003', 'Admin'),
            (1, 1, 800.00, '2025-06-01', 'Bank Transfer', 'Completed', 'PAY004', 'RCP004', 'Admin')
                       """)

        conn.commit()
        print("✅ Sample data added successfully!")

        # Verify
        cursor.execute("SELECT COUNT(*) FROM students")
        print(f"Students: {cursor.fetchone()[0]}")

        cursor.execute("SELECT COUNT(*) FROM payments")
        print(f"Payments: {cursor.fetchone()[0]}")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    fix_reports_data()