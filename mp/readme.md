# threading → multiprocessing

Кое-какие заготовки для перехода с threading на multiprocessing.
Пока не понадобились ввиду достаточной производительности.

### Основная идея

```python3
import multiprocessing as mp
import numpy as np
import ctypes
import time

SHAPE = (240, 320)  # Array shape
TYPE = ctypes.c_uint8  # Array type

def target(arr):
    narr = np.ctypeslib.as_array(arr.get_obj()).reshape(SHAPE)
    for i in range(10, 3, -1):
        print('CHILD READ: [%s]' % narr[0][0])
        narr[0][0] = i
        print('CHILD WRITE: [%s]' % narr[0][0])
        time.sleep(1)

if __name__ == '__main__':
    arr = mp.Array(TYPE, int(np.prod(SHAPE)))
    narr = np.ctypeslib.as_array(arr.get_obj()).reshape(SHAPE)
    proc = mp.Process(target=target, args=(arr,))
    proc.start()

    for i in range(5):
        print('PARENT READ: [%s]' % narr[0][0])
        narr[0][0] = i
        print('PARENT WRITE: [%s]' % narr[0][0])
        time.sleep(1.5)
```