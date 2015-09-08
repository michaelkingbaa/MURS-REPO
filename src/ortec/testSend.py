import struct

def main():
    x=b'\x00'*80

    y=list(x)
    y[1]=b'\x01'
    z=''.join(y)
    print repr(x)
    print repr(z)

    print repr(b'\x00'+b'\x06')

def bitSet(x,off,val):
    x=ord(x)
    mask=1<<off
    x&=~mask
    if val:
        x|=mask
    return chr(x)
        

    
if __name__=="__main__":
    #main()
    i='\x06'
    print repr(i),ord(i)
    #    i=0b11010110
    print 'Starting:  ',bin(ord(i))
    x=bitSet(i,6,1)
    print 'Ending:    ',bin(ord(x))

