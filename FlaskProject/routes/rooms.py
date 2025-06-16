from flask import Blueprint,render_template,request,redirect,url_for,flash,session
from models.database import db
from models.user import has_permission

# simple in-memory booking storage
bookings = []

# Create rooms blueprint
rooms_bp = Blueprint('rooms',__name__,url_prefix='/rooms')


class RoomDB:
    """Room database operations class"""

    @staticmethod
    def get_all_rooms():
        """Get all rooms with occupancy details"""
        try:
            query = """
                    SELECT r.room_id, \
                           r.room_number, \
                           r.room_type, \
                           r.capacity,
                           r.current_occupancy, \
                           r.floor_number, \
                           r.rent_amount, \
                           r.status,
                           r.created_at,
                           COUNT(ra.assignment_id) as assigned_count
                    FROM rooms r
                             LEFT JOIN room_assignments ra ON r.room_id = ra.room_id AND ra.status = 'Active'
                    GROUP BY r.room_id, r.room_number, r.room_type, r.capacity,
                             r.current_occupancy, r.floor_number, r.rent_amount, r.status, r.created_at
                    ORDER BY r.room_number \
                    """
            return db.execute_query(query)
        except Exception as e:
            print(f"Error getting rooms: {e}")
            return []

    @staticmethod
    def get_room_by_id(room_id):
        """Get room by ID with detailed information"""
        try:
            query = """
                    SELECT r.room_id, \
                           r.room_number, \
                           r.room_type, \
                           r.capacity,
                           r.current_occupancy, \
                           r.floor_number, \
                           r.rent_amount, \
                           r.status,
                           r.created_at
                    FROM rooms r
                    WHERE r.room_id = %s \
                    """
            result = db.execute_query(query,(room_id,))
            return result[0] if result else None
        except Exception as e:
            print(f"Error getting room by ID: {e}")
            return None

    @staticmethod
    def get_room_students(room_id):
        """Get students assigned to a specific room"""
        try:
            query = """
                    SELECT s.student_id, \
                           s.student_number, \
                           s.first_name, \
                           s.last_name,
                           s.email, \
                           s.phone, \
                           ra.assigned_date, \
                           ra.status
                    FROM students s
                             INNER JOIN room_assignments ra ON s.student_id = ra.student_id
                    WHERE ra.room_id = %s \
                      AND ra.status = 'Active'
                    ORDER BY ra.assigned_date \
                    """
            return db.execute_query(query,(room_id,))
        except Exception as e:
            print(f"Error getting room students: {e}")
            return []

    @staticmethod
    def add_room(room_data):
        """Add new room"""
        try:
            query = """
                    INSERT INTO rooms (room_number, room_type, capacity, floor_number, rent_amount, status)
                    VALUES (%s, %s, %s, %s, %s, %s) \
                    """
            values = (
                room_data['room_number'],
                room_data['room_type'],
                int(room_data['capacity']),
                int(room_data['floor_number']),
                float(room_data['rent_amount']),
                'Available'  # Default status
            )
            return db.execute_insert(query,values)
        except Exception as e:
            print(f"Error adding room: {e}")
            return None

    @staticmethod
    def update_room(room_id,room_data):
        """Update room information"""
        try:
            query = """
                    UPDATE rooms
                    SET room_number  = %s, \
                        room_type    = %s, \
                        capacity     = %s,
                        floor_number = %s, \
                        rent_amount  = %s, \
                        status       = %s
                    WHERE room_id = %s \
                    """
            values = (
                room_data['room_number'],
                room_data['room_type'],
                int(room_data['capacity']),
                int(room_data['floor_number']),
                float(room_data['rent_amount']),
                room_data['status'],
                room_id
            )
            return db.execute_update(query,values) > 0
        except Exception as e:
            print(f"Error updating room: {e}")
            return False

    @staticmethod
    def delete_room(room_id):
        """Delete room (only if no active assignments)"""
        try:
            # Check for active assignments
            check_query = "SELECT COUNT(*) FROM room_assignments WHERE room_id = %s AND status = 'Active'"
            result = db.execute_query(check_query,(room_id,))

            if result and result[0][0] > 0:
                return False,"Cannot delete room with active assignments"

            # Delete the room
            success = db.execute_update("DELETE FROM rooms WHERE room_id = %s",(room_id,)) > 0
            return success,"Room deleted successfully" if success else "Failed to delete room"
        except Exception as e:
            print(f"Error deleting room: {e}")
            return False,f"Error: {e}"

    @staticmethod
    def get_available_rooms():
        """Get rooms available for assignment"""
        try:
            query = """
                    SELECT room_id, room_number, room_type, capacity, current_occupancy, rent_amount
                    FROM rooms
                    WHERE status = 'Available' \
                      AND current_occupancy < capacity
                    ORDER BY room_number \
                    """
            return db.execute_query(query)
        except Exception as e:
            print(f"Error getting available rooms: {e}")
            return []

    @staticmethod
    def update_room_occupancy():
        """Update room occupancy counts and status"""
        try:
            query = """
                    UPDATE rooms \
                    SET current_occupancy = (SELECT COUNT(*) \
                                             FROM room_assignments \
                                             WHERE room_assignments.room_id = rooms.room_id \
                                               AND room_assignments.status = 'Active'), \
                        status            = CASE \
                                                WHEN (SELECT COUNT(*) \
                                                      FROM room_assignments \
                                                      WHERE room_assignments.room_id = rooms.room_id \
                                                        AND room_assignments.status = 'Active') >= capacity \
                                                    THEN 'Occupied' \
                                                WHEN status = 'Maintenance' THEN 'Maintenance' \
                                                ELSE 'Available' \
                            END \
                    """
            return db.execute_update(query) >= 0
        except Exception as e:
            print(f"Error updating room occupancy: {e}")
            return False


