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
    return psycopg2.connect(
        dbname=db_name, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT
    )

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
        except Exception as e:
            conn.rollback()
            print(f"Skipping {path} due to existing objects or error:", e)

    roles = [("Admin","Administrator role"), ("Regular","Regular user role")]
    for name, desc in roles:
        try:
            cur.execute(
                "INSERT INTO roles(name, description) VALUES (%s,%s) ON CONFLICT (name) DO NOTHING",
                (name, desc)
            )
        except Exception:
            conn.rollback()

    permissions = ["ADD_USER","DELETE_USER","VIEW_USERS"]
    for perm in permissions:
        try:
            cur.execute(
                "INSERT INTO permissions(name) VALUES (%s) ON CONFLICT (name) DO NOTHING",
                (perm,)
            )
        except Exception:
            conn.rollback()

    role_perms = {
        "Admin":["ADD_USER","DELETE_USER","VIEW_USERS"],
        "Regular":["VIEW_USERS"]
    }
    for role, perms in role_perms.items():
        for perm in perms:
            try:
                cur.execute("""
                    INSERT INTO role_permissions(role_id, permission)
                    SELECT r.id, p.name FROM roles r, permissions p
                    WHERE r.name=%s AND p.name=%s
                    ON CONFLICT DO NOTHING
                """,(role,perm))
            except Exception:
                conn.rollback()

    users = [
        ("superadmin","superadmin@example.com","super123","Admin"),
        ("admin","admin@example.com","admin123","Admin"),
        ("john","john@example.com","john123","Regular")
    ]
    for username,email,password,role in users:
        hashed = generate_password_hash(password)
        try:
            cur.execute(
                "INSERT INTO users(username,email,password) VALUES (%s,%s,%s) ON CONFLICT (username) DO NOTHING",
                (username,email,hashed)
            )
            cur.execute("""
                INSERT INTO user_roles(user_id, role_id)
                SELECT u.id, r.id FROM users u, roles r
                WHERE u.username=%s AND r.name=%s
                ON CONFLICT DO NOTHING
            """,(username,role))
        except Exception:
            conn.rollback()

    conn.commit()
    cur.close()
    conn.close()
    print("Database initialized successfully!")

def permission_required(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "user_id" not in session:
                return redirect(url_for("login"))
            if permission not in session.get("permissions", []):
                return "Access denied", 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        username = request.form["username"]
        password = request.form["password"]
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM users WHERE username=%s", (username,))
        user = cur.fetchone()
        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            cur.execute("""
                SELECT rp.permission
                FROM roles r
                JOIN user_roles ur ON r.id = ur.role_id
                JOIN role_permissions rp ON r.id = rp.role_id
                WHERE ur.user_id=%s
            """,(user["id"],))
            session["permissions"] = [row["permission"] for row in cur.fetchall()]
            cur.close()
            conn.close()
            return redirect(url_for("index"))
        cur.close()
        conn.close()
        return "Invalid credentials",401
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

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

@app.route("/users/add", methods=["POST"])
@permission_required("ADD_USER")
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
@permission_required("DELETE_USER")
def delete_user(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE id=%s", (user_id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for("users"))

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

if __name__=="__main__":
    init_db()
    app.run(debug=True)
