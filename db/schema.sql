
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'access_right') THEN
        CREATE TYPE access_right AS ENUM ('READ','WRITE','DELETE');
    END IF;
END$$;

CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT now(),
    metadata JSONB,
    password TEXT
);

CREATE TABLE IF NOT EXISTS admin_users (
    admin_level INT NOT NULL
) INHERITS (users);

CREATE TABLE IF NOT EXISTS regular_users (
    reputation INT DEFAULT 0
) INHERITS (users);

CREATE TABLE IF NOT EXISTS role_permissions (
    role_id INT REFERENCES roles(id),
    permission access_right,
    PRIMARY KEY (role_id, permission)
);
