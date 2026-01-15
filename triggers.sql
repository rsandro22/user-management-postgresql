CREATE OR REPLACE FUNCTION log_user_action()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO audit_log(user_id, action)
        VALUES (NEW.id, 'USER_CREATED');

        RETURN NEW;  

    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO audit_log(user_id, action)
        VALUES (OLD.id, 'USER_DELETED');

        RETURN OLD; 
    END IF;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_users_audit_insert ON users;
CREATE TRIGGER trg_users_audit_insert
AFTER INSERT ON users
FOR EACH ROW
EXECUTE FUNCTION log_user_action();

DROP TRIGGER IF EXISTS trg_users_audit_delete ON users;
CREATE TRIGGER trg_users_audit_delete
BEFORE DELETE ON users
FOR EACH ROW
EXECUTE FUNCTION log_user_action();
