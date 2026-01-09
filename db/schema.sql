CREATE TYPE access_right AS ENUM (
    'READ',
    'WRITE',
    'DELETE'
);


CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    description TEXT
);

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT now(),
    metadata JSONB
);


CREATE TABLE admin_users (
    admin_level INT NOT NULL
) INHERITS (users);

CREATE TABLE regular_users (
    reputation INT DEFAULT 0
) INHERITS (users);


CREATE TABLE role_permissions (
    role_id INT REFERENCES roles(id),
    permission access_right,
    PRIMARY KEY (role_id, permission)
);
