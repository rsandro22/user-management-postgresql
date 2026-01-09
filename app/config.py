import psycopg2
from psycopg2.extras import RealDictCursor

DB_NAME = "user_management"
DB_USER = "postgres"
DB_PASSWORD = "postgres"  
DB_HOST = "localhost"
DB_PORT = "5432"

def get_connection(db_name=DB_NAME):
    conn = psycopg2.connect(
        dbname=db_name, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT
    )
    return conn

def init_db():
    conn = get_connection("postgres") 
    conn.autocommit = True
    cur = conn.cursor()
    
    cur.execute(f"SELECT 1 FROM pg_database WHERE datname='{DB_NAME}'")
    if not cur.fetchone():
        cur.execute(f"CREATE DATABASE {DB_NAME}")
    
    cur.close()
    conn.close()
    
    conn = get_connection()
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
    INSERT INTO users(username,email) VALUES ('admin','admin@example.com') ON CONFLICT DO NOTHING;
    INSERT INTO admin_users(username,email,admin_level) VALUES ('superadmin','superadmin@example.com',10) ON CONFLICT DO NOTHING;
    INSERT INTO regular_users(username,email,reputation) VALUES ('john','john@example.com',5) ON CONFLICT DO NOTHING;
    INSERT INTO role_permissions(role_id, permission) VALUES
        (1,'READ'), (1,'WRITE'), (1,'DELETE'),
        (2,'READ')
    ON CONFLICT DO NOTHING;
    """)
    conn.commit()
    cur.close()
    conn.close()
