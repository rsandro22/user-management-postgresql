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

    for path in ["db/schema.sql", "db/triggers.sql", "db/views.sql"]:
        with open(path, "r") as f:
            sql = f.read()
        try:
            cur.execute(sql)
        except (psycopg2.errors.DuplicateTable,
                psycopg2.errors.DuplicateFunction,
                psycopg2.errors.DuplicateObject,
                psycopg2.errors.DuplicateColumn,
                psycopg2.errors.DuplicateType):
            conn.rollback()
            print(f"Skipping existing objects in {path}")
        except Exception as e:
            conn.rollback()
            print(f"Error executing {path}:", e)

    roles = [("Admin","Administrator role"), ("Regular","Regular user role")]
    for name, desc in roles:
        try:
            cur.execute(
                "INSERT INTO roles(name, description) VALUES (%s,%s) ON CONFLICT DO NOTHING",
                (name, desc)
            )
        except Exception:
            conn.rollback()

    users = [
        ("admin","admin@example.com","admin123"),
        ("superadmin","superadmin@example.com","super123"),
        ("john","john@example.com","john123")
    ]
    for username,email,password in users:
        try:
            hashed = generate_password_hash(password)
            cur.execute(
                "INSERT INTO users(username,email,password) VALUES (%s,%s,%s) ON CONFLICT (username) DO NOTHING",
                (username,email,hashed)
            )
        except Exception:
            conn.rollback()

    cur.execute("""
        INSERT INTO admin_users(id, admin_level)
        SELECT id, 10 FROM users WHERE username='superadmin'
        ON CONFLICT (id) DO NOTHING
    """)

    conn.commit()
    cur.close()
    conn.close()
    print("Database initialized successfully!")

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        if not session.get("is_admin"):
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

        if user:
            cur.execute("""
                SELECT CASE
                    WHEN EXISTS (SELECT 1 FROM admin_users a WHERE a.id=%s) THEN 'ADMIN'
                    WHEN EXISTS (SELECT 1 FROM regular_users r WHERE r.id=%s) THEN 'REGULAR'
                    ELSE 'UNKNOWN'
                END AS user_type
            """, (user["id"], user["id"]))
            user_type = cur.fetchone()["user_type"]

        cur.close()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["is_admin"] = (user_type == "ADMIN") 
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
    cur.execute("SELECT * FROM user_overview ORDER BY created_at DESC")
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
    cur.execute("SELECT * FROM role_permissions_overview")
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
    cur.execute("SELECT * FROM audit_overview ORDER BY action_time DESC LIMIT 100")
    logs = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("audit.html", logs=logs)

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
