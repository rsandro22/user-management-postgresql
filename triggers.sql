CREATE OR REPLACE FUNCTION log_user_action()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO audit_log(user_id, action)
        VALUES (NEW.id, 'USER_CREATED');

    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO audit_log(user_id, action)
        VALUES (OLD.id, 'USER_DELETED');
    END IF;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_users_audit_insert ON users;
DROP TRIGGER IF EXISTS trg_users_audit_delete ON users;

CREATE TRIGGER trg_users_audit_insert
AFTER INSERT ON users
FOR EACH ROW
EXECUTE FUNCTION log_user_action();

CREATE TRIGGER trg_users_audit_delete
AFTER DELETE ON users
FOR EACH ROW
EXECUTE FUNCTION log_user_action();
