from pathos.multiprocessing import ProcessingPool as Pool

p = Pool(4)
class Test(object):
    def plus(self, x, y): 
        return x+y
 
    
x = [2,4,6,8]
y = [1,3,5,7]

t = Test()
p.map(t.plus, x, y)
[4, 6, 8, 10]
 
class Foo(object):
    @staticmethod
    def work(self, x):
        return x+1

f = Foo()
p.apipe(f.work, f, 100)
#<processing.pool.ApplyResult object at 0x10504f8d0>
res = _
res.get()
101