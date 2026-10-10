CREATE SCHEMA IF NOT EXISTS vaxgenesis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
GRANT ALL ON SCHEMA vaxgenesis TO vaxgenesis;
ALTER USER vaxgenesis SET search_path TO vaxgenesis, public;
