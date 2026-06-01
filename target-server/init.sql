-- Initialize Fineract databases in PostgreSQL
CREATE DATABASE fineract_tenants;
CREATE DATABASE fineract_default;

GRANT ALL PRIVILEGES ON DATABASE fineract_tenants TO postgres;
GRANT ALL PRIVILEGES ON DATABASE fineract_default TO postgres;
