CREATE OR REPLACE VIEW user_overview AS
SELECT
    u.id,
    u.username,
    u.email,
    u.created_at,
    STRING_AGG(r.name, ', ') AS roles
FROM users u
LEFT JOIN user_roles ur ON u.id = ur.user_id
LEFT JOIN roles r ON ur.role_id = r.id
GROUP BY u.id;

CREATE OR REPLACE VIEW audit_overview AS
SELECT
    a.id,
    u.username,
    a.action,
    a.action_time
FROM audit_log a
LEFT JOIN users u ON a.user_id = u.id;

CREATE OR REPLACE VIEW role_permissions_overview AS
SELECT
    r.name AS role,
    STRING_AGG(p.name, ', ') AS permissions
FROM roles r
LEFT JOIN role_permissions rp ON r.id = rp.role_id
LEFT JOIN permissions p ON rp.permission_id = p.id
GROUP BY r.name;
