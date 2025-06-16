#!/usr/bin/env python3
"""
Quick test script to check assignment system database connectivity
Run this from your FlaskProject directory: python test_assignments.py
"""

try:
    from models.database import db,AssignmentDB

    print("✅ Successfully imported database modules")
except ImportError as e:
    print(f"❌ Import error: {e}")
    exit(1)


def test_database_connection():
    """Test basic database connectivity"""
    print("\n🔍 Testing database connection...")

    try:
        # Test basic connection
        if db.test_connection():
            print("✅ Database connection successful")
        else:
            print("❌ Database connection failed")
            return False

        # Test if tables exist
        print("\n🔍 Testing table existence...")

        # Check students table
        result = db.execute_query("SELECT COUNT(*) FROM students")
        print(f"✅ Students table: {result[0][0] if result else 0} records")

        # Check rooms table
        result = db.execute_query("SELECT COUNT(*) FROM rooms")
        print(f"✅ Rooms table: {result[0][0] if result else 0} records")

        # Check room_assignments table
        result = db.execute_query("SELECT COUNT(*) FROM room_assignments")
        print(f"✅ Room_assignments table: {result[0][0] if result else 0} records")

        return True

    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False


def test_assignment_functions():
    """Test AssignmentDB functions"""
    print("\n🔍 Testing Assignment functions...")

    try:
        # Test getting unassigned students
        unassigned = AssignmentDB.get_unassigned_students()
        print(f"✅ Unassigned students: {len(unassigned)} found")

        # Test getting available rooms
        available_rooms = AssignmentDB.get_available_rooms()
        print(f"✅ Available rooms: {len(available_rooms)} found")

        # Test getting all assignments
        assignments = AssignmentDB.get_all_assignments()
        print(f"✅ All assignments: {len(assignments)} found")

        # Test getting statistics
        stats = AssignmentDB.get_occupancy_statistics()
        print(f"✅ Statistics loaded: {len(stats)} metrics")

        return True

    except Exception as e:
        print(f"❌ Assignment function test failed: {e}")
        print(f"   Error details: {str(e)}")
        return False


def main():
    print("🚀 Assignment System Database Test")
    print("=" * 50)

    # Test 1: Database Connection
    if not test_database_connection():
        print("\n❌ Database connection failed. Check your MySQL server and credentials.")
        return

    # Test 2: Assignment Functions
    if not test_assignment_functions():
        print("\n❌ Assignment functions failed. Check if AssignmentDB class is properly added.")
        return

    print("\n" + "=" * 50)
    print("🎉 All tests passed! Assignment system should work correctly.")
    print("\nNext steps:")
    print("1. Start your Flask app: python app.py")
    print("2. Visit: http://127.0.0.1:5000/assignments")
    print("3. Try creating a new assignment")


if __name__ == "__main__":
    main()