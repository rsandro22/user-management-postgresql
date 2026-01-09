CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    user_id INT,
    action TEXT NOT NULL,
    action_time TIMESTAMP DEFAULT now()
);


CREATE OR REPLACE FUNCTION log_user_insert()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit_log (user_id, action)
    VALUES (NEW.id, 'USER_CREATED');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


CREATE TRIGGER trg_user_insert
AFTER INSERT ON users
FOR EACH ROW
EXECUTE FUNCTION log_user_insert();


