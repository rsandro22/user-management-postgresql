from flask import Flask, render_template, request, redirect, url_for, session
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

DB_NAME = "user_management"
DB_USER = "postgres"
DB_PASSWORD = "bmw320xd" 
DB_HOST = "localhost"
DB_PORT = "5432"

app = Flask(__name__)
app.secret_key = "tajni_kljuc_za_session"

def get_db_connection(db_name=DB_NAME):
    conn = psycopg2.connect(
        dbname=db_name, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT
    )
    return conn

def init_db():
    conn = get_db_connection("postgres")
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute(f"SELECT 1 FROM pg_database WHERE datname='{DB_NAME}'")
    if not cur.fetchone():
        cur.execute(f"CREATE DATABASE {DB_NAME}")
        print(f"Database {DB_NAME} created")
    cur.close()
    conn.close()

    conn = get_db_connection()
    cur = conn.cursor()
    with open("db/schema.sql", "r") as f:
        cur.execute(f.read())
    with open("db/triggers.sql", "r") as f:
        cur.execute(f.read())
    with open("db/views.sql", "r") as f:
        cur.execute(f.read())
    
    cur.execute("""
    INSERT INTO roles(name, description) VALUES ('Admin','Administrator role') ON CONFLICT DO NOTHING;
    INSERT INTO roles(name, description) VALUES ('Regular','Regular user role') ON CONFLICT DO NOTHING;
    
    INSERT INTO users(username,email,password) 
        VALUES ('admin','admin@example.com', %s) 
        ON CONFLICT (username) DO NOTHING;
    
    INSERT INTO admin_users(username,email,admin_level,password) 
        VALUES ('superadmin','superadmin@example.com',10,%s) 
        ON CONFLICT (username) DO NOTHING;
    
    INSERT INTO regular_users(username,email,reputation,password) 
        VALUES ('john','john@example.com',5,%s) 
        ON CONFLICT (username) DO NOTHING;
    
    INSERT INTO role_permissions(role_id, permission) VALUES
        (1,'READ'),(1,'WRITE'),(1,'DELETE'),
        (2,'READ') ON CONFLICT DO NOTHING;
    """, (generate_password_hash("admin123"), generate_password_hash("super123"), generate_password_hash("john123")))
    
    conn.commit()
    cur.close()
    conn.close()
    print("Database initialized successfully!")

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

@app.route("/login", methods=["GET","POST"])
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

@app.route("/users/add", methods=["POST"])
@admin_required
def add_user():
    data = request.form
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users(username,email,password) VALUES (%s,%s,%s)",
        (data["username"], data["email"], generate_password_hash(data["password"]))
    )
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for("users"))

@app.route("/users/delete/<int:user_id>", methods=["POST"])
@admin_required
def delete_user(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE id=%s", (user_id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for("users"))

@app.route("/")
def index():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("index.html")

@app.route("/users")
def users():
    if "user_id" not in session:
        return redirect(url_for("login"))
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute('SELECT * FROM user_overview ORDER BY created_at DESC')
    users_list = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("users.html", users=users_list)

@app.route("/roles")
def roles():
    if "user_id" not in session:
        return redirect(url_for("login"))
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute('SELECT * FROM role_permissions_overview')
    roles_list = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("roles.html", roles=roles_list)

@app.route("/audit")
def audit():
    if "user_id" not in session:
        return redirect(url_for("login"))
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute('SELECT * FROM audit_overview ORDER BY action_time DESC LIMIT 100')
    logs = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("audit.html", logs=logs)

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
