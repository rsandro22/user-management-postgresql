from flask import Flask, render_template, request, redirect, url_for, session
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os

DB_NAME = "user_management"
DB_USER = "postgres"
DB_PASSWORD = "bmw320xd"
DB_HOST = "localhost"
DB_PORT = "5432"

app = Flask(__name__)
app.secret_key = "tajni_kljuc"


def get_db():
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )


def init_db():
    conn = psycopg2.connect(dbname="postgres", user=DB_USER, password=DB_PASSWORD)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM pg_database WHERE datname=%s", (DB_NAME,))
    if not cur.fetchone():
        cur.execute(f"CREATE DATABASE {DB_NAME}")
    cur.close()
    conn.close()


def run_sql_file(filename):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    full_path = os.path.join(base_dir, filename)



    conn = get_db()
    cur = conn.cursor()

    with open(full_path, "r", encoding="utf-8") as f:
        cur.execute(f.read())

    conn.commit()
    cur.close()
    conn.close()

def create_default_admin():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT id FROM users WHERE username = 'admin'")
    if cur.fetchone():
        cur.close()
        conn.close()
        return

    password_hash = generate_password_hash("admin")

    cur.execute("""
        INSERT INTO users (username, password)
        VALUES (%s, %s)
        RETURNING id
    """, ("admin", password_hash))

    admin_id = cur.fetchone()[0]

    cur.execute("""
        INSERT INTO user_roles (user_id, role_id)
        SELECT %s, id FROM roles WHERE name = 'admin'
    """, (admin_id,))

    conn.commit()
    cur.close()
    conn.close()



def get_user_permissions(user_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT p.name
        FROM permissions p
        JOIN role_permissions rp ON p.id = rp.permission_id
        JOIN user_roles ur ON rp.role_id = ur.role_id
        WHERE ur.user_id = %s
    """, (user_id,))
    permissions = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return permissions


def permission_required(permission):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if "user_id" not in session:
                return redirect(url_for("login"))
            if permission not in session.get("permissions", []):
                return "Access denied", 403
            return f(*args, **kwargs)
        return wrapper
    return decorator


@app.route("/")
def index():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("index.html", permissions=session.get("permissions", []))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        conn = get_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute(
            "SELECT * FROM users WHERE username = %s",
            (request.form["username"],)
        )
        user = cur.fetchone()

        cur.close()
        conn.close()

        if user and check_password_hash(user["password"], request.form["password"]):
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["permissions"] = get_user_permissions(user["id"])

            return redirect(url_for("index"))

        return "Invalid credentials", 401

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/users")
@permission_required("VIEW_USERS")
def users():
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT u.id, u.username,
               COALESCE(STRING_AGG(r.name, ', '), '-') AS role
        FROM users u
        LEFT JOIN user_roles ur ON u.id = ur.user_id
        LEFT JOIN roles r ON ur.role_id = r.id
        GROUP BY u.id
        ORDER BY u.id
    """)
    users = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "users.html",
        users=users,
        current_user={"username": session["username"]},
        permissions=session["permissions"]
    )


@app.route("/users/add", methods=["POST"])
@permission_required("ADD_USER")
def add_user():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO users (username, password)
        VALUES (%s, %s)
        RETURNING id
    """, (
        request.form["username"],
        generate_password_hash(request.form["password"])
    ))

    user_id = cur.fetchone()[0]

    cur.execute("""
        INSERT INTO user_roles (user_id, role_id)
        SELECT %s, id FROM roles WHERE name = %s
    """, (user_id, request.form["role"]))

    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for("users"))


@app.route("/users/delete/<int:user_id>", methods=["POST"])
@permission_required("DELETE_USER")
def delete_user(user_id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
    conn.commit()

    cur.close()
    conn.close()
    return redirect(url_for("users"))

@app.route("/roles")
@permission_required("VIEW_USERS")
def roles():
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT r.id, r.name AS role_name,
               STRING_AGG(p.name, ', ') AS permissions
        FROM roles r
        LEFT JOIN role_permissions rp ON r.id = rp.role_id
        LEFT JOIN permissions p ON rp.permission_id = p.id
        GROUP BY r.id
        ORDER BY r.id
    """)

    roles = cur.fetchall()
    cur.close()
    conn.close()

    return render_template("roles.html", roles=roles)

@app.route("/audit")
@permission_required("VIEW_AUDIT")
def audit():
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT a.id, u.username, a.action, a.action_time
        FROM audit_log a
        LEFT JOIN users u ON a.user_id = u.id
        ORDER BY a.action_time DESC
    """)

    logs = cur.fetchall()
    cur.close()
    conn.close()

    return render_template("audit.html", logs=logs)



if __name__ == "__main__":
    init_db()
    run_sql_file("schema.sql")
    run_sql_file("views.sql")
    run_sql_file("triggers.sql")
    run_sql_file("seed.sql")
    create_default_admin()
    app.run(debug=True)


