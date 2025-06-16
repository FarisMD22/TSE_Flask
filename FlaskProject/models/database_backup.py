import mysql.connector
from mysql.connector import Error
from config import Config


def create_database()

    """Create database and tables with proper foreign key constraints"""
    print("🚀 Starting database setup...")
    print("=" * 60)

    try:
        # Connect to MySQL server (without specifying database)
        print("🔌 Connecting to MySQL server...")
        connection = mysql.connector.connect(
            host=Config.DB_HOST,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD
        )

        cursor = connection.cursor()
        print("✅ Connected to MySQL server!")

        # Create database
        print("📁 Creating database...")
        cursor.execute(f"DROP DATABASE IF EXISTS {Config.DB_NAME}")
        cursor.execute(f"CREATE DATABASE {Config.DB_NAME}")
        print(f"✅ Database '{Config.DB_NAME}' created successfully!")

        # Use the database
        cursor.execute(f"USE {Config.DB_NAME}")

        # Create tables in the correct order (to handle foreign key constraints)
        tables = []

        # 1. Users table (no foreign keys)
        tables.append({
            'name': 'users',
            'sql': """
                   CREATE TABLE users
                   (
                       user_id    INT PRIMARY KEY AUTO_INCREMENT,
                       username   VARCHAR(50) UNIQUE NOT NULL,
                       password   VARCHAR(255)       NOT NULL,
                       role       ENUM('Admin', 'Staff', 'Warden') NOT NULL,
                       full_name  VARCHAR(100)       NOT NULL,
                       email      VARCHAR(100),
                       phone      VARCHAR(15),
                       status     ENUM('Active', 'Inactive') DEFAULT 'Active',
                       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                   ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                   """
        })

        # 2. Students table (no foreign keys)
        tables.append({
            'name': 'students',
            'sql': """
                   CREATE TABLE students
                   (
                       student_id     INT PRIMARY KEY AUTO_INCREMENT,
                       student_number VARCHAR(20) UNIQUE NOT NULL,
                       first_name     VARCHAR(50)        NOT NULL,
                       last_name      VARCHAR(50)        NOT NULL,
                       email          VARCHAR(100) UNIQUE,
                       phone          VARCHAR(15),
                       address        TEXT,
                       guardian_name  VARCHAR(100),
                       guardian_phone VARCHAR(15),
                       course         VARCHAR(100),
                       year_of_study  INT,
                       date_joined    DATE,
                       status         ENUM('Active', 'Inactive', 'Graduated') DEFAULT 'Active',
                       created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                       INDEX          idx_student_number (student_number),
                       INDEX          idx_email (email),
                       INDEX          idx_status (status)
                   ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                   """
        })

        # 3. Rooms table (no foreign keys)
        tables.append({
            'name': 'rooms',
            'sql': """
                   CREATE TABLE rooms
                   (
                       room_id           INT PRIMARY KEY AUTO_INCREMENT,
                       room_number       VARCHAR(10) UNIQUE NOT NULL,
                       room_type         ENUM('Single', 'Double', 'Triple', 'Quad') NOT NULL,
                       capacity          INT                NOT NULL,
                       current_occupancy INT       DEFAULT 0,
                       floor_number      INT,
                       rent_amount       DECIMAL(10, 2),
                       status            ENUM('Available', 'Occupied', 'Maintenance', 'Reserved') DEFAULT 'Available',
                       created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                       INDEX             idx_room_number (room_number),
                       INDEX             idx_status (status)
                   ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                   """
        })

        # 4. Room assignments table (has foreign keys to students and rooms)
        tables.append({
            'name': 'room_assignments',
            'sql': """
                   CREATE TABLE room_assignments
                   (
                       assignment_id INT PRIMARY KEY AUTO_INCREMENT,
                       student_id    INT  NOT NULL,
                       room_id       INT  NOT NULL,
                       assigned_date DATE NOT NULL,
                       checkout_date DATE,
                       status        ENUM('Active', 'Completed', 'Cancelled') DEFAULT 'Active',
                       created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                       FOREIGN KEY (student_id) REFERENCES students (student_id) ON DELETE CASCADE,
                       FOREIGN KEY (room_id) REFERENCES rooms (room_id) ON DELETE CASCADE,
                       INDEX         idx_student_id (student_id),
                       INDEX         idx_room_id (room_id),
                       INDEX         idx_status (status)
                   ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                   """
        })

        # 5. Fee payments table (has foreign key to students)
        tables.append({
            'name': 'fee_payments',
            'sql': """
                   CREATE TABLE fee_payments
                   (
                       payment_id     INT PRIMARY KEY AUTO_INCREMENT,
                       student_id     INT            NOT NULL,
                       amount         DECIMAL(10, 2) NOT NULL,
                       payment_date   DATE           NOT NULL,
                       payment_type   ENUM('Room Rent', 'Admission Fee', 'Security Deposit', 'Fine', 'Other'),
                       payment_method ENUM('Cash', 'Bank Transfer', 'Card', 'Online') DEFAULT 'Cash',
                       receipt_number VARCHAR(50) UNIQUE,
                       status         ENUM('Pending', 'Completed', 'Failed') DEFAULT 'Completed',
                       created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                       FOREIGN KEY (student_id) REFERENCES students (student_id) ON DELETE CASCADE,
                       INDEX          idx_student_id (student_id),
                       INDEX          idx_payment_date (payment_date),
                       INDEX          idx_receipt_number (receipt_number)
                   ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                   """
        })

        # Create all tables
        for table in tables:
            print(f"📋 Creating table: {table['name']}")
            cursor.execute(table['sql'])
            print(f"✅ Table '{table['name']}' created successfully!")

        # Insert default admin user
        print("👤 Creating default admin user...")
        admin_query = """
                      INSERT INTO users (username, password, role, full_name, email)
                      VALUES (%s, %s, %s, %s, %s) \
                      """
        cursor.execute(admin_query,('admin','admin123','Admin','System Administrator','admin@hostel.com'))
        print("✅ Default admin user created (admin/admin123)")

        # Insert some basic rooms
        print("🏠 Creating basic rooms...")
        basic_rooms = [
            ('101','Single',1,1,500.00),
            ('102','Double',2,1,300.00),
            ('103','Triple',3,1,200.00),
            ('201','Single',1,2,500.00),
            ('202','Double',2,2,300.00),
            ('203','Triple',3,2,200.00),
            ('301','Single',1,3,500.00),
            ('302','Double',2,3,300.00),
            ('303','Triple',3,3,200.00),
            ('401','Single',1,4,500.00)
        ]

        room_query = """
                     INSERT INTO rooms (room_number, room_type, capacity, floor_number, rent_amount)
                     VALUES (%s, %s, %s, %s, %s) \
                     """

        cursor.executemany(room_query,basic_rooms)
        print(f"✅ Created {len(basic_rooms)} basic rooms!")

        connection.commit()

        # Verify tables were created
        print("\n🔍 Verifying database structure...")
        cursor.execute("SHOW TABLES")
        tables_created = cursor.fetchall()
        print("📋 Tables created:")
        for table in tables_created:
            cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
            count = cursor.fetchone()[0]
            print(f"   ✅ {table[0]} ({count} records)")

        print("\n" + "=" * 60)
        print("🎉 DATABASE SETUP COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("📊 Summary:")
        print(f"   🗄️  Database: {Config.DB_NAME}")
        print(f"   📋 Tables: {len(tables_created)}")
        print(f"   👤 Admin user: admin / admin123")
        print(f"   🏠 Sample rooms: {len(basic_rooms)}")
        print("=" * 60)
        print("🚀 You can now:")
        print("   1. Run the application: python app.py")
        print("   2. Populate sample data: python populate_sample_data.py")
        print("   3. Access: http://127.0.0.1:5000")
        print("=" * 60)

    except Error as e:
        print(f"❌ Error creating database: {e}")
        print("\n💡 Troubleshooting:")
        print("   1. Make sure MySQL is running")
        print("   2. Check your MySQL password in the script")
        print("   3. Ensure you have CREATE DATABASE privileges")
        print("   4. Try connecting to MySQL manually first")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("🔌 Database connection closed")


if __name__ == "__main__":
    create_database()