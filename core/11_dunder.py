class Person:
    # вызываеться при создании объекта
    def __init__(self, name, age, kids):
        self.name = name
        self.age = age
        self.kids = kids

    # вызываеться когда мы запращиваем строковое представление объекта
    def __str__(self):
        return f"{self.name}({self.age})"

    # техническое представление (в отладке, списках и т.п.)
    def __repr__(self):
        return f"Person(name={self.name!r})"

    # поддержка функции len
    def __len__(self):
        return len(self.kids)

    # позволяет складывать объекты
    def __add__(self, other):
        return Person("Family", self.age + other.age, self.kids + other.kids)

    # объект можно перебирать в for, list(), sum(), и т.д.
    def __iter__(self):
        for i in range(0, self.age):
            yield i

    # объект как функция
    def __call__(self):
        return f"Привет, {self.name}!"


p1 = Person("John", 36, ['A', 'B'])
print(p1) # __str__
print([p1]) # __repr__
print(len(p1)) # __len__

p2 = Person("Alex", 42, [])
print(p1 + p2) # __add__
print(list(p1)) # __iter__
print(p1()) # __call__



class FileManager:
    def __init__(self, path):
        self.path = path

    def __enter__(self):
        print("Открываем файл...")
        self.file = open(self.path, "w")
        return self.file

    def __exit__(self, exc_type, exc, tb):
        print("Закрываем файл...")
        self.file.close()

with FileManager("demo.txt") as f:
    f.write("Hello!")