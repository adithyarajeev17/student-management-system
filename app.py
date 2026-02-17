from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'senior_dev_key'

# Database path
DB_PATH = 'database.db'


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# Initialize DB if it doesn't exist
if not os.path.exists(DB_PATH):
    conn = get_db()
    conn.execute('''CREATE TABLE students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        roll_no TEXT UNIQUE NOT NULL,
        class_name TEXT NOT NULL
    )''')
    conn.execute('''CREATE TABLE marks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        subject TEXT NOT NULL,
        score INTEGER,
        FOREIGN KEY (student_id) REFERENCES students (id)
    )''')
    conn.execute('''CREATE TABLE attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        date TEXT NOT NULL,
        status TEXT NOT NULL,
        FOREIGN KEY (student_id) REFERENCES students (id)
    )''')
    conn.close()

# --- ROUTES ---


@app.route('/')
def home():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == 'admin' and request.form['password'] == 'admin123':
            session['user'] = 'admin'
            return redirect(url_for('dashboard'))
        flash('Invalid Credentials', 'danger')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))


@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    db = get_db()
    stats = db.execute('''
        SELECT s.name, AVG(m.score) as avg_score 
        FROM students s 
        LEFT JOIN marks m ON s.id = m.student_id 
        GROUP BY s.id
    ''').fetchall()
    total_students = db.execute('SELECT COUNT(*) FROM students').fetchone()[0]
    db.close()

    labels = [row['name'] for row in stats]
    data = [row['avg_score'] if row['avg_score'] else 0 for row in stats]
    return render_template('dashboard.html', labels=labels, data=data, total=total_students)


@app.route('/students', methods=['GET', 'POST'])
def students():
    if 'user' not in session:
        return redirect(url_for('login'))
    db = get_db()
    if request.method == 'POST':
        try:
            db.execute('INSERT INTO students (name, roll_no, class_name) VALUES (?, ?, ?)',
                       (request.form['name'], request.form['roll'], request.form['class']))
            db.commit()
            flash('Student added!', 'success')
        except:
            flash('Error: Roll number might already exist.', 'danger')

    students_list = db.execute('SELECT * FROM students').fetchall()
    db.close()
    return render_template('students.html', students=students_list)


@app.route('/marks', methods=['GET', 'POST'])
def marks():
    if 'user' not in session:
        return redirect(url_for('login'))
    db = get_db()
    if request.method == 'POST':
        db.execute('INSERT INTO marks (student_id, subject, score) VALUES (?, ?, ?)',
                   (request.form['student_id'], request.form['subject'], request.form['score']))
        db.commit()
        flash('Marks saved!', 'success')

    students_list = db.execute('SELECT * FROM students').fetchall()
    marks_list = db.execute('''
        SELECT s.name, m.subject, m.score FROM marks m 
        JOIN students s ON s.id = m.student_id
    ''').fetchall()
    db.close()
    return render_template('marks.html', students=students_list, marks_list=marks_list)


@app.route('/attendance', methods=['GET', 'POST'])
def attendance():
    if 'user' not in session:
        return redirect(url_for('login'))
    db = get_db()
    if request.method == 'POST':
        date = request.form['date']
        for key, value in request.form.items():
            if key.startswith('status_'):
                student_id = key.split('_')[1]
                db.execute('INSERT INTO attendance (student_id, date, status) VALUES (?, ?, ?)',
                           (student_id, date, value))
        db.commit()
        flash('Attendance recorded!', 'success')

    students_list = db.execute('SELECT * FROM students').fetchall()
    db.close()
    return render_template('attendance.html', students=students_list)


@app.route('/attendance/report')
def attendance_report():
    if 'user' not in session:
        return redirect(url_for('login'))
    db = get_db()
    records = db.execute('''
        SELECT a.date, s.name, s.roll_no, a.status 
        FROM attendance a 
        JOIN students s ON s.id = a.student_id 
        ORDER BY a.date DESC
    ''').fetchall()
    db.close()
    return render_template('attendance_report.html', records=records)


if __name__ == '__main__':
    app.run(debug=True)
