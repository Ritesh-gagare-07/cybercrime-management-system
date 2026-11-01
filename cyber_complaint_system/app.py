from flask import Flask, render_template
from flask import request, redirect, url_for
from werkzeug.security import generate_password_hash
import sqlite3
from flask import Flask, render_template, request, redirect, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

import os
from werkzeug.utils import secure_filename




app = Flask(__name__)
app.secret_key = 'cyber_secret_key'

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def landing():
    return render_template('landing.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        mobile = request.form['mobile']
        address = request.form['address']
        password = request.form['password']
        confirm = request.form['confirm_password']

        # 🔐 Password match check
        if password != confirm:
            flash("Passwords do not match!", "danger")
            return redirect('/register')

        hashed_password = generate_password_hash(password)
        role = 'citizen'

        try:
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users 
                (name, email, mobile, address, password, role)
                VALUES (?,?,?,?,?,?)
            """, (name, email, mobile, address, hashed_password, role))
            conn.commit()
            conn.close()

            flash("Registration successful! Please login.", "success")
            return redirect('/login')

        except:
            flash("Email already exists!", "danger")
            return redirect('/register')

    return render_template('register.html')


from werkzeug.security import check_password_hash
from flask import session

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email=?", (email,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[5], password):
            session['user_id'] = user[0]
            session['role'] = user[6]

            if user[6] == 'citizen':
                return redirect('/citizen/dashboard')
            elif user[6] == 'officer':
                return redirect('/officer/dashboard')
            else:
                return redirect('/admin/dashboard')

        flash("Invalid email or password!", "danger")
        return redirect('/login')

    return render_template('login.html')

from functools import wraps
from flask import session, redirect

def login_required(role=None):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if 'user_id' not in session:
                return redirect('/login')
            if role and session.get('role') != role:
                return redirect('/login')
            return f(*args, **kwargs)
        return wrapped
    return decorator


@app.route('/citizen/dashboard')
@login_required(role='citizen')
def citizen_dashboard():
    return render_template('citizen/dashboard.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

from datetime import datetime

@app.route('/citizen/complaint', methods=['GET', 'POST'])
@login_required(role='citizen')
def register_complaint():
    if request.method == 'POST':
        title = request.form['title']
        category = request.form['category']
        description = request.form['description']
        user_id = session['user_id']
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M")

        file = request.files['evidence']

        if not file or file.filename == '':
            return "No file selected"

        if not allowed_file(file.filename):
            return "Invalid file type"

        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        # Insert complaint
        # Find officer for this category
        cursor.execute("""
           SELECT id FROM officers
           WHERE category=?
           ORDER BY id ASC LIMIT 1
        """, (category,))
        officer = cursor.fetchone()

        officer_id = officer[0] if officer else None

        cursor.execute("""
             INSERT INTO complaints
             (user_id, title, description, category, created_at, officer_id)
            VALUES (?,?,?,?,?,?)
           """, (user_id, title, description, category, created_at, officer_id))


        complaint_id = cursor.lastrowid

        # Insert evidence
        cursor.execute("""
            INSERT INTO evidence (complaint_id, file_name)
            VALUES (?,?)
        """, (complaint_id, filename))

        conn.commit()
        conn.close()

        return redirect('/citizen/status')

    return render_template('citizen/complaint.html')


@app.route('/citizen/status')
@login_required(role='citizen')
def complaint_status():
    user_id = session['user_id']

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("""
        SELECT complaints.id, complaints.title, complaints.category,
               complaints.status, complaints.created_at, evidence.file_name
        FROM complaints
        LEFT JOIN evidence ON complaints.id = evidence.complaint_id
        WHERE complaints.user_id = ?
        ORDER BY complaints.id DESC
    """, (user_id,))

    complaints = cursor.fetchall()
    conn.close()

    return render_template('citizen/status.html', complaints=complaints)

@app.route('/officer/register', methods=['GET', 'POST'])
def officer_register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirm = request.form['confirm_password']
        category = request.form['category']

        if password != confirm:
            flash("Passwords do not match!", "danger")
            return redirect('/officer/register')

        hashed_password = generate_password_hash(password)

        try:
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO officers (name, email, password, category)
                VALUES (?,?,?,?)
            """, (name, email, hashed_password, category))
            conn.commit()
            conn.close()
            flash("Officer registered successfully! Please login.", "success")
            return redirect('/officer/login')
        except:
            flash("Email already exists!", "danger")
            return redirect('/officer/register')

    return render_template('officer/register.html')

