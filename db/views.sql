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
