from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'devkey')
DB_PATH = 'database.db'


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )""")
    cur.execute(
        """CREATE TABLE IF NOT EXISTS fichajes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                inicio TEXT NOT NULL,
                fin TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )""")
    conn.commit()
    conn.close()


@app.before_first_request
def setup():
    init_db()


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if not username or not password:
            return render_template('register.html', error='Datos requeridos')
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO users (username, password) VALUES (?, ?)',
                         (username, generate_password_hash(password)))
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return render_template('register.html', error='Usuario ya existe')
        conn.close()
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='Credenciales invalidas')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    fichaje = conn.execute(
        'SELECT * FROM fichajes WHERE user_id = ? AND fin IS NULL ORDER BY inicio DESC LIMIT 1',
        (session['user_id'],)).fetchone()
    conn.close()
    return render_template('dashboard.html', fichaje=fichaje)


@app.route('/fichar')
def fichar():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    fichaje = conn.execute(
        'SELECT * FROM fichajes WHERE user_id = ? AND fin IS NULL ORDER BY inicio DESC LIMIT 1',
        (session['user_id'],)).fetchone()
    if fichaje:
        conn.execute('UPDATE fichajes SET fin = ? WHERE id = ?',
                     (datetime.now().isoformat(timespec='seconds'), fichaje['id']))
    else:
        conn.execute('INSERT INTO fichajes (user_id, inicio) VALUES (?, ?)',
                     (session['user_id'], datetime.now().isoformat(timespec='seconds')))
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard'))


@app.route('/mis_fichajes')
def mis_fichajes():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    fichajes = conn.execute('SELECT * FROM fichajes WHERE user_id = ? ORDER BY inicio DESC',
                            (session['user_id'],)).fetchall()
    conn.close()
    return render_template('mis_fichajes.html', fichajes=fichajes)


if __name__ == '__main__':
    app.run(debug=True)
