CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    user_id INT,
    action TEXT NOT NULL,
    action_time TIMESTAMP DEFAULT now()
);

CREATE OR REPLACE FUNCTION log_user_insert()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit_log(user_id, action) VALUES (NEW.id, 'USER_CREATED');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION log_user_update_delete()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'UPDATE' THEN
        INSERT INTO audit_log(user_id, action) VALUES (NEW.id,'USER_UPDATED');
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO audit_log(user_id, action) VALUES (OLD.id,'USER_DELETED');
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_user_insert AFTER INSERT ON users FOR EACH ROW EXECUTE FUNCTION log_user_insert();
CREATE TRIGGER trg_user_update_delete AFTER UPDATE OR DELETE ON users FOR EACH ROW EXECUTE FUNCTION log_user_update_delete();
