"""
yield в фикстуре — это “точка передачи управления тесту”.
Всё, что выше yield, — подготовка,
всё, что ниже — очистка.

setup()
   ↓
 yield  ←– тест выполняется здесь
   ↓
teardown()
"""


# Без yield (всё сразу)
def get_big_list():
    return [i for i in range(10_000_000)]

# С yield (поэлементно)
def get_big_gen():
    for i in range(10_000_000):
        yield i


def fibonacci(n: int):
    seq = [1, 1]
    for i in range(2, n):
        seq.append(seq[-1] + seq[-2])
    return seq


def fibonacci_gen(n: int):
    a, b = 1, 1
    for _ in range(n):
        yield a
        a, b = b, a + b


if __name__=="__main__":
    print(fibonacci(10))

    gen = fibonacci_gen(5)
    print(gen)
    print(next(gen))
    print(next(gen))
    print(next(gen))
    print(next(gen))
    print(next(gen))