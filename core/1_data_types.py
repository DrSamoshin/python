from decimal import Decimal

# text type
text: str = "hello"
'''
slice: "hello"[1:4] -> "ell"
methods: .split(), .join(), .strip(), .replace(), .lower().
f-str: f"Hi {name}".
'''

# numeric type
x: int = 1
y: float = 3.12
z: Decimal = Decimal("0.3") # нужени для точных вычислений

# list, tuple, range, set
a: list = [100, "str", ["str", "str_2"]]
'''
.append, .extend, .insert, .pop, .remove, .sort, .reverse
Сортировка «в месте» возвращает None: xs.sort(); для копии — sorted(xs).
'''

b: range = range(6)
c, d = (100, "str")
e: set = {100, 200, 100} # {200, 100}

# dict - хэш таблица
f: dict = {1: "str_1", 2: "str_2"}
g: dict = {"str_1": 1, 2: "str_2"} # ключами могут быть типы которые можно хешировать

# bool
h: bool = True

# None
i: None = None


def run():
    print(i)

if __name__ == "__main__":
    run()