# Route handlers
@rooms_bp.route('/')
def list_rooms():
    """Display all rooms"""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    try:
        rooms = RoomDB.get_all_rooms()

        # Calculate statistics
        total_rooms = len(rooms)
        available_rooms = len([r for r in rooms if r[7] == 'Available'])
        occupied_rooms = len([r for r in rooms if r[7] == 'Occupied'])
        maintenance_rooms = len([r for r in rooms if r[7] == 'Maintenance'])

        stats = {
            'total_rooms': total_rooms,
            'available_rooms': available_rooms,
            'occupied_rooms': occupied_rooms,
            'maintenance_rooms': maintenance_rooms,
            'occupancy_rate': round((occupied_rooms / total_rooms * 100) if total_rooms > 0 else 0,1)
        }

        return render_template('rooms/list.html',rooms=rooms,stats=stats)
    except Exception as e:
        print(f"Error in list_rooms: {e}")
        flash('Error loading rooms','error')
        return redirect(url_for('dashboard'))


@rooms_bp.route('/add',methods=['GET','POST'])
def add_room():
    """Add new room"""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        try:
            room_data = {
                'room_number': request.form['room_number'].strip(),
                'room_type': request.form['room_type'],
                'capacity': request.form['capacity'],
                'floor_number': request.form['floor_number'],
                'rent_amount': request.form['rent_amount']
            }

            # Validation
            if not room_data['room_number']:
                flash('Room number is required','error')
                return render_template('rooms/add.html')

            if int(room_data['capacity']) <= 0:
                flash('Capacity must be greater than 0','error')
                return render_template('rooms/add.html')

            # Check if room number already exists
            existing = db.execute_query("SELECT room_id FROM rooms WHERE room_number = %s",
                                        (room_data['room_number'],))
            if existing:
                flash('Room number already exists','error')
                return render_template('rooms/add.html')

            # Add room
            room_id = RoomDB.add_room(room_data)
            if room_id:
                flash(f'Room {room_data["room_number"]} added successfully!','success')
                return redirect(url_for('rooms.list_rooms'))
            else:
                flash('Error adding room','error')
        except Exception as e:
            print(f"Error adding room: {e}")
            flash('Error adding room','error')

    return render_template('rooms/add.html')


