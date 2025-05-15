-- Create the database
CREATE DATABASE IF NOT EXISTS student_db;

-- Create the user with password
CREATE USER 'WINstudent'@'%' IDENTIFIED BY 'sutdent999999';

-- Grant privileges only to student_db
GRANT SELECT, INSERT, UPDATE, DELETE ON student_db.* TO 'WINstudent'@'%';
FLUSH PRIVILEGES;

-- Switch to the database
USE student_db;

-- Create student table
CREATE TABLE IF NOT EXISTS student (
    student_id INT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    subject VARCHAR(255) NOT NULL
);

-- Create messages table
CREATE TABLE IF NOT EXISTS messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
INSERT INTO messages (message) VALUES
    ('where there is a will, there is a way'),
    ('long dreamt goal did not necessarily guarantee happiness'),
    ('Thank you I will see you next class');
