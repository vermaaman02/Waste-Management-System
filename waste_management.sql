-- ============================================
-- Web Based Smart Waste Management System
-- Database Schema for MySQL Workbench
-- BCA Major Project
-- ============================================

-- Step 1: Create the database
CREATE DATABASE IF NOT EXISTS waste_management;

-- Step 2: Select the database
USE waste_management;

-- Step 3: Create the complaints table
-- This table stores all garbage complaints reported by citizens
CREATE TABLE IF NOT EXISTS complaints (
    -- Unique identifier for each complaint (auto-incremented)
    id INT PRIMARY KEY AUTO_INCREMENT,
    
    -- Name of the person reporting the complaint
    name VARCHAR(100) NOT NULL,
    
    -- Area/locality where garbage is located (Patna areas)
    area VARCHAR(100) NOT NULL,
    
    -- Detailed description of the garbage issue
    description TEXT,
    
    -- GPS coordinates for location tracking
    latitude VARCHAR(50),
    longitude VARCHAR(50),
    
    -- Path to the uploaded garbage image
    image_path VARCHAR(255),
    
    -- Status of complaint: 'Pending' or 'Cleaned'
    status VARCHAR(50) DEFAULT 'Pending',
    
    -- Timestamp when complaint was created
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- HOW TO USE THIS FILE IN MySQL WORKBENCH:
-- ============================================
-- 1. Open MySQL Workbench
-- 2. Connect to your local MySQL server
-- 3. Go to File > Open SQL Script
-- 4. Select this file (waste_management.sql)
-- 5. Click the lightning bolt icon to execute
-- 6. Refresh the schemas panel to see the new database
-- ============================================
