-- ============================================
--  PostgreSQL PRACTICE DATABASE INITIALIZATION
--  Author: ChatGPT (GPT-5)
--  Purpose: Учебный стенд SQL для практики
-- ============================================

-- 💠 1. Создаём базу и роль
DROP DATABASE IF EXISTS appdb;
CREATE DATABASE appdb;
\c appdb;

DROP ROLE IF EXISTS app;
CREATE ROLE app WITH LOGIN PASSWORD 'app_password';
GRANT ALL PRIVILEGES ON DATABASE appdb TO app;

-- 💠 2. Таблицы
DROP TABLE IF EXISTS transactions CASCADE;
DROP TABLE IF EXISTS accounts CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS users CASCADE;

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    age INT CHECK (age >= 0),
    city TEXT NOT NULL,
    email TEXT UNIQUE
);

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    amount NUMERIC(10,2) NOT NULL CHECK (amount >= 0),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE accounts (
    id SERIAL PRIMARY KEY,
    owner_id INT REFERENCES users(id) ON DELETE CASCADE,
    balance NUMERIC(12,2) NOT NULL CHECK (balance >= 0)
);

CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    from_user INT REFERENCES users(id),
    to_user INT REFERENCES users(id),
    amount NUMERIC(10,2) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 💠 3. Тестовые данные
INSERT INTO users (name, age, city, email) VALUES
('Alice', 25, 'London', 'alice@mail.com'),
('Bob', 32, 'Paris', 'bob@mail.com'),
('Carol', 29, 'Berlin', 'carol@mail.com'),
('David', 40, 'London', 'david@mail.com'),
('Emma', 35, 'Paris', 'emma@mail.com');

INSERT INTO orders (user_id, amount) VALUES
(1, 100.00),
(2, 150.00),
(1, 50.00),
(5, 200.00);

INSERT INTO accounts (owner_id, balance) VALUES
(1, 1000.00),
(2, 200.00),
(3, 500.00),
(4, 1500.00),
(5, 300.00);

-- 💠 4. Индексы
CREATE INDEX idx_users_city ON users(city);
CREATE INDEX idx_orders_user_id ON orders(user_id);

-- 💠 5. Примеры SELECT
-- все пользователи
SELECT * FROM users;

-- старше 30
SELECT name, age FROM users WHERE age > 30;

-- по городам
SELECT city, COUNT(*) AS num_people
FROM users
GROUP BY city;

-- пользователи и заказы
SELECT u.name, o.amount
FROM users u
JOIN orders o ON u.id = o.user_id;

-- общая сумма заказов
SELECT u.name, COALESCE(SUM(o.amount), 0) AS total_spent
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
GROUP BY u.name
ORDER BY total_spent DESC;

-- 💠 6. Тест транзакции (пример перевода)
BEGIN;
SELECT * FROM accounts WHERE owner_id IN (1,2) FOR UPDATE;
UPDATE accounts SET balance = balance - 150.00 WHERE owner_id = 1;
UPDATE accounts SET balance = balance + 150.00 WHERE owner_id = 2;
INSERT INTO transactions (from_user, to_user, amount) VALUES (1, 2, 150.00);
COMMIT;

-- 💠 7. Проверка данных
SELECT * FROM accounts ORDER BY owner_id;
SELECT * FROM transactions;

-- ============================================
--  ✅ Готово. База развёрнута.
--  Можно подключаться: \c appdb
--  Пользователь app / пароль app_password
-- ============================================