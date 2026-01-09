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


INSERT INTO roles(name, description) VALUES ('Admin', 'Administrator role');
INSERT INTO roles(name, description) VALUES ('Regular', 'Regular user role');

INSERT INTO users(username, email) VALUES ('admin', 'admin@example.com');
INSERT INTO admin_users(username, email, admin_level) VALUES ('superadmin', 'superadmin@example.com', 10);
INSERT INTO regular_users(username, email, reputation) VALUES ('john', 'john@example.com', 5);

INSERT INTO role_permissions(role_id, permission) VALUES
(1, 'READ'), (1, 'WRITE'), (1, 'DELETE'),
(2, 'READ');
