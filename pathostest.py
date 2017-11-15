from pathos.multiprocessing import ProcessingPool as Pool
from itertools import repeat

p = Pool(4)
class Test(object):
    def plus(self, x, y, z): 
        return x,y,z
 
    
x = [2,4,6,8]
y = [1,3,5,7]
z = [3,2,1,0]

t = Test()
temp = p.map(t.plus, repeat(x), y, z)
#[4, 6, 8, 10]
 
#class Foo(object):
#    @staticmethod
#    def work(self, x):
#        return x+1
#
#f = Foo()
#p.apipe(f.work, f, 100)
##<processing.pool.ApplyResult object at 0x10504f8d0>
#res = _
#res.get()
#101