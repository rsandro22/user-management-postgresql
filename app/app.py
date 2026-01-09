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
            try:
                cur.execute(f.read())
            except Exception as e:
                conn.rollback()
                print(f"Skipping {path} due to existing objects or error: {e}")

    cur.execute("INSERT INTO roles(name, description) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                ("SuperAdmin", "Full control"))
    cur.execute("INSERT INTO roles(name, description) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                ("Admin", "Can add users"))
    cur.execute("INSERT INTO roles(name, description) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                ("Regular", "Regular user"))
    
    perms = ["ADD_USER", "DELETE_USER", "VIEW_AUDIT", "EDIT_ROLE"]
    for perm in perms:
        cur.execute("INSERT INTO permissions(name) VALUES (%s) ON CONFLICT DO NOTHING", (perm,))

    cur.execute("SELECT id FROM roles WHERE name='SuperAdmin'")
    superadmin_id = cur.fetchone()[0]
    cur.execute("SELECT id FROM roles WHERE name='Admin'")
    admin_id = cur.fetchone()[0]
    cur.execute("SELECT id FROM roles WHERE name='Regular'")
    regular_id = cur.fetchone()[0]

    cur.execute("SELECT id, name FROM permissions")
    perm_map = {row[1]: row[0] for row in cur.fetchall()}

    for p in perms:
        cur.execute("INSERT INTO role_permissions(role_id, permission_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                    (superadmin_id, perm_map[p]))

    cur.execute("INSERT INTO role_permissions(role_id, permission_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                (admin_id, perm_map["ADD_USER"]))

    hashed = generate_password_hash("super123")
    cur.execute("INSERT INTO users(username,email,password) VALUES (%s,%s,%s) ON CONFLICT DO NOTHING",
                ("superadmin","superadmin@example.com", hashed))
    cur.execute("INSERT INTO users(username,email,password) VALUES (%s,%s,%s) ON CONFLICT DO NOTHING",
                ("admin","admin@example.com", generate_password_hash("admin123")))
    cur.execute("INSERT INTO users(username,email,password) VALUES (%s,%s,%s) ON CONFLICT DO NOTHING",
                ("john","john@example.com", generate_password_hash("john123")))

    cur.execute("SELECT id FROM users WHERE username='superadmin'")
    super_id = cur.fetchone()[0]
    cur.execute("SELECT id FROM users WHERE username='admin'")
    admin_user_id = cur.fetchone()[0]
    cur.execute("SELECT id FROM users WHERE username='john'")
    john_id = cur.fetchone()[0]

    cur.execute("INSERT INTO user_roles(user_id, role_id) VALUES (%s,%s) ON CONFLICT DO NOTHING", (super_id, superadmin_id))
    cur.execute("INSERT INTO user_roles(user_id, role_id) VALUES (%s,%s) ON CONFLICT DO NOTHING", (admin_user_id, admin_id))
    cur.execute("INSERT INTO user_roles(user_id, role_id) VALUES (%s,%s) ON CONFLICT DO NOTHING", (john_id, regular_id))

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
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM users WHERE username=%s", (username,))
        user = cur.fetchone()
        if user and check_password_hash(user["password"], password):
            cur.execute("""
                SELECT p.name AS permission
                FROM users u
                JOIN user_roles ur ON u.id = ur.user_id
                JOIN role_permissions rp ON ur.role_id = rp.role_id
                JOIN permissions p ON rp.permission_id = p.id
                WHERE u.id=%s
            """, (user["id"],))
            session["permissions"] = [row["permission"] for row in cur.fetchall()]
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            cur.close()
            conn.close()
            return redirect(url_for("index"))
        cur.close()
        conn.close()
        return "Invalid credentials", 401
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
@permission_required("VIEW_AUDIT")
def audit():
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