@rooms_bp.route('/view/<int:room_id>')
def view_room(room_id):
    """View room details"""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    try:
        room = RoomDB.get_room_by_id(room_id)
        if not room:
            flash('Room not found','error')
            return redirect(url_for('rooms.list_rooms'))

        students = RoomDB.get_room_students(room_id)

        return render_template('rooms/view.html',room=room,students=students)
    except Exception as e:
        print(f"Error viewing room: {e}")
        flash('Error loading room details','error')
        return redirect(url_for('rooms.list_rooms'))


@rooms_bp.route('/edit/<int:room_id>',methods=['GET','POST'])
def edit_room(room_id):
    """Edit room details"""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    try:
        room = RoomDB.get_room_by_id(room_id)
        if not room:
            flash('Room not found','error')
            return redirect(url_for('rooms.list_rooms'))

        if request.method == 'POST':
            room_data = {
                'room_number': request.form['room_number'].strip(),
                'room_type': request.form['room_type'],
                'capacity': request.form['capacity'],
                'floor_number': request.form['floor_number'],
                'rent_amount': request.form['rent_amount'],
                'status': request.form['status']
            }

            # Validation
            if not room_data['room_number']:
                flash('Room number is required','error')
                return render_template('rooms/edit.html',room=room)

            if int(room_data['capacity']) <= 0:
                flash('Capacity must be greater than 0','error')
                return render_template('rooms/edit.html',room=room)

            # Check if room number exists (excluding current room)
            existing = db.execute_query("SELECT room_id FROM rooms WHERE room_number = %s AND room_id != %s",
                                        (room_data['room_number'],room_id))
            if existing:
                flash('Room number already exists','error')
                return render_template('rooms/edit.html',room=room)

            # Update room
            if RoomDB.update_room(room_id,room_data):
                flash(f'Room {room_data["room_number"]} updated successfully!','success')
                return redirect(url_for('rooms.view_room',room_id=room_id))
            else:
                flash('Error updating room','error')

        return render_template('rooms/edit.html',room=room)
    except Exception as e:
        print(f"Error editing room: {e}")
        flash('Error loading room for editing','error')
        return redirect(url_for('rooms.list_rooms'))


@rooms_bp.route('/delete/<int:room_id>',methods=['POST'])
def delete_room(room_id):
    """Delete room"""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    try:
        success,message = RoomDB.delete_room(room_id)
        if success:
            flash(message,'success')
        else:
            flash(message,'error')
    except Exception as e:
        print(f"Error deleting room: {e}")
        flash('Error deleting room','error')

    return redirect(url_for('rooms.list_rooms'))


@rooms_bp.route('/book/<int:room_id>', methods=['POST'])
def book_room(room_id):
    """Allow a logged in user to book a room (in-memory demo)"""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if not has_permission(session.get('role','Read Only'), 'book_room'):
        flash('You do not have permission to book rooms','error')
        return redirect(url_for('rooms.list_rooms'))

    user_id = session['user_id']
    for b in bookings:
        if b['user_id'] == user_id and b['room_id'] == room_id:
            flash('You already booked this room','info')
            return redirect(url_for('rooms.list_rooms'))

    bookings.append({'user_id': user_id, 'room_id': room_id})
    flash('Room booked successfully','success')
    return redirect(url_for('rooms.list_rooms'))


@rooms_bp.route('/refresh-occupancy')
def refresh_occupancy():
    """Refresh room occupancy counts"""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    try:
        if RoomDB.update_room_occupancy():
            flash('Room occupancy updated successfully','success')
        else:
            flash('Error updating room occupancy','error')
    except Exception as e:
        print(f"Error refreshing occupancy: {e}")
        flash('Error updating room occupancy','error')

    return redirect(url_for('rooms.list_rooms'))