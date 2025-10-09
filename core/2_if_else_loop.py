# if/else
x = 10
if x > 10:
    ...
elif 5 <= x <= 10:
    ...
else:
    ...

# loop
for y in range(6):
    print(y)

for i, val in enumerate([10, 20, 30], start=1):
    print(i, val)

while x > 0:
    print(x)
    x -= 1

# continue, brake, else
def run():

    # break
    target = 20
    for x in [10, 20, 30]:
        if x == target:
            print("found")
            break
    else:
        print("not found")  # выполнится, если не было break

    # continue
    fruits = ["apple", "banana", "cherry"]
    for f in fruits:
        if f == "banana":
            continue
        print(f)

if __name__=="__main__":
    run()