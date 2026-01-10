CREATE OR REPLACE FUNCTION log_user_action()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO audit_log(user_id, action)
        VALUES (NEW.id, 'USER_CREATED');

    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO audit_log(user_id, action)
        VALUES (NULL, 'USER_DELETED');
    END IF;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;
