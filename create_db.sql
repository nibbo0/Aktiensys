CREATE ROLE IF NOT EXISTS dau_jones_admin;
CREATE USER IF NOT EXISTS 'dau_jones'@'%';
CREATE DATABASE IF NOT EXISTS dau_jones;

GRANT ALL PRIVILEGES ON dau_jones.* TO dau_jones_admin;
GRANT dau_jones_admin TO dau_jones;
SET DEFAULT ROLE dau_jones_admin FOR dau_jones;

USE dau_jones;
SET @@time_zone = '+00:00';
