CREATE VIEW user_overview AS
SELECT
    id,
    username,
    email,
    created_at
FROM users;


CREATE VIEW audit_overview AS
SELECT
    a.id,
    u.username,
    a.action,
    a.action_time
FROM audit_log a
LEFT JOIN users u ON a.user_id = u.id;


CREATE VIEW role_permissions_overview AS
SELECT 
    r.id,
    r.name AS role_name,
    r.description,
    STRING_AGG(rp.permission::TEXT, ', ') AS permissions
FROM roles r
LEFT JOIN role_permissions rp ON r.id = rp.role_id
GROUP BY r.id;
