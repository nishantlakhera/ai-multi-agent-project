-- Database setup script for AI Multi-Agent Project
-- Run this script to create the necessary tables

-- Drop tables if they exist (for clean setup)
DROP TABLE IF EXISTS user_sessions CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS orders CASCADE;

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create user_sessions table for tracking login sessions
CREATE TABLE IF NOT EXISTS user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create orders table (example for e-commerce use case)
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    total_amount DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample users
INSERT INTO users (name, email, created_at, last_login_at) VALUES
    ('John Doe', 'john.doe@example.com', NOW() - INTERVAL '30 days', NOW() - INTERVAL '1 day'),
    ('Jane Smith', 'jane.smith@example.com', NOW() - INTERVAL '25 days', NOW() - INTERVAL '2 hours'),
    ('Bob Johnson', 'bob.johnson@example.com', NOW() - INTERVAL '20 days', NOW() - INTERVAL '5 hours'),
    ('Alice Williams', 'alice.williams@example.com', NOW() - INTERVAL '15 days', NOW()),
    ('Charlie Brown', 'charlie.brown@example.com', NOW() - INTERVAL '10 days', NOW() - INTERVAL '30 minutes'),
    ('Diana Prince', 'diana.prince@example.com', NOW() - INTERVAL '5 days', NOW() - INTERVAL '1 hour'),
    ('Eve Adams', 'eve.adams@example.com', NOW() - INTERVAL '3 days', NOW() - INTERVAL '15 minutes'),
    ('Frank Miller', 'frank.miller@example.com', NOW() - INTERVAL '2 days', NOW() - INTERVAL '3 hours'),
    ('Grace Lee', 'grace.lee@example.com', NOW() - INTERVAL '1 day', NOW()),
    ('Henry Ford', 'henry.ford@example.com', NOW(), NOW());

-- Insert sample user sessions for today
INSERT INTO user_sessions (user_id, session_token, created_at, last_activity)
SELECT
    id,
    'session_' || id || '_' || EXTRACT(EPOCH FROM NOW())::TEXT,
    NOW() - (random() * INTERVAL '8 hours'),
    NOW() - (random() * INTERVAL '1 hour')
FROM users
WHERE id <= 7;  -- Only 7 users logged in today

-- Insert sample orders
INSERT INTO orders (user_id, total_amount, status, created_at) VALUES
    (1, 99.99, 'completed', NOW() - INTERVAL '5 days'),
    (1, 149.50, 'completed', NOW() - INTERVAL '2 days'),
    (2, 299.99, 'pending', NOW() - INTERVAL '1 day'),
    (3, 49.99, 'completed', NOW() - INTERVAL '10 days'),
    (4, 199.99, 'shipped', NOW() - INTERVAL '3 days'),
    (5, 79.99, 'completed', NOW() - INTERVAL '1 day'),
    (6, 129.99, 'pending', NOW()),
    (7, 89.99, 'completed', NOW() - INTERVAL '2 hours'),
    (8, 399.99, 'shipped', NOW() - INTERVAL '1 day');

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON user_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_users_last_login ON users(last_login_at);

-- Verify setup
SELECT 'Users created:' as info, COUNT(*) as count FROM users
UNION ALL
SELECT 'Sessions created:', COUNT(*) FROM user_sessions
UNION ALL
SELECT 'Orders created:', COUNT(*) FROM orders;

