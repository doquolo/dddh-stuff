import multiprocessing as mp
import time

def foo(q):
    q[0] = 1
    # q.put([5, 6, 7, 8])


if __name__ == '__main__':
    arr = mp.Array("i", [])
    ctx = mp.get_context('spawn')
    q = ctx.Queue()
    p = ctx.Process(target=foo, args=(arr,))
    p.start()
    print(arr[:])
    # print(arr.get())
