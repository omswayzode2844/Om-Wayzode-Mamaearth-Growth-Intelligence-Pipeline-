/*
================================================================================
 MAMA EARTH GROWTH INTELLIGENCE PIPELINE
  Capstone Project - SQL Component
 Database Engine: SQLite
 File: report.sql
 Description: Database Schema DDL & Evaluated Task Queries (a through i)
================================================================================
*/

PRAGMA foreign_keys = ON;

-- ============================================================================
-- SECTION 1: SCHEMA DEFINITIONS (DDL) [Also saved in sql/schema.sql]
-- ============================================================================

CREATE TABLE IF NOT EXISTS customers (
	customer_id VARCHAR(10) PRIMARY KEY,
	name VARCHAR(50) NOT NULL,
	city VARCHAR(50) NOT NULL,
	city_tier INT NOT NULL,
	signup_date DATE NOT NULL,
	acquisition_source VARCHAR(20) NOT NULL
);

CREATE TABLE IF NOT EXISTS products (
	product_id VARCHAR(10) PRIMARY KEY,
	product_name VARCHAR(100) NOT NULL,
	category VARCHAR(30) NOT NULL,
	price DECIMAL(10, 2) NOT NULL
);

CREATE TABLE IF NOT EXISTS orders (
	order_id VARCHAR(10) PRIMARY KEY,
	customer_id VARCHAR(10) NOT NULL,
	product_id VARCHAR(10) NOT NULL,
	order_date DATE NOT NULL,
	quantity INT NOT NULL,
	discount_pct INT,
	payment_method VARCHAR(10) NOT NULL,
	rating INT,
	returned INT NOT NULL DEFAULT 0,
	FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
	FOREIGN KEY (product_id) REFERENCES products(product_id)
);


-- ============================================================================
-- SECTION 2: EVALUATED TASK QUERIES
-- ============================================================================

/*
--------------------------------------------------------------------------------
 TASK a: Order Totals (2 Marks)
 Problem: Calculate total orders, total revenue, and average order value (AOV).
          Treat NULL discount_pct as 0% discount.
 Revenue Formula: price * quantity * (1 - COALESCE(discount_pct, 0) / 100.0)
 Expected Output:
   total_orders | total_revenue | avg_order_value
   180          | 99860.2       | 554.78
--------------------------------------------------------------------------------
*/
SELECT 
    COUNT(*) AS total_orders,
    ROUND(SUM(p.price * o.quantity * (1 - COALESCE(o.discount_pct, 0) / 100.0)), 2) AS total_revenue,
    ROUND(AVG(p.price * o.quantity * (1 - COALESCE(o.discount_pct, 0) / 100.0)), 2) AS avg_order_value
FROM orders o
JOIN products p ON o.product_id = p.product_id;


/*
--------------------------------------------------------------------------------
 TASK b: COUNT(*) vs COUNT(col) (2 Marks)
 Problem: Demonstrate how many orders have no rating using COUNT(*) vs COUNT(col).
 Concept: COUNT(*) counts all rows (180).
          COUNT(rating) counts non-NULL values (165).
          Difference = unrated orders (15).
 Expected Output:
   total_orders | rated_orders | unrated_orders
   180          | 165          | 15
--------------------------------------------------------------------------------
*/
SELECT 
    COUNT(*) AS total_orders,
    COUNT(rating) AS rated_orders,
    COUNT(*) - COUNT(rating) AS unrated_orders
FROM orders;


/*
--------------------------------------------------------------------------------
 TASK c: LEFT JOIN + NOT IN (3 Marks)
 Problem: Find customers who have placed zero orders using TWO distinct methods.
          Both queries must return the exact same matching result.
 Expected Output:
   customer_id | name   | city
   C045        | Vihaan | Mumbai
--------------------------------------------------------------------------------
*/

-- Method 1: Using LEFT JOIN
SELECT 
    c.customer_id, 
    c.name, 
    c.city
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
WHERE o.order_id IS NULL;

-- Method 2: Using NOT IN
SELECT 
    c.customer_id, 
    c.name, 
    c.city
FROM customers c
WHERE c.customer_id NOT IN (
    SELECT DISTINCT customer_id 
    FROM orders 
    WHERE customer_id IS NOT NULL
);


/*
--------------------------------------------------------------------------------
 TASK d: GROUP BY + HAVING (3 Marks)
 Problem: Calculate return rate percentage by city, keeping only cities with 
          a return rate strictly above 20%.
 Formula: AVG(returned) * 100.0
 Expected Output:
   city      | total_orders | returned_orders | return_rate_pct
   Jaipur    | 19           | 8               | 42.11
   Lucknow   | 49           | 15              | 30.61
   Bangalore | 33           | 8               | 24.24
--------------------------------------------------------------------------------
*/
SELECT 
    c.city,
    COUNT(o.order_id) AS total_orders,
    SUM(o.returned) AS returned_orders,
    ROUND(AVG(o.returned) * 100.0, 2) AS return_rate_pct
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
GROUP BY c.city
HAVING AVG(o.returned) * 100.0 > 20.0
ORDER BY return_rate_pct DESC;


