from flask import Flask, render_template, request, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor
from config import Config

app = Flask(__name__)
config = Config()

def get_db_connection():
    conn = psycopg2.connect(config.DATABASE_URL)
    return conn

@app.route('/')
def index():
    return render_template('index.html')

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