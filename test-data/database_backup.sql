-- Payment Database Schema
-- WARNING: Contains sensitive payment information

CREATE TABLE customers (
    id INT PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100),
    credit_card VARCHAR(20),
    created_at TIMESTAMP
);

-- Test data for development
INSERT INTO customers (id, name, email, credit_card, created_at) VALUES
(1, 'Alice Johnson', 'alice@example.com', '4532123456789010', '2025-01-01 10:00:00'),
(2, 'Bob Smith', 'bob@example.com', '5425233430109903', '2025-01-02 11:30:00'),
(3, 'Carol Williams', 'carol@example.com', '378282246310005', '2025-01-03 14:15:00'),
(4, 'David Brown', 'david@example.com', '6011111111111117', '2025-01-04 09:45:00'),
(5, 'Eve Davis', 'eve@example.com', '4111111111111111', '2025-01-05 16:20:00');

-- Payment transactions
CREATE TABLE transactions (
    id INT PRIMARY KEY,
    customer_id INT,
    card_used VARCHAR(20),
    amount DECIMAL(10,2),
    transaction_date TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

-- Sample transactions with full card numbers (SECURITY RISK!)
INSERT INTO transactions VALUES
(101, 1, '4532123456789010', 250.00, '2025-01-15 10:30:00'),
(102, 2, '5425233430109903', 150.75, '2025-01-16 11:45:00'),
(103, 3, '378282246310005', 500.00, '2025-01-17 13:20:00');
