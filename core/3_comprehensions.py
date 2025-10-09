squares = [x*x for x in range(5)]
evens = [x for x in range(10) if x % 2 == 0]
pairs = [(i, j) for i in range(3) for j in range(2)]
mapping = {c: ord(c) for c in "abc"}
unique = {x % 3 for x in range(10)}

gen = (x*x for x in range(10))
for x in gen:
    print(x)