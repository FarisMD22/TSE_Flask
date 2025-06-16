from models.database import b

print("Testing database connection...")
try:
    db.connect()
    result = db.execute_query("SELECT COUNT(*) FROM students")
    print(f"✅ Connection successful! Students count: {result[0][0] if result else 0}")

    # Test each table
    tables = ['students','rooms','users','room_assignments','fee_payments']
    for table in tables:
        try:
            result = db.execute_query(f"SELECT COUNT(*) FROM {table}")
            count = result[0][0] if result else 0
            print(f"✅ {table}: {count} records")
        except Exception as e:
            print(f"❌ {table}: Error - {e}")

except Exception as e:
    print(f"❌ Database connection failed: {e}")
    print("💡 Check your MySQL password and make sure MySQL is running")