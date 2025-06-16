from flask import Blueprint,render_template,request,redirect,url_for,session,flash
from models.database import db

auth_bp = Blueprint('auth',__name__)


@auth_bp.route('/login',methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        query = "SELECT user_id, username, role, full_name FROM users WHERE username = %s AND password = %s AND status = 'Active'"
        user = db.execute_query(query,(username,password))

        if user:
            user_data = user[0]
            session['user_id'] = user_data[0]
            session['username'] = user_data[1]
            session['role'] = user_data[2]
            session['full_name'] = user_data[3]
            flash('Login successful!','success')
            return redirect(url_for('dashboard.dashboard'))
        else:
            flash('Invalid username or password!','error')

    return render_template('auth/login.html')


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out!','info')
    return redirect(url_for('auth.login'))