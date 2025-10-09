from urllib.parse import urlencode
"""
*args - cобирает не именованные аргументы в tuple
**kwargs - собирает именованные (keyword) аргументы в dict
"""
def run(a, b, *args, **kwargs):
    print("a:", a)
    print("b:", b)
    print("args:", args)
    print("kwargs:", kwargs)


def info(name, age):
    print(name, age)

data = {"name": "Alex", "age": 25}
info(**data)  # распакует словарь в аргументы

# test example
def build_url(base, **params):
    return f"{base}?{urlencode(params)}"

print(build_url("https://example.com", page=2, search="python", sort="desc"))


x = lambda a : a + 10
print(x(5))


x = lambda a, b : a * b
print(x(5, 6))

if __name__=="__main__":
    run(1, 2, 3, 4, x=10, y=20)
