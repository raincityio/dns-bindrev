CREATE DATABASE IF NOT EXISTS bindrev;

USE bindrev;

CREATE TABLE IF NOT EXISTS rev (
    ip VARCHAR(64) NOT NULL,
    resolve VARCHAR(256) NOT NULL
);

CREATE USER IF NOT EXISTS 'bindrev'@'%' IDENTIFIED WITH mysql_native_password BY 'verdnib';
GRANT SELECT, INSERT ON bindrev.rev TO 'bindrev'@'%';

CREATE USER IF NOT EXISTS 'bindrevro'@'%' IDENTIFIED WITH mysql_native_password BY 'verdnib';
GRANT SELECT ON bindrev.rev TO 'bindrevro'@'%';