/*
--------------------------------------------------------------------------------
 TASK e: ORDER BY + LIMIT / OFFSET (3 Marks)
 Problem: 
   Part 1: Find the Top 5 customers by total spend.
   Part 2: Retrieve customers ranked 3 to 5 using OFFSET.
 Expected Output Part 1 (Top 5):
   C043 (Reyansh, Bangalore): 12920.00
   C026 (Isha, Lucknow): 8371.60
   C008 (Meera, Lucknow): 4564.60
   C011 (Arjun, Bangalore): 4111.00
   C042 (Sanya, Mumbai): 3785.00
 Expected Output Part 2 (Ranks 3 to 5):
   C008 (Meera, Lucknow): 4564.60
   C011 (Arjun, Bangalore): 4111.00
   C042 (Sanya, Mumbai): 3785.00
--------------------------------------------------------------------------------
*/

-- Part 1: Top 5 Spenders
SELECT 
    c.customer_id,
    c.name,
    c.city,
    ROUND(SUM(p.price * o.quantity * (1 - COALESCE(o.discount_pct, 0) / 100.0)), 2) AS total_spend
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
JOIN products p ON o.product_id = p.product_id
GROUP BY c.customer_id, c.name, c.city
ORDER BY total_spend DESC
LIMIT 5;

-- Part 2: Ranks 3 to 5 (OFFSET 2 skips ranks 1 and 2, LIMIT 3 takes ranks 3, 4, 5)
SELECT 
    c.customer_id,
    c.name,
    c.city,
    ROUND(SUM(p.price * o.quantity * (1 - COALESCE(o.discount_pct, 0) / 100.0)), 2) AS total_spend
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
JOIN products p ON o.product_id = p.product_id
GROUP BY c.customer_id, c.name, c.city
ORDER BY total_spend DESC
LIMIT 3 OFFSET 2;


/*
--------------------------------------------------------------------------------
 TASK f: Three-Table JOIN (3 Marks)
 Problem: Calculate total order count and net revenue broken down by product category.
 Tables Joined: orders, products, and customers.
 Expected Output:
   category     | order_count | total_revenue
   Haircare     | 54          | 44956.10
   Skincare     | 60          | 27346.00
   Babycare     | 30          | 16805.00
   PersonalCare | 36          | 10753.10
--------------------------------------------------------------------------------
*/
SELECT 
    p.category,
    COUNT(o.order_id) AS order_count,
    ROUND(SUM(p.price * o.quantity * (1 - COALESCE(o.discount_pct, 0) / 100.0)), 2) AS total_revenue
FROM orders o
JOIN products p ON o.product_id = p.product_id
JOIN customers c ON o.customer_id = c.customer_id
GROUP BY p.category
ORDER BY total_revenue DESC;


/*
--------------------------------------------------------------------------------
 TASK g: LIKE Pattern Matching (2 Marks)
 Problem: Retrieve all customers whose name begins with the letter "A".
 Expected Output: 10 customer records (Aarav, Aditi, Ananya, Arjun, Aryan, Anika, Aditya, Aisha, Ayaan, Aria)
--------------------------------------------------------------------------------
*/
SELECT 
    customer_id, 
    name, 
    city, 
    city_tier, 
    signup_date
FROM customers
WHERE name LIKE 'A%'
ORDER BY customer_id;


/*
--------------------------------------------------------------------------------
 TASK h: DISTINCT Values (1 Mark)
 Problem: Retrieve all distinct customer acquisition sources.
 Expected Output:
   acquisition_source
   Ad
   Organic
   Referral
   Social
--------------------------------------------------------------------------------
*/
SELECT DISTINCT 
    acquisition_source
FROM customers
ORDER BY acquisition_source;


/*
--------------------------------------------------------------------------------
 TASK i: ALTER TABLE + UPDATE CASE (1 Mark)
 Problem: Add a new column 'loyalty_tier' to customers table.
          Assign 'Gold' for tier-1 cities (Mumbai, Delhi, Bangalore),
          and 'Silver' for all other cities (Lucknow, Jaipur).
 Expected Distribution:
   Gold:   28 customers
   Silver: 17 customers
   Total:  45 customers
--------------------------------------------------------------------------------
*/

-- Step 1: Add new column
ALTER TABLE customers ADD COLUMN loyalty_tier TEXT;

-- Step 2: Update values conditionally using CASE
UPDATE customers
SET loyalty_tier = CASE 
    WHEN city_tier = 1 THEN 'Gold'
    ELSE 'Silver'
END;

-- Step 3: Verification Query
SELECT 
    customer_id, 
    name, 
    city, 
    city_tier, 
    loyalty_tier
FROM customers
LIMIT 10;

-- Step 4: Loyalty Tier Summary Distribution
SELECT 
    loyalty_tier, 
    COUNT(*) AS total_customers
FROM customers
GROUP BY loyalty_tier;
