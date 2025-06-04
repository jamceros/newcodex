from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'devkey')

# MySQL configuration obtained from environment variables
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = int(os.environ.get('DB_PORT', '3306'))
DB_USER = os.environ.get('DB_USER', 'root')
DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
DB_NAME = os.environ.get('DB_NAME', 'fichador')


def init_db():
    conn = mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
    )
    cur = conn.cursor()
    cur.execute(
        """CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL
            )""")
    cur.execute(
        """CREATE TABLE IF NOT EXISTS fichajes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                inicio DATETIME NOT NULL,
                fin DATETIME,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )""")
    conn.commit()
    cur.close()
    conn.close()


@app.before_first_request
def setup():
    init_db()


def get_db_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
    )


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
        cur = conn.cursor()
        try:
            cur.execute(
                'INSERT INTO users (username, password) VALUES (%s, %s)',
                (username, generate_password_hash(password))
            )
            conn.commit()
        except mysql.connector.IntegrityError:
            cur.close()
            conn.close()
            return render_template('register.html', error='Usuario ya existe')
        cur.close()
        conn.close()
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute('SELECT * FROM users WHERE username = %s', (username,))
        user = cur.fetchone()
        cur.close()
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
    cur = conn.cursor(dictionary=True)
    cur.execute(
        'SELECT * FROM fichajes WHERE user_id = %s AND fin IS NULL ORDER BY inicio DESC LIMIT 1',
        (session['user_id'],))
    fichaje = cur.fetchone()
    cur.close()
    conn.close()
    return render_template('dashboard.html', fichaje=fichaje)


@app.route('/fichar')
def fichar():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        'SELECT * FROM fichajes WHERE user_id = %s AND fin IS NULL ORDER BY inicio DESC LIMIT 1',
        (session['user_id'],))
    fichaje = cur.fetchone()
    if fichaje:
        cur.execute(
            'UPDATE fichajes SET fin = %s WHERE id = %s',
            (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), fichaje['id'])
        )
    else:
        cur.execute(
            'INSERT INTO fichajes (user_id, inicio) VALUES (%s, %s)',
            (session['user_id'], datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        )
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('dashboard'))


@app.route('/mis_fichajes')
def mis_fichajes():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        'SELECT * FROM fichajes WHERE user_id = %s ORDER BY inicio DESC',
        (session['user_id'],))
    fichajes = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('mis_fichajes.html', fichajes=fichajes)


if __name__ == '__main__':
    app.run(debug=True)
