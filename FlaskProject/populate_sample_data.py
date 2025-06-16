import mysql.connector
from mysql.connector import Error
from datetime import datetime,timedelta
import random


def populate_sample_data():
    """Populate database with sample student data for testing"""
    print("🚀 Starting sample data population...")
    print("📁 Database exists, adding sample data...")
    print("=" * 50)

    try:
        # Connect to database
        print("🔌 Connecting to database...")
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='password',  # ✅ Your actual password
            database='hostel_management'
        )

        cursor = connection.cursor()
        print("✅ Database connection successful!")

        # Check current counts
        print("🔍 Checking current data...")
        cursor.execute("SELECT COUNT(*) FROM students")
        current_students = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM rooms")
        current_rooms = cursor.fetchone()[0]
        print(f"   📊 Current students: {current_students}")
        print(f"   📊 Current rooms: {current_rooms}")

        # Add some basic rooms if none exist
        if current_rooms == 0:
            print("🏠 Adding basic rooms...")
            basic_rooms = [
                ('101','Single',1,1,500.00),
                ('102','Double',2,1,300.00),
                ('103','Triple',3,1,200.00),
                ('201','Single',1,2,500.00),
                ('202','Double',2,2,300.00),
                ('203','Triple',3,2,200.00),
                ('301','Single',1,3,500.00),
                ('302','Double',2,3,300.00)
            ]

            room_query = """
                         INSERT INTO rooms (room_number, room_type, capacity, floor_number, rent_amount)
                         VALUES (%s, %s, %s, %s, %s) \
                         """

            for room_data in basic_rooms:
                cursor.execute(room_query,room_data)
                print(f"   ✅ Added room: {room_data[0]}")

            connection.commit()
            print(f"✅ Added {len(basic_rooms)} rooms!")

        # Add sample students if none exist
        if current_students == 0:
            print("👨‍🎓 Adding sample students...")
            students_data = [
                # (student_number, first_name, last_name, email, phone, address, guardian_name, guardian_phone, course, year_of_study, date_joined)
                ('STU20251001','John','Doe','john.doe@university.edu','+60 12-345-6789','123 Main St, Kuala Lumpur',
                 'Robert Doe','+60 12-111-1111','Computer Science',3,'2023-01-15'),
                ('STU20251002','Sarah','Johnson','sarah.j@university.edu','+60 13-456-7890',
                 '456 Oak Ave, Petaling Jaya','Mary Johnson','+60 13-222-2222','Information Technology',2,'2023-02-01'),
                ('STU20251003','Ahmad','Hassan','ahmad.hassan@university.edu','+60 14-567-8901',
                 '789 Pine Rd, Shah Alam','Abdullah Hassan','+60 14-333-3333','Software Engineering',1,'2024-01-10'),
                ('STU20251004','Emily','Chen','emily.chen@university.edu','+60 15-678-9012','321 Elm St, Subang Jaya',
                 'David Chen','+60 15-444-4444','Data Science',4,'2022-03-20'),
                ('STU20251005','Muhammad','Ali','muhammad.ali@university.edu','+60 16-789-0123',
                 '654 Maple Dr, Cyberjaya','Hassan Ali','+60 16-555-5555','Cybersecurity',2,'2023-05-15'),
                ('STU20251006','Lisa','Wong','lisa.wong@university.edu','+60 17-890-1234','987 Cedar Ln, Ampang',
                 'Peter Wong','+60 17-666-6666','Computer Science',3,'2022-09-01'),
                ('STU20251007','David','Kumar','david.kumar@university.edu','+60 18-901-2345','147 Birch St, Kajang',
                 'Raj Kumar','+60 18-777-7777','Information Systems',1,'2024-02-14'),
                ('STU20251008','Aisha','Ibrahim','aisha.ibrahim@university.edu','+60 19-012-3456',
                 '258 Spruce Ave, Putrajaya','Fatimah Ibrahim','+60 19-888-8888','Digital Media',2,'2023-08-10')
            ]

            # Insert students
            insert_student_query = """
                                   INSERT INTO students (student_number, first_name, last_name, email, phone, address,
                                                         guardian_name, guardian_phone, course, year_of_study, \
                                                         date_joined)
                                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) \
                                   """

            student_ids = []
            for student_data in students_data:
                cursor.execute(insert_student_query,student_data)
                student_ids.append(cursor.lastrowid)
                print(f"   ✅ Added student: {student_data[1]} {student_data[2]} (ID: {cursor.lastrowid})")

            connection.commit()
            print(f"✅ Added {len(students_data)} students!")

            # Get available rooms
            cursor.execute("SELECT room_id, room_number FROM rooms ORDER BY room_id")
            available_rooms = cursor.fetchall()

            # Assign some students to rooms
            print("🏠 Assigning students to rooms...")
            room_assignments = []

            # Assign first 5 students to first 5 rooms
            for i in range(min(5,len(student_ids),len(available_rooms))):
                student_id = student_ids[i]
                room_id = available_rooms[i][0]
                room_number = available_rooms[i][1]
                assigned_date = (datetime.now() - timedelta(days=random.randint(1,180))).date()

                room_assignments.append((student_id,room_id,assigned_date))
                print(f"   ✅ Assigned student ID {student_id} to room {room_number}")

            if room_assignments:
                assignment_query = """
                                   INSERT INTO room_assignments (student_id, room_id, assigned_date, status)
                                   VALUES (%s, %s, %s, 'Active') \
                                   """

                cursor.executemany(assignment_query,room_assignments)
                connection.commit()
                print(f"✅ Created {len(room_assignments)} room assignments!")

                # Update room occupancy
                update_room_query = """
                                    UPDATE rooms \
                                    SET current_occupancy = (SELECT COUNT(*) \
                                                             FROM room_assignments \
                                                             WHERE room_assignments.room_id = rooms.room_id \
                                                               AND room_assignments.status = 'Active'), \
                                        status            = CASE \
                                                                WHEN (SELECT COUNT(*) \
                                                                      FROM room_assignments \
                                                                      WHERE room_assignments.room_id = rooms.room_id \
                                                                        AND room_assignments.status = 'Active') >= \
                                                                     capacity THEN 'Occupied' \
                                                                ELSE 'Available' \
                                            END \
                                    """
                cursor.execute(update_room_query)
                connection.commit()
                print("✅ Room occupancy updated!")

            # Add some sample payments
            print("💰 Adding sample payment records...")
            payments_data = []
            for i,student_id in enumerate(student_ids[:5]):  # Payments for first 5 students
                # Each student gets 2-3 payment records
                for j in range(random.randint(2,3)):
                    amount = random.choice([500.00,300.00,1000.00,200.00])
                    payment_date = (datetime.now() - timedelta(days=random.randint(1,120))).date()
                    payment_type = random.choice(['Room Rent','Admission Fee','Security Deposit'])
                    payment_method = random.choice(['Cash','Bank Transfer','Online'])
                    receipt_number = f"RCP{payment_date.strftime('%Y%m%d')}{student_id:03d}{j + 1}"

                    payments_data.append((
                        student_id,amount,payment_date,payment_type,
                        payment_method,receipt_number,'Completed'
                    ))

            payment_query = """
                            INSERT INTO fee_payments (student_id, amount, payment_date, payment_type, payment_method, \
                                                      receipt_number, status)
                            VALUES (%s, %s, %s, %s, %s, %s, %s) \
                            """

            cursor.executemany(payment_query,payments_data)
            connection.commit()
            print(f"✅ Added {len(payments_data)} payment records!")

        # Final statistics
        print("\n" + "=" * 50)
        print("📊 FINAL DATABASE STATUS")
        print("=" * 50)

        cursor.execute("SELECT COUNT(*) FROM students")
        total_students = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM rooms")
        total_rooms = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM room_assignments WHERE status = 'Active'")
        active_assignments = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM fee_payments")
        total_payments = cursor.fetchone()[0]

        print(f"👨‍🎓 Total Students: {total_students}")
        print(f"🏠 Total Rooms: {total_rooms}")
        print(f"🔗 Active Room Assignments: {active_assignments}")
        print(f"💰 Payment Records: {total_payments}")
        print("=" * 50)
        print("🎉 DATABASE POPULATED SUCCESSFULLY!")
        print("🚀 Your Flask app should now work with data!")
        print("🔗 Go to: http://127.0.0.1:5000")
        print("=" * 50)

    except Error as e:
        print(f"❌ Error populating data: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("🔌 Database connection closed")


if __name__ == "__main__":
    populate_sample_data()