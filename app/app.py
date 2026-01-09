from flask import Flask, render_template, request, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor
from config import Config
from functools import wraps

app = Flask(__name__)
from flask import session, redirect, url_for, request
from werkzeug.security import generate_password_hash, check_password_hash

app.secret_key = "tajni_kljuc_za_session" 

config = Config()

def get_db_connection():
    conn = psycopg2.connect(config.DATABASE_URL)
    return conn

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM admin_users WHERE id=%s", (session["user_id"],))
        is_admin = cur.fetchone()
        cur.close()
        conn.close()
        if not is_admin:
            return "Access denied", 403
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return render_template('index.html')

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM users WHERE username=%s", (username,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("index"))
        else:
            return "Invalid credentials", 401

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route('/users')
def users():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute('SELECT * FROM user_overview ORDER BY created_at DESC')
    users_list = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('users.html', users=users_list)

@app.route('/roles')
def roles():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute('SELECT * FROM role_permissions_overview')
    roles_list = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('roles.html', roles=roles_list)

@app.route('/audit')
def audit():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute('SELECT * FROM audit_overview ORDER BY action_time DESC LIMIT 100')
    logs = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('audit.html', logs=logs)

if __name__ == '__main__':
    app.run(debug=True)