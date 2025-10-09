"""
with — это контекстный менеджер в Python,
и его смысл — автоматически управлять ресурсами (например: файлы, соединения, блокировки, сессии).
"""

with open("demo.txt", "w") as f:
    f.write("Hello!")
# после выхода из блока with, Python автоматически вызовет f.close(), даже если внутри произошла ошибка.

# свой контекстный менеджер
class FileManager:
    def __init__(self, path):
        self.path = path

    def __enter__(self):
        print("Открываем файл...")
        self.file = open(self.path, "w")
        return self.file

    def __exit__(self, exc_type, exc_value, traceback):
        print("Закрываем файл...")
        self.file.close()

with FileManager("demo.txt") as f:
    f.write("Test data")

# пример работы с DB, with автоматически вызывает conn.commit() и conn.close().
import sqlite3

with sqlite3.connect("db.sqlite") as conn:
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT)")
    cursor.execute("INSERT INTO users (name) VALUES ('Alex')")
# автоматически commit и закрытие соединения


# Можно создать контекстный менеджер из обычной функции:
from contextlib import contextmanager

@contextmanager
def open_file(path, mode):
    f = open(path, mode)
    try:
        yield f
    finally:
        f.close()

with open_file("demo.txt", "w") as f:
    f.write("Hello world!")
