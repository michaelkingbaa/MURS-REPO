def Get(i):
    if i ==3:
        raise RuntimeError("I got to here")
    return i+1 



i=0
while True:
    i+=1
    print i
    try:
        x=Get(i)
        if x >7:
            break
    except RuntimeError as e:
        print e
        pass
