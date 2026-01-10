INSERT INTO permissions (name)
SELECT unnest(ARRAY[
    'VIEW_USERS',
    'ADD_USER',
    'DELETE_USER'
])
ON CONFLICT (name) DO NOTHING;

INSERT INTO roles (name)
SELECT unnest(ARRAY[
    'admin',
    'user'
])
ON CONFLICT (name) DO NOTHING;

INSERT INTO role_permissions
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.name = 'admin'
ON CONFLICT DO NOTHING;

INSERT INTO role_permissions
SELECT r.id, p.id
FROM roles r
JOIN permissions p ON p.name = 'VIEW_USERS'
WHERE r.name = 'user'
ON CONFLICT DO NOTHING;


