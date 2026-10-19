DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_roles
        WHERE rolname = 'neurolens_admin'
    ) THEN
CREATE ROLE neurolens_admin
    LOGIN
            NOBYPASSRLS;
END IF;
END
$$;

ALTER ROLE neurolens_admin
    WITH LOGIN NOBYPASSRLS PASSWORD 'postgres';

GRANT CONNECT ON DATABASE neurolens_test
    TO neurolens_admin;

GRANT USAGE ON SCHEMA public
    TO neurolens_admin;