@app.route('/officer/login', methods=['GET','POST'])
def officer_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM officers WHERE email=?", (email,))
        officer = cursor.fetchone()
        conn.close()

        if officer and check_password_hash(officer[3], password):
            session['user_id'] = officer[0]
            session['role'] = 'officer'
            session['category'] = officer[4]
            return redirect('/officer/dashboard')
        else:
            flash("Invalid email or password!", "danger")
            return redirect('/officer/login')

    return render_template('officer/login.html')

@app.route('/officer/dashboard')
@login_required(role='officer')
def officer_dashboard():

    officer_id = session['user_id']
    officer_category = session['category']

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    # Auto-assign unassigned complaints for this officer category
    cursor.execute("""
     UPDATE complaints
     SET officer_id=?
     WHERE officer_id IS NULL
     AND category=?
    """, (officer_id, officer_category))
    conn.commit()


    cursor.execute("""
        SELECT complaints.id, users.name, complaints.title,
               complaints.category, complaints.status,
               complaints.officer_id, evidence.file_name
        FROM complaints
        JOIN users ON complaints.user_id = users.id
        LEFT JOIN evidence ON complaints.id = evidence.complaint_id
        ORDER BY complaints.id DESC
    """)

    complaints = cursor.fetchall()

    # Count assigned cases
    cursor.execute("""
        SELECT COUNT(*) FROM complaints
        WHERE officer_id=?
    """, (officer_id,))
    assigned_count = cursor.fetchone()[0]

    conn.close()

    return render_template(
        'officer/dashboard.html',
        complaints=complaints,
        officer_id=officer_id,
        officer_category=officer_category,
        assigned_count=assigned_count
    )

@app.route('/messages/<int:cid>', methods=['GET','POST'])
@login_required()
def messages(cid):

    sender = session['role']
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    if request.method == 'POST':
        msg = request.form['message']
        cursor.execute("""
            INSERT INTO messages (complaint_id, sender, message, timestamp)
            VALUES (?,?,?,?)
        """, (cid, sender, msg, timestamp))
        conn.commit()

    cursor.execute("""
        SELECT id, sender, message, timestamp
        FROM messages
        WHERE complaint_id=?
        ORDER BY id ASC
    """, (cid,))
    messages = cursor.fetchall()
    conn.close()

    return render_template('messages.html', messages=messages, cid=cid)

@app.route('/officer/report/<int:cid>', methods=['GET','POST'])
@login_required(role='officer')
def generate_report(cid):

    if request.method == 'POST':
        findings = request.form['findings']
        conclusion = request.form['conclusion']
        action = request.form['action']

        year = datetime.now().year
        report_id = f"CCMS/{year}/{cid}"

        full_report = f"""
FINDINGS:
{findings}

CONCLUSION:
{conclusion}

ACTION TAKEN:
{action}
"""

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE complaints
            SET report=?, report_id=?, status='Resolved'
            WHERE id=?
        """, (full_report, report_id, cid))

        conn.commit()
        conn.close()

        return redirect('/officer/dashboard')

    return render_template('officer/report.html')

@app.route('/citizen/report/<int:cid>')
@login_required(role='citizen')
def view_report(cid):

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("""
        SELECT report, report_id
        FROM complaints
        WHERE id=?
    """, (cid,))

    data = cursor.fetchone()
    conn.close()

    return render_template(
        'citizen/report.html',
        report=data[0],
        report_id=data[1]
    )


if __name__ == '__main__':
    app.run(debug=True)
