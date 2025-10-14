-- 2.1 Создаём базу и роль
CREATE DATABASE appdb;
CREATE ROLE app WITH LOGIN PASSWORD 'app_password';

-- 2.2 Права
GRANT ALL PRIVILEGES ON DATABASE appdb TO app;

-- 2.3 Переключаемся в новую базу
\c appdb

-- 2.4 (Опционально) схема
CREATE SCHEMA IF NOT EXISTS app AUTHORIZATION app;
SET search_path TO app, public;

-- 2.5 Разрешения в схеме
GRANT USAGE, CREATE ON SCHEMA app TO app;




-- 3.1 Пользователи
CREATE TABLE app.users (
  id        SERIAL PRIMARY KEY,
  name      TEXT        NOT NULL,
  age       INT         NOT NULL CHECK (age >= 0),
  city      TEXT        NOT NULL
);

-- 3.2 Заказы
CREATE TABLE app.orders (
  id         SERIAL PRIMARY KEY,
  user_id    INT NOT NULL REFERENCES app.users(id) ON DELETE CASCADE,
  amount     NUMERIC(10,2) NOT NULL CHECK (amount >= 0),
  created_at TIMESTAMPTZ   NOT NULL DEFAULT now()
);

-- Индексы (ускорим частые выборки)
CREATE INDEX idx_users_city      ON app.users(city);
CREATE INDEX idx_orders_user_id  ON app.orders(user_id);

-- 3.3 Счета (для демонстрации транзакций и блокировок)
CREATE TABLE app.accounts (
  id        SERIAL PRIMARY KEY,
  owner_id  INT NOT NULL REFERENCES app.users(id) ON DELETE CASCADE,
  balance   NUMERIC(12,2) NOT NULL CHECK (balance >= 0)
);

INSERT INTO app.users (name, age, city) VALUES
  ('Alice', 25, 'London'),
  ('Bob',   32, 'Paris'),
  ('Carol', 29, 'Berlin'),
  ('David', 40, 'London'),
  ('Emma',  35, 'Paris');

INSERT INTO app.orders (user_id, amount) VALUES
  (1, 100.00),  -- Alice
  (2, 150.00),  -- Bob
  (1,  50.00),  -- Alice
  (5, 200.00);  -- Emma

INSERT INTO app.accounts (owner_id, balance) VALUES
  (1, 1000.00),   -- Alice
  (2,  200.00),   -- Bob
  (3,  500.00),   -- Carol
  (4, 1500.00),   -- David
  (5,  300.00);   -- Emma

SELECT * FROM app.users;
SELECT * FROM app.orders;
SELECT * FROM app.accounts;





-- все пользователи
SELECT * FROM app.users;

-- фильтр по условию
SELECT name, age FROM app.users WHERE city = 'London';

-- логика AND/OR
SELECT * FROM app.users WHERE age > 30 AND city = 'Paris';

-- сортировка
SELECT * FROM app.users ORDER BY age DESC;

-- ограничение строк
SELECT * FROM app.users ORDER BY id LIMIT 3;





-- количество пользователей в каждом городе
SELECT city, COUNT(*) AS cnt
FROM app.users
GROUP BY city
ORDER BY cnt DESC;

-- средний возраст по городам
SELECT city, AVG(age) AS avg_age
FROM app.users
GROUP BY city;

-- пользователи только из городов, где людей больше 1
SELECT city, COUNT(*) AS cnt
FROM app.users
GROUP BY city
HAVING COUNT(*) > 1;




-- 7.1 INNER JOIN: только те, у кого есть заказы
SELECT u.name, o.amount, o.created_at
FROM app.users u
JOIN app.orders o ON u.id = o.user_id
ORDER BY o.created_at;

-- 7.2 LEFT JOIN: все пользователи + (если есть) их заказы
SELECT u.name, o.amount
FROM app.users u
LEFT JOIN app.orders o ON u.id = o.user_id
ORDER BY u.name;

-- 7.3 Агрегация с JOIN: сумма заказов на пользователя
SELECT u.name, COALESCE(SUM(o.amount), 0) AS total_spent
FROM app.users u
LEFT JOIN app.orders o ON u.id = o.user_id
GROUP BY u.name
ORDER BY total_spent DESC;

-- 7.4 Мульти-условие в JOIN (пример)
SELECT u.name, u.city, o.id AS order_id, o.amount
FROM app.users u
JOIN app.orders o ON u.id = o.user_id AND o.amount >= 100;





-- 8.1 INSERT
INSERT INTO app.users (name, age, city) VALUES ('Frank', 28, 'Rome');

-- 8.2 UPDATE (всегда помни про WHERE!)
UPDATE app.users
SET age = 29, city = 'Milan'
WHERE name = 'Frank';

-- 8.3 DELETE
DELETE FROM app.users
WHERE name = 'Frank';





BEGIN;

-- найдём нужные счета и заблокируем строки
SELECT id, owner_id, balance FROM app.accounts WHERE owner_id = 1 FOR UPDATE; -- Alice
SELECT id, owner_id, balance FROM app.accounts WHERE owner_id = 2 FOR UPDATE; -- Bob

-- проверим баланс (проверка на стороне клиента или с помощью CHECK/триггера)
-- уменьшаем у Alice
UPDATE app.accounts
SET balance = balance - 150.00
WHERE owner_id = 1;

-- увеличиваем у Bob
UPDATE app.accounts
SET balance = balance + 150.00
WHERE owner_id = 2;

-- убедимся, что баланс Alice не ушёл в минус
-- (если такой риск есть, можно проверять и откатывать)
-- SELECT balance FROM app.accounts WHERE owner_id = 1;

COMMIT;






BEGIN;

SELECT id, owner_id, balance FROM app.accounts WHERE owner_id = 2 FOR UPDATE; -- Bob
SELECT id, owner_id, balance FROM app.accounts WHERE owner_id = 3 FOR UPDATE; -- Carol

-- попытаемся снять больше, чем есть у Bob (допустим у него 350.00, а снимем 1000.00)
UPDATE app.accounts SET balance = balance - 1000.00 WHERE owner_id = 2;

-- эта операция нарушит CHECK (balance >= 0) при COMMIT (в некоторых СУБД — сразу)
-- лучше самим проверить и откатить:
SELECT balance FROM app.accounts WHERE owner_id = 2;

-- обнаружили проблему → откатываем
ROLLBACK;





BEGIN;

-- заблокируем и начнём сложную последовательность операций
SELECT id FROM app.accounts WHERE owner_id IN (1,2) FOR UPDATE;

-- шаг 1
UPDATE app.accounts SET balance = balance - 50 WHERE owner_id = 1;
SAVEPOINT step1_done;

-- шаг 2 (что-то пошло не так)
UPDATE app.accounts SET balance = balance - 1000 WHERE owner_id = 2;

-- откатываемся только к savepoint
ROLLBACK TO SAVEPOINT step1_done;

-- продолжаем чем-то ещё безопасным
UPDATE app.accounts SET balance = balance + 10 WHERE owner_id = 1;

COMMIT;



SELECT DISTINCT city FROM users ORDER BY city; == SELECT city FROM users GROUP BY city;