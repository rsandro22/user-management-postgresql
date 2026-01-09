CREATE OR REPLACE VIEW user_overview AS
SELECT 
    id,
    username,
    email,
    created_at,
    CASE
        WHEN EXISTS (SELECT 1 FROM admin_users a WHERE a.id = u.id) THEN 'ADMIN'
        WHEN EXISTS (SELECT 1 FROM regular_users r WHERE r.id = u.id) THEN 'REGULAR'
        ELSE 'UNKNOWN'
    END AS user_type
FROM users u;



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
