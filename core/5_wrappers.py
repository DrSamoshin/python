
def log_call(func):
    def wrapper(*args, **kwargs):
        print(f"Calling {func.__name__}")
        print(f"args = {args}")
        print(f"kwargs = {kwargs}")

        result = func(*args, **kwargs)

        print(f"Result = {result}")
        print("-" * 30)
        return result
    return wrapper

@log_call
def greet(name, age=None):
    msg = f"Hello, {name}!"
    if age:
        msg += f" You are {age} years old."
    return msg

# # simple calling
# wrapper_greet = log_call(greet)
# wrapper_greet("Sergey", age=34)
# # call with decorator
# greet("Alex", age=25)


import time

def timeit(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        func(*args, **kwargs)
        end = time.time()
        return f"{func.__name__} was done in {end - start:.4f} sec."
    return wrapper

@timeit
def slow_func():
    time.sleep(1)

# print(slow_func())

def repeat(n, name):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for _ in range(n):
                func(*args, **kwargs)
                print(name)
        return wrapper
    return decorator

@repeat(3, "Sergey")
def say_hi():
    print("Hi!")

# # simple calling
# decorator_say_hi = repeat(3, name="Sergey")
# wrapper_say_hi = decorator_say_hi(say_hi)
# wrapper_say_hi()
# # call with decorator
# say_hi()


import time

def timing_decorator(print_time=True):
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            if print_time:
                end_time = time.time()
                elapsed_time = end_time - start_time
                print(f"Elapsed time: {elapsed_time:.2f} seconds")
            return result
        return wrapper
    return decorator


@timing_decorator(print_time=True)
def add(a1, b1):
    time.sleep(2)
    return a1 + b1


print(add(3, 4))