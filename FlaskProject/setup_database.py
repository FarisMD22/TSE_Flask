import mysql.connector
from config import Config
import mysql.connector
from mysql.connector import Error



def create_database():
    connection = None  # Initialize connection variable
    try:
        # Connect without specifying a database first
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='password',  #Set the password directly here
        )

        if connection.is_connected():
            cursor = connection.cursor()

            # Create database
            cursor.execute("CREATE DATABASE IF NOT EXISTS your_database_name")
            print("Database created successfully")

            # Use the database
            cursor.execute("USE your_database_name")

            # Create your tables here
            # cursor.execute("CREATE TABLE IF NOT EXISTS ...")

        # Create tables
        tables = [
            # Users table
            """
            CREATE TABLE IF NOT EXISTS users
            (
                user_id
                INT
                PRIMARY
                KEY
                AUTO_INCREMENT,
                username
                VARCHAR
            (
                50
            ) UNIQUE NOT NULL,
                password VARCHAR
            (
                255
            ) NOT NULL,
                role ENUM
            (
                'Admin',
                'Staff',
                'Warden'
            ) NOT NULL,
                full_name VARCHAR
            (
                100
            ) NOT NULL,
                email VARCHAR
            (
                100
            ),
                phone VARCHAR
            (
                15
            ),
                status ENUM
            (
                'Active',
                'Inactive'
            ) DEFAULT 'Active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """,

            # Students table
            """
            CREATE TABLE IF NOT EXISTS students
            (
                student_id
                INT
                PRIMARY
                KEY
                AUTO_INCREMENT,
                student_number
                VARCHAR
            (
                20
            ) UNIQUE NOT NULL,
                first_name VARCHAR
            (
                50
            ) NOT NULL,
                last_name VARCHAR
            (
                50
            ) NOT NULL,
                email VARCHAR
            (
                100
            ) UNIQUE,
                phone VARCHAR
            (
                15
            ),
                address TEXT,
                guardian_name VARCHAR
            (
                100
            ),
                guardian_phone VARCHAR
            (
                15
            ),
                course VARCHAR
            (
                100
            ),
                year_of_study INT,
                date_joined DATE,
                status ENUM
            (
                'Active',
                'Inactive',
                'Graduated'
            ) DEFAULT 'Active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """,

            # Rooms table
            """
            CREATE TABLE IF NOT EXISTS rooms
            (
                room_id
                INT
                PRIMARY
                KEY
                AUTO_INCREMENT,
                room_number
                VARCHAR
            (
                10
            ) UNIQUE NOT NULL,
                room_type ENUM
            (
                'Single',
                'Double',
                'Triple',
                'Quad'
            ) NOT NULL,
                capacity INT NOT NULL,
                current_occupancy INT DEFAULT 0,
                floor_number INT,
                rent_amount DECIMAL
            (
                10,
                2
            ),
                status ENUM
            (
                'Available',
                'Occupied',
                'Maintenance',
                'Reserved'
            ) DEFAULT 'Available',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """,

            # Room assignments table
            """
            CREATE TABLE IF NOT EXISTS room_assignments
            (
                assignment_id
                INT
                PRIMARY
                KEY
                AUTO_INCREMENT,
                student_id
                INT,
                room_id
                INT,
                assigned_date
                DATE
                NOT
                NULL,
                checkout_date
                DATE,
                status
                ENUM
            (
                'Active',
                'Completed',
                'Cancelled'
            ) DEFAULT 'Active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY
            (
                student_id
            ) REFERENCES students
            (
                student_id
            ) ON DELETE CASCADE,
                FOREIGN KEY
            (
                room_id
            ) REFERENCES rooms
            (
                room_id
            )
              ON DELETE CASCADE
                )
            """,

            # Fee payments table
            """
            CREATE TABLE IF NOT EXISTS fee_payments
            (
                payment_id
                INT
                PRIMARY
                KEY
                AUTO_INCREMENT,
                student_id
                INT,
                amount
                DECIMAL
            (
                10,
                2
            ) NOT NULL,
                payment_date DATE NOT NULL,
                payment_type ENUM
            (
                'Room Rent',
                'Admission Fee',
                'Security Deposit',
                'Fine',
                'Other'
            ),
                payment_method ENUM
            (
                'Cash',
                'Bank Transfer',
                'Card',
                'Online'
            ) DEFAULT 'Cash',
                receipt_number VARCHAR
            (
                50
            ) UNIQUE,
                status ENUM
            (
                'Pending',
                'Completed',
                'Failed'
            ) DEFAULT 'Completed',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY
            (
                student_id
            ) REFERENCES students
            (
                student_id
            ) ON DELETE CASCADE
                )
            """
        ]

        for table in tables:
            cursor.execute(table)

        # Insert default admin user
        admin_query = """
                      INSERT INTO users (username, password, role, full_name, email)
                      VALUES (%s, %s, %s, %s, %s) ON DUPLICATE KEY \
                      UPDATE username=username \
                      """
        # Note: In production, hash this password properly
        cursor.execute(admin_query,('admin','admin123','Admin','System Administrator','admin@hostel.com'))

        connection.commit()
        print("Database and tables created successfully!")

    except Error as e:

        print(f"Error creating database: {e}")

    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

    print("MySQL connection closed")


if __name__ == "__main__":
    create_database()