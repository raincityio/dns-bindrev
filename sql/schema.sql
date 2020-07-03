CREATE DATABASE IF NOT EXISTS bindrev;

USE bindrev;

CREATE TABLE IF NOT EXISTS IPS (
    id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    ip VARCHAR(64) NOT NULL,
    domain VARCHAR(256) NOT NULL,
    latest BOOLEAN NOT NULL
);

CREATE USER IF NOT EXISTS 'bindrev'@'%' IDENTIFIED WITH mysql_native_password BY 'verdnib';
GRANT SELECT, INSERT, UPDATE ON bindrev.ips TO 'bindrev'@'%';

CREATE USER IF NOT EXISTS 'bindrevro'@'%' IDENTIFIED WITH mysql_native_password BY 'verdnib';
GRANT SELECT ON bindrev.ips TO 'bindrevro'@'%';

CREATE INDEX ip ON ips (ip);
