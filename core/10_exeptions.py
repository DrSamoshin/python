try:
    f = open("demofile.txt")
    try:
        f.write("Lorum Ipsum")
    except:
        print("Something went wrong when writing to the file")
    else:
        print("Nothing went wrong")
    finally:
        f.close()
except:
    print("Something went wrong when opening the file")