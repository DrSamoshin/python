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